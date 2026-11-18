# Benchmark Versions

The published scorecard is still v0.4. v0.5 is the proposed next version, but
it remains a draft and is not frozen or scoreable. Here's a side-by-side look
at what would change:

| | v0.4: current scorecard | v0.5: proposed test |
| --- | --- | --- |
| **Status** | Published results are available. The scorecard reads saved outputs. | Draft only; no results collected yet. |
| **Inputs** | Ten H-suite passages. | Ten newly written passages, each paired in en-US and en-GB, with locale cues: 20 inputs. |
| **Scored pillars** | Spelling 43.75%; grammar 31.25%; writer's voice 25%. | Spelling, grammar, voice, and negative-control preservation, each 25%. |
| **Controls and extra reporting** | Unapproved edits are reported separately; there is no control-preservation pillar. | Adds a 25% negative-control pillar. Each control is checked in both language versions, for 20 checks in total. |
| **Engines** | Seven engines in the published scorecard. | No fixed engine count yet; each engine in a run must receive the same 20 inputs. |

Here, “H-suite” means the ten-passage test set used by the v0.4 scorecard.
V0.5 uses different passages and scoring, so its results won't continue the
v0.4 series. The draft may still change. The
[manifest](../../benchmark_data/v0.5_anchor_draft.json) shows its passages and
locale cues. Its controls are disclosed, not blind; similarity and rights
review is still open. See the [dataset scope and licence](../../benchmark_data/README.md)
and [collection requirements](../benchmark-v0.5-draft.md#freeze-and-collection-requirements).

See the [current v0.4 results and run instructions](../../README.md) and
[scoring details](../benchmark-details.md).

## Help improve the benchmark

We welcome ideas from writers, researchers, developers, providers, and anyone
who cares about fair testing. Useful feedback could cover passage realism,
regional language, annotation decisions, negative controls, scoring, or how to
make collection and results easier to reproduce.

Please [open an issue](https://github.com/IBIYP/Voice-Preserving-AI-Spellcheck-Benchmar/issues)
or submit a pull request. Say which version or draft section your suggestion
concerns, explain why it would improve the test, and include a concrete
example where possible. Ideas are welcome, though we may not adopt every
suggestion. Feedback is most useful before the protocol is frozen and outputs
are collected. Don't include private, confidential, or provider-restricted
text or results.

Thank you!
