"""Score paired en-US and en-GB H-suite runs from a complete cached result file."""

import json
import math
from pathlib import Path

from benchmark_4pillars_hybrid import (
    ENGINES,
    UNSEEN_BENCHMARK_UNITS,
    _mean_recorded_latency,
    _stable_digest,
    evaluate_unit,
)
from text_matching import VOICE_SCORING_REVISION, aggregate_writer_voice


ROOT = Path(__file__).parent
LOCALES = ("en-US", "en-GB")
RAW_RESULTS_PATH = ROOT / "raw_results" / "h_suite_locale_runs_v1.json"
GOLDEN_TEXTS_PATH = ROOT / "raw_results" / "h_suite_locale_golden_texts.json"
OUTPUT_PATH = ROOT / "raw_results" / "h_suite_locale_eval_v1.json"


def _validate_locale_runs(results):
    if not isinstance(results, dict):
        raise ValueError("Locale run cache must be a JSON object")
    metadata = results.get("metadata")
    if not isinstance(metadata, dict) or metadata.get("status") != "complete":
        raise ValueError("Locale run cache must be marked complete")

    locale_runs = results.get("locale_runs")
    if not isinstance(locale_runs, dict) or set(locale_runs) != set(LOCALES):
        raise ValueError("Locale run cache must contain exactly en-US and en-GB")

    expected_ids = {unit["id"] for unit in UNSEEN_BENCHMARK_UNITS}
    for locale in LOCALES:
        locale_run = locale_runs[locale]
        if not isinstance(locale_run, dict) or locale_run.get("locale") != locale:
            raise ValueError(f"Locale run metadata must identify {locale}")
        passages = locale_run.get("passages")
        if not isinstance(passages, dict) or set(passages) != expected_ids:
            missing = sorted(expected_ids - set(passages or {}))
            unexpected = sorted(set(passages or {}) - expected_ids)
            raise ValueError(
                f"{locale} passage coverage mismatch; missing={missing}, "
                f"unexpected={unexpected}"
            )
        for passage_id, passage_runs in passages.items():
            if not isinstance(passage_runs, dict) or set(passage_runs) != set(ENGINES):
                actual = set(passage_runs) if isinstance(passage_runs, dict) else set()
                missing = sorted(set(ENGINES) - actual)
                unexpected = sorted(actual - set(ENGINES))
                raise ValueError(
                    f"{locale} engine coverage mismatch on {passage_id}; "
                    f"missing={missing}, unexpected={unexpected}"
                )
            for engine, run in passage_runs.items():
                if (
                    not isinstance(run, dict)
                    or not isinstance(run.get("text"), str)
                    or not run["text"].strip()
                ):
                    raise ValueError(
                        f"{locale} result is missing valid text for {engine} "
                        f"on {passage_id}"
                    )
                latency = run.get("lat")
                if latency is not None and (
                    isinstance(latency, bool)
                    or not isinstance(latency, (int, float))
                    or not math.isfinite(latency)
                    or latency < 0
                ):
                    raise ValueError(
                        f"Invalid {locale} latency for {engine} on "
                        f"{passage_id}: {latency}"
                    )


def _locale_targets(golden_texts, locale):
    target_sets = golden_texts["metadata"].get("locale_spelling_targets")
    if not isinstance(target_sets, dict):
        raise ValueError("Golden references are missing locale_spelling_targets")
    targets = {}
    for passage_id, mapping in target_sets.items():
        if passage_id not in {unit["id"] for unit in UNSEEN_BENCHMARK_UNITS}:
            raise ValueError(f"Unexpected locale target passage: {passage_id}")
        if not isinstance(mapping, dict):
            raise ValueError(f"Invalid locale targets for {passage_id}")
        targets[passage_id] = {}
        for source, forms in mapping.items():
            if not isinstance(forms, dict) or not isinstance(forms.get(locale), str):
                raise ValueError(
                    f"Missing {locale} spelling form for {passage_id}: {source}"
                )
            targets[passage_id][source] = forms[locale]
    return targets


