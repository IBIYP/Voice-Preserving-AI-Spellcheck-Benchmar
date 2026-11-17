import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

try:
    from evaluate_blind_v4 import (
        ENGINES,
        GROUND_TRUTH,
        _validate_live_runs,
        run_evaluation,
    )
except FileNotFoundError as error:
    raise unittest.SkipTest(str(error))


class BlindSuiteInputValidationTests(unittest.TestCase):
    def test_current_annotations_exclude_retired_score_fields(self):
        self.assertEqual(len(GROUND_TRUTH), 10)
        self.assertEqual(len(ENGINES), 6)
        for annotations in GROUND_TRUTH.values():
            current_fields = {"spelling", "grammar", "voice_markers", "over_edits"}
            self.assertTrue(current_fields.issubset(annotations))
            self.assertNotIn("hallucinations", annotations)

    def test_missing_engine_output_is_rejected(self):
        incomplete = {
            passage_id: {"input": "A test passage."}
            for passage_id in GROUND_TRUTH
        }

        with self.assertRaisesRegex(ValueError, "BCorrect \\(FMM\\).*B-01"):
            _validate_live_runs(incomplete)

    def test_scored_metadata_reports_routes_and_unrecorded_timestamps(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            export_path = Path(temp_dir) / "scoreboard.json"
            with redirect_stdout(io.StringIO()):
                report = run_evaluation(str(export_path))
            self.assertTrue(export_path.exists())

        self.assertEqual(set(report["engine_run_metadata"]), set(ENGINES))
        for metadata in report["engine_run_metadata"].values():
            self.assertEqual(metadata["collection_timestamp_utc"], "not recorded")
            self.assertIn("collection_route", metadata)
            self.assertIn("source_url", metadata)
            self.assertIn("locale", metadata)


if __name__ == "__main__":
    unittest.main()
