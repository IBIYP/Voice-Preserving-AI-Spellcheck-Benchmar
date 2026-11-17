# v0.5 Four-Pillar Scoring Details

This page describes the v0.5 draft only. The protocol is not frozen, no
scorecard exists, and the scorer will reject the draft until review is complete.
The [machine-readable manifest](../benchmark_data/v0.5_anchor_draft.json) is
the source for its paired inputs and annotations.

## Test shape

The fixed anchor contains ten passages with a paired en-US and en-GB input,
for 20 samples total. Each passage has the same underlying writing scenario and
one explicit spelling cue for its locale. The input text (not a locale option
passed to the provider) must drive automatic dialect handling. Record the
provider's locale configuration for every run and do not force en-US or en-GB.

Each base passage has exactly one predefined negative control. The same
control is applied to both locale variants, yielding 20 control observations
per engine. Controls and their rationales must be frozen before new outputs are
collected.

## Pillars

### 1. Spelling

Score annotated source occurrences against their locale-specific accepted
forms using aligned correction-site matching. Correct dialect cue forms are
identity targets: retaining the form in the input earns credit, while
switching it to the other locale's spelling does not. Pool accepted hits and
targets across the complete paired anchor.

### 2. Grammar

Use the passage-specific grammar annotations in the protocol manifest and
aligned correction-site matching. Identity-only annotations are excluded from
the denominator. Pool accepted hits and applicable targets across the anchor.

### 3. Writer's voice

Use the deterministic lexical-token LCS F1 outside annotated correction spans,
multiplied by curated voice-marker retention. Apply the existing suite-level
over-edit penalty after averaging passage-level scores. This is a lexical
heuristic; it does not understand meaning, tone, or whether every correction is
semantically valid.

### 4. Negative-control preservation

For each output, case-insensitive exact phrase matching with word boundaries
assigns one of three labels:

- `preserved`: protected span is present and no listed false form is present;
  score 100.
- `known_negative_control_hit`: a predefined false form is present; score 0.
- `unclassified_change`: neither the protected span nor a listed false form is
  present; score 0 and flag for review.

If a known false form and the protected phrase both occur, the known hit takes
precedence. Approximate matches and unlisted edits are not promoted to known
hits. A hit is evidence about the specified control only, not a general
hallucination label, rate, or causal explanation.

The preservation pillar is the count of preserved controls divided by the
number of control observations. Report known hits and unclassified changes
separately. All four pillar scores are combined at equal 25% weights.

## Reporting limits

Only the measured spelling and grammar targets and the fixed protected spans
are scored. The protocol cannot claim that all unlisted changes are correct or
incorrect. It also cannot establish a provider's overall hallucination rate,
semantic fidelity, or real-world performance.

The weekly challenge set is separate from the fixed anchor. Compare engines
within the same week's challenge set; use the unchanged fixed anchor for
week-to-week trend tracking. See the [draft protocol](benchmark-v0.5-draft.md)
for the freeze and collection requirements.
