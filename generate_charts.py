"""Generate current v0.4 charts from saved H-suite artifacts."""

import html
import json
from pathlib import Path


ROOT = Path(__file__).parent
RESULTS_PATH = ROOT / "raw_results" / "blind_4pillars_eval_run_v4.json"
PAIRED_RESULTS_PATH = ROOT / "raw_results" / "h_suite_locale_eval_v1.json"
QUALITY_HISTORY_PATH = ROOT / "raw_results" / "quality_history.json"
ASSETS = ROOT / "assets"

CURRENT_ENGINE_COLORS = {
    "BCorrect (FMM)": "#D86C1C",
    "LanguageTool API": "#409DC6",
    "TextGears API": "#F2E8DB",
    "DeepL Write": "#D5CDE1",
    "Sapling Grammar Checker": "#E9DFA9",
    "JSpell Free Web Checker": "#D47440",
    "Grammarly Free Grammar Checker": "#D8976F",
}


def _validate_engine_roster(scores, source, expected_engines):
    if set(scores) != set(expected_engines):
        missing = sorted(set(expected_engines) - set(scores))
        unexpected = sorted(set(scores) - set(expected_engines))
        details = []
        if missing:
            details.append("missing: " + ", ".join(missing))
        if unexpected:
            details.append("unexpected: " + ", ".join(unexpected))
        raise ValueError(f"{source} competitor roster mismatch ({'; '.join(details)})")




def _load_results():
    with RESULTS_PATH.open("r", encoding="utf-8") as file:
        results = json.load(file)
    if results["benchmark_metadata"].get("version") != "4.0":
        raise ValueError(f"{RESULTS_PATH} does not contain v4.0 results")
    summary = results["engine_summary"]
    _validate_engine_roster(summary, str(RESULTS_PATH), CURRENT_ENGINE_COLORS)
    return summary


def _load_paired_results():
    with PAIRED_RESULTS_PATH.open("r", encoding="utf-8") as file:
        results = json.load(file)
    if results["benchmark_metadata"].get("version") != "4.1-locale-paired":
        raise ValueError(f"{PAIRED_RESULTS_PATH} does not contain paired locale results")
    locale_results = results["locales"]
    if set(locale_results) != {"en-US", "en-GB"}:
        raise ValueError(f"{PAIRED_RESULTS_PATH} must contain en-US and en-GB")
    for locale, result in locale_results.items():
        _validate_engine_roster(
            result["engine_summary"],
            f"{PAIRED_RESULTS_PATH} ({locale})",
            CURRENT_ENGINE_COLORS,
        )
    return locale_results


def _load_quality_history():
    with QUALITY_HISTORY_PATH.open("r", encoding="utf-8") as file:
        history = json.load(file)
    if history.get("schema_version") not in (1, 2):
        raise ValueError(f"{QUALITY_HISTORY_PATH} has an unsupported schema version")
    snapshots = history.get("snapshots")
    if not isinstance(snapshots, list) or not snapshots:
        raise ValueError(f"{QUALITY_HISTORY_PATH} must contain measured snapshots")

    loaded = []
    seen_ids = set()
    required_fields = {
        "id",
        "release",
        "artifact",
        "result_version",
        "score_field",
        "metric",
        "methodology",
    }
    for snapshot in snapshots:
        if not isinstance(snapshot, dict) or not required_fields.issubset(snapshot):
            raise ValueError(f"Invalid snapshot entry in {QUALITY_HISTORY_PATH}")
        if snapshot["id"] in seen_ids:
            raise ValueError(f"Duplicate snapshot id: {snapshot['id']}")
        seen_ids.add(snapshot["id"])
        artifact_path = (ROOT / snapshot["artifact"]).resolve()
        try:
            artifact_path.relative_to(ROOT.resolve())
        except ValueError as error:
            raise ValueError("Quality-history artifacts must be inside the repository") from error
        with artifact_path.open("r", encoding="utf-8") as file:
            artifact = json.load(file)
        metadata = artifact.get("benchmark_metadata", {})
        if metadata.get("version") != snapshot["result_version"]:
            raise ValueError(
                f"{artifact_path} does not contain version "
                f"{snapshot['result_version']}"
            )
        summary = artifact.get("engine_summary")
        if not isinstance(summary, dict) or not summary:
            raise ValueError(f"{artifact_path} has no engine summary")
        if history["schema_version"] == 2:
            pillar_fields = snapshot.get("pillar_fields")
            pillars = snapshot.get("pillars")
            if not isinstance(pillar_fields, dict) or not pillar_fields:
                raise ValueError(
                    f"{snapshot['id']} has no artifact field mapping for its pillars"
                )
            if not isinstance(pillars, dict) or set(pillars) != set(summary):
                raise ValueError(
                    f"{snapshot['id']} pillar engine roster does not match "
                    f"{artifact_path}"
                )
            for engine, recorded_pillars in pillars.items():
                if (
                    not isinstance(recorded_pillars, dict)
                    or set(recorded_pillars) != set(pillar_fields)
                ):
                    raise ValueError(
                        f"{snapshot['id']} has invalid pillar fields for {engine}"
                    )
                for pillar, field_path in pillar_fields.items():
                    if not isinstance(field_path, str) or not field_path:
                        raise ValueError(
                            f"{snapshot['id']} has an invalid source for pillar {pillar}"
                        )
                    source_value = summary[engine]
                    for field in field_path.split("."):
                        if not isinstance(source_value, dict) or field not in source_value:
                            raise ValueError(
                                f"{snapshot['id']} source field {field_path} is missing "
                                f"for {engine}"
                            )
                        source_value = source_value[field]
                    if recorded_pillars[pillar] != source_value:
                        raise ValueError(
                            f"{snapshot['id']} pillar {pillar} for {engine} does not "
                            f"match {artifact_path}"
                        )
        scores = {}
        for engine, result in summary.items():
            score = result.get(snapshot["score_field"])
            if (
                isinstance(score, bool)
                or not isinstance(score, (int, float))
                or not 0 <= score <= 100
            ):
                raise ValueError(
                    f"Invalid {snapshot['score_field']} score for {engine} "
                    f"in {artifact_path}"
                )
            scores[engine] = score
        evaluation_date = metadata.get("eval_date")
        if not isinstance(evaluation_date, str) or not evaluation_date:
            raise ValueError(f"{artifact_path} has no evaluation date")
        loaded.append(
            {
                **snapshot,
                "evaluation_date": evaluation_date,
                "scores": scores,
            }
        )
    return loaded


