#!/usr/bin/env python3
"""Collect JSpell Cloud API outputs for the v0.4 H-suite."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from benchmark_4pillars_hybrid import UNSEEN_BENCHMARK_UNITS


ROOT = Path(__file__).resolve().parent
API_URL = "https://jspell-checker.p.rapidapi.com/check"
API_HOST = "jspell-checker.p.rapidapi.com"
API_KEY_NAME = "x-rapidapi-key"
OUTPUT_PATH = ROOT / "raw_results" / "jspell_control_outputs.json"
REQUEST_INTERVAL_SECONDS = 0.25

API_CONFIG = {
    "forceUpperCase": False,
    "ignoreDouble": False,
    "ignoreFirstCaps": True,
    "ignoreIrregularCaps": False,
    "ignoreUpper": False,
    "ignoreWordsWithNumbers": True,
}


def load_local_api_key():
    """Load the RapidAPI app key from the process environment or ignored .env."""
    key = os.environ.get(API_KEY_NAME, "").strip()
    if key:
        return key

    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            candidate = line.strip()
            if not candidate or candidate.startswith("#"):
                continue
            if candidate.startswith("export "):
                candidate = candidate[len("export "):].strip()
            name, separator, value = candidate.partition("=")
            if separator and name.strip().casefold() == API_KEY_NAME:
                value = value.strip()
                if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
                    value = value[1:-1]
                if value:
                    return value

    raise RuntimeError(
        "RapidAPI key is not configured. Set x-rapidapi-key in the process "
        "environment or in the ignored local .env file. Do not paste the key into chat."
    )


def utf16_offset_to_index(text, offset):
    """Convert a JSpell UTF-16 offset to a Python string index."""
    if type(offset) is not int or offset < 0:
        raise ValueError("JSpell returned an invalid UTF-16 offset")

    units = 0
    for index, character in enumerate(text):
        if units == offset:
            return index
        character_units = 2 if ord(character) > 0xFFFF else 1
        if units < offset < units + character_units:
            raise ValueError("JSpell offset splits a UTF-16 surrogate pair")
        units += character_units

    if units == offset:
        return len(text)
    raise ValueError("JSpell offset is outside the submitted text")


def request_jspell(text, api_key, opener=None):
    """Submit one passage to JSpell and return its decoded JSON response."""
    payload = {
        "language": "enUS",
        "fieldvalues": text,
        "config": API_CONFIG,
    }
    request = Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": API_HOST,
        },
        method="POST",
    )
    open_url = opener or urlopen
    try:
        with open_url(request, timeout=30) as response:
            response_body = response.read()
    except HTTPError as error:
        error_body = error.read().decode("utf-8", errors="replace")
        detail = safe_http_error_detail(error_body, api_key, text)
        request_id = error.headers.get("x-rapidapi-request-id") if error.headers else None
        message = "JSpell/RapidAPI returned HTTP %d" % error.code
        if request_id:
            message += " (request ID %s)" % request_id
        if detail:
            message += ": " + detail
        raise RuntimeError(message) from None

    try:
        result = json.loads(response_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("JSpell returned a non-JSON response") from error
    if not isinstance(result, dict):
        raise ValueError("JSpell response must be a JSON object")
    return result


def safe_http_error_detail(response_body, api_key, submitted_text):
    """Extract a short provider message without echoing credentials or input."""
    try:
        payload = json.loads(response_body)
    except json.JSONDecodeError:
        return "non-JSON error details withheld"
    if not isinstance(payload, dict):
        return "error details withheld"

    messages = []
    for field in ("message", "error", "detail"):
        value = payload.get(field)
        if isinstance(value, str):
            messages.append(value)
        elif isinstance(value, dict):
            for nested_field in ("message", "detail", "code"):
                nested_value = value.get(nested_field)
                if isinstance(nested_value, str):
                    messages.append(nested_value)

    if not messages:
        return "error details withheld"

    detail = " | ".join(messages)
    for private_value in (api_key, submitted_text):
        if private_value:
            detail = detail.replace(private_value, "[redacted]")
    return detail[:500]


def process_response(text, response):
    """Validate JSpell errors and apply each first suggestion once."""
    elements = response.get("elements")
    if not isinstance(elements, list) or len(elements) != 1:
        raise ValueError("JSpell response must contain exactly one text element")

    raw_errors = elements[0].get("errors") if isinstance(elements[0], dict) else None
    if not isinstance(raw_errors, list):
        raise ValueError("JSpell response is missing its errors list")

    errors = []
    for error in raw_errors:
        if not isinstance(error, dict):
            raise ValueError("JSpell returned a malformed spelling error")
        word = error.get("word")
        position = error.get("position")
        suggestions = error.get("suggestions")
        if not isinstance(word, str) or not word:
            raise ValueError("JSpell returned an invalid error word")
        if not isinstance(suggestions, list) or any(
            not isinstance(suggestion, str) for suggestion in suggestions
        ):
            raise ValueError("JSpell returned an invalid suggestions list")

        start = utf16_offset_to_index(text, position)
        end = utf16_offset_to_index(text, position + len(word.encode("utf-16-le")) // 2)
        if text[start:end] != word:
            raise ValueError("JSpell error word does not match the submitted text")

        errors.append({
            "word": word,
            "position_utf16": position,
            "start": start,
            "end": end,
            "suggestions": suggestions,
        })

    ordered_errors = sorted(errors, key=lambda item: (item["start"], item["end"]))
    for previous, current in zip(ordered_errors, ordered_errors[1:]):
        if current["start"] < previous["end"]:
            raise ValueError("JSpell returned overlapping spelling errors")

    edits = []
    corrected_text = text
    for error in reversed(ordered_errors):
        if not error["suggestions"]:
            continue
        replacement = error["suggestions"][0]
        corrected_text = (
            corrected_text[:error["start"]]
            + replacement
            + corrected_text[error["end"]:]
        )
        edits.append({
            "word": error["word"],
            "replacement": replacement,
            "start": error["start"],
            "end": error["end"],
        })

    return {
        "text": corrected_text,
        "errors": ordered_errors,
        "edits": list(reversed(edits)),
    }


def collect_passage(text, api_key):
    """Collect and time a single JSpell check."""
    request_started_at_utc = datetime.now(timezone.utc).isoformat()
    started = time.perf_counter()
    response = request_jspell(text, api_key)
    latency_ms = (time.perf_counter() - started) * 1000
    request_completed_at_utc = datetime.now(timezone.utc).isoformat()
    result = process_response(text, response)
    result["lat"] = round(latency_ms, 1)
    result["request_started_at_utc"] = request_started_at_utc
    result["request_completed_at_utc"] = request_completed_at_utc
    result["source_input_sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return result


def write_results_atomically(results, output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=str(output_path.parent),
            prefix=output_path.name + ".",
            suffix=".tmp",
            delete=False,
        ) as file:
            temporary_path = Path(file.name)
            json.dump(results, file, ensure_ascii=False, indent=2)
            file.write("\n")
        os.replace(str(temporary_path), str(output_path))
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def collect_all(api_key):
    """Collect every current H-suite passage."""
    run_started_at_utc = datetime.now(timezone.utc).isoformat()
    h_inputs = {
        unit["id"]: unit["input"] for unit in UNSEEN_BENCHMARK_UNITS
    }
    all_passages = [
        ("h_suite", passage_id, text)
        for passage_id, text in h_inputs.items()
    ]

    results = {
        "benchmark_metadata": {
            "engine": "JSpell Cloud Spell Check API",
            "source": "RapidAPI JSpell Cloud Spell Check API",
            "collection_mode": "api",
            "source_url": API_URL,
            "gateway": "RapidAPI",
            "api_host": API_HOST,
            "product_version": "not reported",
            "api_version": "not reported",
            "language": "enUS",
            "suggestion_policy": (
                "Apply the first JSpell suggestion for each reported word once "
                "at its original offset; do not recheck after edits."
            ),
            "latency_definition": (
                "Elapsed time for one HTTP request and JSON response read; "
                "does not include the inter-request pause."
            ),
            "run_started_at_utc": run_started_at_utc,
            "request_count": len(all_passages),
        },
        "h_suite": {},
    }

    for index, (suite, passage_id, text) in enumerate(all_passages, start=1):
        print("Checking %s (%d/%d)" % (passage_id, index, len(all_passages)))
        results[suite][passage_id] = collect_passage(text, api_key)
        if index < len(all_passages):
            time.sleep(REQUEST_INTERVAL_SECONDS)

    results["benchmark_metadata"]["run_completed_at_utc"] = (
        datetime.now(timezone.utc).isoformat()
    )
    latencies = [
        result["lat"]
        for result in results["h_suite"].values()
    ]
    results["benchmark_metadata"]["average_latency_ms"] = round(
        sum(latencies) / len(latencies), 1
    )
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Collect JSpell Cloud API outputs for the v0.4 H-suite."
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace the existing raw output file and spend another set of API checks.",
    )
    args = parser.parse_args(argv)

    if OUTPUT_PATH.exists() and not args.overwrite:
        raise FileExistsError(
            "JSpell outputs already exist; pass --overwrite only if you intend "
            "to run the API checks again."
        )

    api_key = load_local_api_key()
    results = collect_all(api_key)
    write_results_atomically(results, OUTPUT_PATH)
    print("Saved JSpell raw outputs to %s" % OUTPUT_PATH.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        sys.exit(2)
