import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from benchmark_4pillars_hybrid import (
    UNSEEN_BENCHMARK_UNITS,
    _load_grammarly_runs,
    _validate_cached_runs,
    evaluate_unit,
)
from text_matching import score_writer_voice


class HSuiteScoringTests(unittest.TestCase):
    def test_h06_noop_annotations_do_not_earn_grammar_credit_or_change_voice_score(self):
        unit = next(item for item in UNSEEN_BENCHMARK_UNITS if item["id"] == "H-06")

        result = evaluate_unit(unit, unit["input"])
        expected_voice = score_writer_voice(
            unit["input"],
            unit["input"],
            unit["spelling_targets"],
            unit["grammar_targets"],
            unit["voice_tokens"],
            unit["dialect_equivalents"],
            unit["forbidden_rewrites"],
        )["score"]

        self.assertEqual(result["grammar_acc"], 0.0)
        self.assertEqual(result["grammar_target_hits"], 0)
        self.assertEqual(result["grammar_target_count"], 1)
        self.assertEqual(result["voice_preservation"], expected_voice)

    def test_missing_engine_output_is_rejected(self):
        unit = next(item for item in UNSEEN_BENCHMARK_UNITS if item["id"] == "H-01")
        incomplete = {"H-01": {"BCorrect (FMM)": {"text": unit["input"]}}}

        with patch("benchmark_4pillars_hybrid.UNSEEN_BENCHMARK_UNITS", [unit]):
            with self.assertRaisesRegex(ValueError, "LanguageTool API.*H-01"):
                _validate_cached_runs(incomplete)

    def test_complete_grammarly_h_suite_loads_without_inventing_latency(self):
        runs, metadata = _load_grammarly_runs()

        self.assertEqual(set(runs), {unit["id"] for unit in UNSEEN_BENCHMARK_UNITS})
        self.assertTrue(all(result["lat"] is None for result in runs.values()))
        self.assertEqual(metadata["collection_mode"], "web_demo")

    def test_incomplete_grammarly_h_suite_is_rejected(self):
        path = Path(__file__).parents[1] / "raw_results" / "grammarly_web_checker_outputs.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        del data["four_pillar"]["H-10"]

        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as file:
            json.dump(data, file)
            temporary_path = file.name
        try:
            with self.assertRaisesRegex(ValueError, "missing=.*H-10"):
                _load_grammarly_runs(temporary_path)
        finally:
            Path(temporary_path).unlink()

    def test_grammarly_web_demo_latency_must_remain_unmeasured(self):
        path = Path(__file__).parents[1] / "raw_results" / "grammarly_web_checker_outputs.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["four_pillar"]["H-01"]["lat"] = 123

        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as file:
            json.dump(data, file)
            temporary_path = file.name
        try:
            with self.assertRaisesRegex(ValueError, "latency must remain null"):
                _load_grammarly_runs(temporary_path)
        finally:
            Path(temporary_path).unlink()

    def test_locale_golden_references_cover_every_h_suite_passage(self):
        path = Path(__file__).parents[1] / "raw_results" / "h_suite_locale_golden_texts.json"
        references = json.loads(path.read_text(encoding="utf-8"))
        passages = references["passages"]

        self.assertEqual(set(passages), {unit["id"] for unit in UNSEEN_BENCHMARK_UNITS})
        self.assertTrue(
            all(
                isinstance(passage.get(locale), str) and passage[locale]
                for passage in passages.values()
                for locale in ("en-US", "en-GB")
            )
        )
        self.assertIn("flavor", passages["H-04"]["en-US"])
        self.assertIn("flavour", passages["H-04"]["en-GB"])
        self.assertIn("dreamed", passages["H-05"]["en-US"])
        self.assertIn("dreamt", passages["H-05"]["en-GB"])


if __name__ == "__main__":
    unittest.main()