def _start_svg(width, height, title, subtitle):
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        'style="background:#0d1117; font-family:-apple-system,BlinkMacSystemFont,'
        '\'Segoe UI\',Helvetica,Arial,sans-serif;">',
        f'<rect x="1" y="1" width="{width - 2}" height="{height - 2}" '
        'fill="none" stroke="#30363d" stroke-width="1"/>',
        f'<text x="{width / 2:g}" y="32" fill="#f0f6fc" font-size="18" '
        f'font-weight="700" text-anchor="middle">{html.escape(title)}</text>',
        f'<text x="{width / 2:g}" y="54" fill="#8b949e" font-size="13" '
        f'text-anchor="middle">{html.escape(subtitle)}</text>',
    ]


def _write_svg(filename, lines):
    lines.append("</svg>")
    (ASSETS / filename).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Generated assets/{filename}")


def build_quality_chart(scores):
    engines = sorted(
        scores.items(),
        key=lambda item: item[1]["quality_composite"],
        reverse=True,
    )
    height = 100 + len(engines) * 42 + 62
    svg = _start_svg(
        1200,
        height,
        "V0.4 H-SUITE QUALITY COMPOSITE",
        "Public benchmark release v0.4 (result artifact version 4.0); single-locale baseline",
    )
    x0, chart_width = 300, 760
    for pct in (0, 25, 50, 75, 100):
        x = x0 + chart_width * pct / 100
        svg.append(
            f'<line x1="{x:g}" y1="68" x2="{x:g}" y2="{height - 48}" '
            f'stroke="#30363d" stroke-width="1"/>'
        )
        svg.append(
            f'<text x="{x:g}" y="{height - 28}" fill="#8b949e" font-size="10" '
            f'text-anchor="middle">{pct}%</text>'
        )
    for index, (engine, result) in enumerate(engines):
        y = 76 + index * 42
        score = result["quality_composite"]
        color = CURRENT_ENGINE_COLORS[engine]
        svg.append(
            f'<text x="288" y="{y + 17}" fill="{color}" font-size="11" '
            f'text-anchor="end">{html.escape(engine)}</text>'
        )
        svg.append(
            f'<rect x="{x0}" y="{y}" width="{chart_width * score / 100:.2f}" '
            f'height="24" fill="{color}" stroke="#f0f6fc" stroke-width="1"/>'
        )
        svg.append(
            f'<text x="{x0 + chart_width * score / 100 + 8:.2f}" y="{y + 17}" '
            f'fill="#f0f6fc" font-size="11" font-weight="700">{score:.1f}%</text>'
        )
    svg.append(
        f'<text x="600" y="{height - 6}" fill="#8b949e" font-size="10" '
        'text-anchor="middle">Weights: spelling 43.75%, grammar 31.25%, voice 25% '
        '| November 14, 2026</text>'
    )
    _write_svg("hybrid_score_comparison.svg", svg)


