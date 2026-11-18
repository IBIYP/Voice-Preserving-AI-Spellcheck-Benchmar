# Roadmap

We are preparing one fixed-anchor, four-pillar protocol for v0.5. There are no
published v0.5 scores yet.

## 1. Review and freeze the anchor

- Review all 20 paired inputs, spelling and grammar annotations, locale cues,
  and ten control definitions.
- Confirm each control's rationale and disclose controls inspired by earlier
  observations.
- Complete the text similarity/reuse review and the external spelling-panel
  provenance/reuse review; verify the separate CC0-1.0 scope.
- Freeze the protocol only after review; record its digest and freeze timestamp.

## 2. Collect a complete paired run

- Use the same frozen inputs and controls for every engine in a run.
- Do not force a locale; record each provider's automatic/default locale
  handling, product version, route, source URL, and collection timestamp.
- Validate a complete cache before scoring. The evaluator rejects partial
  caches, changed inputs, forced locales, or collection that predates the
  control freeze.
- Publish a result only when collection provenance and publication permissions
  have been reviewed.

## 3. Track change without confusing datasets

- Keep the fixed anchor and its scoring method stable for longitudinal
  comparisons.
- Create a separate dated weekly challenge set to reveal new behaviour.
- Compare weekly challenge results only within the same batch. Do not treat
  scores across different challenge sets as a controlled trend.
- Keep any future spelling-only diagnostic separate from the four-pillar
  composite and publish it only after its source and reuse terms are verified.

No engine outputs should be collected until the user has reviewed and approved
the frozen protocol.
