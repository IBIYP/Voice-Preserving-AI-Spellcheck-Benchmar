#!/usr/bin/env python3
"""Replay cached Blind Suite outputs with the v4 correction-site diagnostic."""

import json
import hashlib
import math
import os
import sys

from correction_site_diagnostic import (
    score_correction_sites,
    score_target_accuracy,
)
from blind_suite_data import (
    ENGINES,
    GOLD_REFERENCES,
    GROUND_TRUTH,
    calculate_sari_keep,
)
from text_matching import (
    VOICE_SCORING_REVISION,
    aggregate_writer_voice,
    score_writer_voice,
)
from collection_provenance import (
    COLLECTION_LOCALES,
    COLLECTION_MODES,
    COLLECTION_ROUTES,
    COLLECTION_SOURCE_URLS,
)

TARGET_SCORING_REVISION = "aligned-correction-sites-v1"


def _stable_digest(value):
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _validate_live_runs(live_runs):
    if not isinstance(live_runs, dict):
        raise ValueError("Blind Suite results must be an object keyed by passage ID")
    expected_ids = set(GROUND_TRUTH)
    if set(live_runs) != expected_ids:
        missing = sorted(expected_ids - set(live_runs))
        unexpected = sorted(set(live_runs) - expected_ids)
        raise ValueError(
            f"Blind Suite passage coverage mismatch; missing={missing}, "
            f"unexpected={unexpected}"
        )
    for passage_id in GROUND_TRUTH:
        unit = live_runs[passage_id]
        if not isinstance(unit, dict) or not isinstance(unit.get("input"), str):
            raise ValueError(f"Blind Suite input is missing for {passage_id}")
        for engine in ENGINES:
            engine_run = unit.get(engine)
            if not isinstance(engine_run, dict) or not isinstance(
                engine_run.get("text"), str
            ):
                raise ValueError(
                    f"Blind Suite result is missing text for {engine} on {passage_id}"
                )


def _recorded_latency(engine_runs, engine, passage_ids):
    values = []
    for passage_id in passage_ids:
        value = engine_runs[passage_id][engine].get("lat")
        if value is None:
            continue
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value < 0
        ):
            raise ValueError(f"Invalid latency for {engine} on {passage_id}: {value}")
        values.append(value)
    return (round(sum(values) / len(values), 1) if values else None, len(values))


def _load_outputs():
    runs_path = os.path.join("Docs", "Notes", "blind_v3_live_runs_full.json")
    if not os.path.exists(runs_path):
        raise FileNotFoundError(f"Missing cached Blind Suite outputs at {runs_path}")
    with open(runs_path, "r", encoding="utf-8") as file:
        live_runs = json.load(file)
    if not isinstance(live_runs, dict):
        raise ValueError("Blind Suite results must be an object keyed by passage ID")

    sapling_path = os.path.join(
        "archive", "v0.3", "blind_v3_sapling_outputs.json"
    )
    with open(sapling_path, "r", encoding="utf-8") as file:
        sapling_runs = json.load(file)["passages"]
    for passage_id, output in sapling_runs.items():
        if passage_id not in live_runs:
            raise ValueError(f"Sapling result references unknown passage {passage_id}")
        live_runs[passage_id]["Sapling Grammar Checker"] = {"text": output["text"]}

    jspell_path = os.path.join(
        "archive", "v0.3", "jspell_web_checker_outputs.json"
    )
    with open(jspell_path, "r", encoding="utf-8") as file:
        jspell_runs = json.load(file).get("blind_v3")
    if not isinstance(jspell_runs, dict):
            raise ValueError("JSpell web-checker results are missing saved Blind-suite outputs")
    for passage_id in GROUND_TRUTH:
        output = jspell_runs.get(passage_id)
        if not isinstance(output, dict) or not isinstance(output.get("text"), str):
            raise ValueError(f"JSpell web-checker result is missing {passage_id}")
        live_runs[passage_id]["JSpell Free Web Checker"] = {
            "text": output["text"],
            "lat": None,
        }
    _validate_live_runs(live_runs)
    return live_runs


