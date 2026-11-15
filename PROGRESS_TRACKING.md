# Progress Tracking Policy

The benchmark reports both current performance and change over time, without
treating scores from different test batches as if they were measured on the
same inputs.

## Two separate series

### Public anchor

Use the fixed H-suite as a public regression-control set. Run it with each
engine revision using the same evaluator and collection procedure. This series
is suitable for comparing an engine with its earlier versions, but the public
test and annotations can be learned or optimized against. It must not be
presented as a blind generalization score.

Record a point only when the engine revision and run are identifiable. If a
provider does not expose a version, record `not reported`; do not infer a
version from the run date.

### Weekly fresh challenge

Each weekly batch is a fresh, full-size challenge. Keep its score attached to
that batch ID and publish it as a dated snapshot. Because every engine is run
on the same batch, its within-week scores, rankings, and pairwise score gaps
are valid head-to-head comparisons, even when the batch is harder or easier
than the previous one.

Across weeks, report relative rankings and pairwise score gaps as a descriptive
measure of competitive position. Do not treat raw score changes as proof of
absolute improvement: engines can respond differently to changed difficulty,
domains, or error types. The public-anchor series is the controlled measure
for comparing an engine with its own earlier revisions on identical inputs.

Keep unreleased inputs and annotations private until their release. A weekly
report is final only after every planned participant has a result, including
manual web-checker runs. Clearly label incomplete results as pending and do not
silently omit a missing participant from a final comparison.

## Required run metadata

For each engine and evaluated suite, preserve:

- run date and immutable run ID;
- engine/provider name and reported version, or `not reported`;
- collection mode (`api`, `local`, or `web_demo`) and relevant interaction
  details;
- suite/batch ID, input digest, and evaluator revision;
- spelling, grammar, voice, correction-site diagnostic, and quality-composite scores;
- latency only when measured under a documented procedure; otherwise `null`;
- completion status and any unavailable result reason.

The current cached v4 artifacts derive a stable result ID from the saved
outputs and record dataset/output hashes and `aligned-correction-sites-v1`.
The original provider versions and per-engine run IDs were not captured, so
they are explicitly recorded as `not reported`/`not recorded`; a derived
result ID is not a substitute for provider run provenance. Record those fields
at collection time for future runs.

Sapling and JSpell are full participants in every sub-benchmark. For web-only
checks, collect and record their output for every passage using the documented
one-pass procedure; do not omit them from a suite because collection is manual.
Represent unavailable latency as JSON `null` and display it as `n/a`. Never
estimate latency.

Never overwrite an earlier run to make a chart look smoother. Corrections to
recorded data should be traceable and explained.

## Retrospective chart estimates

The historical chart retains the v3-era trend for context. Values before the
final v3 point are approximate historical estimates, not saved run results;
they must not be added to raw results or used to claim verified improvement.
The final v3 points are measured H-suite results read from
`raw_results/blind_4pillars_eval_run.json`. BCorrect and the API competitors'
earlier points are estimates. JSpell's earlier points assume a flat score
equal to its measured v3 result. Sapling's pre-November status is shown only as
a recollection-based estimate below 60%; no exact score or before-November run
is available. Its November v3 point is measured. None of these assumptions is
a provider-version record or a controlled before-and-after comparison.

The charts use hollow markers or range bars for approximate points and filled
markers or bars for measured v3 results. v4 charts use the saved v4 H-suite
artifact; v3 and v4 composite scores are not directly comparable. Going
forward, publish only dated, reproducible measurements as measured results,
with estimates kept visibly separate.

## Interpretation

Use the public-anchor series for longitudinal engine-version comparisons and
the fresh-challenge series for current, less-overfit performance and
same-week head-to-head comparisons. Keep a consistent participant cohort when
reporting cross-week rank or score-gap trends; if the cohort changes, disclose
it. A change in one series does not imply the same change in the other. Keep
API, local, and web-demo results visibly separated; in particular, web-demo
latency is unavailable unless it was actually measured.

Scores from different evaluator or scoring revisions are not directly
comparable. Rerun the same saved outputs under one revision before making a
longitudinal comparison; otherwise mark the methodology break and keep the
legacy series separate.

## Version 4.0 Correction-Site Edit Diagnostic

The v4 diagnostic examines only annotated spelling and grammar correction
sites. It reports unapproved edits at those sites against the same accepted
forms for every engine. It is a lexical diff signal, not a general hallucination
detector or a real-world hallucination rate.

Spelling and grammar accuracy also use source-aligned sites, but measure
accepted target forms rather than unapproved edits. An unchanged source counts
as correct only when it is explicitly an accepted form; identity-only
annotations are excluded. Both accuracy pillars are pooled over target sites
across the suite. Voice scoring remains the separate lexical-F1, curated
marker-retention, and over-edit-penalty formula.

- Use only deterministic, public, versioned rules; do not call an LLM/SLM or
  have a person judge the outputs.
- A site is applicable when its source phrase is present in the input and the
  annotation lists at least one distinct accepted correction form.
- An output site is approved when it is unchanged or aligns to one of the
  accepted correction forms. Otherwise, count one unapproved edit at that site.
- Publish `unapproved edits / applicable sites`, the raw counts, and the
  percentage. If no sites apply, report `n/a`.
- Apply the same annotation catalog and matching behavior to every engine on
  the same batch. Never use engine-specific annotations for this diagnostic.
- The diagnostic does not assess edits outside annotated correction sites and
  cannot determine semantic correctness. Do not label its rate a hallucination
  score or include it in the v4 quality composite.
- Preserve the v3 engine-specific signature metric and four-pillar composite
  as legacy results. Do not compare them directly with v4 values.
