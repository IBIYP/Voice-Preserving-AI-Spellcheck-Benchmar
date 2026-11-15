# Reproduction & Verification Guide: Benchmark v4.0
**Voice-Preserving AI-Spellcheck Benchmark**  
*Evaluation Date: November 14, 2026 | Benchmark Version: 4.0*

This guide explains how to replay the saved v4 results, regenerate all current SVG charts, and verify the tracked artifacts locally.

---

## 1. Prerequisites & Environment Setup

The benchmark is designed to run in standard Python 3.9+ without heavyweight deep learning dependencies.

### Step 1: Clone the Repository
```bash
git clone https://github.com/IBIYP/voice-preserving-ai-spellcheck-benchmark.git
cd voice-preserving-ai-spellcheck-benchmark
```

### Step 2: Initialize Virtual Environment
```bash
python -m venv .venv

# On Linux / macOS:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

---

## 2. Benchmark Execution

### Run the H-suite v4 Evaluation
Evaluates cached outputs across spelling, grammar, writer's voice, and a separate correction-site edit diagnostic.

**Execution Command:**
```bash
python benchmark_4pillars_hybrid.py
```

### Run the Blind v4 Evaluation
This command requires the private local input/output cache at `Docs/Notes/blind_v3_live_runs_full.json`, which is not included in a clean public clone:
```bash
python evaluate_blind_v4.py
```
The Blind output records hashes and the target-scoring revision, but does not
reveal the private cache. A clean public clone can run the test suite and the
public H-suite; it cannot regenerate the Blind leaderboard.

### Run the automated tests
```bash
python -m unittest discover -s tests
```

**What this script does:**
1. Loads the 10 blind unseen domain evaluation units across distinct human writing styles (Urban Slang, Southern Gothic, Cyberpunk Noir, Food Critique, Severe Dysgraphia, SaaS Pitch, Sports Locker Room, Poetic Melancholy, Field Biology, and Legal Shorthand).
2. Calculates independent, decoupled metrics:
   - **Spelling Accuracy (43.75% of the quality composite).**
   - **Grammar Accuracy (31.25% of the quality composite).**
   - **Writer's Voice (25% of the quality composite)** - decoupled from spelling, with multi-reference dialect tolerance (`rockin` = `rocking`).
   - **Correction-Site Edit Diagnostic** - reports unapproved edits at shared annotated correction sites; it is not a semantic or hallucination rate.
   - **Quality composite** - includes only the three weighted quality pillars.
3. Reports latency only where a value was measured or recorded. Sapling and JSpell were tested through interactive web demos, not APIs, and have no latency measurements.
4. Outputs a formatted ASCII leaderboard to the console.
5. Saves the Blind v4 artifact to `raw_results/blind_v4_official_scoreboard.json`. The H-suite evaluator writes `raw_results/blind_4pillars_eval_run_v4.json`; the older v3 artifact remains a legacy record.

---

## 3. Regenerating Visual Charts

To regenerate all monochrome 90-degree SVG charts:
```bash
python generate_charts.py
```

After a complete paired en-US/en-GB cache has been collected, score it with:
```bash
python evaluate_paired_locales.py
```
The evaluator requires `raw_results/h_suite_locale_runs_v1.json`; it fails on
missing engines or passages instead of falling back to baseline outputs.

**Generated Visual Assets in `assets/`:**
- `assets/hybrid_score_comparison.svg`: v4 H-suite quality composite.
- `assets/pillars_breakdown.svg`: v4 spelling, grammar, and voice breakdown.
- `assets/correction_site_diagnostic.svg`: Unapproved edit counts and denominators; lower is fewer unapproved target-site edits.
- `assets/latency_comparison.svg`: Means of recorded per-passage REST timings from the v4 H-suite artifact; not product compute latency. DeepL and the web demos have no recorded H-suite timings.
- `assets/progress_over_time.svg`: approximate pre-v0.3 trend points aligned to the v0.4 score scale, with measured v0.3 and v0.4 endpoints.
- `assets/progress_bar_chart_over_time.svg`: grouped v0.3/v0.4 history for all seven competitors; Grammarly has no v0.3 endpoint.
- `assets/paired_locale_quality_comparison.svg`, `assets/paired_locale_pillars.svg`, `assets/paired_locale_diagnostic.svg`, and `assets/paired_locale_latency.svg`: paired en-US/en-GB v4.1 charts, generated only after the complete paired-locale score artifact exists.

The four current H-suite charts contain seven systems, including the complete
Grammarly web-demo result. The Blind suite has no Grammarly result; the blended
history chart includes its measured v0.4 endpoint only. Current H-suite scores are a single-locale
baseline; see `raw_results/h_suite_locale_golden_texts.json` for full corrected
en-US and en-GB references. Those references are not exact-string targets, and
paired locale scores will require fresh outputs collected in both locales.

---

## 4. Codebase Hygiene & Character Audit

To verify that all files in the repository contain 0 non-ASCII characters or malformed tokens:
```bash
python bad_character_scanner.py
```

---

## 5. Metric Formulas & Scoring Architecture

$$\text{Pillar 1 (Spelling)} = \frac{\text{Accepted Forms at Aligned Spelling Sites}}{\text{Total Applicable Spelling Sites}} \times 100\%$$

$$\text{Pillar 2 (Grammar)} = \frac{\text{Accepted Forms at Aligned Grammar Sites}}{\text{Total Applicable Grammar Sites}} \times 100\%$$

Scores are pooled across target sites in both suites. An unchanged source form
counts only when the annotation explicitly lists it as an accepted variant;
identity-only annotations do not enter the accuracy denominator. A matching
phrase elsewhere in the output does not satisfy the target.

$$\text{Pillar 3 (Voice)} = \text{mean}(\text{Lexical F1} \times \text{Marker Retention}) \times \left(1 - \frac{\min(10 \times \text{Over-Edit Signatures}, 80)}{100}\right)$$

Lexical F1 is calculated from case-folded word-token LCS outside annotated
correction spans. Voice-marker retention uses the curated phrases and accepted
dialect equivalents. The over-edit penalty is applied suite-wide after passage
scores are averaged; these deterministic annotations do not judge meaning or
tone.

Version 4 replaces the v3 engine-specific signature metric with a shared
correction-site edit diagnostic. At each annotated spelling/grammar site, the
evaluator aligns output tokens against input tokens and counts the site as an
unapproved edit if the output is neither unchanged nor one of the shared
accepted correction forms. The report includes raw `unapproved_edits`,
`applicable_sites`, and their percentage; it reports `n/a` when there are no
applicable sites. It is not a semantic evaluator, does not examine unannotated
output, and is excluded from the quality composite.

$$\text{V4 Quality Composite} = (0.4375 \times \text{Spelling}) + (0.3125 \times \text{Grammar}) + (0.25 \times \text{Voice})$$

The v0.3 signature diagnostic and composites remain in their original files as
legacy results. Historical charts show their raw endpoints separately and
apply an explicitly illustrative additive alignment to earlier points; they
do not rescore the v0.3 results under v0.4. See the README's blended-history
notes before interpreting those estimates.

---

## 6. Verifying Local Output Against Published Numbers

When you run `python benchmark_4pillars_hybrid.py`, confirm the H-suite v4 results:
- **Spelling Leader:** ★ Sapling Grammar Checker (93.9%; web demo)
- **Grammar Leader:** ★ Sapling Grammar Checker (100.0%; web demo)
- **Voice Leader:** ★ Sapling Grammar Checker (89.1%; web demo)
- **Correction-site diagnostic:** Sapling 2/61 (3.3%); not a semantic correctness score.
- **Quality Composite Leader:** ★ Sapling Grammar Checker (94.6%; web demo)
- **Lowest recorded REST latency:** LanguageTool API (~652.8 ms across 10 requests)

Sapling and JSpell web-demo scores use a one-pass policy: apply each initial visible suggestion once, without running the checker again. The evaluators consume saved outputs; they do not query either service. These results are directional and should not be presented as API or latency comparisons. Both are third-party services; check their privacy policies before submitting non-public text. JSpell is a spelling-only checker, but its result is scored across the selected quality pillars, so its missed grammar targets remain part of the composite.

The recorded H-suite REST timings are API round-trip observations, not local
engine execution times. DeepL's cached H-suite entries have no recorded timing;
do not infer or estimate one.

### JSpell Web-Checker Results
The published JSpell results were collected from the [free JSpell checker](https://www.jspell.com/checker/) using its interactive English (US) interface. They are **not** from the JSpell Cloud API or RapidAPI endpoint. For each flagged word, the first displayed suggestion was applied once in the same checker session; no second check was run. Web-demo latency was not measured.

The saved record is [raw_results/jspell_web_checker_outputs.json](raw_results/jspell_web_checker_outputs.json). It contains outputs, applied initial suggestions, and source-input SHA-256 fingerprints. The private Blind source passages are not included. The separate `run_jspell_control.py` collector targets the Cloud API and requires a local `JSPELL_RAPIDAPI_KEY`; that API route returned HTTP 403 during collection and did not produce the published web-checker results.

---

## 7. Raw Artifact References
- [raw_results/README.md](raw_results/README.md): Methodology and schema documentation.
- [raw_results/blind_4pillars_eval_run_v4.json](raw_results/blind_4pillars_eval_run_v4.json): H-suite v4 structured per-passage output and metrics.
- [raw_results/blind_v4_official_scoreboard.json](raw_results/blind_v4_official_scoreboard.json): Blind v4 aggregate scores.
- [raw_results/blind_4pillars_eval_run.json](raw_results/blind_4pillars_eval_run.json) and [raw_results/blind_v3_official_scoreboard.json](raw_results/blind_v3_official_scoreboard.json): legacy v3 records.
- [raw_results/unseen_10_domains_live_run.json](raw_results/unseen_10_domains_live_run.json): Raw outputs and measured latencies where available.
- [raw_results/blind_v3_sapling_outputs.json](raw_results/blind_v3_sapling_outputs.json): Sapling B-suite web-demo outputs and one-pass suggestion record.
- [raw_results/jspell_web_checker_outputs.json](raw_results/jspell_web_checker_outputs.json): JSpell H- and B-suite web-checker outputs and one-pass suggestion record.