def build_pillars_chart(scores):
    engines = sorted(
        scores.items(),
        key=lambda item: item[1]["quality_composite"],
        reverse=True,
    )
    height = 145 + len(engines) * 54 + 40
    svg = _start_svg(
        1400,
        height,
        "V0.4 H-SUITE QUALITY PILLARS",
        "Single-locale baseline; locale settings vary or are unreported",
    )
    columns = [
        ("Spelling", "spelling_accuracy"),
        ("Grammar", "grammar_accuracy"),
        ("Voice", "voice_preservation"),
    ]
    x_positions = [500, 800, 1100]
    for (label, _), x in zip(columns, x_positions):
        svg.append(
            f'<text x="{x}" y="88" fill="#f0f6fc" font-size="16" '
            f'font-weight="700" text-anchor="middle">{label}</text>'
        )
    for row, (engine, result) in enumerate(engines):
        y = 112 + row * 54
        color = CURRENT_ENGINE_COLORS[engine]
        svg.append(
            f'<text x="350" y="{y + 20}" fill="{color}" font-size="16" '
            f'text-anchor="end">{html.escape(engine)}</text>'
        )
        for (_, key), x in zip(columns, x_positions):
            score = result[key]
            bar_x = x - 110
            svg.append(
                f'<rect x="{bar_x}" y="{y}" width="220" height="28" '
                'fill="#161b22" stroke="#30363d" stroke-width="1"/>'
            )
            svg.append(
                f'<rect x="{bar_x}" y="{y}" width="{220 * score / 100:.2f}" '
                f'height="28" fill="{color}" opacity="0.72"/>'
            )
            svg.append(
                f'<text x="{x + 120}" y="{y + 20}" fill="#f0f6fc" font-size="13" '
                f'font-weight="700">{score:.1f}%</text>'
            )
    svg.append(
        f'<text x="700" y="{height - 8}" fill="#8b949e" font-size="12" '
        'text-anchor="middle">Scores are recomputed from saved H-suite outputs under v4.0</text>'
    )
    _write_svg("pillars_breakdown.svg", svg)


