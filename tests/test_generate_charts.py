import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree

import generate_charts


class CurrentChartTests(unittest.TestCase):
    def test_v04_charts_include_every_engine_without_estimated_history(self):
        scores = generate_charts._load_results()
        builders = (
            generate_charts.build_quality_chart,
            generate_charts.build_pillars_chart,
            generate_charts.build_diagnostic_chart,
            generate_charts.build_latency_chart,
        )
        with tempfile.TemporaryDirectory() as output_directory:
            with patch.object(generate_charts, "ASSETS", Path(output_directory)):
                for builder in builders:
                    builder(scores)
            charts = {
                path.name: path.read_text(encoding="utf-8")
                for path in Path(output_directory).glob("*.svg")
            }

        self.assertEqual(
            set(charts),
            {
                "hybrid_score_comparison.svg",
                "pillars_breakdown.svg",
                "correction_site_diagnostic.svg",
                "latency_comparison.svg",
            },
        )
        for chart_name, chart in charts.items():
            ElementTree.fromstring(chart)
            for engine in generate_charts.CURRENT_ENGINE_COLORS:
                self.assertIn(engine, chart, chart_name)
            self.assertNotIn("estimate", chart.lower(), chart_name)
            self.assertNotIn("v0.3", chart.lower(), chart_name)

    def test_pillars_profile_chart_renders_all_competitors_and_pillars(self):
        scores = generate_charts._load_results()
        with tempfile.TemporaryDirectory() as output_directory:
            with patch.object(generate_charts, "ASSETS", Path(output_directory)):
                generate_charts.build_pillars_profile_chart(scores)
            chart = (Path(output_directory) / "pillars_profile.svg").read_text(encoding="utf-8")

        ElementTree.fromstring(chart)
        self.assertIn("THE 4 EVALUATION PILLARS: ENGINE BREAKDOWN", chart)
        self.assertIn("P1: Spelling", chart)
        self.assertIn("P2: Grammar", chart)
        self.assertIn("P3: Voice", chart)
        self.assertIn("P4: Site Retention", chart)
        self.assertIn("<polyline", chart)
        for engine in generate_charts.CURRENT_ENGINE_COLORS:
            self.assertIn(engine, chart)

    def test_pillar_engine_labels_do_not_overlap_the_bars(self):
        scores = generate_charts._load_results()
        with tempfile.TemporaryDirectory() as output_directory:
            with patch.object(generate_charts, "ASSETS", Path(output_directory)):
                generate_charts.build_pillars_chart(scores)
            chart = ElementTree.parse(
                Path(output_directory) / "pillars_breakdown.svg"
            ).getroot()

        namespace = {"svg": "http://www.w3.org/2000/svg"}
        texts = {
            element.text: element
            for element in chart.findall("svg:text", namespace)
            if element.text
        }
        first_column_background = next(
            element
            for element in chart.findall("svg:rect", namespace)
            if element.attrib.get("fill") == "#161b22"
        )
        self.assertEqual(first_column_background.attrib["x"], "390")
        for engine in generate_charts.CURRENT_ENGINE_COLORS:
            self.assertEqual(texts[engine].attrib["x"], "350")
            self.assertGreater(
                float(first_column_background.attrib["x"])
                - float(texts[engine].attrib["x"]),
                30,
            )

    def test_history_chart_shows_separate_measured_rubrics(self):
        snapshots = generate_charts._load_quality_history()
        with tempfile.TemporaryDirectory() as output_directory:
            with patch.object(generate_charts, "ASSETS", Path(output_directory)):
                generate_charts.build_quality_history_chart(snapshots)
            chart = (
                Path(output_directory) / "quality_history.svg"
            ).read_text(encoding="utf-8")

        ElementTree.fromstring(chart)
        self.assertIn("v0.3", chart)
        self.assertIn("v0.4", chart)
        self.assertIn("93.8%", chart)
        self.assertIn("96.5%", chart)
        self.assertIn("not comparable", chart)
        self.assertIn("no earlier measured trend", chart)
        self.assertNotIn("<polyline", chart)

    def test_history_rejects_pillar_values_that_differ_from_source_artifact(self):
        history = json.loads(
            generate_charts.QUALITY_HISTORY_PATH.read_text(encoding="utf-8")
        )
        history["snapshots"][1]["pillars"]["DeepL Write"]["spelling"] = 0.0
        with tempfile.TemporaryDirectory() as directory:
            history_path = Path(directory) / "quality_history.json"
            history_path.write_text(json.dumps(history), encoding="utf-8")
            with patch.object(generate_charts, "QUALITY_HISTORY_PATH", history_path):
                with self.assertRaisesRegex(ValueError, "does not match"):
                    generate_charts._load_quality_history()

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
            chart = (
                Path(output_directory) / "correction_site_diagnostic.svg"
            ).read_text(encoding="utf-8")

        self.assertIn("n/a (0/0)", chart)

    def test_latency_chart_explains_unavailable_web_demo_timings(self):
        scores = generate_charts._load_results()
        with tempfile.TemporaryDirectory() as output_directory:
            with patch.object(generate_charts, "ASSETS", Path(output_directory)):
                generate_charts.build_latency_chart(scores)
            chart = (
                Path(output_directory) / "latency_comparison.svg"
            ).read_text(encoding="utf-8")

        self.assertIn("n/a (web demo)", chart)
        self.assertIn("n/a (not recorded)", chart)

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
                path.name: path.read_text(encoding="utf-8")
                for path in Path(output_directory).glob("*.svg")
            }

        self.assertEqual(len(charts), len(builders))
        for chart_name, chart in charts.items():
            for engine in generate_charts.CURRENT_ENGINE_COLORS:
                self.assertIn(engine, chart, chart_name)
            self.assertIn("en-US", chart, chart_name)
            self.assertIn("en-GB", chart, chart_name)


if __name__ == "__main__":
    unittest.main()
