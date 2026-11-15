import unittest

from evaluate_blind_v4 import GROUND_TRUTH, _validate_live_runs


class BlindSuiteInputValidationTests(unittest.TestCase):
    def test_missing_engine_output_is_rejected(self):
        incomplete = {
            passage_id: {"input": "A test passage."}
            for passage_id in GROUND_TRUTH
        }

        with self.assertRaisesRegex(ValueError, "BCorrect \\(FMM\\).*B-01"):
            _validate_live_runs(incomplete)


if __name__ == "__main__":
    unittest.main()