def _score_locale(locale, locale_run, locale_targets):
    per_engine = {
        engine: {
            "spelling_target_hits": 0,
            "spelling_target_count": 0,
            "grammar_target_hits": 0,
            "grammar_target_count": 0,
            "voice_metrics": [],
            "diagnostic_sites": [],
        }
        for engine in ENGINES
    }
    passages = []

    for unit in UNSEEN_BENCHMARK_UNITS:
        passage_id = unit["id"]
        passage_scores = {"id": passage_id, "domain": unit["domain"], "scores": {}}
        for engine in ENGINES:
            run = locale_run["passages"][passage_id][engine]
            metrics = evaluate_unit(
                unit,
                run["text"],
                locale=locale,
                locale_spelling_targets=locale_targets.get(passage_id, {}),
            )
            totals = per_engine[engine]
            totals["spelling_target_hits"] += metrics["spelling_target_hits"]
            totals["spelling_target_count"] += metrics["spelling_target_count"]
            totals["grammar_target_hits"] += metrics["grammar_target_hits"]
            totals["grammar_target_count"] += metrics["grammar_target_count"]
            totals["voice_metrics"].append(
                {
                    "score": metrics["voice_preservation"],
                    "lexical_f1": metrics["voice_lexical_f1"],
                    "voice_marker_retention": metrics["voice_marker_retention"],
                    "over_edit_count": metrics["voice_over_edit_count"],
                }
            )
            totals["diagnostic_sites"].extend(
                metrics["correction_site_diagnostic"]["sites"]
            )
            passage_scores["scores"][engine] = {
                "text": run["text"],
                "metrics": metrics,
            }
        passages.append(passage_scores)

    summary = {}
    for engine, totals in per_engine.items():
        voice = aggregate_writer_voice(totals["voice_metrics"])
        spelling_count = totals["spelling_target_count"]
        grammar_count = totals["grammar_target_count"]
        spelling_accuracy = (
            round(totals["spelling_target_hits"] / spelling_count * 100, 1)
            if spelling_count
            else 100.0
        )
        grammar_accuracy = (
            round(totals["grammar_target_hits"] / grammar_count * 100, 1)
            if grammar_count
            else 100.0
        )
        sites = totals["diagnostic_sites"]
        unapproved = sum(
            site["classification"] == "unapproved_edit" for site in sites
        )
        unchanged = sum(site["classification"] == "unchanged" for site in sites)
        accepted = sum(
            site["classification"] == "accepted_correction" for site in sites
        )
        applicable = len(sites)
        latency, latency_samples = _mean_recorded_latency(
            locale_run["passages"], engine
        )
        summary[engine] = {
            "spelling_accuracy": spelling_accuracy,
            "spelling_accepted_targets": totals["spelling_target_hits"],
            "spelling_total_targets": spelling_count,
            "grammar_accuracy": grammar_accuracy,
            "grammar_accepted_targets": totals["grammar_target_hits"],
            "grammar_total_targets": grammar_count,
            "voice_preservation": voice["score"],
            "voice_lexical_f1": voice["lexical_f1"],
            "voice_marker_retention": voice["voice_marker_retention"],
            "voice_over_edit_count": voice["over_edit_count"],
            "voice_over_edit_penalty": voice["over_edit_penalty"],
            "correction_site_diagnostic": {
                "applicable_sites": applicable,
                "unchanged_sites": unchanged,
                "accepted_corrections": accepted,
                "unapproved_edits": unapproved,
                "unapproved_edit_rate": (
                    round(unapproved / applicable * 100, 1) if applicable else None
                ),
            },
            "quality_composite": round(
                0.4375 * spelling_accuracy
                + 0.3125 * grammar_accuracy
                + 0.25 * voice["score"],
                1,
            ),
            "latency_ms": latency,
            "latency_samples": latency_samples,
        }

    for engine, result in summary.items():
        penalty_factor = 1.0 - result["voice_over_edit_penalty"] / 100.0
        for passage in passages:
            metrics = passage["scores"][engine]["metrics"]
            metrics["voice_base_score"] = metrics["voice_preservation"]
            metrics["voice_over_edit_penalty"] = result["voice_over_edit_penalty"]
            metrics["voice_preservation"] = round(
                metrics["voice_base_score"] * penalty_factor, 2
            )
            metrics["quality_composite"] = round(
                0.4375 * metrics["spelling_acc"]
                + 0.3125 * metrics["grammar_acc"]
                + 0.25 * metrics["voice_preservation"],
                2,
            )
    return {"engine_summary": summary, "passages": passages}


def run_evaluation(raw_path=RAW_RESULTS_PATH, output_path=OUTPUT_PATH):
    with Path(raw_path).open("r", encoding="utf-8") as file:
        raw_results = json.load(file)
    _validate_locale_runs(raw_results)
    with GOLDEN_TEXTS_PATH.open("r", encoding="utf-8") as file:
        golden_texts = json.load(file)

    locale_scores = {}
    for locale in LOCALES:
        locale_scores[locale] = _score_locale(
            locale,
            raw_results["locale_runs"][locale],
            _locale_targets(golden_texts, locale),
        )

    paired_changes = {}
    for engine in ENGINES:
        us = locale_scores["en-US"]["engine_summary"][engine]
        gb = locale_scores["en-GB"]["engine_summary"][engine]
        paired_changes[engine] = {
            metric: round(gb[metric] - us[metric], 1)
            for metric in (
                "spelling_accuracy",
                "grammar_accuracy",
                "voice_preservation",
                "quality_composite",
            )
        }

    digest = _stable_digest(raw_results["locale_runs"])
    artifact = {
        "benchmark_metadata": {
            "title": "Open Spelling & Grammar Benchmark: Paired Locale Evaluation",
            "version": "4.1-locale-paired",
            "eval_date": raw_results["metadata"].get("collection_date"),
            "run_id": f"h-suite-paired-v1-{digest[:16]}",
            "cached_outputs_sha256": digest,
            "voice_scoring_revision": VOICE_SCORING_REVISION,
            "locale_scoring_note": (
                "Locale-specific spelling forms are scored at aligned source "
                "sites. The Voice formula is unchanged. Full references are "
                "examples, not exact-string targets."
            ),
            "weights": {
                "spelling": "43.75%",
                "grammar": "31.25%",
                "voice": "25%",
            },
        },
        "locales": locale_scores,
        "en-GB_minus_en-US": paired_changes,
    }
    with Path(output_path).open("w", encoding="utf-8") as file:
        json.dump(artifact, file, indent=2)
    return artifact


if __name__ == "__main__":
    result = run_evaluation()
    print(f"Saved paired-locale results to {OUTPUT_PATH}")
    for engine, changes in result["en-GB_minus_en-US"].items():
        print(
            f"{engine}: quality {changes['quality_composite']:+.1f} pp; "
            f"spelling {changes['spelling_accuracy']:+.1f} pp"
        )
