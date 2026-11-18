# Data and Tooling Provenance

## v0.5 anchor

The v0.5 draft contains ten newly composed passages with paired
English-locale cues, scoring annotations, and negative controls. No text from
the former H-suite candidate was intentionally reused. The original text and
annotations are dedicated under CC0-1.0 in
[`benchmark_data/LICENSE.txt`](../benchmark_data/LICENSE.txt). The draft has
not yet been checked against all third-party corpora for phrase overlap; that
review is required before public release.

The annotations and controls are benchmark protocol choices; they are not
claims of affiliation with or endorsement by a provider or research
organisation. Each candidate false form was drafted before any v0.5 outputs
were collected. The controls are disclosed in the public manifest and are not
blind.

The v0.5 scorer uses deterministic local functions for aligned spelling and
grammar target matching and lexical writer-voice comparison. It does not call
an LLM to judge outputs. Its negative-control matcher checks only predefined
exact phrases; the resulting rate is not a general hallucination measure.

## Separate spelling-pair panel: review pending

An earlier local `norvig_birkbeck_30_pairs.json` candidate does not record
per-pair provenance and is excluded from the fresh repository. Peter Norvig's
[spelling-corrector article](https://norvig.com/spell-correct.html) documents
an algorithm and language-model example; it is not, by itself, documentation
for this 30-pair dataset. The
[Birkbeck misspelling-corpora page](https://www.dcs.bbk.ac.uk/~ROGER/corpora.html)
describes the Birkbeck corpus, but does not establish which entries in the
local file came from it or the reuse terms for those entries.

That panel is not part of the four-pillar composite or the v0.5 protocol. Do
not redistribute it until the exact sources, attribution, and applicable
permissions have been verified.

## Context and identification

CoNLL-2014, BEA-2019, JFLEG, and ERRANT are relevant prior GEC research and
tools, but they are not source datasets or runtime dependencies for the v0.5
anchor. Product and service names used in future result artifacts identify the
systems tested and do not imply endorsement or sponsorship.

The repository's licence applies only to material the project has rights to
license. It does not relicense third-party software, datasets, or provider
outputs. Review third-party terms before collecting or publishing their
material.
