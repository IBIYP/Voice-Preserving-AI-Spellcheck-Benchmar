"""Generate current and blended historical charts from saved H-suite artifacts."""

import html
import json
from pathlib import Path


ROOT = Path(__file__).parent
RESULTS_PATH = ROOT / "raw_results" / "blind_4pillars_eval_run_v4.json"
PAIRED_RESULTS_PATH = ROOT / "raw_results" / "h_suite_locale_eval_v1.json"
ASSETS = ROOT / "assets"

ENGINE_COLORS = {
    "BCorrect (FMM)": "#E69F00",
    "LanguageTool API": "#56B4E9",
    "TextGears API": "#009E73",
    "DeepL Write": "#CC79A7",
    "Sapling Grammar Checker": "#F0E442",
    "JSpell Free Web Checker": "#D55E00",
}

CURRENT_ENGINE_COLORS = {
    **ENGINE_COLORS,
    "Grammarly Free Grammar Checker": "#58a6ff",
}

LEGACY_ESTIMATES = {
    "DeepL Write": [78.0, 80.0, 81.5],
    "TextGears API": [64.0, 67.5, 70.5],
    "LanguageTool API": [65.0, 68.0, 70.2],
    "BCorrect (FMM)": [32.0, 38.5, 38.0],
    "JSpell Free Web Checker": [65.1, 65.1, 65.1],
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


def _load_legacy_results():
    legacy_path = ROOT / "raw_results" / "blind_4pillars_eval_run.json"
    with legacy_path.open("r", encoding="utf-8") as file:
        results = json.load(file)
    if results["benchmark_metadata"].get("version") != "3.0-blind":
        raise ValueError(f"{legacy_path} does not contain v3.0 results")
    summary = results["engine_summary"]
    _validate_engine_roster(summary, str(legacy_path), ENGINE_COLORS)
    return summary


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


def _start_svg(width, height, title, subtitle):
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        'style="background:#0d1117; font-family:-apple-system,BlinkMacSystemFont,'
        '\'Segoe UI\',Helvetica,Arial,sans-serif;">',
        f'<rect x="1" y="1" width="{width - 2}" height="{height - 2}" '
        'fill="none" stroke="#30363d" stroke-width="1"/>',
        f'<text x="{width / 2:g}" y="32" fill="#f0f6fc" font-size="14" '
        f'font-weight="700" text-anchor="middle">{html.escape(title)}</text>',
        f'<text x="{width / 2:g}" y="52" fill="#8b949e" font-size="11" '
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
    height = 100 + len(engines) * 42 + 55
    svg = _start_svg(
        1200,
        height,
        "V0.4 H-SUITE QUALITY PILLARS",
        "Single-locale baseline; locale settings vary or are unreported",
    )
    columns = [
        ("Spelling", "spelling_accuracy"),
        ("Grammar", "grammar_accuracy"),
        ("Voice", "voice_preservation"),
    ]
    x_positions = [360, 610, 860]
    for (label, _), x in zip(columns, x_positions):
        svg.append(
            f'<text x="{x}" y="78" fill="#f0f6fc" font-size="11" '
            f'font-weight="700" text-anchor="middle">{label}</text>'
        )
    for row, (engine, result) in enumerate(engines):
        y = 96 + row * 42
        color = CURRENT_ENGINE_COLORS[engine]
        svg.append(
            f'<text x="288" y="{y + 17}" fill="{color}" font-size="11" '
            f'text-anchor="end">{html.escape(engine)}</text>'
        )
        for (_, key), x in zip(columns, x_positions):
            score = result[key]
            svg.append(
                f'<rect x="{x - 90}" y="{y}" width="180" height="22" '
                'fill="#161b22" stroke="#30363d" stroke-width="1"/>'
            )
            svg.append(
                f'<rect x="{x - 90}" y="{y}" width="{180 * score / 100:.2f}" '
                f'height="22" fill="{color}" opacity="0.72"/>'
            )
            svg.append(
                f'<text x="{x}" y="{y + 16}" fill="#0d1117" font-size="10" '
                f'font-weight="700" text-anchor="middle">{score:.1f}%</text>'
            )
    svg.append(
        f'<text x="600" y="{height - 8}" fill="#8b949e" font-size="10" '
        'text-anchor="middle">Scores are recomputed from saved H-suite outputs under v4.0</text>'
    )
    _write_svg("pillars_breakdown.svg", svg)


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
            svg.append(
                f'<text x="{x0}" y="{y + 17}" fill="#8b949e" font-size="11">n/a</text>'
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
    locale_colors = {"en-US": "#58a6ff", "en-GB": "#f0a6ff"}
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
    locale_colors = {"en-US": "#58a6ff", "en-GB": "#f0a6ff"}
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
    locale_colors = {"en-US": "#58a6ff", "en-GB": "#f0a6ff"}
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
    locale_colors = {"en-US": "#58a6ff", "en-GB": "#f0a6ff"}
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


def _align_legacy_estimate_to_v4(estimate, legacy_score, current_score):
    return max(0.0, min(100.0, estimate + current_score - legacy_score))


def build_legacy_progress_chart(legacy_scores, current_scores):
    points = [150, 330, 510, 690, 860]
    y_base, y_scale = 405, 3.2
    svg = _start_svg(
        1200,
        630,
        "V0.3 -> V0.4 SCORE HISTORY",
        "Historical estimates shifted to the v0.4 scale; v0.3 and v0.4 endpoints are both shown",
    )
    for pct in (0, 20, 40, 60, 80, 100):
        y = y_base - pct * y_scale
        svg.append(
            f'<line x1="115" y1="{y:g}" x2="895" y2="{y:g}" '
            'stroke="#30363d" stroke-width="1"/>'
        )
        svg.append(
            f'<text x="103" y="{y + 4:g}" fill="#8b949e" font-size="10" '
            f'text-anchor="end">{pct}%</text>'
        )

    labels = [
        "Q1 2025 est.",
        "Q3 2025 est.",
        "Early Fall est.",
        "Nov 2026 v0.3",
        "Nov 2026 v0.4",
    ]
    for x, label in zip(points, labels):
        svg.append(
            f'<line x1="{x}" y1="72" x2="{x}" y2="{y_base}" '
            'stroke="#21262d" stroke-dasharray="3,4"/>'
        )
        svg.append(
            f'<text x="{x}" y="432" fill="#c9d1d9" font-size="10" '
            f'text-anchor="middle">{html.escape(label)}</text>'
        )

    for engine, color in CURRENT_ENGINE_COLORS.items():
        current_score = current_scores[engine]["quality_composite"]
        current_y = y_base - current_score * y_scale
        if engine in LEGACY_ESTIMATES:
            legacy_score = legacy_scores[engine]["hybrid_meta_score"]
            estimates = [
                _align_legacy_estimate_to_v4(value, legacy_score, current_score)
                for value in LEGACY_ESTIMATES[engine]
            ]
            coordinates = [
                f"{x},{y_base - value * y_scale:g}"
                for x, value in zip(points[:3], estimates)
            ]
            coordinates.append(f"{points[4]},{current_y:g}")
            svg.append(
                f'<polyline points="{" ".join(coordinates)}" fill="none" '
                f'stroke="{color}" stroke-width="2" stroke-dasharray="4,3"/>'
            )
            for x, value in zip(points[:3], estimates):
                y = y_base - value * y_scale
                svg.append(
                    f'<circle cx="{x}" cy="{y:g}" r="4" fill="#0d1117" '
                    f'stroke="{color}" stroke-width="1.5"/>'
                )
        elif engine == "Sapling Grammar Checker":
            legacy_score = legacy_scores[engine]["hybrid_meta_score"]
            upper_bound = _align_legacy_estimate_to_v4(
                60.0,
                legacy_score,
                current_score,
            )
            bound_y = y_base - upper_bound * y_scale
            svg.append(
                f'<rect x="{points[2] - 6}" y="{bound_y:g}" width="12" '
                f'height="{y_base - bound_y:g}" fill="{color}" opacity="0.18" '
                f'stroke="{color}" stroke-width="1" stroke-dasharray="3,2"/>'
            )
            svg.append(
                f'<polyline points="{points[2]},{bound_y:g} '
                f'{points[4]},{current_y:g}" fill="none" stroke="{color}" '
                'stroke-width="2" stroke-dasharray="4,3"/>'
            )
            svg.append(
                f'<circle cx="{points[2]}" cy="{bound_y:g}" r="4" '
                f'fill="#0d1117" stroke="{color}" stroke-width="1.5"/>'
            )

        if engine in legacy_scores:
            legacy_score = legacy_scores[engine]["hybrid_meta_score"]
            legacy_y = y_base - legacy_score * y_scale
            x = points[3]
            svg.append(
                f'<rect x="{x - 4}" y="{legacy_y - 4:g}" width="8" height="8" '
                f'fill="#0d1117" stroke="{color}" stroke-width="1.5" '
                f'transform="rotate(45 {x} {legacy_y:g})"/>'
            )
        svg.append(
            f'<circle cx="{points[4]}" cy="{current_y:g}" r="5" fill="{color}"/>'
        )

    for index, (engine, color) in enumerate(CURRENT_ENGINE_COLORS.items()):
        y = 94 + index * 28
        svg.append(
            f'<line x1="920" y1="{y}" x2="948" y2="{y}" stroke="{color}" '
            'stroke-width="2" stroke-dasharray="4,3"/>'
        )
        score = current_scores[engine]["quality_composite"]
        svg.append(
            f'<text x="956" y="{y + 4}" fill="{color}" font-size="9">'
            f'{html.escape(engine)} ({score:.1f}%)</text>'
        )
    svg.append(
        '<circle cx="924" cy="310" r="4" fill="#0d1117" stroke="#c9d1d9" '
        'stroke-width="1.5"/>'
    )
    svg.append(
        '<text x="940" y="314" fill="#8b949e" font-size="9">'
        'v0.4-aligned historical estimate</text>'
    )
    svg.append(
        '<rect x="920" y="325" width="8" height="8" fill="#0d1117" '
        'stroke="#c9d1d9" stroke-width="1.5" transform="rotate(45 924 329)"/>'
    )
    svg.append(
        '<text x="940" y="334" fill="#8b949e" font-size="9">'
        'measured v0.3 composite</text>'
    )
    svg.append('<circle cx="924" cy="349" r="5" fill="#c9d1d9"/>')
    svg.append(
        '<text x="940" y="353" fill="#8b949e" font-size="9">'
        'measured v0.4 composite</text>'
    )
    svg.append(
        '<text x="600" y="472" fill="#8b949e" font-size="10" '
        "text-anchor=\"middle\">v0.3 estimates are shifted by each shared engine's measured "
        'v0.4-minus-v0.3 endpoint delta; historical values remain estimates.</text>'
    )
    svg.append(
        '<text x="600" y="494" fill="#8b949e" font-size="10" '
        'text-anchor="middle">This additive alignment is illustrative, not a rescore or '
        'evidence of historical performance on the v0.4 rubric.</text>'
    )
    svg.append(
        '<text x="600" y="516" fill="#8b949e" font-size="10" '
        "text-anchor=\"middle\">Sapling's earlier point is an estimated below-60% v0.3 "
        'upper bound; Grammarly has no v0.3 result.</text>'
    )
    svg.append(
        '<text x="600" y="538" fill="#8b949e" font-size="10" '
        'text-anchor="middle">The v0.3 signature-based anti-hallucination pillar is retired; '
        'the v0.4 diagnostic is not a hallucination rate.</text>'
    )
    svg.append(
        '<text x="600" y="560" fill="#8b949e" font-size="9" '
        'text-anchor="middle">Public release labels v0.3/v0.4; source artifacts identify '
        'these results as 3.0/4.0.</text>'
    )
    _write_svg("progress_over_time.svg", svg)


def build_legacy_progress_bar_chart(legacy_scores, current_scores):
    centres = [145, 325, 505, 685, 865]
    y_base, y_scale = 380, 3.2
    bar_width, gap = 10, 3
    group_width = len(CURRENT_ENGINE_COLORS) * bar_width + (
        len(CURRENT_ENGINE_COLORS) - 1
    ) * gap
    svg = _start_svg(
        1200,
        640,
        "V0.3 -> V0.4 COMPOSITE HISTORY",
        "Estimated history aligned to v0.4 scale; measured v0.3 and v0.4 endpoints shown separately",
    )
    for pct in (0, 20, 40, 60, 80, 100):
        y = y_base - pct * y_scale
        svg.append(
            f'<line x1="95" y1="{y:g}" x2="915" y2="{y:g}" '
            'stroke="#30363d" stroke-width="1"/>'
        )
        svg.append(
            f'<text x="83" y="{y + 4:g}" fill="#8b949e" font-size="10" '
            f'text-anchor="end">{pct}%</text>'
        )

    labels = [
        "Q1 2025 est.",
        "Q3 2025 est.",
        "Early Fall est.",
        "Nov 2026 v0.3",
        "Nov 2026 v0.4",
    ]
    for point_index, (centre, label) in enumerate(zip(centres, labels)):
        svg.append(
            f'<line x1="{centre}" y1="70" x2="{centre}" y2="{y_base}" '
            'stroke="#21262d" stroke-dasharray="3,4"/>'
        )
        svg.append(
            f'<text x="{centre}" y="408" fill="#c9d1d9" font-size="9" '
            f'text-anchor="middle">{html.escape(label)}</text>'
        )
        start = centre - group_width / 2
        for engine_index, (engine, color) in enumerate(CURRENT_ENGINE_COLORS.items()):
            x = start + engine_index * (bar_width + gap)
            current_score = current_scores[engine]["quality_composite"]
            if engine in LEGACY_ESTIMATES and point_index < 3:
                legacy_score = legacy_scores[engine]["hybrid_meta_score"]
                score = _align_legacy_estimate_to_v4(
                    LEGACY_ESTIMATES[engine][point_index],
                    legacy_score,
                    current_score,
                )
                fill, opacity, dash = color, "0.55", ' stroke-dasharray="2,2"'
            elif engine == "Sapling Grammar Checker" and point_index == 2:
                legacy_score = legacy_scores[engine]["hybrid_meta_score"]
                score = _align_legacy_estimate_to_v4(
                    60.0,
                    legacy_score,
                    current_score,
                )
                fill, opacity, dash = color, "0.18", ' stroke-dasharray="2,2"'
            elif engine in legacy_scores and point_index == 3:
                score = legacy_scores[engine]["hybrid_meta_score"]
                fill, opacity, dash = "#0d1117", "1", ""
            elif point_index == 4:
                score = current_score
                fill, opacity, dash = color, "1", ""
            else:
                continue

            height = score * y_scale
            y = y_base - height
            svg.append(
                f'<rect x="{x:g}" y="{y:g}" width="{bar_width}" '
                f'height="{height:g}" fill="{fill}" opacity="{opacity}" '
                f'stroke="{color}" stroke-width="1"{dash}/>'
            )

    for index, (engine, color) in enumerate(CURRENT_ENGINE_COLORS.items()):
        row, column = divmod(index, 3)
        x = 120 + column * 350
        y = 458 + row * 24
        svg.append(
            f'<rect x="{x}" y="{y - 9}" width="12" height="10" '
            f'fill="{color}" stroke="{color}" stroke-width="1"/>'
        )
        svg.append(
            f'<text x="{x + 18}" y="{y}" fill="{color}" font-size="9">'
            f'{html.escape(engine)}</text>'
        )
    svg.append(
        '<rect x="120" y="535" width="12" height="10" fill="#0d1117" '
        'stroke="#c9d1d9" stroke-width="1"/>'
    )
    svg.append(
        '<text x="140" y="544" fill="#8b949e" font-size="9">'
        'Measured v0.3 composite</text>'
    )
    svg.append(
        '<rect x="300" y="535" width="12" height="10" fill="#c9d1d9" '
        'stroke="#c9d1d9" stroke-width="1"/>'
    )
    svg.append(
        '<text x="320" y="544" fill="#8b949e" font-size="9">'
        'Measured v0.4 composite</text>'
    )
    svg.append(
        '<rect x="500" y="535" width="12" height="10" fill="#c9d1d9" '
        'opacity="0.35" stroke="#c9d1d9" stroke-width="1" '
        'stroke-dasharray="2,2"/>'
    )
    svg.append(
        '<text x="520" y="544" fill="#8b949e" font-size="9">'
        'v0.4-aligned estimate (Sapling bar is an upper bound)</text>'
    )
    svg.append(
        '<text x="600" y="578" fill="#8b949e" font-size="9" '
        'text-anchor="middle">Historical estimates are shifted by the per-engine endpoint '
        'delta, not rescored historical outputs.</text>'
    )
    svg.append(
        '<text x="600" y="598" fill="#8b949e" font-size="9" '
        'text-anchor="middle">v0.3 signature-based anti-hallucination scores are retired; '
        'v0.4 edit diagnostics are not hallucination rates.</text>'
    )
    svg.append(
        '<text x="600" y="618" fill="#8b949e" font-size="9" '
        'text-anchor="middle">Public release labels v0.3/v0.4; source artifacts identify '
        'these results as 3.0/4.0.</text>'
    )
    _write_svg("progress_bar_chart_over_time.svg", svg)


if __name__ == "__main__":
    ASSETS.mkdir(exist_ok=True)
    summary = _load_results()
    legacy_summary = _load_legacy_results()
    build_quality_chart(summary)
    build_pillars_chart(summary)
    build_diagnostic_chart(summary)
    build_latency_chart(summary)
    build_legacy_progress_chart(legacy_summary, summary)
    build_legacy_progress_bar_chart(legacy_summary, summary)
    if PAIRED_RESULTS_PATH.exists():
        paired_results = _load_paired_results()
        build_paired_locale_quality_chart(paired_results)
        build_paired_locale_pillars_chart(paired_results)
        build_paired_locale_diagnostic_chart(paired_results)
        build_paired_locale_latency_chart(paired_results)
    else:
        print("Skipped paired-locale charts: paired outputs have not been collected.")
