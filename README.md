# Voice-Preserving AI Spellcheck Benchmark v0.4
**An Open Benchmark for AI Spelling, Grammar, and Keeping the Writer's Voice**  
*Maintained by the Open Voice-Preserving Benchmark Working Group*  
*Evaluation Date: November 14, 2026 | Public Benchmark Release: v0.4 | Result Artifact Version: 4.0*

[![License: MIT (Benchmark Code Only)](https://img.shields.io/badge/License-MIT%20(Benchmark%20Only)-blue.svg)](LICENSE)
[![Benchmark Date: November 14, 2026](https://img.shields.io/badge/Benchmark%20Date-November%2014%2C%202026-blue.svg)]()
[![Latency: Per-Run Observations](https://img.shields.io/badge/Latency-Per--Run%20Observations-orange.svg)]()
[![Evaluated Dataset: Blind Suite v0.4](https://img.shields.io/badge/Benchmark-v0.4-blue.svg)]()
[![Roadmap: v4.0 to v4.1](https://img.shields.io/badge/Roadmap-v4.0%20to%20v4.1-brightgreen.svg)](ROADMAP.md)
[![Reproducibility: Cached Scoring](https://img.shields.io/badge/Reproducibility-Cached%20Scoring-success.svg)]()

---

> **Benchmark Mission & Transparency Statement:**  
> The **Voice-Preserving AI-Spellcheck Benchmark** is an **open, independent testing suite** measuring how effectively spelling and grammar tools fix real mistakes without destroying the writer's authentic voice, slang, or tone. Rather than serving as marketing collateral for a single vendor, our mission is to provide an honest, open standard that participating engine creators (BCorrect, LanguageTool, TextGears, DeepL Write, Sapling, JSpell, Grammarly, and independent researchers) can verify, test, and build upon. Systems are scored on the same benchmark inputs, with interaction-mode differences disclosed rather than presented as identical execution conditions.

---

## Quick Start: Replaying the Cached v0.4 Evaluation

The v0.4 evaluators replay cached engine outputs offline and do not make API calls or require API keys. Result artifacts identify this release as version `4.0`. The Blind suite requires the local run log at `Docs/Notes/blind_v3_live_runs_full.json`; that private input/output cache is excluded from this public repository. The H-suite and JSpell web-checker outputs are tracked.

The public H-suite can be rescored from a clean clone. The Blind results cannot
be independently regenerated without the private cache; the published Blind
scoreboard is a cached result, not a clean-clone reproduction. Evaluator tests
run without that cache using `python -m unittest discover -s tests`.

```bash
# Score the Blind v4 outputs (requires the separately supplied private run log):
python evaluate_blind_v4.py

# Score the H-suite v4 outputs:
python benchmark_4pillars_hybrid.py

# Score paired en-US / en-GB H-suite runs (requires the complete locale cache):
python evaluate_paired_locales.py

# Regenerate every current and historical SVG:
python generate_charts.py
```

> The previous engine-specific signature scores remain in the v3 artifacts for historical reference. They are not v4 results and are not comparable with the replacement diagnostic.
>
> **Technical Specification & Roadmap:** See [ROADMAP.md](ROADMAP.md) for the v4 scoring policy, deterministic diagnostic, and planned benchmark expansion.

---

## Executive Summary: Three Quality Pillars and a Separate Diagnostic
*Latest Benchmark Run: November 14, 2026*

Version 4.0 reports three weighted quality pillars in a quality composite. A deterministic correction-site diagnostic is reported separately and is not included in the composite:

```
+--------------------------------------------------------------------------+
|                    V0.4 QUALITY PILLARS + DIAGNOSTIC                     |
+--------------------------------------------------------------------------+
| 1. SPELLING ACCURACY                         43.75% of quality composite  |
| 2. GRAMMAR & SYNTACTIC ACCURACY               31.25% of quality composite |
| 3. MAINTAINING WRITER'S VOICE                 25.00% of quality composite |
| 4. CORRECTION-SITE EDIT DIAGNOSTIC            Reported separately         |
+==========================================================================+
| Quality composite excludes the diagnostic; v3 composite scores are legacy.|
+--------------------------------------------------------------------------+
```

### Why Existing APIs Diverge
When developers integrate spelling and grammar engines into word processors, code editors, form inputs, or chat systems, they need an engine that balances mechanical correction against voice preservation:
- **Correction-site diagnostic:** The v3 evaluator used engine-specific signatures and produced misleadingly incomparable results. Version 4.0 instead reports unapproved edits at the same annotated spelling/grammar sites for every engine. This lexical measure does not determine whether an output is semantically hallucinated.
- **Over-Editing & Voice Erasure (Failing Pillar 3):** Neural writing rewriters (such as **DeepL Write**) aggressively rephrase informal idioms, expand natural contractions, and convert casual or dialectal speech into standardized corporate textbook prose.
- **Syntactic Agreement Deficits (Failing Pillar 2):** Word-level geometric engines (such as **BCorrect FMM**) achieve top-tier spelling recovery on severe dysgraphia, but struggle with sequence-level subject-verb agreements without a language model layer.

![v0.4 H-suite quality composite](assets/hybrid_score_comparison.svg?v=4.0-aligned)

### H-suite Quality Breakdown and Diagnostic
These charts use the H-01 through H-10 suite. The B-01 through B-10 Blind suite uses different inputs; compare results only within the same suite.

![v0.4 quality-pillar breakdown](assets/pillars_breakdown.svg?v=4.0-aligned)

![v0.4 correction-site edit diagnostic](assets/correction_site_diagnostic.svg?v=4.0-aligned)

### Blended Historical Progress (v0.3 and v0.4)
The charts show all seven current competitors. The v0.3 raw composite endpoint is marked separately from each measured v0.4 endpoint. Earlier trend estimates are shifted onto the v0.4 scale by adding each shared engine's measured v0.4-minus-v0.3 endpoint difference. This is an illustrative alignment only: it does not rescore historical outputs under v0.4, and must not be read as measured historical v0.4 performance. Sapling's earlier point remains a recollection-based v0.3 estimate below 60%; Grammarly has no v0.3 data and appears only at its measured v0.4 endpoint.

The v0.3 and v0.4 composites use different rubrics. The v0.3 engine-specific signature-based anti-hallucination pillar is retired and is not a general hallucination measure; v0.4 instead reports a correction-site edit diagnostic separately from its three-pillar composite. That diagnostic is not a hallucination rate. The v0.4 H-suite and Blind suite contain seven and six systems, respectively; Grammarly has no Blind-suite outputs.

The current v4 H-suite is a single-locale baseline, not a paired locale comparison. LanguageTool and TextGears were queried with `en-US`; JSpell reports English (US), while the locale used for the other engines, including Grammarly, is unreported. Full corrected en-US and en-GB reference passages and locale-specific spelling targets are available in [raw_results/h_suite_locale_golden_texts.json](raw_results/h_suite_locale_golden_texts.json). These are reference examples, not exact-string targets: scoring remains aligned to correction sites and writer's voice. Paired scoring requires a complete `raw_results/h_suite_locale_runs_v1.json` cache with all seven engines and ten passages in both locales. The paired evaluator then creates separate locale scorecards and charts without replacing the single-locale baseline.

![Blended v0.3 and v0.4 estimates and measured endpoints for all seven engines](assets/progress_over_time.svg?v=4.0)

![Grouped v0.3 and v0.4 estimates and measured endpoints for all seven engines](assets/progress_bar_chart_over_time.svg?v=4.0)

### Tracking progress as engines improve

The blended history chart above uses the v0.3 and v0.4 H-suite artifacts, but
its earlier points are not controlled, same-input v0.4 runs. Going forward,
reports will separate two series:

- **Public anchor (regression control):** rerun the same published H-suite with
  each engine version. This is the comparable series for tracking changes over
  time, including BCorrect improvements. Because the anchor is public, it is
  not a blind leaderboard test.
- **Weekly fresh challenge:** evaluate each week's new full-size batch. Publish
  its results as a dated snapshot. Because all engines receive the same
  batch, its rankings and score gaps are valid head-to-head comparisons for
  that week. Across weeks, track relative rankings and paired score gaps as
  competitive position, but treat raw score changes as descriptive: engines
  can respond differently to changes in difficulty or writing domain.

Each recorded run should identify the engine/version, collection mode, suite
and dataset digest, evaluator revision, date, pillar scores, diagnostic counts,
quality composite, and measured latency (or `null` when unavailable). API, local, and manual web
results remain distinct. A final weekly comparison is published only after all
planned participants, including manual web checks, have results.

See the [progress tracking policy](PROGRESS_TRACKING.md) for the comparison and
recording rules.

---

## 1. v0.4 Evaluation Methodology (Result Artifact Version 4.0)

$$\text{Pillar 1 (Spelling)} = \frac{\text{Accepted Forms at Aligned Spelling Sites}}{\text{Applicable Spelling Sites}} \times 100\%$$

$$\text{Pillar 2 (Grammar)} = \frac{\text{Accepted Forms at Aligned Grammar Sites}}{\text{Applicable Grammar Sites}} \times 100\%$$

$$\text{Pillar 3 (Voice)} = \text{mean}(\text{Lexical F1} \times \text{Marker Retention}) \times \left(1 - \frac{\min(10 \times \text{Over-Edit Signatures}, 80)}{100}\right)$$

$$\text{V4 Quality Composite} = (0.4375 \times \text{Spelling}) + (0.3125 \times \text{Grammar}) + (0.25 \times \text{Voice})$$

The v4 **Correction-Site Edit Diagnostic** is reported separately. It aligns
the output tokens to the input and examines only annotated spelling and grammar
sites. An edit is accepted when the aligned output is unchanged or matches one
of the same published correction forms used for every engine. The report
includes `unapproved edits / applicable sites` and a descriptive percentage;
an empty denominator is `n/a`. The diagnostic does not contribute to the
quality composite.

This diagnostic is deterministic but lexical, not semantic: it can flag a
valid alternative that is missing from the accepted forms, and it can miss
unsupported content outside annotated correction sites. It must not be called
a hallucination detector or a real-world hallucination rate. No LLM/SLM or
human output reviewer is used to score it.

The v3 engine-specific signature metric and four-pillar composites are retained
in the versioned v3 raw result files as legacy data. They are not v4 scores and
should not be compared to v4 values.

Public grammatical-error-correction benchmarks do not provide transferable
per-engine hallucination scores for this suite. The [BEA-2019 shared task](https://aclanthology.org/W19-4406/)
uses ERRANT F0.5 to evaluate corrections against shared references, and the
[CoNLL-2014 shared task](https://aclanthology.org/W14-1701/) evaluates a
different GEC test set. Their published scores cannot be used to estimate
these seven products' v0.3/v0.4 hallucination performance. Future correction
quality comparisons should use common inputs and references with edit
precision/recall (for example, ERRANT F0.5); semantic factuality would require
a separate human-reviewed preservation test and should not be inferred from
those GEC scores.

Spelling and grammar accuracy count accepted forms at their aligned annotated
source sites, pooled across the suite. A correct phrase elsewhere cannot earn
credit for a missed correction. An unchanged source form counts only when the
annotation explicitly accepts it (for dialect and valid variants); identity-
only annotations are not accuracy targets.

The Voice scorer is unchanged: it uses case-folded word-token LCS F1 outside
annotated correction spans, multiplies it by curated voice-marker retention,
and applies the documented suite-wide over-edit penalty. This rewards systems
that avoid putting words in the writer's mouth and adapt to the writer's
dialect. It does not understand meaning, tone, cadence, or register. The
correction-site alignment is deterministic, not reviewed by a person.

The test passages are fixed, curated inputs; the evaluator does not generate or randomize new essays. "Blind/unseen" is the suite's label, not a claim of dynamically sampled or adversarially secret tests: H-suite inputs and annotations are public, and B-suite source inputs are private locally while much of their scoring logic is public. Every engine is evaluated on the same passage text. Target checks are deterministic and source-aligned; they do not establish semantic correctness.

---

## 2. Benchmark Scorecards & Visual Charts

### A. Blind Benchmark v4.0 (10 Writing Domains)
*Benchmark Run Date: November 14, 2026*

Evaluated across 10 brand-new, unseen writing styles: Urban Slang, Southern Gothic, Cyberpunk Noir, Culinary Critique, Severe Dysgraphia, SaaS Pitch, Sports Banter, Poetic Melancholy, Field Biology, and Legal Contract Shorthand.

| Engine / Model | Spelling | Grammar | Voice | Unapproved edits / sites | Quality composite | Latency |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Sapling Grammar Checker** *(web demo; one-pass)* | **★ 93.6%** | **★ 100.0%** | **★ 88.3%** | 0 / 48 (0.0%) | **★ 94.3%** | n/a |
| **DeepL Write** *(Rewriter)* | 91.5% | **★ 100.0%** | 24.1% | 4 / 48 (8.3%) | 77.3% | ~1,280 ms |
| **TextGears API** | **★ 68.1%** | **★ 100.0%** | 85.2% | 15 / 48 (31.2%) | **★ 82.3%** | ~967 ms |
| **LanguageTool API** | 66.0% | **★ 100.0%** | 64.4% | 16 / 48 (33.3%) | 76.2% | ~677 ms |
| **BCorrect (FMM Engine)** | 63.8% | **★ 100.0%** | **★ 86.6%** | 13 / 48 (27.1%) | 80.8% | ~614 ms |
| **JSpell Free Web Checker** *(web checker; one-pass)* | 63.8% | 0.0% | 77.5% | 16 / 48 (33.3%) | 47.3% | n/a |

The diagnostic column reports a deterministic lexical check at shared
annotated correction sites. It is not a hallucination score and does not
establish that a system's other output is semantically correct. Stars identify
the best score within the displayed column; the diagnostic is not ranked as a
quality score.

> **Software Architecture Distinction:**
> - **In-Place Developer APIs (BCorrect, LanguageTool, TextGears):** Designed for keystroke-level text entry, code comments, and chat. They surgically fix orthography without rewriting the author's tone, vocabulary, or cadence.
> - **Neural Text Rewriters (DeepL Write):** Designed for full-document paraphrasing. DeepL scores 91.5% spelling and 100.0% grammar target accuracy in this Blind v4 run, but scores 24.1% for Writer's Voice under the benchmark's lexical/marker heuristic.
> - **Sapling Grammar Checker:** Tested once through its interactive free web demo, not a production API. Initial visible suggestions were accepted once at their original offsets; the checker was not rerun after edits. Latency was not measured, so this is not an API throughput or latency result. The [Blind v3 output and suggestion record](raw_results/blind_v3_sapling_outputs.json) is saved; v4 results are in the [Blind v4 scoreboard](raw_results/blind_v4_official_scoreboard.json) and H-suite results in the [H-suite v4 artifact](raw_results/blind_4pillars_eval_run_v4.json). The demo is a third-party service; consult its privacy policy before submitting non-public text.
> - **JSpell Free Web Checker:** Tested through JSpell's interactive free checker, not its Cloud API or RapidAPI endpoint. The first visible suggestion for each flagged word was applied once, with no recheck. It is a dictionary-based spelling-only tool; it does not check grammar. Latency was not measured. See the [saved output and one-pass suggestion record](raw_results/jspell_web_checker_outputs.json).

Sapling and JSpell are full benchmark participants, not excluded web-demo side notes: both are scored in every sub-benchmark alongside the API engines. Their v4 H-suite and Blind results are in the [H-suite artifact](raw_results/blind_4pillars_eval_run_v4.json) and [Blind scoreboard](raw_results/blind_v4_official_scoreboard.json). Web-portal collection is manual and one-pass; latency is reported as `n/a` (JSON `null`), never estimated.

**Interpreting DeepL's voice scores:** DeepL scores 67.1% on the H-suite and 24.1% on the Blind suite. The gap reflects different passages and annotations, not a semantic understanding of voice. Treat these scores as diagnostic signals, not proof of reliable voice preservation.

The v3 four-pillar composites remain available as legacy results in versioned raw files; the v4 quality composites use only spelling, grammar, and voice. Do not compare the two composite versions as if they were the same scale.

The JSpell Cloud API's separate RapidAPI route returned HTTP 403 in this environment and was not used for these scores. The free web checker is a different product interface and should not be described as an API evaluation. The B-suite source passages are not included in the public JSpell raw file; only corrected outputs and source fingerprints are recorded.

---

### B. Subcategory Performance Analysis & Class Winners
*Benchmark Run Date: November 14, 2026*

This class-winner table uses the B-01 through B-10 Blind v4 outputs above. The separate H-01 through H-10 results are shown in the charts and reproduction guide.

These scorecards use `aligned-correction-sites-v1`; spelling and grammar
targets are pooled across aligned source sites. Voice scoring remains
`lexical-marker-f1-v2` and is unchanged. Earlier phrase-presence scores are not
comparable with this rescored table.

*(Black stars ★ indicate category-winning benchmark performance)*

| Evaluation Category | In-Place API Winner | Score | Generative / Neural Winner | Technical Rationale |
| :--- | :--- | :---: | :--- | :--- |
| **Spelling Accuracy** | **★ TextGears API** | **68.1%** | DeepL Write (91.5%) | Best spelling score in the API-only class; DeepL has the highest overall spelling score. |
| **Grammar & Agreement** | **★ BCorrect / LanguageTool / TextGears** | **100.0%** | DeepL Write (100.0%) | Multiple systems tie at 100.0%; JSpell's spelling-only checker leaves the target unchanged. |
| **Maintaining Voice** | **★ BCorrect (FMM)** | **86.6%** | Sapling (88.3%) | BCorrect leads the in-place APIs; Sapling has the highest overall voice score. |
| **Correction-site diagnostic** | Not ranked | — | Not ranked | Counts unapproved edits at shared annotated correction sites; it is not a semantic or hallucination score. |
| **Quality composite** | **★ TextGears API** | **82.3%** | Sapling (94.3%) | TextGears leads the in-place API class; Sapling has the highest overall quality composite. |
| **Recorded latency** | **★ BCorrect (FMM)** | **~614 ms** | DeepL Write (~1,280 ms) | Cached response timings vary by suite and network conditions; they are not product compute latency. Web-demo latency was not measured. |

Sapling's web-demo result is 100.0% for grammar and 94.3% for the Blind v4 quality composite, but is not grouped as an API or a neural rewriter in the class-winner columns above. TextGears is the strongest in-place API on the quality composite at 82.3%, while Sapling leads overall at 94.3%. JSpell is a spelling-only web checker, not an API result. Neither web demo's latency was measured and neither value should be interpreted as zero.

![v0.4 H-suite latency comparison](assets/latency_comparison.svg?v=4.0-aligned)

---

## 3. Qualitative Case Studies: Dedicated APIs Under Stress

### Case Study A: Casual Dialogue & Slang (Anti-Paraphrase Evaluation)
> **Author Input:** *"Honestly, I'm just gonna chill here tonite, grab sum pizza, and vibe out with the music. No way I'm goin to that party."*  
> **Intended Corrections:** *tonite* -> *tonight*, *sum* -> *some*, *goin* -> *going*.

| Engine | Resulting Output Text | Voice Preserved? | Qualitative Assessment |
| :--- | :--- | :---: | :--- |
| **BCorrect (FMM)** | *"Honestly, I'm just gonna chill here **tonight**, grab **some** pizza, and vibe out with the music. No way I'm **going** to that party."* | **Yes (100%)** | **Surgical correction.** Resolves errors; leaves *"gonna chill"*, *"vibe out"*, and conversational rhythm intact. |
| **LanguageTool API** | *"Honestly, I'm just gonna chill here **tonight**, grab **some** pizza, and vibe out with the music. No way I'm **going** to that party."* | **Yes (100%)** | Conservative rule check; preserves tone without over-editing. |
| **TextGears API** | *"Honestly, I'm just gonna chill here **tonight**, grab **some** pizza, and vibe out with the music. No way I'm goin to that party."* | **Partial** | Corrected early tokens; missed final colloquial participle *goin*. |
| **DeepL Write** | *"Honestly, I'm just **going to relax** here tonight, **get** some pizza, and **enjoy the music**. **I'm definitely not going** to that party."* | **No (0%)** | **Tone flattening.** Rewrites clauses into standardised textbook sentence structures. |

---

### Case Study B: Regional Vernacular & Cadence (Dialect Preservation Evaluation)
> **Author Input:** *"Granddaddy sat on the porch rockin slow, watchin the crik rise after the floodin. He reckned the old barn wouldnt survive another downpoar."*  
> **Intended Corrections:** *rockin* -> *rocking*, *watchin* -> *watching*, *crik* -> *creek*, *floodin* -> *flooding*, *reckned* -> *reckoned*, *wouldnt* -> *wouldn't*, *downpoar* -> *downpour*.

| Engine | Resulting Output Text | Voice Preserved? | Qualitative Assessment |
| :--- | :--- | :---: | :--- |
| **BCorrect (FMM)** | *"Granddaddy sat on the porch rockin slow, watch in the cri rise after the flooding. He reckoned the old barn wouldn't survive another downpour."* | **Moderate** | Preserved cadence and regional terms; struggled with multi-token phonetic cluster *crik rise*. |
| **TextGears API** | *"Granddaddy sat on the porch rocking slow, watchin the crick rise after the flooding. He reckoned the old barn wouldn't survive another downpour."* | **Moderate** | Retained colloquial flavor, substituted regional variant *crick*. |
| **LanguageTool API** | *"Granddaddy sat on the porch rocking slow, watching the Erik rise after the flooding. He reckoned the old barn wouldn't survive another downpour."* | **Low** | Mutated *crik* into personal name *Erik*. |
| **DeepL Write** | *"My grandfather sat on the porch, rocking slowly, watching the creek rise after the flood. He reckoned the old barn would not survive another heavy rainstorm."* | **Low** | Substitutes formal terminology (*My grandfather*, *heavy rainstorm*) and standardises phrasing. |

---

### Case Study C: Technical Developer Notes & CLI Shorthand (Developer Voice Evaluation)
> **Author Input:** *"Ran npm install, spund up the docker container, and verifeid port 8080 was listenin. Everything lookd solid."*  
> **Intended Corrections:** *spund* -> *spun*, *verifeid* -> *verified*, *listenin* -> *listening*, *lookd* -> *looked*.

| Engine | Resulting Output Text | Voice Preserved? | Qualitative Assessment |
| :--- | :--- | :---: | :--- |
| **BCorrect (FMM)** | *"Ran npm install, **spun** up the docker container, and **verified** port 8080 was **listening**. Everything **looked** solid."* | **Yes (100%)** | **Technical shorthand preserved.** Corrects spelling; retains concise dev log format. |
| **TextGears API** | *"Ran npm install, **spun** up the docker container, and **verified** port 8080 was **listening**. Everything **looked** solid."* | **Yes (100%)** | Accurately resolved past-tense technical verbs. |
| **LanguageTool API** | *"Ran npm install, **spun** up the docker container, and **verified** port 8080 was **listening**. Everything **looked** solid."* | **Yes (100%)** | Handled technical log accurately. |
| **DeepL Write** | *"I ran npm install, launched the docker container, and verified that port 8080 was listening. Everything seemed solid."* | **Moderate** | Injected first-person pronoun *"I"* and replaced developer jargon *"spun up"* with *"launched"*. |

---

## 4. Academic GEC Context: CoNLL-2014 & BEA-2019

To maintain complete academic transparency, BCorrect was also evaluated against traditional grammatical error correction corpora:

| Dataset | Standard Metric | BCorrect Score | Baseline Systems (T5 / GECToR) | Why the Gap Exists |
| :--- | :---: | :---: | :---: | :--- |
| **CoNLL-2014** | $F_{0.5}$ (m2scorer) | **9.34%** | 65.0% to 72.0% | CoNLL annotations reward full sentence restructuring and preposition swaps to formal ESL textbook standards. BCorrect deliberately leaves valid non-standard syntax untouched. |
| **BEA-2019 Dev** | $F_{0.5}$ (ERRANT) | **14.2%** | 68.0% to 75.0% | Traditional GEC rewards high edit density. A non-invasive model that fixes only clear typos will mechanically score low on reference edit overlap. |

BCorrect's intended design follows the **Minimal Intervention Principle**:
- Mechanically resolves orthography, phonetics, and syntax without imposing stylistic templates.
- A separate local-runtime claim is not measured by the cached API-response timings in this benchmark.

---

## 5. Methodology, Protocol & Limitations

### Evaluation Protocol
1. **Blind Unseen Corpus:** The test set consists of 10 passages spanning distinct stylistic domains (slang, regional dialect, poetry, technical notes, legal text, severe dysgraphia). No system was tuned or calibrated on these passages.
2. **Standardised Error Tagging:** Each passage defines explicit spelling targets, grammar targets, stylistic voice markers, and forbidden rewrites.
3. **Execution Environment:**
   - Dedicated APIs (BCorrect, TextGears, LanguageTool) were queried via HTTP REST endpoints; DeepL Write was evaluated separately.
   - Sapling and JSpell were tested through interactive web demos by applying initial suggestions once without rechecking. Neither result is an API run.
   - Latency is reported only when measured; no web-demo latency was collected.

### Known Limitations
- **Sample Size:** The blind suite currently contains 10 comprehensive passages (approx. 400 words total across domains). While representative of diverse registers, larger-scale corpora are continually being added.
- **Latency Variance:** The cached BCorrect, TextGears, and LanguageTool values are REST response timings and depend on network routing; they do not measure local engine execution. DeepL and web-demo latency were not recorded for the H suite, and no product-speed comparison is made from missing values.

---

## 6. Local Reproduction & Verification

The evaluation suite is open-source and reproducible. For comprehensive instructions, environment setup, and troubleshooting, see the [Independent Reproduction Guide](REPRODUCTION_GUIDE.md).

### 1. Installation
```bash
git clone https://github.com/IBIYP/voice-preserving-ai-spellcheck-benchmark.git
cd voice-preserving-ai-spellcheck-benchmark
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install requests
```

### 2. Configure API Keys (Optional for Live Cloud API Testing)
Create a `.env` file in the project root:
```env
BCORRECT_API_KEY=your_bcorrect_key_here
TEXTGEARS_API_KEY=your_textgears_rapidapi_key_here
```

### 3. Execution Commands

```bash
# Run the official Blind Suite v4.0 evaluation (cached outputs)
python evaluate_blind_v4.py

# Run the H-suite v4.0 evaluation
python benchmark_4pillars_hybrid.py

# Regenerate all monochrome 90-degree SVG charts
python generate_charts.py

# Run codebase character hygiene scanner (verifies 0 non-ASCII anomalies)
python bad_character_scanner.py
```

---

## 7. Documentation & Raw Results Repository

### Raw Test Results & Data Logs (`raw_results/`)
- **Raw Test Logs & Methodology Guide:** [raw_results/README.md](raw_results/README.md)
- **H-suite v4 Evaluation Log (JSON):** [raw_results/blind_4pillars_eval_run_v4.json](raw_results/blind_4pillars_eval_run_v4.json)
- **Blind v4 Scoreboard (JSON):** [raw_results/blind_v4_official_scoreboard.json](raw_results/blind_v4_official_scoreboard.json)
- **Legacy v3 Result Files:** [H-suite v3](raw_results/blind_4pillars_eval_run.json) and [Blind v3](raw_results/blind_v3_official_scoreboard.json)
- **Unseen 10-Domain Outputs & Measured Latencies (JSON):** [raw_results/unseen_10_domains_live_run.json](raw_results/unseen_10_domains_live_run.json)
- **Blind v3 Sapling Web-Demo Outputs (JSON):** [raw_results/blind_v3_sapling_outputs.json](raw_results/blind_v3_sapling_outputs.json)
- **JSpell Web-Checker Outputs (JSON):** [raw_results/jspell_web_checker_outputs.json](raw_results/jspell_web_checker_outputs.json)
- **Grammarly Web-Checker Outputs (complete H-suite only):** [raw_results/grammarly_web_checker_outputs.json](raw_results/grammarly_web_checker_outputs.json)
- **H-suite en-US/en-GB Full-Passage References:** [raw_results/h_suite_locale_golden_texts.json](raw_results/h_suite_locale_golden_texts.json)
- **Norvig & Birkbeck 30 Human Spelling Pairs (JSON):** [raw_results/norvig_birkbeck_30_pairs.json](raw_results/norvig_birkbeck_30_pairs.json)

### Scorecards & Independent Reproduction
- **Step-by-Step Reproduction Guide:** [REPRODUCTION_GUIDE.md](REPRODUCTION_GUIDE.md)
- **Engine Submission Protocol & Legal Waiver:** [SUBMISSIONS.md](SUBMISSIONS.md)

---

## 8. Submitting an Engine for Official Benchmark Inclusion

We welcome independent researchers, open-source maintainers, and commercial API creators to submit their spelling, grammar, or writing assistance systems for official benchmark evaluation:
- **Submission Protocol & Legal Waiver:** Review [SUBMISSIONS.md](SUBMISSIONS.md) for full eligibility criteria and binding legal disclaimers.
- **Engine Submission Form:** Open a submission request using the [New Engine Submission Template](https://github.com/IBIYP/voice-preserving-ai-spellcheck-benchmark/issues/new?template=engine_submission.md).
- **Safe Credential Handshake:** All test API keys must enforce a mandatory **$1.00 USD hard spending cap**. Maintainers bear zero financial liability, and submitters assume full responsibility for credential safety and revocation.
- **Verified Community Registry:** All official evaluation outputs are archived transparently in [raw_results/submissions/](raw_results/submissions/).

---

## 9. Legal Notices & Fair Use Attribution

> **Scope of MIT License & Proprietary Technology Notice:**  
> The MIT License provided in this repository applies strictly and exclusively to the open benchmark scripts, evaluation test harnesses, scoring functions, and documentation. Nothing herein grants, conveys, or implies any license or rights to the proprietary architectures, models, or APIs of any evaluated engines (including DeepL Write, LanguageTool, TextGears, BCorrect, Sapling, or JSpell), all of which remain the exclusive intellectual property of their respective creators and organizations.
> 
> **Nominative Fair Use & Non-Affiliation:**  
> TextGears is a registered trademark of TextGears Ltd. LanguageTool is a registered trademark of LanguageTooler GmbH. Grammarly is a registered trademark of Grammarly, Inc. DeepL is a registered trademark of DeepL SE. Google Docs is a trademark of Google LLC. ProWritingAid is a trademark of Orpheus Technology Ltd. BCorrect is a proprietary technology of its respective owners.  
> 
> The Open Voice-Preserving Benchmark Working Group is an independent research collective. This benchmark repository is not affiliated with, sponsored by, or endorsed by any evaluated commercial entity or API provider. All third-party product names and trademarks are used strictly for comparative identification and scientific benchmarking under **Nominative Fair Use** (15 U.S.C. Section 1125(c)(3)).