def build_pillars_profile_chart(scores):
    """Parallel coordinates profile line chart across evaluation pillars.
    Draws a distinct line for each competitor across P1 (Spelling), P2 (Grammar),
    P3 (Voice), and P4 (Site Retention) showing distinct engineering tradeoffs.
    """
    width = 1200
    height = 540
    svg = _start_svg(
        width,
        height,
        "THE 4 EVALUATION PILLARS: ENGINE BREAKDOWN",
        "H-01 to H-10 | Voice scoring: lexical-marker-f1-v2 | November 14, 2026",
    )

    columns = [
        ("P1: Spelling", "spelling_accuracy", "43.75% weight", 240),
        ("P2: Grammar", "grammar_accuracy", "31.25% weight", 520),
        ("P3: Voice", "voice_preservation", "25.0% weight", 800),
        ("P4: Site Retention", "site_retention", "100% - Unapproved", 1040),
    ]

    y_top = 100
    y_bottom = 400
    y_range = y_bottom - y_top

    for pct in (0, 25, 50, 75, 100):
        y_line = y_bottom - (pct * y_range / 100)
        dash = ' stroke-dasharray="2 2"' if pct > 0 else ""
        svg.append(
            f'<line x1="120" y1="{y_line:g}" x2="1140" y2="{y_line:g}" '
            f'stroke="#30363d" stroke-width="1"{dash}/>'
        )
        svg.append(
            f'<text x="110" y="{y_line + 4:g}" fill="#8b949e" font-size="10" '
            f'text-anchor="end">{pct}%</text>'
        )

    for title, _, weight_subtext, x in columns:
        svg.append(
            f'<line x1="{x}" y1="{y_top}" x2="{x}" y2="{y_bottom}" '
            'stroke="#21262d" stroke-width="1" stroke-dasharray="3 3"/>'
        )
        svg.append(
            f'<text x="{x}" y="{y_bottom + 22}" fill="#f0f6fc" font-size="11" '
            f'font-weight="700" text-anchor="middle">{title}</text>'
        )
        svg.append(
            f'<text x="{x}" y="{y_bottom + 36}" fill="#8b949e" font-size="10" '
            f'text-anchor="middle">({weight_subtext})</text>'
        )

    engine_styles = {
        "BCorrect (FMM)": {"stroke": "#ffffff", "width": 3, "dash": "", "marker": "square_solid"},
        "DeepL Write": {"stroke": "#D5CDE1", "width": 2, "dash": ' stroke-dasharray="2 3"', "marker": "square_open"},
        "TextGears API": {"stroke": "#F2E8DB", "width": 2, "dash": ' stroke-dasharray="6 3"', "marker": "square_solid"},
        "LanguageTool API": {"stroke": "#409DC6", "width": 2, "dash": ' stroke-dasharray="6 3 2 3"', "marker": "square_open"},
        "Sapling Grammar Checker": {"stroke": "#E9DFA9", "width": 2, "dash": ' stroke-dasharray="4 2"', "marker": "square_solid"},
        "JSpell Free Web Checker": {"stroke": "#D47440", "width": 2, "dash": ' stroke-dasharray="2 4"', "marker": "square_open"},
        "Grammarly Free Grammar Checker": {"stroke": "#D8976F", "width": 2, "dash": ' stroke-dasharray="5 3"', "marker": "square_solid"},
    }

    for engine, style in engine_styles.items():
        if engine not in scores:
            continue
        data = scores[engine]
        points = []
        coords = []
        for _, key, _, x in columns:
            if key == "site_retention":
                diag = data.get("correction_site_diagnostic", {})
                rate = diag.get("unapproved_edit_rate")
                val = 100.0 - rate if rate is not None else 100.0
            else:
                val = data.get(key, 0.0)
            val = max(0.0, min(100.0, float(val)))
            y_pos = y_bottom - (val * y_range / 100.0)
            coords.append((x, y_pos, val))
            points.append(f"{x:g},{y_pos:g}")

        svg.append(
            f'<polyline points="{" ".join(points)}" fill="none" stroke="{style["stroke"]}" '
            f'stroke-width="{style["width"]}"{style["dash"]}/>'
        )

        for x, y_pos, val in coords:
            fill = style["stroke"] if style["marker"] == "square_solid" else "#0d1117"
            svg.append(
                f'<rect x="{x - 4}" y="{y_pos - 4}" width="8" height="8" '
                f'fill="{fill}" stroke="{style["stroke"]}" stroke-width="1.5"/>'
            )
            if engine == "BCorrect (FMM)":
                offset_y = -8
                weight_val = ' font-weight="700"'
                label_color = "#ffffff"
            elif engine in ("DeepL Write", "Sapling Grammar Checker"):
                offset_y = -8
                weight_val = ""
                label_color = style["stroke"]
            else:
                offset_y = 14
                weight_val = ""
                label_color = style["stroke"]
            svg.append(
                f'<text x="{x + 6}" y="{y_pos + offset_y}" fill="{label_color}" '
                f'font-size="9"{weight_val}>{val:.0f}%</text>'
            )

    svg.append(
        '<rect x="80" y="475" width="1040" height="42" fill="#161b22" '
        'stroke="#30363d" stroke-width="1"/>'
    )
    legend_engines = [e for e in engine_styles if e in scores]
    legend_spacing = 1040 / max(1, len(legend_engines))
    for i, engine in enumerate(legend_engines):
        style = engine_styles[engine]
        lx = 95 + i * legend_spacing
        ly = 496
        svg.append(
            f'<line x1="{lx}" y1="{ly}" x2="{lx + 18}" y2="{ly}" stroke="{style["stroke"]}" '
            f'stroke-width="{style["width"]}"{style["dash"]}/>'
        )
        fill = style["stroke"] if style["marker"] == "square_solid" else "#0d1117"
        svg.append(
            f'<rect x="{lx + 5}" y="{ly - 4}" width="8" height="8" fill="{fill}" '
            f'stroke="{style["stroke"]}" stroke-width="1.5"/>'
        )
        svg.append(
            f'<text x="{lx + 24}" y="{ly + 4}" fill="{style["stroke"]}" font-size="10">'
            f'{html.escape(engine)}</text>'
        )

    _write_svg("pillars_profile.svg", svg)


