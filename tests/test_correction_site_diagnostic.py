import unittest

from correction_site_diagnostic import (
    score_correction_sites,
    score_target_accuracy,
)


class CorrectionSiteDiagnosticTests(unittest.TestCase):
    def test_accepts_approved_correction_and_unchanged_source(self):
        source = "My keybord is ready."
        targets = [{"keybord": ["keyboard"]}]

        corrected = score_correction_sites(source, "My keyboard is ready.", targets)
        unchanged = score_correction_sites(source, source, targets)

        self.assertEqual(corrected["accepted_corrections"], 1)
        self.assertEqual(corrected["unapproved_edits"], 0)
        self.assertEqual(unchanged["unchanged_sites"], 1)
        self.assertEqual(unchanged["unapproved_edit_rate"], 0.0)

    def test_flags_wrong_replacement_at_annotated_site(self):
        result = score_correction_sites(
            "My keybord is ready.",
            "My cupboard is ready.",
            [{"keybord": ["keyboard"]}],
        )

        self.assertEqual(result["applicable_sites"], 1)
        self.assertEqual(result["unapproved_edits"], 1)
        self.assertEqual(result["sites"][0]["observed"], "cupboard")

    def test_uses_same_rules_without_engine_specific_inputs(self):
        targets = [{"freind": ["friend"]}]
        outputs = [
            "My friend arrived.",
            "My freind arrived.",
            "My stranger arrived.",
        ]

        scores = [
            score_correction_sites("My freind arrived.", output, targets)
            for output in outputs
        ]

        self.assertEqual(
            [score["unapproved_edits"] for score in scores],
            [0, 0, 1],
        )

    def test_handles_adjacent_corrections_with_an_inserted_word(self):
        result = score_correction_sites(
            "My keybord glitchd.",
            "My keyboard is glitched.",
            [{"keybord": ["keyboard"], "glitchd": ["glitched"]}],
        )

        self.assertEqual(result["accepted_corrections"], 2)
        self.assertEqual(result["unapproved_edits"], 0)

    def test_does_not_accept_an_extra_word_at_a_single_target_site(self):
        result = score_correction_sites(
            "The typo is teh.",
            "The typo is the unicorn.",
            [{"teh": ["the"]}],
        )

        self.assertEqual(result["unapproved_edits"], 1)

    def test_reports_no_applicable_sites_as_not_applicable(self):
        result = score_correction_sites(
            "The original text has no annotated error.",
            "The revised text has no annotated error.",
            [{"typo": ["correction"]}],
        )

        self.assertEqual(result["applicable_sites"], 0)
        self.assertIsNone(result["unapproved_edit_rate"])

    def test_target_score_requires_a_correction_at_the_annotated_site(self):
        source = "My freind arrived. The word friend appears later."
        result = score_target_accuracy(
            source,
            source,
            {"freind": ["friend"]},
        )

        self.assertEqual(result["accepted_targets"], 0)
        self.assertEqual(result["total_targets"], 1)
        self.assertEqual(result["accuracy"], 0.0)

    def test_identity_annotations_do_not_count_as_correction_targets(self):
        result = score_target_accuracy(
            "Our cac dropped, but we moved to fast.",
            "Our CAC dropped, but we moved to fast.",
            {"cac": ["cac", "CAC"], "to fast": ["too fast"]},
        )

        self.assertEqual(result["accepted_targets"], 0)
        self.assertEqual(result["total_targets"], 1)
        self.assertEqual(result["accuracy"], 0.0)

    def test_locale_targets_can_score_an_accepted_unchanged_form(self):
        result = score_target_accuracy(
            "The flavor was excellent.",
            "The flavor was excellent.",
            {"flavor": ["flavor"]},
            include_identity_only=True,
        )

        self.assertEqual(result["accepted_targets"], 1)
        self.assertEqual(result["total_targets"], 1)
        self.assertEqual(result["accuracy"], 100.0)

    def test_explicitly_accepted_source_form_is_counted_at_its_site(self):
        result = score_target_accuracy(
            "We say cuz.",
            "We say cuz.",
            {"cuz": ["cuz", "because"]},
        )

        self.assertEqual(result["accepted_targets"], 1)
        self.assertEqual(result["total_targets"], 1)
        self.assertEqual(result["accuracy"], 100.0)


if __name__ == "__main__":
    unittest.main()
