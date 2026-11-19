import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from run_h_suite_repeat import (
    ENGINE_NAMES,
    JSPELL_WEB_ENGINE,
    MANIFEST_PATH,
    ROOT,
    _empty_run,
    _available_repeat_engines,
    _load_or_create_run,
    _read_manifest,
    _request_bcorrect,
    _request_textgears,
    _score_suite,
    apply_textgears_suggestions,
    record_weekly_history,
)


class RepeatSuiteManifestTests(unittest.TestCase):
    def test_v2_manifest_matches_original_target_counts_and_does_not_overlap_v1(self):
        v1 = _read_manifest(MANIFEST_PATH)
        v2_path = ROOT / "benchmark_data" / "h_suite_repeat_v2.json"
        v2 = _read_manifest(v2_path)

        self.assertEqual(len(v2["passages"]), 10)
        self.assertEqual(
            sum(len(p["spelling_targets"]) for p in v2["passages"]),
            49,
        )
        self.assertEqual(
            sum(len(p["grammar_targets"]) for p in v2["passages"]),
            12,
        )
        v1_inputs = {p["input"] for p in v1["passages"]}
        v2_inputs = {p["input"] for p in v2["passages"]}
        self.assertFalse(v1_inputs & v2_inputs)

    def test_scoring_includes_jspell_web_when_complete(self):
        complete = {
            f"HR-{index:02d}": {
                "BCorrect (FMM)": {},
                "TextGears API": {},
                JSPELL_WEB_ENGINE: {},
            }
            for index in range(1, 11)
        }
        self.assertIn(JSPELL_WEB_ENGINE, _available_repeat_engines(complete))

    def test_record_weekly_history_upserts_without_duplicating_batch(self):
        manifest = _read_manifest(ROOT / "benchmark_data" / "h_suite_repeat_v2.json")
        fake_scorecard = {
            "repeat_dataset_sha256": "abc123",
            "new_repeat_suite": {
                "engine_summary": {
                    "BCorrect (FMM)": {"quality_composite": 75.0},
                }
            },
            "jspell_same_api_control": {
                "status": "blocked",
                "engine": "JSpell Cloud Spell Check API",
                "old_h_suite_score": None,
                "new_repeat_suite_score": None,
                "error": "blocked",
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            history_path = Path(tmp) / "history.json"
            score_path = ROOT / "raw_results" / "h_suite_repeat_v2_scores.json"
            record_weekly_history(
                manifest, fake_scorecard, score_path=score_path, history_path=history_path
            )
            history = record_weekly_history(
                manifest, fake_scorecard, score_path=score_path, history_path=history_path
            )
            self.assertEqual(len(history["entries"]), 1)
            self.assertEqual(history["entries"][0]["suite_id"], "h-suite-repeat-v2")

    def test_new_passages_match_original_target_counts_and_accept_annotations(self):
        manifest = _read_manifest()

        self.assertEqual(len(manifest["passages"]), 10)
        self.assertEqual(
            sum(len(passage["spelling_targets"]) for passage in manifest["passages"]),
            49,
        )
        self.assertEqual(
            sum(len(passage["grammar_targets"]) for passage in manifest["passages"]),
            12,
        )
        self.assertEqual(manifest["metadata"]["status"], "frozen")
        self.assertTrue(MANIFEST_PATH.is_file())

    def test_resume_adds_provider_failures_field_to_older_partial_run(self):
        manifest = _read_manifest()
        old_run = _empty_run(manifest)
        old_run.pop("provider_failures")

        with tempfile.TemporaryDirectory() as temporary_directory:
            run_path = Path(temporary_directory) / "partial.json"
            run_path.write_text(json.dumps(old_run), encoding="utf-8")
            with patch("run_h_suite_repeat.RUNS_PATH", run_path):
                resumed = _load_or_create_run(manifest, resume=True)

        self.assertEqual(resumed["provider_failures"], {})

    def test_scoring_includes_deepl_only_when_every_passage_has_its_output(self):
        complete = {
            f"HR-{index:02d}": {
                "BCorrect (FMM)": {},
                "TextGears API": {},
                "DeepL Write": {},
            }
            for index in range(1, 11)
        }
        partial = {
            **complete,
            "HR-10": {"BCorrect (FMM)": {}, "TextGears API": {}},
        }

        self.assertIn("DeepL Write", _available_repeat_engines(complete))
        self.assertNotIn("DeepL Write", _available_repeat_engines(partial))

    def test_fully_corrected_repeat_outputs_score_under_the_shared_rubric(self):
        manifest = _read_manifest()
        outputs = {}
        for passage in manifest["passages"]:
            corrected = passage["input"]
            for source, target in passage["spelling_targets"].items():
                corrected = corrected.replace(source, target, 1)
            for source, target in passage["grammar_targets"].items():
                corrected = corrected.replace(source, target, 1)
            outputs[passage["id"]] = {
                engine: {"text": corrected} for engine in ENGINE_NAMES
            }

        summary, _ = _score_suite(manifest["passages"], outputs, ENGINE_NAMES)

        for score in summary.values():
            self.assertEqual(score["spelling_accuracy"], 100.0)
            self.assertEqual(score["grammar_accuracy"], 100.0)
            self.assertEqual(score["quality_composite"], 100.0)


class ProviderAdapterTests(unittest.TestCase):
    def test_textgears_applies_suggestions_using_original_offsets(self):
        text = "The freind was in the gardn."
        errors = [
            {
                "offset": text.index("gardn"),
                "length": len("gardn"),
                "bad": "gardn",
                "better": ["garden"],
            },
            {
                "offset": text.index("freind"),
                "length": len("freind"),
                "bad": "freind",
                "better": ["friend", "fiend"],
            },
        ]

        self.assertEqual(
            apply_textgears_suggestions(text, errors),
            "The friend was in the garden.",
        )

    def test_textgears_rejects_an_offset_that_does_not_match_the_input(self):
        with self.assertRaisesRegex(ValueError, "does not match"):
            apply_textgears_suggestions(
                "The freind arrived.",
                [{
                    "offset": 4,
                    "length": 6,
                    "bad": "friend",
                    "better": ["friend"],
                }],
            )

    def test_bcorrect_request_uses_saved_api_contract_and_validates_response(self):
        text = "The freind arrived."
        response = {
            "originalText": text,
            "correctedText": "The friend arrived.",
            "corrections": [],
        }
        with patch(
            "run_h_suite_repeat._request_json",
            return_value=(response, 8.5, "started", "completed", 200),
        ) as request:
            result = _request_bcorrect(text, "test-secret")

        self.assertEqual(result["text"], "The friend arrived.")
        self.assertEqual(result["latency_ms"], 8.5)
        args, kwargs = request.call_args
        self.assertEqual(args[0], "https://bcorrect-api.fly.dev/api/v1/check")
        self.assertEqual(args[1]["X-API-Key"], "test-secret")
        self.assertEqual(
            json.loads(kwargs["data"]),
            {"text": text, "locale": "en-US"},
        )

    def test_textgears_request_uses_correct_endpoint(self):
        text = "The freind arrived."
        response = {"status": True, "response": {"corrected": "The friend arrived."}}
        with patch(
            "run_h_suite_repeat._request_json",
            return_value=(response, 8.5, "started", "completed", 200),
        ) as request:
            result = _request_textgears(text, "test-secret")

        self.assertEqual(result["text"], "The friend arrived.")
        args, kwargs = request.call_args
        self.assertEqual(
            args[0],
            "https://textgears-textgears-v1.p.rapidapi.com/correct",
        )
        self.assertEqual(args[1]["X-RapidAPI-Key"], "test-secret")
        self.assertEqual(
            args[1]["X-RapidAPI-Host"],
            "textgears-textgears-v1.p.rapidapi.com",
        )
        self.assertEqual(
            args[1]["Content-Type"],
            "application/x-www-form-urlencoded",
        )
        self.assertEqual(
            kwargs["data"].decode("utf-8"),
            "text=The+freind+arrived.&language=en-US",
        )


if __name__ == "__main__":
    unittest.main()