def build_diagnostic_chart(scores):
    engines = sorted(
        scores.items(),
        key=lambda item: (
            item[1]["correction_site_diagnostic"]["unapproved_edit_rate"] is None,
            item[1]["correction_site_diagnostic"]["unapproved_edit_rate"] or 0,
            item[0],
        ),
    )
    height = 100 + len(engines) * 42 + 65
    svg = _start_svg(
        1200,
        height,
        "V0.4 CORRECTION-SITE EDIT DIAGNOSTIC",
        "Single-locale baseline; lower is fewer unapproved edits; not a hallucination rate",
    )
    x0, chart_width, axis_max = 300, 660, 50
    for pct in (0, 10, 20, 30, 40, 50):
        x = x0 + chart_width * pct / axis_max
        svg.append(
            f'<line x1="{x:g}" y1="68" x2="{x:g}" y2="{height - 54}" '
            f'stroke="#30363d" stroke-width="1"/>'
        )
        svg.append(
            f'<text x="{x:g}" y="{height - 34}" fill="#8b949e" font-size="10" '
            f'text-anchor="middle">{pct}%</text>'
        )
    for index, (engine, result) in enumerate(engines):
        y = 76 + index * 42
        diagnostic = result["correction_site_diagnostic"]
        rate = diagnostic["unapproved_edit_rate"]
        count = diagnostic["unapproved_edits"]
        applicable = diagnostic["applicable_sites"]
        color = CURRENT_ENGINE_COLORS[engine]
        svg.append(
            f'<text x="288" y="{y + 17}" fill="{color}" font-size="11" '
            f'text-anchor="end">{html.escape(engine)}</text>'
        )
        if rate is None:
            svg.append(
                f'<text x="{x0}" y="{y + 17}" fill="#8b949e" font-size="11">'
                f'n/a ({count}/{applicable})</text>'
            )
        else:
            width = chart_width * min(rate, axis_max) / axis_max
            svg.append(
                f'<rect x="{x0}" y="{y}" width="{width:.2f}" height="24" '
                f'fill="{color}" stroke="#f0f6fc" stroke-width="1"/>'
            )
            svg.append(
                f'<text x="{x0 + width + 8:.2f}" y="{y + 17}" fill="#f0f6fc" '
                f'font-size="11">{count}/{applicable} ({rate:.1f}%)</text>'
            )
    svg.append(
        f'<text x="600" y="{height - 9}" fill="#8b949e" font-size="10" '
        'text-anchor="middle">Shared rules across engines; only annotated spelling/grammar sites are examined</text>'
    )
    _write_svg("correction_site_diagnostic.svg", svg)


def build_latency_chart(scores):
    measured = sorted(
        (
            (engine, result["latency_ms"])
            for engine, result in scores.items()
            if result["latency_ms"] is not None
        ),
        key=lambda item: item[1],
    )
    unmeasured = [
        (engine, None)
        for engine, result in scores.items()
        if result["latency_ms"] is None
    ]
    rows = measured + unmeasured
    height = 100 + len(rows) * 42 + 50
    svg = _start_svg(
        1200,
        height,
        "V0.4 H-SUITE LATENCY",
        "Single-locale baseline; mean recorded REST timings; web-demo timing unavailable",
    )
    x0, chart_width, max_latency = 300, 700, 1400
    for ms in (0, 350, 700, 1050, 1400):
        x = x0 + chart_width * ms / max_latency
        svg.append(
            f'<line x1="{x:g}" y1="68" x2="{x:g}" y2="{height - 48}" '
            f'stroke="#30363d" stroke-width="1"/>'
        )
        svg.append(
            f'<text x="{x:g}" y="{height - 28}" fill="#8b949e" font-size="10" '
            f'text-anchor="middle">{ms} ms</text>'
        )
    for index, (engine, latency) in enumerate(rows):
        y = 76 + index * 42
        color = CURRENT_ENGINE_COLORS[engine]
        svg.append(
            f'<text x="288" y="{y + 17}" fill="{color}" font-size="11" '
            f'text-anchor="end">{html.escape(engine)}</text>'
        )
        if latency is None:
            reason = (
                "n/a (web demo)"
                if CURRENT_ENGINE_COLORS[engine]
                and engine
                in {
                    "Grammarly Free Grammar Checker",
                    "Sapling Grammar Checker",
                    "JSpell Free Web Checker",
                }
                else "n/a (not recorded)"
            )
            svg.append(
                f'<text x="{x0}" y="{y + 17}" fill="#8b949e" '
                f'font-size="11">{reason}</text>'
            )
        else:
            width = chart_width * min(latency, max_latency) / max_latency
            samples = scores[engine].get("latency_samples")
            sample_label = f" ({samples} samples)" if samples is not None else ""
            svg.append(
                f'<rect x="{x0}" y="{y}" width="{width:.2f}" height="24" '
                f'fill="{color}" stroke="#f0f6fc" stroke-width="1"/>'
            )
            svg.append(
                f'<text x="{x0 + width + 8:.2f}" y="{y + 17}" fill="#f0f6fc" '
                f'font-size="11">~{latency:g} ms{sample_label}</text>'
            )
    svg.append(
        f'<text x="600" y="{height - 6}" fill="#8b949e" font-size="10" '
        'text-anchor="middle">Latency values are carried in the saved v4 H-suite artifact</text>'
    )
    _write_svg("latency_comparison.svg", svg)


