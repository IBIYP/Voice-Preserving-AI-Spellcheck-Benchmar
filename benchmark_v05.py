#!/usr/bin/env python3
"""Evaluate a frozen v0.5 four-pillar anchor cache; draft protocols cannot be scored."""

import hashlib
import json
import math
from datetime import datetime
from pathlib import Path

from correction_site_diagnostic import score_target_accuracy
from text_matching import aggregate_writer_voice, contains_phrase, score_writer_voice


ROOT = Path(__file__).parent
PROTOCOL_PATH = ROOT / "benchmark_data" / "v0.5_anchor_draft.json"
RAW_RESULTS_PATH = ROOT / "raw_results" / "v0.5_anchor_runs.json"
OUTPUT_PATH = ROOT / "raw_results" / "v0.5_anchor_eval.json"
LOCALES = ("en-US", "en-GB")
PILLAR_WEIGHTS = {
    "spelling": 25,
    "grammar": 25,
    "voice": 25,
    "negative_control_preservation": 25,
}
PASSAGE_IDS = tuple(f"V05-{index:02d}" for index in range(1, 11))


def _read_json(path):
    with Path(path).open("r", encoding="utf-8") as file:
        return json.load(file)


def _sha256_text(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _stable_digest(value):
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _parse_utc_timestamp(value, field):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a timezone-aware ISO 8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(
            f"{field} must be a timezone-aware ISO 8601 timestamp"
        ) from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must include a UTC offset")
    if parsed.utcoffset().total_seconds() != 0:
        raise ValueError(f"{field} must use UTC")
    return parsed


def _sample_records(protocol):
    return {
        f'{passage["id"]}-{locale}': {
            "passage": passage,
            "locale": locale,
            "input": passage["inputs"][locale],
        }
        for passage in protocol["passages"]
        for locale in LOCALES
    }


def _validate_protocol(protocol, require_frozen=False):
    if not isinstance(protocol, dict) or not isinstance(protocol.get("metadata"), dict):
        raise ValueError("v0.5 protocol must be a JSON object with metadata")
    metadata = protocol["metadata"]
    if metadata.get("status") not in ("draft", "frozen"):
        raise ValueError("v0.5 protocol status must be draft or frozen")
    if require_frozen and metadata.get("status") != "frozen":
        raise ValueError("v0.5 protocol is a draft; review and freeze it before scoring")
    if not isinstance(metadata.get("protocol_version"), str) or not metadata[
        "protocol_version"
    ]:
        raise ValueError("v0.5 protocol_version is required")
    if require_frozen and metadata["protocol_version"].endswith("-draft"):
        raise ValueError("Update protocol_version when freezing the v0.5 protocol")
    if metadata.get("locale_mode") != "automatic detection; do not force a locale":
        raise ValueError("v0.5 protocol must require automatic locale detection")

    scoring = protocol.get("scoring")
    if not isinstance(scoring, dict) or scoring.get("weights") != PILLAR_WEIGHTS:
        raise ValueError("v0.5 scoring must use four equal 25% pillars")
    if scoring.get("control_matching") != "case-insensitive exact phrase with word boundaries":
        raise ValueError("Unsupported negative-control matching rule")
    if scoring.get("known_control_hits_are_hallucination_labels") is not False:
        raise ValueError("Known control hits must not be labelled hallucinations")
    if scoring.get("unlisted_or_approximate_changes_are_scored_as_hallucinations") is not False:
        raise ValueError("Unlisted or approximate changes must not be labelled hallucinations")
    weekly_challenge = protocol.get("weekly_challenge")
    if (
        not isinstance(weekly_challenge, dict)
        or not isinstance(weekly_challenge.get("comparison_rule"), str)
        or not weekly_challenge["comparison_rule"]
    ):
        raise ValueError("v0.5 protocol must define its weekly-challenge comparison rule")

    passages = protocol.get("passages")
    expected_ids = set(PASSAGE_IDS)
    if not isinstance(passages, list) or len(passages) != len(expected_ids):
        raise ValueError("v0.5 protocol must define exactly V05-01 through V05-10")
    if any(not isinstance(passage, dict) for passage in passages):
        raise ValueError("Every v0.5 passage must be an object")
    if {passage.get("id") for passage in passages} != expected_ids:
        raise ValueError("v0.5 protocol must define exactly V05-01 through V05-10")

    control_ids = set()
    for passage in passages:
        passage_id = passage["id"]
        inputs = passage.get("inputs")
        locale_cue = passage.get("locale_cue")
        targets = passage.get("locale_spelling_targets")
        dialects = passage.get("dialect_equivalents")
        grammar_targets = passage.get("grammar_targets")
        voice_tokens = passage.get("voice_tokens")
        forbidden_rewrites = passage.get("forbidden_rewrites")
        control = passage.get("negative_control")
        if not isinstance(passage.get("domain"), str) or not passage["domain"]:
            raise ValueError(f"{passage_id} must have a domain")
        if not isinstance(inputs, dict) or set(inputs) != set(LOCALES):
            raise ValueError(f"{passage_id} must have exactly en-US and en-GB inputs")
        if not isinstance(locale_cue, dict) or set(locale_cue) != set(LOCALES):
            raise ValueError(f"{passage_id} must define a cue for each locale")
        if (
            not isinstance(locale_cue.get("en-US"), str)
            or not isinstance(locale_cue.get("en-GB"), str)
            or locale_cue["en-US"].casefold() == locale_cue["en-GB"].casefold()
        ):
            raise ValueError(f"{passage_id} locale cues must be distinct")
        if (
            not isinstance(targets, dict)
            or set(targets) != set(LOCALES)
            or any(not isinstance(targets[locale], dict) or not targets[locale] for locale in LOCALES)
        ):
            raise ValueError(f"{passage_id} must have spelling targets for both locales")
        if not isinstance(dialects, dict):
            raise ValueError(f"{passage_id} dialect_equivalents must be an object")
        if not isinstance(grammar_targets, dict):
            raise ValueError(f"{passage_id} grammar_targets must be an object")
        if not isinstance(voice_tokens, list) or not voice_tokens:
            raise ValueError(f"{passage_id} voice_tokens must be a non-empty list")
        if not isinstance(forbidden_rewrites, list):
            raise ValueError(f"{passage_id} forbidden_rewrites must be a list")
        if not isinstance(control, dict):
            raise ValueError(f"{passage_id} must define one negative control")
        control_id = control.get("id")
        if not isinstance(control_id, str) or not control_id.strip() or control_id in control_ids:
            raise ValueError("Negative-control IDs must be unique non-empty strings")
        control_ids.add(control_id)

        for locale in LOCALES:
            input_text = inputs[locale]
            locale_targets = targets[locale]
            if not isinstance(input_text, str) or not input_text.strip():
                raise ValueError(f"{passage_id} has an empty {locale} input")
            cue = locale_cue[locale]
            if (
                not isinstance(cue, str)
                or not cue
                or not contains_phrase(input_text, cue)
                or targets[locale].get(cue) != cue
            ):
                raise ValueError(f"{passage_id} has an invalid {locale} dialect cue")
            if not isinstance(locale_targets, dict):
                raise ValueError(f"{passage_id} {locale} targets must be an object")
            for source, target in locale_targets.items():
                if (
                    not isinstance(source, str)
                    or not source
                    or not isinstance(target, str)
                    or not target
                    or not contains_phrase(input_text, source)
                ):
                    raise ValueError(
                        f"Invalid or absent spelling target {source!r} in "
                        f"{passage_id} {locale}"
                    )
            for source, target in grammar_targets.items():
                if (
                    not isinstance(source, str)
                    or not source
                    or not isinstance(target, str)
                    or not target
                    or not contains_phrase(input_text, source)
                ):
                    raise ValueError(
                        f"Invalid or absent grammar target {source!r} in "
                        f"{passage_id} {locale}"
                    )
            if any(not isinstance(marker, str) or not marker for marker in voice_tokens):
                raise ValueError(f"{passage_id} has invalid voice markers")
        for canonical, variants in dialects.items():
            candidates = [variants] if isinstance(variants, str) else variants
            if (
                not isinstance(canonical, str)
                or not canonical
                or not isinstance(candidates, list)
                or not candidates
                or any(not isinstance(item, str) or not item for item in candidates)
            ):
                raise ValueError(f"{passage_id} has invalid dialect equivalents")
        if any(not isinstance(item, str) or not item for item in forbidden_rewrites):
            raise ValueError(f"{passage_id} has invalid forbidden rewrites")

        protected_span = control.get("protected_span")
        false_forms = control.get("known_false_forms")
        if not isinstance(protected_span, str) or not protected_span:
            raise ValueError(f"{control_id} protected_span must be a non-empty string")
        if not isinstance(false_forms, list) or not false_forms:
            raise ValueError(f"{control_id} must define known_false_forms")
        for locale in LOCALES:
            if not contains_phrase(inputs[locale], protected_span):
                raise ValueError(
                    f"{control_id} protected span is absent from {passage_id} {locale}"
                )
        for false_form in false_forms:
            if (
                not isinstance(false_form, dict)
                or not isinstance(false_form.get("text"), str)
                or not false_form["text"]
                or not isinstance(false_form.get("basis"), str)
                or not false_form["basis"]
            ):
                raise ValueError(f"{control_id} has an invalid known false form")
            if contains_phrase(protected_span, false_form["text"]):
                raise ValueError(f"{control_id} false form duplicates its protected span")
        if not isinstance(control.get("why_wrong"), str) or not control["why_wrong"]:
            raise ValueError(f"{control_id} must explain why the control matters")

    return protocol


def _validate_raw_runs(raw_results, protocol):
    _validate_protocol(protocol, require_frozen=True)
    if not isinstance(raw_results, dict):
        raise ValueError("v0.5 raw results must be a JSON object")
    metadata = raw_results.get("metadata")
    if not isinstance(metadata, dict) or metadata.get("status") != "complete":
        raise ValueError("v0.5 raw results must be marked complete")
    if metadata.get("protocol_version") != protocol["metadata"]["protocol_version"]:
        raise ValueError("Raw results use a different v0.5 protocol version")
    if metadata.get("protocol_sha256") != _stable_digest(protocol):
        raise ValueError("Raw results do not match the frozen protocol digest")
    if metadata.get("locale_mode") != "automatic":
        raise ValueError("Raw results must use automatic locale detection")

    frozen_at = _parse_utc_timestamp(
        metadata.get("control_set_frozen_at_utc"), "control_set_frozen_at_utc"
    )
    collected_at = _parse_utc_timestamp(
        metadata.get("collection_started_at_utc"), "collection_started_at_utc"
    )
    if collected_at <= frozen_at:
        raise ValueError("Collection must start after the controls are frozen")

    engine_metadata = metadata.get("engine_metadata")
    if not isinstance(engine_metadata, dict) or not engine_metadata:
        raise ValueError("Raw results must include engine provenance metadata")
    for engine, details in engine_metadata.items():
        if not isinstance(engine, str) or not engine.strip() or not isinstance(details, dict):
            raise ValueError("Invalid engine provenance metadata")
        for field in ("product_version", "collection_route", "source_url"):
            if not isinstance(details.get(field), str) or not details[field].strip():
                raise ValueError(f"Missing {field} for {engine}")
        if details.get("locale_setting") not in ("auto-detect", "not-set"):
            raise ValueError(
                f"{engine} must record auto-detect or not-set locale handling"
            )

    outputs = raw_results.get("outputs")
    expected_samples = _sample_records(protocol)
    if not isinstance(outputs, dict) or set(outputs) != set(expected_samples):
        missing = sorted(set(expected_samples) - set(outputs or {}))
        unexpected = sorted(set(outputs or {}) - set(expected_samples))
        raise ValueError(
            f"v0.5 sample coverage mismatch; missing={missing}, unexpected={unexpected}"
        )
    expected_engines = set(engine_metadata)
    for sample_id, sample in expected_samples.items():
        result = outputs[sample_id]
        if not isinstance(result, dict):
            raise ValueError(f"Missing output record for {sample_id}")
        if result.get("input_sha256") != _sha256_text(sample["input"]):
            raise ValueError(f"Input hash mismatch for {sample_id}")
        engine_outputs = result.get("engine_outputs")
        if not isinstance(engine_outputs, dict) or set(engine_outputs) != expected_engines:
            actual = set(engine_outputs) if isinstance(engine_outputs, dict) else set()
            missing = sorted(expected_engines - actual)
            unexpected = sorted(actual - expected_engines)
            raise ValueError(
                f"Engine coverage mismatch for {sample_id}; missing={missing}, "
                f"unexpected={unexpected}"
            )
        for engine, run in engine_outputs.items():
            if not isinstance(run, dict) or not isinstance(run.get("text"), str) or not run["text"].strip():
                raise ValueError(f"Missing valid output text for {engine} on {sample_id}")
            latency = run.get("latency_ms")
            if latency is not None and (
                isinstance(latency, bool)
                or not isinstance(latency, (int, float))
                or not math.isfinite(latency)
                or latency < 0
            ):
                raise ValueError(f"Invalid latency for {engine} on {sample_id}")
    return raw_results


def _control_result(control, output_text):
    hit = next(
        (
            false_form["text"]
            for false_form in control["known_false_forms"]
            if contains_phrase(output_text, false_form["text"])
        ),
        None,
    )
    if hit is not None:
        return {
            "classification": "known_negative_control_hit",
            "score": 0.0,
            "matched_false_form": hit,
        }
    if contains_phrase(output_text, control["protected_span"]):
        return {
            "classification": "preserved",
            "score": 100.0,
            "matched_false_form": None,
        }
    return {
        "classification": "unclassified_change",
        "score": 0.0,
        "matched_false_form": None,
    }


def _evaluate_sample(passage, locale, output_text):
    input_text = passage["inputs"][locale]
    locale_targets = passage["locale_spelling_targets"][locale]
    dialect_equivalents = {}
    for canonical, variants in passage["dialect_equivalents"].items():
        variants = [variants] if isinstance(variants, str) else list(variants)
        dialect_equivalents[canonical] = list(
            dict.fromkeys([canonical] + variants)
        )

    spelling = score_target_accuracy(
        input_text,
        output_text,
        locale_targets,
        include_identity_only=True,
    )
    grammar = score_target_accuracy(
        input_text, output_text, passage["grammar_targets"]
    )
    voice = score_writer_voice(
        input_text,
        output_text,
        locale_targets,
        passage["grammar_targets"],
        passage["voice_tokens"],
        dialect_equivalents,
        passage["forbidden_rewrites"],
    )
    return {
        "spelling_acc": spelling["accuracy"],
        "spelling_target_hits": spelling["accepted_targets"],
        "spelling_target_count": spelling["total_targets"],
        "grammar_acc": grammar["accuracy"],
        "grammar_target_hits": grammar["accepted_targets"],
        "grammar_target_count": grammar["total_targets"],
        "voice_preservation": voice["score"],
        "voice_precision": voice["precision"],
        "voice_recall": voice["recall"],
        "voice_lexical_f1": voice["lexical_f1"],
        "voice_marker_retention": voice["voice_marker_retention"],
        "voice_over_edit_count": voice["over_edit_count"],
    }


def score_runs(protocol, raw_results):
    _validate_raw_runs(raw_results, protocol)
    samples = _sample_records(protocol)
    engines = raw_results["metadata"]["engine_metadata"]
    per_engine = {
        engine: {
            "spelling_hits": 0,
            "spelling_targets": 0,
            "grammar_hits": 0,
            "grammar_targets": 0,
            "voice_metrics": [],
            "controls": [],
            "passages": [],
        }
        for engine in engines
    }

    for sample_id, sample in samples.items():
        run = raw_results["outputs"][sample_id]["engine_outputs"]
        for engine in engines:
            output_text = run[engine]["text"]
            metrics = _evaluate_sample(sample["passage"], sample["locale"], output_text)
            control = _control_result(
                sample["passage"]["negative_control"], output_text
            )
            aggregate = per_engine[engine]
            aggregate["spelling_hits"] += metrics["spelling_target_hits"]
            aggregate["spelling_targets"] += metrics["spelling_target_count"]
            aggregate["grammar_hits"] += metrics["grammar_target_hits"]
            aggregate["grammar_targets"] += metrics["grammar_target_count"]
            aggregate["voice_metrics"].append(
                {
                    "score": metrics["voice_preservation"],
                    "lexical_f1": metrics["voice_lexical_f1"],
                    "voice_marker_retention": metrics["voice_marker_retention"],
                    "over_edit_count": metrics["voice_over_edit_count"],
                }
            )
            aggregate["controls"].append(control)
            aggregate["passages"].append(
                {
                    "sample_id": sample_id,
                    "locale": sample["locale"],
                    "negative_control_id": sample["passage"]["negative_control"]["id"],
                    "metrics": metrics,
                    "negative_control": control,
                    "output_text": output_text,
                }
            )

    summary = {}
    for engine, aggregate in per_engine.items():
        spelling = (
            100.0 * aggregate["spelling_hits"] / aggregate["spelling_targets"]
            if aggregate["spelling_targets"]
            else 100.0
        )
        grammar = (
            100.0 * aggregate["grammar_hits"] / aggregate["grammar_targets"]
            if aggregate["grammar_targets"]
            else 100.0
        )
        voice = aggregate_writer_voice(aggregate["voice_metrics"])["score"]
        preserved = sum(
            result["classification"] == "preserved"
            for result in aggregate["controls"]
        )
        control_count = len(aggregate["controls"])
        control_score = 100.0 * preserved / control_count if control_count else 100.0
        pillars = {
            "spelling": round(spelling, 2),
            "grammar": round(grammar, 2),
            "voice": round(voice, 2),
            "negative_control_preservation": round(control_score, 2),
        }
        summary[engine] = {
            "pillars": pillars,
            "weights": PILLAR_WEIGHTS.copy(),
            "overall_score": round(
                sum(pillars[name] * PILLAR_WEIGHTS[name] for name in PILLAR_WEIGHTS)
                / 100.0,
                2,
            ),
            "spelling_targets": {
                "hits": aggregate["spelling_hits"],
                "total": aggregate["spelling_targets"],
            },
            "grammar_targets": {
                "hits": aggregate["grammar_hits"],
                "total": aggregate["grammar_targets"],
            },
            "negative_controls": {
                "preserved": preserved,
                "known_negative_control_hits": sum(
                    result["classification"] == "known_negative_control_hit"
                    for result in aggregate["controls"]
                ),
                "unclassified_changes": sum(
                    result["classification"] == "unclassified_change"
                    for result in aggregate["controls"]
                ),
                "total": control_count,
            },
            "passages": aggregate["passages"],
        }

    return {
        "metadata": {
            "protocol_version": protocol["metadata"]["protocol_version"],
            "protocol_sha256": _stable_digest(protocol),
            "status": "scored",
            "control_set_frozen_at_utc": raw_results["metadata"][
                "control_set_frozen_at_utc"
            ],
            "collection_started_at_utc": raw_results["metadata"][
                "collection_started_at_utc"
            ],
            "engine_metadata": raw_results["metadata"]["engine_metadata"],
            "sample_count": len(samples),
            "comparison_note": protocol["weekly_challenge"]["comparison_rule"],
        },
        "engine_summary": summary,
    }


def run_evaluation(
    protocol_path=PROTOCOL_PATH,
    raw_path=RAW_RESULTS_PATH,
    output_path=OUTPUT_PATH,
):
    protocol = _validate_protocol(_read_json(protocol_path), require_frozen=True)
    report = score_runs(protocol, _read_json(raw_path))
    with Path(output_path).open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, ensure_ascii=False)
    print(f"Saved v0.5 evaluation results to {output_path}")
    return report


if __name__ == "__main__":
    run_evaluation()
