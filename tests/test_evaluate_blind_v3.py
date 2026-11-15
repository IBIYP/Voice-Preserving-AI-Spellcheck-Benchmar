from pathlib import Path
import tempfile
import unittest
from xml.etree import ElementTree
from unittest.mock import patch

import generate_charts
from evaluate_blind_v3 import count_detected_hallucinations, run_evaluation


class CountDetectedHallucinationsTests(unittest.TestCase):
    def test_counts_only_signatures_present_in_output(self):
        signatures = ["incorrect substitution", "changed phrase", "missing phrase"]

        count = count_detected_hallucinations(
            "The output includes an Incorrect Substitution and a changed phrase.",
            signatures,
        )

        self.assertEqual(count, 2)

    def test_returns_zero_when_no_signatures_are_present(self):
        self.assertEqual(
            count_detected_hallucinations("A corrected output.", ["hallucination"]),
            0,
        )

    def test_live_mode_is_rejected_before_loading_cached_data(self):
        with self.assertRaisesRegex(ValueError, "live API evaluation is not implemented"):
            run_evaluation(mode="live")


class V4AlignedHistoryTests(unittest.TestCase):
    def test_alignment_uses_endpoint_delta_and_clamps_to_score_range(self):
        self.assertEqual(
            generate_charts._align_legacy_estimate_to_v4(40, 50, 45),
            35,
        )
        self.assertEqual(
            generate_charts._align_legacy_estimate_to_v4(95, 40, 60),
            100,
        )
        self.assertEqual(
            generate_charts._align_legacy_estimate_to_v4(5, 60, 40),
            0,
        )


class BenchmarkChartCoverageTests(unittest.TestCase):
    def test_generated_charts_include_all_competitors_and_mark_estimates(self):
        current_scores = generate_charts._load_results()
        legacy_scores = generate_charts._load_legacy_results()
        with tempfile.TemporaryDirectory() as output_directory:
            with patch.object(generate_charts, "ASSETS", Path(output_directory)):
                generate_charts.build_quality_chart(current_scores)
                generate_charts.build_pillars_chart(current_scores)
                generate_charts.build_diagnostic_chart(current_scores)
                generate_charts.build_latency_chart(current_scores)
                generate_charts.build_legacy_progress_chart(
                    legacy_scores,
                    current_scores,
                )
                generate_charts.build_legacy_progress_bar_chart(
                    legacy_scores,
                    current_scores,
                )
            charts = {
                chart_path.name: chart_path.read_text(encoding="utf-8")
                for chart_path in Path(output_directory).glob("*.svg")
            }

        self.assertEqual(len(charts), 6)
        current_charts = {
            "hybrid_score_comparison.svg",
            "pillars_breakdown.svg",
            "correction_site_diagnostic.svg",
            "latency_comparison.svg",
        }
        for chart_name, chart in charts.items():
            engines = generate_charts.CURRENT_ENGINE_COLORS
            for engine in engines:
                self.assertIn(engine, chart, chart_name)
        for chart_name in current_charts | {
            "progress_over_time.svg",
            "progress_bar_chart_over_time.svg",
        }:
            self.assertIn("Grammarly Free Grammar Checker", charts[chart_name])

        history = charts["progress_over_time.svg"]
        self.assertIn("v0.4-aligned historical estimate", history)
        self.assertIn("measured v0.3 composite", history)
        self.assertIn("measured v0.4 composite", history)
        self.assertIn("below-60% v0.3 upper bound", history)

        bar_chart = ElementTree.fromstring(
            charts["progress_bar_chart_over_time.svg"]
        )
        legend_colors = {
            element.text: element.attrib["fill"]
            for element in bar_chart.iter()
            if element.tag.endswith("text")
            and element.text in generate_charts.CURRENT_ENGINE_COLORS
        }
        self.assertEqual(legend_colors, generate_charts.CURRENT_ENGINE_COLORS)
        self.assertEqual(
            len(set(legend_colors.values())),
            len(generate_charts.CURRENT_ENGINE_COLORS),
        )

    def test_diagnostic_chart_renders_n_a_rates(self):
        scores = generate_charts._load_results()
        engine = next(iter(scores))
        scores[engine] = dict(scores[engine])
        scores[engine]["correction_site_diagnostic"] = dict(
            scores[engine]["correction_site_diagnostic"],
            applicable_sites=0,
            unapproved_edits=0,
            unapproved_edit_rate=None,
        )

        with tempfile.TemporaryDirectory() as output_directory:
            with patch.object(generate_charts, "ASSETS", Path(output_directory)):
                generate_charts.build_diagnostic_chart(scores)
            chart = (Path(output_directory) / "correction_site_diagnostic.svg").read_text(
                encoding="utf-8"
            )

        self.assertIn("n/a (0/0)", chart)

    def test_paired_locale_charts_render_every_engine_for_both_locales(self):
        baseline = generate_charts._load_results()
        paired = {
            "en-US": {"engine_summary": baseline},
            "en-GB": {"engine_summary": baseline},
        }
        builders = (
            generate_charts.build_paired_locale_quality_chart,
            generate_charts.build_paired_locale_pillars_chart,
            generate_charts.build_paired_locale_diagnostic_chart,
            generate_charts.build_paired_locale_latency_chart,
        )
        with tempfile.TemporaryDirectory() as output_directory:
            with patch.object(generate_charts, "ASSETS", Path(output_directory)):
                for builder in builders:
                    builder(paired)
            charts = {
                chart_path.name: chart_path.read_text(encoding="utf-8")
                for chart_path in Path(output_directory).glob("*.svg")
            }

        self.assertEqual(len(charts), len(builders))
        for chart_name, chart in charts.items():
            for engine in generate_charts.CURRENT_ENGINE_COLORS:
                self.assertIn(engine, chart, chart_name)
            self.assertIn("en-US", chart, chart_name)
            self.assertIn("en-GB", chart, chart_name)


if __name__ == "__main__":
    unittest.main()