def build_quality_history_chart(snapshots):
    engines = list(CURRENT_ENGINE_COLORS)
    for snapshot in snapshots:
        engines.extend(
            engine for engine in snapshot["scores"] if engine not in engines
        )
    panel_height = 42 + len(engines) * 28
    height = 94 + len(snapshots) * panel_height + 42
    width = 1400
    svg = _start_svg(
        width,
        height,
        "H-SUITE HISTORICAL ACCURACY & PROGRESSION OVER TIME",
        "Benchmark upgrade date (V0.3 to V0.4): Nov 14, 2026 artifact date; exact transition not recorded; scores are not comparable",
    )
    chart_x, chart_width = 330, 950
    snapshot_colors = ("#A97070", "#6E9A80", "#C99B5B", "#6B8EAC")
    for snapshot_index, snapshot in enumerate(snapshots):
        panel_top = 72 + snapshot_index * panel_height
        color = snapshot_colors[snapshot_index % len(snapshot_colors)]
        dash = ' stroke-dasharray="5 3"' if snapshot_index % 2 == 0 else ""
        svg.append(
            f'<text x="24" y="{panel_top + 20}" fill="#f0f6fc" font-size="18" '
            f'font-weight="700">{html.escape(snapshot["release"])} - '
            f'{html.escape(snapshot["metric"])}</text>'
        )
        svg.append(
            f'<text x="{width - 24}" y="{panel_top + 20}" fill="#8b949e" '
            f'font-size="14" text-anchor="end">'
            f'{html.escape(snapshot["evaluation_date"])}</text>'
        )
        svg.append(
            f'<text x="24" y="{panel_top + 38}" fill="#8b949e" font-size="13">'
            f'{html.escape(snapshot["methodology"])}</text>'
        )
        for tick in (0, 25, 50, 75, 100):
            x = chart_x + chart_width * tick / 100
            svg.append(
                f'<line x1="{x:g}" y1="{panel_top + 40}" x2="{x:g}" '
                f'y2="{panel_top + panel_height - 4}" stroke="#30363d" '
                'stroke-width="1"/>'
            )
            svg.append(
                f'<text x="{x:g}" y="{panel_top + panel_height + 9}" '
                'fill="#8b949e" font-size="12" text-anchor="middle">'
                f'{tick}%</text>'
            )
        for row, engine in enumerate(engines):
            y = panel_top + 44 + row * 28
            score = snapshot["scores"].get(engine)
            label_color = CURRENT_ENGINE_COLORS.get(engine, "#c9d1d9")
            svg.append(
                f'<text x="315" y="{y + 14}" fill="{label_color}" '
                f'font-size="14" text-anchor="end">{html.escape(engine)}</text>'
            )
            if score is None:
                svg.append(
                    f'<text x="{chart_x}" y="{y + 14}" fill="#8b949e" '
                    'font-size="13">not evaluated in this snapshot</text>'
                )
                continue
            bar_width = chart_width * score / 100
            svg.append(
                f'<rect x="{chart_x}" y="{y}" width="{bar_width:.2f}" '
                f'height="18" fill="{color}" stroke="#f0f6fc"{dash} '
                'stroke-width="1"/>'
            )
            svg.append(
                f'<text x="{chart_x + bar_width + 7:.2f}" y="{y + 14}" '
                'fill="#f0f6fc" font-size="13" font-weight="700">'
                f'{score:.1f}%</text>'
            )
    svg.append(
        f'<text x="{width / 2:g}" y="{height - 10}" fill="#8b949e" '
        'font-size="12" text-anchor="middle">'
        'Both available snapshots are dated November 14, 2026; no earlier measured trend is available. '
        'Add future dated runs only within the matching scoring methodology.</text>'
    )
    _write_svg("quality_history.svg", svg)


