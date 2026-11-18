# Four-Pillar Anchor v0.5 (Draft)

**Status: draft; not frozen, not yet scoreable, and no new engine outputs have
been collected. Historical scorecards and output files are excluded from the
fresh repository.**

The candidate protocol is defined in
[`benchmark_data/v0.5_anchor_draft.json`](../benchmark_data/v0.5_anchor_draft.json).
It pairs ten newly drafted passages in en-US and en-GB, adds a clear locale cue
to each, and defines one negative control per base passage. The former H-suite
candidate was not reused. All engines in a run must receive the same 20 inputs.
The original passage text, annotations, and controls are dedicated under
CC0-1.0; the separate data licence and scope are documented in
[`benchmark_data/README.md`](../benchmark_data/README.md).

## Proposed score

The four pillars have equal weight:

| Pillar | Weight | Measurement |
| --- | ---: | --- |
| Spelling | 25% | Accuracy at annotated spelling sites, including strict locale forms and the added dialect cues |
| Grammar | 25% | Accuracy at the existing annotated grammar sites |
| Voice | 25% | The existing lexical and voice-marker heuristic, with accepted locale variants normalized |
| Negative-control preservation | 25% | Whether each protected span survives the output |

Spelling and grammar targets are pooled over the 20 samples. The voice score
uses the existing suite-level aggregation and over-edit penalty. Each of the
20 control observations is worth one point: it is **preserved** if its protected
phrase remains, unless a predefined known-false phrase is also present. A
known-false exact match is reported as `known_negative_control_hit`; if neither
the protected phrase nor a known-false phrase is found, the result is
`unclassified_change`. Both receive zero preservation points, but the
unclassified result is not described as hallucination.

Control matching is case-insensitive, exact phrase matching with word
boundaries. It does not infer that a similar-looking or semantically related
edit is a control hit. A control hit is evidence only about this predefined
test item, not a general hallucination rate or a claim about why an engine
changed text. The JSON manifest records each control's rationale and whether
its candidate was previously observed. Previously observed candidates are
disclosed and are not blind.

Scores reflect deterministic, repeatable outputs within this open test harness
and are offered in good faith as fair-use comparative commentary. They do not
imply malicious intent or bad faith toward any participating provider. To the
extent the law allows, the maintainers accept no liability for alleged
reputational or commercial harm resulting from published scores; see the full
[collection, publication, and legal policy](submission-policy.md). Providers
wishing to exclude their tools from future runs may do so via our
[opt-out procedure](submission-policy.md#provider-opt-out-procedure).

## Comparisons over time

Keep the fixed anchor and its control set stable after review and freeze. It is
the basis for week-to-week trend comparisons. A separate weekly challenge set
can rotate to expose new behaviour, but scores from different weekly challenge
sets should not be compared as if they were the same test. Compare engines
within that week's challenge set; use the fixed anchor for the longitudinal
trend.

The separate Norvig/Birkbeck spelling-pair candidate is not part of this
composite or the fresh-repository data. Its exact source mapping and reuse
terms are still under review; do not treat it as cleared for redistribution or
as evidence for sentence-level grammar or voice.

## Freeze and collection requirements

Before any outputs are collected, review the paired inputs, all ten controls,
and their rationales; then change the protocol status to `frozen` and update
its version from the draft suffix to the frozen release identifier. Complete
the text similarity/reuse review and confirm all accepted locale forms. A complete result
cache must identify the frozen protocol digest, record a timezone-aware freeze
time earlier than collection, identify each engine and its route/version/source,
and confirm that locale was auto-detected or not set.
The scorer rejects a draft protocol, incomplete sample/engine coverage,
changed input hashes, mismatched protocol digests, and forced locale settings.

This draft deliberately has no scorecard and no collected outputs. Do not use
outputs collected under another protocol as if they were collected under this
one.
