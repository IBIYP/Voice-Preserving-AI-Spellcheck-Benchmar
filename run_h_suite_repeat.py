#!/usr/bin/env python3
"""Collect and score a fresh H-suite repeat against three provider APIs."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from benchmark_4pillars_hybrid import UNSEEN_BENCHMARK_UNITS, evaluate_unit
from run_jspell_control import (
    API_HOST as JSPELL_API_HOST,
    API_URL as JSPELL_API_URL,
    process_response as process_jspell_response,
    request_jspell,
    write_results_atomically,
)
from text_matching import aggregate_writer_voice


ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = ROOT / "benchmark_data" / "h_suite_repeat_v1.json"
RUNS_PATH = ROOT / "raw_results" / "h_suite_repeat_v1_runs.json"
SCORE_PATH = ROOT / "raw_results" / "h_suite_repeat_v1_scores.json"
WEEKLY_HISTORY_PATH = ROOT / "raw_results" / "h_suite_weekly_history.json"

BCORRECT_URL = "https://bcorrect-api.fly.dev/api/v1/check"
TEXTGEARS_HOST = "textgears-textgears-v1.p.rapidapi.com"
TEXTGEARS_URL = f"https://{TEXTGEARS_HOST}/correct"
JSPELL_ENGINE = "JSpell Cloud Spell Check API"
JSPELL_WEB_ENGINE = "JSpell Free Web Checker"
LANGUAGETOOL_WEB_ENGINE = "LanguageTool (Web)"
DEEPL_ENGINE = "DeepL Write"
ENGINE_NAMES = ("BCorrect (FMM)", "TextGears API", JSPELL_ENGINE)
REQUEST_INTERVAL_SECONDS = 0.25
SCORING_WEIGHTS = {
    "spelling": 43.75,
    "grammar": 31.25,
    "voice": 25,
}


def _read_manifest(path=MANIFEST_PATH):
    with Path(path).open("r", encoding="utf-8") as file:
        manifest = json.load(file)
    validate_manifest(manifest)
    return manifest


def _stable_digest(value):
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _sha256_text(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _dotenv_values():
    values = {}
    env_path = ROOT / ".env"
    if not env_path.exists():
        return values
    for line in env_path.read_text(encoding="utf-8").splitlines():
        candidate = line.strip()
        if not candidate or candidate.startswith("#"):
            continue
        if candidate.startswith("export "):
            candidate = candidate[len("export "):].strip()
        name, separator, value = candidate.partition("=")
        if not separator:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[name.strip()] = value
    return values


def _load_key(name, *fallback_names):
    dotenv = _dotenv_values()
    for candidate in (name, *fallback_names):
        value = os.environ.get(candidate, "").strip() or dotenv.get(candidate, "").strip()
        if value:
            return value
    names = ", ".join((name, *fallback_names))
    raise RuntimeError(f"Missing API key; configure one of these names in .env: {names}")


def _passage_digest(passages):
    return _stable_digest(passages)


def validate_manifest(manifest):
    if not isinstance(manifest, dict) or not isinstance(manifest.get("metadata"), dict):
        raise ValueError("Repeat-suite manifest must be an object with metadata")
    metadata = manifest["metadata"]
    if metadata.get("status") != "frozen":
        raise ValueError("Repeat-suite manifest must be frozen before collection")
    passages = manifest.get("passages")
    expected_ids = {f"HR-{index:02d}" for index in range(1, 11)}
    if not isinstance(passages, list) or len(passages) != len(expected_ids):
        raise ValueError("Repeat suite must contain exactly ten passages")
    if any(not isinstance(passage, dict) for passage in passages):
        raise ValueError("Every repeat-suite passage must be an object")
    if {passage.get("id") for passage in passages} != expected_ids:
        raise ValueError("Repeat-suite IDs must be HR-01 through HR-10")

    spelling_count = 0
    grammar_count = 0
    old_inputs = {unit["input"] for unit in UNSEEN_BENCHMARK_UNITS}
    for passage in passages:
        passage_id = passage["id"]
        text = passage.get("input")
        if not isinstance(text, str) or not text.strip() or not text.isascii():
            raise ValueError(f"{passage_id} must have non-empty ASCII input text")
        if text in old_inputs:
            raise ValueError(f"{passage_id} reuses an original H-suite input")
        for field in ("spelling_targets", "grammar_targets"):
            if not isinstance(passage.get(field), dict):
                raise ValueError(f"{passage_id} is missing {field}")
        if not isinstance(passage.get("voice_tokens"), list) or not passage["voice_tokens"]:
            raise ValueError(f"{passage_id} must define voice tokens")
        if not isinstance(passage.get("forbidden_rewrites"), list):
            raise ValueError(f"{passage_id} must define forbidden rewrites")

        corrected = text
        for source, target in passage["spelling_targets"].items():
            if not isinstance(source, str) or not source or not isinstance(target, str):
                raise ValueError(f"{passage_id} has an invalid spelling annotation")
            if source not in corrected:
                raise ValueError(f"{passage_id} spelling source is absent: {source}")
            corrected = corrected.replace(source, target, 1)
        for source, target in passage["grammar_targets"].items():
            if not isinstance(source, str) or not source or not isinstance(target, str):
                raise ValueError(f"{passage_id} has an invalid grammar annotation")
            if source not in corrected:
                raise ValueError(f"{passage_id} grammar source is absent: {source}")
            corrected = corrected.replace(source, target, 1)
        metrics = evaluate_unit(passage, corrected)
        if metrics["spelling_acc"] != 100 or metrics["grammar_acc"] != 100:
            raise ValueError(f"{passage_id} annotations fail their declared corrections")
        spelling_count += len(passage["spelling_targets"])
        grammar_count += len(passage["grammar_targets"])

    if spelling_count != metadata.get("spelling_target_count"):
        raise ValueError("Repeat-suite spelling target count does not match metadata")
    if grammar_count != metadata.get("grammar_target_count"):
        raise ValueError("Repeat-suite grammar target count does not match metadata")
    if spelling_count != 49 or grammar_count != 12:
        raise ValueError(
            "Repeat suite must match the original H-suite's 49 spelling and 12 grammar targets"
        )


def _request_json(url, headers, *, data=None, redactions=(), timeout=30):
    request = Request(url, data=data, headers=headers, method="POST" if data else "GET")
    started_at = datetime.now(timezone.utc).isoformat()
    started = time.perf_counter()
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read()
            status = response.status
    except HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        for private_value in redactions:
            if private_value:
                body = body.replace(private_value, "[redacted]")
        request_id = error.headers.get("x-rapidapi-request-id") if error.headers else None
        detail = " ".join(body.split())[:300]
        message = f"Provider returned HTTP {error.code}"
        if request_id:
            message += f" (request ID {request_id})"
        if detail:
            message += f": {detail}"
        raise RuntimeError(message) from None
    except URLError as error:
        raise RuntimeError(
            f"Provider request failed ({type(error.reason).__name__})"
        ) from None

    elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
    completed_at = datetime.now(timezone.utc).isoformat()
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("Provider returned a non-JSON response") from error
    if not isinstance(payload, dict):
        raise ValueError("Provider response must be a JSON object")
    return payload, elapsed_ms, started_at, completed_at, status


def _request_bcorrect(text, api_key):
    body = json.dumps({"text": text, "locale": "en-US"}).encode("utf-8")
    payload, elapsed, started, completed, status = _request_json(
        BCORRECT_URL,
        {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-API-Key": api_key,
        },
        data=body,
        redactions=(api_key, text),
    )
    if status != 200:
        raise RuntimeError(f"BCorrect returned unexpected HTTP status {status}")
    if payload.get("originalText") != text:
        raise ValueError("BCorrect response originalText does not match submitted text")
    corrected = payload.get("correctedText")
    if not isinstance(corrected, str) or not corrected.strip():
        raise ValueError("BCorrect response is missing correctedText")
    return {
        "text": corrected,
        "latency_ms": elapsed,
        "request_started_at_utc": started,
        "request_completed_at_utc": completed,
        "provider_response": payload,
    }


def apply_textgears_suggestions(text, errors):
    if not isinstance(errors, list):
        raise ValueError("TextGears response errors must be a list")
    checked = []
    for error in errors:
        if not isinstance(error, dict):
            raise ValueError("TextGears returned a malformed error")
        offset = error.get("offset")
        length = error.get("length")
        bad = error.get("bad")
        better = error.get("better")
        if (
            type(offset) is not int
            or type(length) is not int
            or offset < 0
            or length < 0
            or not isinstance(bad, str)
            or not isinstance(better, list)
            or any(not isinstance(item, str) for item in better)
        ):
            raise ValueError("TextGears returned invalid correction details")
        if offset + length > len(text) or text[offset:offset + length] != bad:
            raise ValueError("TextGears correction offset does not match source text")
        checked.append((offset, length, bad, better))

    ordered = sorted(checked, key=lambda item: (item[0], item[1]))
    for previous, current in zip(ordered, ordered[1:]):
        if current[0] < previous[0] + previous[1] or current[0] == previous[0]:
            raise ValueError("TextGears returned overlapping correction spans")

    corrected = text
    for offset, length, _bad, suggestions in reversed(ordered):
        if suggestions:
            corrected = corrected[:offset] + suggestions[0] + corrected[offset + length:]
    return corrected


def _request_textgears(text, api_key):
    body = urlencode({"text": text, "language": "en-US"}).encode("utf-8")
    payload, elapsed, started, completed, status = _request_json(
        TEXTGEARS_URL,
        {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": TEXTGEARS_HOST,
        },
        data=body,
        redactions=(api_key, text),
    )
    if status != 200:
        raise RuntimeError(f"TextGears returned unexpected HTTP status {status}")
    if payload.get("status") is not True:
        code = payload.get("error_code", "not reported")
        raise RuntimeError(f"TextGears returned status=false (error code {code})")
    response = payload.get("response")
    if not isinstance(response, dict):
        raise ValueError("TextGears response is missing its response object")
    if isinstance(response.get("corrected"), str) and response["corrected"].strip():
        corrected = response["corrected"]
    elif "errors" in response:
        corrected = apply_textgears_suggestions(text, response.get("errors"))
    else:
        raise ValueError("TextGears response is missing corrected text and errors list")
    return {
        "text": corrected,
        "latency_ms": elapsed,
        "request_started_at_utc": started,
        "request_completed_at_utc": completed,
        "provider_response": payload,
    }


def _request_jspell(text, api_key):
    started = datetime.now(timezone.utc).isoformat()
    start_clock = time.perf_counter()
    response = request_jspell(text, api_key)
    elapsed = round((time.perf_counter() - start_clock) * 1000, 1)
    completed = datetime.now(timezone.utc).isoformat()
    result = process_jspell_response(text, response)
    return {
        "text": result["text"],
        "latency_ms": elapsed,
        "request_started_at_utc": started,
        "request_completed_at_utc": completed,
        "errors": result["errors"],
        "edits": result["edits"],
    }


def _empty_run(manifest):
    old_suite_digest = _passage_digest(UNSEEN_BENCHMARK_UNITS)
    repeat_digest = _passage_digest(manifest["passages"])
    now = datetime.now(timezone.utc).isoformat()
    return {
        "metadata": {
            "status": "running",
            "suite_id": manifest["metadata"]["suite_id"],
            "suite_version": manifest["metadata"]["suite_version"],
            "repeat_dataset_sha256": repeat_digest,
            "old_h_suite_dataset_sha256": old_suite_digest,
            "scoring_weights": SCORING_WEIGHTS,
            "collection_started_at_utc": now,
            "engine_metadata": {
                "BCorrect (FMM)": {
                    "collection_mode": "api",
                    "source_url": BCORRECT_URL,
                    "locale": "en-US",
                    "api_version": "not reported",
                },
                "TextGears API": {
                    "collection_mode": "api",
                    "source_url": TEXTGEARS_URL,
                    "locale": "en-US",
                    "suggestion_policy": "Apply the first suggestion at each returned correction site once.",
                },
                JSPELL_ENGINE: {
                    "collection_mode": "api",
                    "source_url": JSPELL_API_URL,
                    "api_host": JSPELL_API_HOST,
                    "locale": "en-US",
                    "suggestion_policy": "Apply the first suggestion at each returned correction site once.",
                },
            },
        },
        "old_h_suite_jspell_control": {"outputs": {}},
        "repeat_suite_outputs": {},
        "provider_failures": {},
    }


def _load_or_create_run(manifest, resume, runs_path=None):
    target_path = Path(runs_path) if runs_path is not None else RUNS_PATH
    if not target_path.exists():
        if resume:
            raise FileNotFoundError("--resume was requested, but no partial run file exists")
        results = _empty_run(manifest)
        write_results_atomically(results, target_path)
        return results
    if not resume:
        raise FileExistsError(
            f"{target_path} already exists; use --resume for a partial run"
        )
    with target_path.open("r", encoding="utf-8") as file:
        results = json.load(file)
    expected = _empty_run(manifest)
    for field in ("repeat_dataset_sha256", "old_h_suite_dataset_sha256"):
        if results.get("metadata", {}).get(field) != expected["metadata"][field]:
            raise ValueError(f"Cannot resume: {field} does not match this run")
    if results.get("metadata", {}).get("status") == "complete":
        raise ValueError("Run is already complete; refusing to collect duplicate API calls")
    if not isinstance(results.get("old_h_suite_jspell_control"), dict) or not isinstance(
        results.get("repeat_suite_outputs"), dict
    ):
        raise ValueError("Partial run file has an invalid structure")
    provider_failures = results.setdefault("provider_failures", {})
    if not isinstance(provider_failures, dict):
        raise ValueError("Partial run file has an invalid provider_failures field")
    return results


def _save_run(results, runs_path=None):
    target_path = Path(runs_path) if runs_path is not None else RUNS_PATH
    write_results_atomically(results, target_path)


def _score_suite(passages, output_by_id, expected_engines):
    expected_ids = {passage["id"] for passage in passages}
    if set(output_by_id) != expected_ids:
        missing = sorted(expected_ids - set(output_by_id))
        unexpected = sorted(set(output_by_id) - expected_ids)
        raise ValueError(f"Scoring coverage mismatch; missing={missing}, unexpected={unexpected}")

    aggregate = {}
    breakdown = []
    for engine in expected_engines:
        aggregate[engine] = {
            "spelling_hits": 0,
            "spelling_count": 0,
            "grammar_hits": 0,
            "grammar_count": 0,
            "voice_metrics": [],
            "diagnostic_sites": [],
        }

    for passage in passages:
        passage_id = passage["id"]
        entry = {"id": passage_id, "domain": passage["domain"], "scores": {}}
        engine_outputs = output_by_id[passage_id]
        if set(engine_outputs) != set(expected_engines):
            raise ValueError(f"Engine coverage mismatch for {passage_id}")
        for engine, output in engine_outputs.items():
            text = output.get("text") if isinstance(output, dict) else None
            if not isinstance(text, str) or not text.strip():
                raise ValueError(f"Missing output text for {engine} on {passage_id}")
            metrics = evaluate_unit(passage, text)
            totals = aggregate[engine]
            totals["spelling_hits"] += metrics["spelling_target_hits"]
            totals["spelling_count"] += metrics["spelling_target_count"]
            totals["grammar_hits"] += metrics["grammar_target_hits"]
            totals["grammar_count"] += metrics["grammar_target_count"]
            totals["voice_metrics"].append({
                "score": metrics["voice_preservation"],
                "lexical_f1": metrics["voice_lexical_f1"],
                "voice_marker_retention": metrics["voice_marker_retention"],
                "over_edit_count": metrics["voice_over_edit_count"],
            })
            totals["diagnostic_sites"].extend(
                metrics["correction_site_diagnostic"]["sites"]
            )
            entry["scores"][engine] = {"text": text, "metrics": metrics}
        breakdown.append(entry)

    summary = {}
    for engine, totals in aggregate.items():
        voice = aggregate_writer_voice(totals["voice_metrics"])
        spelling_accuracy = round(
            totals["spelling_hits"] / totals["spelling_count"] * 100, 1
        )
        grammar_accuracy = round(
            totals["grammar_hits"] / totals["grammar_count"] * 100, 1
        )
        sites = totals["diagnostic_sites"]
        applicable = len(sites)
        unapproved = sum(
            site["classification"] == "unapproved_edit" for site in sites
        )
        composite = round(
            SCORING_WEIGHTS["spelling"] * spelling_accuracy / 100
            + SCORING_WEIGHTS["grammar"] * grammar_accuracy / 100
            + SCORING_WEIGHTS["voice"] * voice["score"] / 100,
            1,
        )
        summary[engine] = {
            "spelling_accuracy": spelling_accuracy,
            "spelling_target_hits": totals["spelling_hits"],
            "spelling_target_count": totals["spelling_count"],
            "grammar_accuracy": grammar_accuracy,
            "grammar_target_hits": totals["grammar_hits"],
            "grammar_target_count": totals["grammar_count"],
            "voice_preservation": voice["score"],
            "quality_composite": composite,
            "unapproved_edits": unapproved,
            "correction_site_count": applicable,
            "unapproved_edit_rate": (
                round(unapproved / applicable * 100, 1) if applicable else None
            ),
        }
    return summary, breakdown


def _old_jspell_outputs(results):
    outputs = results["old_h_suite_jspell_control"]["outputs"]
    return {
        passage_id: {JSPELL_ENGINE: result}
        for passage_id, result in outputs.items()
    }


def _new_engine_outputs(results, passages):
    outputs = {}
    for passage in passages:
        passage_id = passage["id"]
        record = results["repeat_suite_outputs"].get(passage_id, {})
        engine_outputs = record.get("engine_outputs", {})
        outputs[passage_id] = engine_outputs
    return outputs


def _available_repeat_engines(outputs):
    engines = ["BCorrect (FMM)", "TextGears API"]
    for optional_engine in (
        JSPELL_ENGINE,
        JSPELL_WEB_ENGINE,
        LANGUAGETOOL_WEB_ENGINE,
        DEEPL_ENGINE,
    ):
        if all(optional_engine in passage_outputs for passage_outputs in outputs.values()):
            engines.append(optional_engine)
    return tuple(engines)


def record_weekly_history(
    manifest,
    scorecard,
    *,
    score_path=SCORE_PATH,
    history_path=WEEKLY_HISTORY_PATH,
    run_date=None,
    status_note=None,
):
    history_file = Path(history_path)
    if history_file.exists():
        with history_file.open("r", encoding="utf-8") as file:
            history = json.load(file)
    else:
        history = {
            "schema_version": 1,
            "series": "Weekly fresh H-suite challenge",
            "comparison_policy": (
                "Compare providers within the same frozen batch. Across batches, "
                "differing passages make score changes descriptive rather than "
                "controlled evidence of provider improvement. Use the fixed anchor "
                "for same-input longitudinal comparisons."
            ),
            "entries": [],
        }

    now_utc = datetime.now(timezone.utc).isoformat()
    recorded_date = run_date or datetime.now(timezone.utc).date().isoformat()
    suite_id = manifest["metadata"]["suite_id"]
    dataset_sha = scorecard["repeat_dataset_sha256"]
    rel_score_path = str(Path(score_path).resolve().relative_to(ROOT)).replace("\\", "/")

    jspell_ctrl = scorecard.get("jspell_same_api_control", {})
    if status_note is None:
        if jspell_ctrl.get("status") == "complete":
            status_note = "complete"
        else:
            err = jspell_ctrl.get("error", "JSpell API control unavailable")
            status_note = f"partial; {err}"

    entry = {
        "week_start_date": recorded_date,
        "suite_id": suite_id,
        "suite_version": manifest["metadata"]["suite_version"],
        "dataset_sha256": dataset_sha,
        "scoring_protocol": manifest["metadata"]["scoring_protocol"],
        "status": status_note,
        "results_recorded_at_utc": now_utc,
        "provider_scores": scorecard["new_repeat_suite"]["engine_summary"],
        "jspell_same_api_control": {
            "status": jspell_ctrl.get("status"),
            "engine": jspell_ctrl.get("engine", JSPELL_ENGINE),
            "old_h_suite_score": jspell_ctrl.get("old_h_suite_score"),
            "new_repeat_suite_score": jspell_ctrl.get("new_repeat_suite_score"),
            **(
                {"error": jspell_ctrl["error"]}
                if "error" in jspell_ctrl
                else {}
            ),
        },
        "scorecard": rel_score_path,
    }

    entries = history.setdefault("entries", [])
    updated = False
    for idx, existing in enumerate(entries):
        if existing.get("suite_id") == suite_id and existing.get("dataset_sha256") == dataset_sha:
            entries[idx] = entry
            updated = True
            break
    if not updated:
        entries.append(entry)

    write_results_atomically(history, history_file)
    return history


def score_existing_run(
    manifest_path=MANIFEST_PATH,
    runs_path=RUNS_PATH,
    score_path=SCORE_PATH,
    *,
    record_history=False,
    run_date=None,
):
    manifest = _read_manifest(manifest_path)
    runs_file = Path(runs_path)
    score_file = Path(score_path)
    with runs_file.open("r", encoding="utf-8") as file:
        results = json.load(file)

    old_outputs = results.get("old_h_suite_jspell_control", {}).get("outputs", {})
    new_outputs = results.get("repeat_suite_outputs", {})
    old_jspell_inputs = {unit["id"]: unit["input"] for unit in UNSEEN_BENCHMARK_UNITS}
    old_jspell_complete = set(old_outputs) == set(old_jspell_inputs)
    new_engine_outputs = _new_engine_outputs(results, manifest["passages"])
    if set(new_outputs) != {passage["id"] for passage in manifest["passages"]}:
        raise ValueError("Repeat-suite raw output coverage mismatch")

    new_jspell_complete = all(
        JSPELL_ENGINE in outputs for outputs in new_engine_outputs.values()
    )
    available_engines = _available_repeat_engines(new_engine_outputs)
    scoreable_outputs = {
        passage_id: {
            engine: engine_output[engine]
            for engine in available_engines
            if engine in engine_output
        }
        for passage_id, engine_output in new_engine_outputs.items()
    }
    new_summary, new_breakdown = _score_suite(
        manifest["passages"], scoreable_outputs, available_engines
    )
    old_summary = None
    old_breakdown = []
    if old_jspell_complete:
        old_summary, old_breakdown = _score_suite(
            UNSEEN_BENCHMARK_UNITS,
            _old_jspell_outputs(results),
            (JSPELL_ENGINE,),
        )

    collection_complete = old_jspell_complete and new_jspell_complete
    results["metadata"]["raw_outputs_sha256"] = _stable_digest({
        "old_h_suite_jspell_control": old_outputs,
        "repeat_suite_outputs": new_outputs,
    })
    results["metadata"]["results_updated_at_utc"] = datetime.now(timezone.utc).isoformat()
    _save_run(results, runs_file)

    previous_failure = results.get("provider_failures", {}).get(JSPELL_ENGINE)
    jspell_error = previous_failure.get("error") if previous_failure else None
    jspell_control = {"status": "complete" if collection_complete else "blocked"}
    if collection_complete:
        jspell_old_score = old_summary[JSPELL_ENGINE]["quality_composite"]
        jspell_new_score = new_summary[JSPELL_ENGINE]["quality_composite"]
        jspell_control.update({
            "engine": JSPELL_ENGINE,
            "old_h_suite_score": old_summary[JSPELL_ENGINE],
            "new_repeat_suite_score": new_summary[JSPELL_ENGINE],
            "quality_composite_change_points": round(
                jspell_new_score - jspell_old_score, 1
            ),
            "old_h_suite_passages": old_breakdown,
        })
    else:
        jspell_control.update({
            "engine": JSPELL_ENGINE,
            "old_h_suite_score": (
                old_summary[JSPELL_ENGINE] if old_summary is not None else None
            ),
            "new_repeat_suite_score": None,
            "error": jspell_error or "JSpell API outputs are incomplete",
        })

    suite_version = manifest["metadata"]["suite_version"]
    scorecard = {
        "benchmark": f"H-suite repeat v{suite_version}",
        "scoring_protocol": "v0.4 H-suite",
        "engine_metadata": results["metadata"]["engine_metadata"],
        "repeat_dataset_sha256": results["metadata"]["repeat_dataset_sha256"],
        "old_h_suite_dataset_sha256": results["metadata"]["old_h_suite_dataset_sha256"],
        "raw_outputs_sha256": results["metadata"]["raw_outputs_sha256"],
        "score_note": (
            "Separate fresh repeat-set results under the v0.4 rubric; these do not "
            "replace the original public leaderboard. Different batches use fresh "
            "passages and are descriptive observations over time."
        ),
        "new_repeat_suite": {
            "status": "complete" if new_jspell_complete else "partial",
            "engine_summary": new_summary,
            "passages": new_breakdown,
        },
        "jspell_same_api_control": jspell_control,
    }
    write_results_atomically(scorecard, score_file)
    if record_history:
        record_weekly_history(
            manifest,
            scorecard,
            score_path=score_file,
            run_date=run_date,
        )
    return scorecard


def collect_and_score(
    *,
    resume=False,
    skip_jspell=False,
    retry_jspell=False,
    manifest_path=MANIFEST_PATH,
    runs_path=RUNS_PATH,
    score_path=SCORE_PATH,
    record_history=False,
):
    manifest = _read_manifest(manifest_path)
    runs_file = Path(runs_path)
    score_file = Path(score_path)
    bcorrect_key = _load_key("BCORRECT_API_KEY")
    textgears_key = _load_key("TEXTGEARS_API_KEY")
    jspell_key = None if skip_jspell else _load_key("JSPELL_RAPIDAPI_KEY", "x-rapidapi-key")
    results = _load_or_create_run(manifest, resume, runs_path=runs_file)
    results["metadata"]["engine_metadata"]["TextGears API"]["source_url"] = TEXTGEARS_URL
    old_outputs = results["old_h_suite_jspell_control"]["outputs"]
    new_outputs = results["repeat_suite_outputs"]

    for index, passage in enumerate(manifest["passages"], start=1):
        passage_id = passage["id"]
        record = new_outputs.setdefault(passage_id, {
            "input_sha256": _sha256_text(passage["input"]),
            "engine_outputs": {},
        })
        if record["input_sha256"] != _sha256_text(passage["input"]):
            raise ValueError(f"Input hash mismatch for {passage_id}")
        providers = (
            ("BCorrect (FMM)", lambda: _request_bcorrect(passage["input"], bcorrect_key)),
            ("TextGears API", lambda: _request_textgears(passage["input"], textgears_key)),
        )
        for engine, request in providers:
            if engine in record["engine_outputs"]:
                continue
            print(f"{engine} {passage_id} ({index}/10)")
            record["engine_outputs"][engine] = request()
            _save_run(results, runs_file)
            time.sleep(REQUEST_INTERVAL_SECONDS)

    previous_failure = results["provider_failures"].get(JSPELL_ENGINE)
    jspell_error = previous_failure.get("error") if previous_failure else None
    if skip_jspell:
        jspell_error = (
            jspell_error
            or "Collection skipped after the JSpell API returned HTTP 403 (Cloudflare error 1010)."
        )
        results["provider_failures"][JSPELL_ENGINE] = {
            "failed_at_utc": datetime.now(timezone.utc).isoformat(),
            "error": jspell_error,
        }
        _save_run(results, runs_file)
    elif previous_failure and not retry_jspell:
        print("Skipping JSpell retry; use --retry-jspell after fixing API access.")
    else:
        try:
            for index, passage in enumerate(UNSEEN_BENCHMARK_UNITS, start=1):
                passage_id = passage["id"]
                if passage_id not in old_outputs:
                    print(f"JSpell old-suite control {passage_id} ({index}/10)")
                    old_outputs[passage_id] = _request_jspell(passage["input"], jspell_key)
                    old_outputs[passage_id]["input_sha256"] = _sha256_text(passage["input"])
                    _save_run(results, runs_file)
                    time.sleep(REQUEST_INTERVAL_SECONDS)
            for index, passage in enumerate(manifest["passages"], start=1):
                passage_id = passage["id"]
                record = new_outputs[passage_id]
                engine_outputs = record["engine_outputs"]
                if JSPELL_ENGINE not in engine_outputs:
                    print(f"JSpell repeat-suite {passage_id} ({index}/10)")
                    engine_outputs[JSPELL_ENGINE] = _request_jspell(
                        passage["input"], jspell_key
                    )
                    _save_run(results, runs_file)
                    time.sleep(REQUEST_INTERVAL_SECONDS)
            results["provider_failures"].pop(JSPELL_ENGINE, None)
            jspell_error = None
        except (RuntimeError, ValueError) as error:
            jspell_error = str(error)
            results["provider_failures"][JSPELL_ENGINE] = {
                "failed_at_utc": datetime.now(timezone.utc).isoformat(),
                "error": jspell_error,
            }
            _save_run(results, runs_file)

    old_jspell_inputs = {unit["id"]: unit["input"] for unit in UNSEEN_BENCHMARK_UNITS}
    old_jspell_complete = set(old_outputs) == set(old_jspell_inputs)
    for passage_id, result in old_outputs.items():
        if result.get("input_sha256") != _sha256_text(old_jspell_inputs[passage_id]):
            raise ValueError(f"Old-suite JSpell input hash mismatch for {passage_id}")
    new_engine_outputs = _new_engine_outputs(results, manifest["passages"])
    if set(new_outputs) != {passage["id"] for passage in manifest["passages"]}:
        raise ValueError("Repeat-suite raw output coverage mismatch")
    new_jspell_complete = all(
        JSPELL_ENGINE in outputs for outputs in new_engine_outputs.values()
    )
    collection_complete = old_jspell_complete and new_jspell_complete
    results["metadata"]["status"] = "complete" if collection_complete else "partial"
    results["metadata"]["collection_completed_at_utc"] = datetime.now(timezone.utc).isoformat()
    _save_run(results, runs_file)

    scorecard = score_existing_run(
        manifest_path=manifest_path,
        runs_path=runs_file,
        score_path=score_file,
        record_history=record_history,
    )
    new_summary = scorecard["new_repeat_suite"]["engine_summary"]
    jspell_control = scorecard["jspell_same_api_control"]
    print("\nRepeat-suite scorecard")
    print("Engine                         | Spelling | Grammar | Voice  | Composite")
    print("-------------------------------|----------|---------|--------|----------")
    for engine, score in sorted(
        new_summary.items(), key=lambda item: item[1]["quality_composite"], reverse=True
    ):
        print(
            f"{engine:30} | {score['spelling_accuracy']:7.1f}% | "
            f"{score['grammar_accuracy']:6.1f}% | {score['voice_preservation']:5.1f}% | "
            f"{score['quality_composite']:8.1f}%"
        )
    if jspell_control.get("status") == "complete":
        jspell_old_score = jspell_control["old_h_suite_score"]["quality_composite"]
        jspell_new_score = jspell_control["new_repeat_suite_score"]["quality_composite"]
        print(
            f"\nJSpell API control: old H-suite {jspell_old_score:.1f}%, "
            f"new repeat suite {jspell_new_score:.1f}% "
            f"({jspell_control['quality_composite_change_points']:+.1f} points)"
        )
    else:
        print(f"\nJSpell API control incomplete: {jspell_control['error']}")
    print(f"Saved raw outputs to {runs_file.resolve().relative_to(ROOT)}")
    print(f"Saved scores to {score_file.resolve().relative_to(ROOT)}")
    return scorecard


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Collect BCorrect, TextGears, and JSpell API outputs on a fresh H-suite."
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=MANIFEST_PATH,
        help="Path to the frozen repeat-suite manifest JSON.",
    )
    parser.add_argument(
        "--runs",
        type=Path,
        default=RUNS_PATH,
        help="Path to save or resume raw provider outputs JSON.",
    )
    parser.add_argument(
        "--scores",
        type=Path,
        default=SCORE_PATH,
        help="Path to write the scored repeat-suite JSON.",
    )
    parser.add_argument(
        "--rescore-only",
        action="store_true",
        help="Rescore an existing runs JSON without making any API calls.",
    )
    parser.add_argument(
        "--record-history",
        action="store_true",
        help="Upsert this batch summary into raw_results/h_suite_weekly_history.json.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Continue a partial run without repeating completed API requests.",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--skip-jspell",
        action="store_true",
        help="Score BCorrect and TextGears without retrying the blocked JSpell API.",
    )
    group.add_argument(
        "--retry-jspell",
        action="store_true",
        help="Retry JSpell control requests after repairing API access; requires --resume.",
    )
    args = parser.parse_args(argv)
    if args.retry_jspell and not args.resume:
        parser.error("--retry-jspell requires --resume")
    if args.rescore_only:
        scorecard = score_existing_run(
            manifest_path=args.manifest,
            runs_path=args.runs,
            score_path=args.scores,
            record_history=args.record_history,
        )
        for engine, score in sorted(
            scorecard["new_repeat_suite"]["engine_summary"].items(),
            key=lambda item: item[1]["quality_composite"],
            reverse=True,
        ):
            print(
                f"{engine:30} | {score['spelling_accuracy']:7.1f}% | "
                f"{score['grammar_accuracy']:6.1f}% | {score['voice_preservation']:5.1f}% | "
                f"{score['quality_composite']:8.1f}%"
            )
        return 0
    collect_and_score(
        resume=args.resume,
        skip_jspell=args.skip_jspell,
        retry_jspell=args.retry_jspell,
        manifest_path=args.manifest,
        runs_path=args.runs,
        score_path=args.scores,
        record_history=args.record_history,
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RuntimeError, ValueError, FileNotFoundError, FileExistsError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(2)