def build_paired_locale_quality_chart(locale_results):
    engines = sorted(
        CURRENT_ENGINE_COLORS,
        key=lambda engine: sum(
            locale_results[locale]["engine_summary"][engine]["quality_composite"]
            for locale in ("en-US", "en-GB")
        ) / 2,
        reverse=True,
    )
    height = 100 + len(engines) * 54 + 62
    svg = _start_svg(
        1200,
        height,
        "V4.1 PAIRED LOCALE QUALITY COMPOSITE",
        "Matched en-US and en-GB runs; locale-specific spelling targets included",
    )
    x0, chart_width = 300, 760
    locale_colors = {"en-US": "#409DC6", "en-GB": "#D8976F"}
    for pct in (0, 25, 50, 75, 100):
        x = x0 + chart_width * pct / 100
        svg.append(
            f'<line x1="{x:g}" y1="68" x2="{x:g}" y2="{height - 48}" '
            'stroke="#30363d" stroke-width="1"/>'
        )
        svg.append(
            f'<text x="{x:g}" y="{height - 28}" fill="#8b949e" font-size="10" '
            f'text-anchor="middle">{pct}%</text>'
        )
    for index, engine in enumerate(engines):
        y = 76 + index * 54
        color = CURRENT_ENGINE_COLORS[engine]
        svg.append(
            f'<text x="288" y="{y + 22}" fill="{color}" font-size="11" '
            f'text-anchor="end">{html.escape(engine)}</text>'
        )
        for offset, locale in ((0, "en-US"), (17, "en-GB")):
            score = locale_results[locale]["engine_summary"][engine][
                "quality_composite"
            ]
            width = chart_width * score / 100
            svg.append(
                f'<rect x="{x0}" y="{y + offset}" width="{width:.2f}" '
                f'height="13" fill="{locale_colors[locale]}"/>'
            )
            svg.append(
                f'<text x="{x0 + width + 7:.2f}" y="{y + offset + 11}" '
                f'fill="#f0f6fc" font-size="10">{locale} {score:.1f}%</text>'
            )
    svg.append(
        f'<text x="600" y="{height - 6}" fill="#8b949e" font-size="10" '
        'text-anchor="middle">Quality weights: spelling 43.75%, grammar 31.25%, voice 25%</text>'
    )
    _write_svg("paired_locale_quality_comparison.svg", svg)


def build_paired_locale_pillars_chart(locale_results):
    engines = sorted(
        CURRENT_ENGINE_COLORS,
        key=lambda engine: sum(
            locale_results[locale]["engine_summary"][engine]["quality_composite"]
            for locale in ("en-US", "en-GB")
        ) / 2,
        reverse=True,
    )
    height = 110 + len(engines) * 54 + 48
    svg = _start_svg(
        1200,
        height,
        "V4.1 PAIRED LOCALE QUALITY PILLARS",
        "Locale-specific spelling targets; voice scoring formula unchanged",
    )
    columns = [
        ("Spelling", "spelling_accuracy"),
        ("Grammar", "grammar_accuracy"),
        ("Voice", "voice_preservation"),
    ]
    centres = [400, 660, 920]
    locale_colors = {"en-US": "#409DC6", "en-GB": "#D8976F"}
    for (label, _), x in zip(columns, centres):
        svg.append(
            f'<text x="{x}" y="82" fill="#f0f6fc" font-size="11" '
            f'font-weight="700" text-anchor="middle">{label}</text>'
        )
    for row, engine in enumerate(engines):
        y = 100 + row * 54
        svg.append(
            f'<text x="288" y="{y + 22}" fill="{CURRENT_ENGINE_COLORS[engine]}" '
            f'font-size="11" text-anchor="end">{html.escape(engine)}</text>'
        )
        for (_, metric), centre in zip(columns, centres):
            for offset, locale in ((0, "en-US"), (17, "en-GB")):
                score = locale_results[locale]["engine_summary"][engine][metric]
                width = 170 * score / 100
                x = centre - 85
                svg.append(
                    f'<rect x="{x}" y="{y + offset}" width="{width:.2f}" '
                    f'height="13" fill="{locale_colors[locale]}"/>'
                )
                svg.append(
                    f'<text x="{centre}" y="{y + offset + 11}" fill="#0d1117" '
                    'font-size="9" font-weight="700" text-anchor="middle">'
                    f'{locale} {score:.1f}%</text>'
                )
    svg.append(
        f'<text x="600" y="{height - 8}" fill="#8b949e" font-size="10" '
        'text-anchor="middle">US and GB denote the en-US and en-GB locale runs</text>'
    )
    _write_svg("paired_locale_pillars.svg", svg)


