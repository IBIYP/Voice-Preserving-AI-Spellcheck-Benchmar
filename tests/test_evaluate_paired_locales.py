import json
import tempfile
import unittest
from pathlib import Path

from benchmark_4pillars_hybrid import (
    ENGINES,
    UNSEEN_BENCHMARK_UNITS,
    evaluate_unit,
)
from evaluate_paired_locales import (
    LOCALES,
    _validate_locale_runs,
    run_evaluation,
)


ROOT = Path(__file__).parents[1]


def _golden_texts():
    path = ROOT / "raw_results" / "h_suite_locale_golden_texts.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _complete_runs():
    references = _golden_texts()["passages"]
    return {
        "metadata": {
            "status": "complete",
            "collection_date": "2026-11-14",
        },
        "locale_runs": {
            locale: {
                "locale": locale,
                "passages": {
                    unit["id"]: {
                        engine: {
                            "text": references[unit["id"]][locale],
                            "lat": None,
                        }
                        for engine in ENGINES
                    }
                    for unit in UNSEEN_BENCHMARK_UNITS
                },
            }
            for locale in LOCALES
        },
    }


class PairedLocaleValidationTests(unittest.TestCase):
    def test_requires_both_locales_and_complete_engine_coverage(self):
        incomplete = _complete_runs()
        del incomplete["locale_runs"]["en-GB"]["passages"]["H-10"][ENGINES[0]]

        with self.assertRaisesRegex(ValueError, "engine coverage mismatch"):
            _validate_locale_runs(incomplete)

    def test_locale_spelling_targets_distinguish_us_and_uk_forms(self):
        unit = next(item for item in UNSEEN_BENCHMARK_UNITS if item["id"] == "H-04")
        passage = _golden_texts()["passages"]["H-04"]
        us_targets = {"flavor": "flavor"}
        gb_targets = {"flavor": "flavour"}

        us_result = evaluate_unit(
            unit, passage["en-US"], locale="en-US", locale_spelling_targets=us_targets
        )
        gb_result = evaluate_unit(
            unit, passage["en-GB"], locale="en-GB", locale_spelling_targets=gb_targets
        )
        wrong_locale = evaluate_unit(
            unit, passage["en-US"], locale="en-GB", locale_spelling_targets=gb_targets
        )

        self.assertEqual(us_result["spelling_target_count"], 5)
        self.assertEqual(us_result["spelling_target_hits"], 5)
        self.assertEqual(gb_result["spelling_target_hits"], 5)
        self.assertEqual(wrong_locale["spelling_target_hits"], 4)

    def test_paired_evaluator_writes_two_locale_scorecards(self):
        runs = _complete_runs()
        with tempfile.TemporaryDirectory() as temporary_directory:
            input_path = Path(temporary_directory) / "locale-runs.json"
            output_path = Path(temporary_directory) / "locale-scores.json"
            input_path.write_text(json.dumps(runs), encoding="utf-8")

            artifact = run_evaluation(input_path, output_path)

            self.assertTrue(output_path.exists())
            self.assertEqual(set(artifact["locales"]), set(LOCALES))
            for locale in LOCALES:
                self.assertEqual(
                    set(artifact["locales"][locale]["engine_summary"]),
                    set(ENGINES),
                )
                self.assertEqual(
                    len(artifact["locales"][locale]["passages"]),
                    len(UNSEEN_BENCHMARK_UNITS),
                )


if __name__ == "__main__":
    unittest.main()