def run_evaluation(export_path="raw_results/blind_v4_official_scoreboard.json"):
    """Score all saved outputs under the shared v4 rules."""
    live_runs = _load_outputs()
    passage_ids = list(GROUND_TRUTH)
    dataset_digest = _stable_digest(
        {
            passage_id: {
                "input": live_runs[passage_id]["input"],
                "spelling": GROUND_TRUTH[passage_id]["spelling"],
                "grammar": GROUND_TRUTH[passage_id]["grammar"],
            }
            for passage_id in passage_ids
        }
    )
    outputs_digest = _stable_digest(live_runs)
    report = {
        "benchmark": "Voice-Preserving AI-Spellcheck Benchmark (Blind Suite v4.0)",
        "benchmark_version": "4.0",
        "voice_scoring_revision": VOICE_SCORING_REVISION,
        "target_scoring_revision": TARGET_SCORING_REVISION,
        "diagnostic_revision": "unapproved-correction-site-v1",
        "evaluation_date": "November 14, 2026",
        "run_id": f"blind-suite-v4-{outputs_digest[:16]}",
        "dataset_sha256": dataset_digest,
        "cached_outputs_sha256": outputs_digest,
        "target_scoring_methodology_note": (
            "Accepted forms are matched at aligned annotated source sites. "
            "An unchanged source counts only when explicitly accepted; "
            "identity-only annotations are excluded. Target hits are pooled."
        ),
        "engine_run_metadata": {
            engine: {
                "version": "not reported",
                "source_run_id": "not recorded",
                "collection_timestamp_utc": "not recorded",
                "collection_mode": COLLECTION_MODES[engine],
                "collection_route": COLLECTION_ROUTES[engine],
                "source_url": COLLECTION_SOURCE_URLS[engine],
                "locale": COLLECTION_LOCALES[engine],
            }
            for engine in ENGINES
        },
        "mode": "cached",
        "latency_methodology": (
            "Arithmetic mean of non-null per-passage latencies recorded in "
            "the cached output log; null when no timing was recorded."
        ),
        "diagnostic_methodology_note": (
            "Counts edits at annotated spelling and grammar sites that are not "
            "unchanged or an accepted form shared across engines. This deterministic "
            "lexical diagnostic is not a general hallucination or semantic-correctness rate."
        ),
        "quality_composite_weights": {
            "spelling": 0.4375,
            "grammar": 0.3125,
            "voice": 0.25,
        },
        "engines": {},
    }

    for engine in ENGINES:
        spelling_hits = 0
        grammar_hits = 0
        spelling_total = 0
        grammar_total = 0
        voice_metrics_by_passage = []
        voice_precisions = []
        voice_recalls = []
        diagnostics = []
        sari_scores = []

        for passage_id in passage_ids:
            unit = live_runs[passage_id]
            ground_truth = GROUND_TRUTH[passage_id]
            engine_run = unit[engine]
            output_text = engine_run["text"]
            spelling_result = score_target_accuracy(
                unit["input"], output_text, ground_truth["spelling"]
            )
            grammar_result = score_target_accuracy(
                unit["input"], output_text, ground_truth["grammar"]
            )
            spelling_hits += spelling_result["accepted_targets"]
            spelling_total += spelling_result["total_targets"]
            grammar_hits += grammar_result["accepted_targets"]
            grammar_total += grammar_result["total_targets"]

            voice_metrics = score_writer_voice(
                unit["input"],
                output_text,
                ground_truth["spelling"],
                ground_truth["grammar"],
                ground_truth["voice_markers"],
                forbidden_rewrites=ground_truth["over_edits"],
            )
            voice_metrics_by_passage.append(voice_metrics)
            voice_precisions.append(voice_metrics["precision"])
            voice_recalls.append(voice_metrics["recall"])
            diagnostics.append(
                score_correction_sites(
                    unit["input"],
                    output_text,
                    [ground_truth["spelling"], ground_truth["grammar"]],
                )
            )
            sari_scores.append(
                calculate_sari_keep(
                    unit["input"], GOLD_REFERENCES[passage_id], output_text
                )
            )

        spelling_accuracy = (
            round(spelling_hits / spelling_total * 100.0, 1)
            if spelling_total
            else 100.0
        )
        grammar_accuracy = (
            round(grammar_hits / grammar_total * 100.0, 1)
            if grammar_total
            else 100.0
        )
        voice_summary = aggregate_writer_voice(voice_metrics_by_passage)
        all_sites = [site for diagnostic in diagnostics for site in diagnostic["sites"]]
        applicable_sites = len(all_sites)
        unapproved_edits = sum(
            site["classification"] == "unapproved_edit" for site in all_sites
        )
        unchanged_sites = sum(
            site["classification"] == "unchanged" for site in all_sites
        )
        accepted_corrections = sum(
            site["classification"] == "accepted_correction" for site in all_sites
        )
        quality_composite = round(
            0.4375 * spelling_accuracy
            + 0.3125 * grammar_accuracy
            + 0.25 * voice_summary["score"],
            1,
        )
        average_latency, latency_samples = _recorded_latency(
            live_runs, engine, passage_ids
        )
        report["engines"][engine] = {
            "spelling_accuracy": spelling_accuracy,
            "spelling_accepted_targets": spelling_hits,
            "spelling_total_targets": spelling_total,
            "grammar_accuracy": grammar_accuracy,
            "grammar_accepted_targets": grammar_hits,
            "grammar_total_targets": grammar_total,
            "voice_preservation": round(voice_summary["score"], 1),
            "voice_precision": round(sum(voice_precisions) / len(voice_precisions), 1),
            "voice_recall": round(sum(voice_recalls) / len(voice_recalls), 1),
            "voice_lexical_f1": round(voice_summary["lexical_f1"], 1),
            "voice_marker_retention": round(
                voice_summary["voice_marker_retention"], 1
            ),
            "voice_over_edit_penalty": round(
                voice_summary["over_edit_penalty"], 1
            ),
            "correction_site_diagnostic": {
                "applicable_sites": applicable_sites,
                "unchanged_sites": unchanged_sites,
                "accepted_corrections": accepted_corrections,
                "unapproved_edits": unapproved_edits,
                "unapproved_edit_rate": (
                    round(unapproved_edits / applicable_sites * 100.0, 1)
                    if applicable_sites
                    else None
                ),
            },
            "quality_composite": quality_composite,
            "latency_ms": average_latency,
            "latency_samples": latency_samples,
            "sari_keep_score": round(sum(sari_scores) / len(sari_scores), 1),
        }

    print("VOICE-PRESERVING AI-SPELLCHECK BENCHMARK - BLIND SUITE v4.0")
    print(
        f"{'Engine':<26} | {'Spell':>7} | {'Grammar':>7} | {'Voice':>7} | "
        f"{'Unapproved / sites':>20} | {'Quality':>8}"
    )
    for engine, scores in report["engines"].items():
        diagnostic = scores["correction_site_diagnostic"]
        rate = diagnostic["unapproved_edit_rate"]
        formatted_diagnostic = (
            f"{diagnostic['unapproved_edits']}/{diagnostic['applicable_sites']} "
            f"({rate:.1f}%)"
            if rate is not None
            else "n/a"
        )
        print(
            f"{engine:<26} | {scores['spelling_accuracy']:>6.1f}% | "
            f"{scores['grammar_accuracy']:>6.1f}% | "
            f"{scores['voice_preservation']:>6.1f}% | "
            f"{formatted_diagnostic:>20} | "
            f"{scores['quality_composite']:>7.1f}%"
        )

    with open(export_path, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)
    print(f"Saved v4 evaluation results to {export_path}")
    return report


if __name__ == "__main__":
    try:
        run_evaluation()
    except (FileNotFoundError, KeyError, TypeError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