def build_paired_locale_diagnostic_chart(locale_results):
    engines = sorted(
        CURRENT_ENGINE_COLORS,
        key=lambda engine: sum(
            locale_results[locale]["engine_summary"][engine][
                "correction_site_diagnostic"
            ]["unapproved_edit_rate"] or 0
            for locale in ("en-US", "en-GB")
        ) / 2,
    )
    height = 100 + len(engines) * 54 + 65
    svg = _start_svg(
        1200,
        height,
        "V4.1 PAIRED LOCALE CORRECTION-SITE DIAGNOSTIC",
        "Unapproved edits at annotated sites; not a semantic or hallucination rate",
    )
    x0, chart_width, axis_max = 300, 660, 50
    locale_colors = {"en-US": "#409DC6", "en-GB": "#D8976F"}
    for pct in (0, 10, 20, 30, 40, 50):
        x = x0 + chart_width * pct / axis_max
        svg.append(
            f'<line x1="{x:g}" y1="68" x2="{x:g}" y2="{height - 54}" '
            'stroke="#30363d" stroke-width="1"/>'
        )
        svg.append(
            f'<text x="{x:g}" y="{height - 34}" fill="#8b949e" font-size="10" '
            f'text-anchor="middle">{pct}%</text>'
        )
    for index, engine in enumerate(engines):
        y = 76 + index * 54
        svg.append(
            f'<text x="288" y="{y + 22}" fill="{CURRENT_ENGINE_COLORS[engine]}" '
            f'font-size="11" text-anchor="end">{html.escape(engine)}</text>'
        )
        for offset, locale in ((0, "en-US"), (17, "en-GB")):
            diagnostic = locale_results[locale]["engine_summary"][engine][
                "correction_site_diagnostic"
            ]
            rate = diagnostic["unapproved_edit_rate"]
            x = x0
            if rate is None:
                label = f'{locale} n/a ({diagnostic["unapproved_edits"]}/{diagnostic["applicable_sites"]})'
            else:
                width = chart_width * min(rate, axis_max) / axis_max
                svg.append(
                    f'<rect x="{x0}" y="{y + offset}" width="{width:.2f}" '
                    f'height="13" fill="{locale_colors[locale]}"/>'
                )
                x += width + 7
                label = (
                    f'{locale} {diagnostic["unapproved_edits"]}/'
                    f'{diagnostic["applicable_sites"]} ({rate:.1f}%)'
                )
            svg.append(
                f'<text x="{x:.2f}" y="{y + offset + 11}" fill="#f0f6fc" '
                f'font-size="10">{label}</text>'
            )
    svg.append(
        f'<text x="600" y="{height - 9}" fill="#8b949e" font-size="10" '
        'text-anchor="middle">Lower is fewer unapproved edits at shared annotated correction sites</text>'
    )
    _write_svg("paired_locale_diagnostic.svg", svg)


def build_paired_locale_latency_chart(locale_results):
    rows = []
    for engine in CURRENT_ENGINE_COLORS:
        for locale in ("en-US", "en-GB"):
            result = locale_results[locale]["engine_summary"][engine]
            rows.append((engine, locale, result["latency_ms"], result["latency_samples"]))
    rows.sort(
        key=lambda row: (row[2] is None, row[2] if row[2] is not None else 0)
    )
    height = 100 + len(rows) * 28 + 54
    svg = _start_svg(
        1200,
        height,
        "V4.1 PAIRED LOCALE RECORDED LATENCY",
        "Mean recorded request timings only; web-demo latency remains unavailable",
    )
    x0, chart_width, max_latency = 300, 700, 1400
    locale_colors = {"en-US": "#409DC6", "en-GB": "#D8976F"}
    for ms in (0, 350, 700, 1050, 1400):
        x = x0 + chart_width * ms / max_latency
        svg.append(
            f'<line x1="{x:g}" y1="68" x2="{x:g}" y2="{height - 45}" '
            'stroke="#30363d" stroke-width="1"/>'
        )
        svg.append(
            f'<text x="{x:g}" y="{height - 25}" fill="#8b949e" font-size="10" '
            f'text-anchor="middle">{ms} ms</text>'
        )
    for index, (engine, locale, latency, samples) in enumerate(rows):
        y = 76 + index * 28
        svg.append(
            f'<text x="288" y="{y + 13}" fill="{CURRENT_ENGINE_COLORS[engine]}" '
            f'font-size="10" text-anchor="end">{html.escape(engine)} {locale}</text>'
        )
        if latency is None:
            svg.append(
                f'<text x="{x0}" y="{y + 13}" fill="#8b949e" font-size="10">n/a</text>'
            )
            continue
        width = chart_width * min(latency, max_latency) / max_latency
        svg.append(
            f'<rect x="{x0}" y="{y}" width="{width:.2f}" height="18" '
            f'fill="{locale_colors[locale]}"/>'
        )
        svg.append(
            f'<text x="{x0 + width + 7:.2f}" y="{y + 13}" fill="#f0f6fc" '
            f'font-size="10">~{latency:g} ms ({samples} samples)</text>'
        )
    _write_svg("paired_locale_latency.svg", svg)








if __name__ == "__main__":
    ASSETS.mkdir(exist_ok=True)
    summary = _load_results()
    build_quality_chart(summary)
    build_pillars_chart(summary)
    build_pillars_profile_chart(summary)
    build_diagnostic_chart(summary)
    build_latency_chart(summary)
    build_quality_history_chart(_load_quality_history())
    if PAIRED_RESULTS_PATH.exists():
        paired_results = _load_paired_results()
        build_paired_locale_quality_chart(paired_results)
        build_paired_locale_pillars_chart(paired_results)
        build_paired_locale_diagnostic_chart(paired_results)
        build_paired_locale_latency_chart(paired_results)
    else:
        print("Skipped paired-locale charts: paired outputs have not been collected.")
