# Tracking Benchmark Progress

The v0.5 protocol is still a draft, with no results collected under that
protocol. A separate v0.4 H-suite repeat series is now being tracked for fresh
10-passage batches; completed rounds (`h-suite-repeat-v1` and
`h-suite-repeat-v2`) are logged in
[`../raw_results/h_suite_weekly_history.json`](../raw_results/h_suite_weekly_history.json)
and plotted as time-based line graphs by `generate_charts.py` (with solid lines
for retested engines and dashed carry-forward reference lines for engines last
measured on the `2026-11-14` v0.4 H-suite). The v0.4 pillar bar chart
(`assets/pillars_breakdown.svg`) also shows the snapshot date and 95% confidence
intervals (`n=49` Spelling, `n=12` Grammar, `n=10` Voice passages).

## Fixed anchor

The ten paired passages and their controls are intended to remain unchanged
after review and freeze. Each run uses both locale variants for every passage,
with automatic dialect detection and no forced locale. This fixed set provides
the basis for week-to-week comparisons of the same inputs.

Keep each run immutable and record its protocol digest, collection timestamp,
engine/provider version (or `not reported`), route, source URL, locale
configuration, and latency method. Preserve missing latency as JSON `null`;
never estimate it. A provider output collected before the protocol was frozen
cannot be scored under the v0.5 cache contract.

## Weekly challenge

Each weekly repeat uses ten new H-suite passages and the existing v0.4 scoring
weights. Compare providers tested on the same frozen weekly batch. Keep every
batch and output immutable, with its dataset digest and collection provenance.

Scores from different weekly batches are tracked as descriptive observations,
not as a controlled measure of provider improvement: the passages differ, so
their difficulty may differ. Use the fixed anchor for same-input longitudinal
comparisons. When available, the same-route JSpell API control can help
interpret batch-to-batch difficulty, but it does not make different passages
equivalent. Keep JSpell Cloud API results separate from the JSpell free web
checker.

## Reporting

Publish only complete, provenance-recorded runs. Keep spelling, grammar, voice,
and negative-control-preservation pillars visible alongside the equal-weight
composite. Report known negative-control hits separately from unclassified
changes. Neither category is a general hallucination measure.

If the engine cohort, scoring method, or anchor changes, document a separate
series rather than silently joining scores. Do not publish a chart before
there are valid results.
