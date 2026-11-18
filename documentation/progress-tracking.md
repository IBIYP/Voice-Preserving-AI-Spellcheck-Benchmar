# Tracking Benchmark Progress

The v0.5 protocol is still a draft. We have not collected engine outputs, so
there are no scores to plot or report yet.

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

A weekly challenge may use new passages and controls. It is a separate series:
compare engines tested on the same week's batch, but do not treat score changes
across different batches as evidence of improvement. The fixed anchor provides
the same-input longitudinal signal; challenge results show performance on that
week's material.

## Reporting

Publish only complete, provenance-recorded runs. Keep spelling, grammar, voice,
and negative-control-preservation pillars visible alongside the equal-weight
composite. Report known negative-control hits separately from unclassified
changes. Neither category is a general hallucination measure.

If the engine cohort, scoring method, or anchor changes, document a separate
series rather than silently joining scores. Do not publish a chart before
there are valid results.
