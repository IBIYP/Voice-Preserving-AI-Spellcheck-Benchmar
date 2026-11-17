# Voice-Preserving Spellcheck Benchmark

A transparent, reproducible benchmark evaluating how effectively spelling and
grammar tools correct text without degrading authorial voice or altering meaning.

## Start here

- [Four equal pillars](#four-equal-pillars)
- [Benchmark results](#results)
- [How scoring works](documentation/benchmark-details.md)
- [Protocol data: paired inputs, annotations, and controls](benchmark_data/v0.5_anchor_draft.json)
- [Documentation index](documentation/README.md)

## Four equal pillars

| Pillar | Weight | What it measures |
| --- | ---: | --- |
| Spelling | 25% | Annotated spelling corrections, including expected locale forms |
| Grammar | 25% | Annotated grammar corrections |
| Voice | 25% | Lexical preservation and curated voice-marker retention |
| Negative-control preservation | 25% | Preservation of one predefined protected span per passage |

## Results

![Overall quality score comparison](assets/hybrid_score_comparison.svg)

### H-suite: 10 passages, 7 engines

| Engine | Spelling | Grammar | Voice | Unapproved edits | Quality composite | Latency |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Grammarly** | 93.9% | 100.0% | 96.8% | 3 / 61 (4.9%) | **96.5%** | n/a |
| **Sapling** | 93.9% | 100.0% | 89.1% | 2 / 61 (3.3%) | **94.6%** | n/a |
| **DeepL Write** | 87.8% | 66.7% | 67.1% | 10 / 61 (16.4%) | **76.0%** | n/a |
| **BCorrect (FMM)** | 79.6% | 58.3% | 88.9% | 7 / 61 (11.5%) | **75.3%** | ~776.5 ms |
| **TextGears** | 75.5% | 66.7% | 83.2% | 7 / 61 (11.5%) | **74.7%** | ~974.3 ms |
| **LanguageTool** | 75.5% | 50.0% | 84.1% | 16 / 61 (26.2%) | **69.7%** | ~652.8 ms |
| **JSpell** | 71.4% | 33.3% | 84.9% | 18 / 61 (29.5%) | **62.9%** | n/a |

![Pillars breakdown](assets/pillars_breakdown.svg)

### Run the benchmark

The benchmark runs offline with zero third-party dependencies and evaluates saved engine outputs:

```bash
# Score the H-suite outputs and display the scorecard
python benchmark_4pillars_hybrid.py

# Regenerate all SVG charts in assets/
python generate_charts.py
```

## Verification and tests

Run the unit test suite with Python 3:

```bash
# Run all 59 unit tests:
python -m unittest discover -s tests -v

# Run the focused v0.5 protocol validation tests:
python -m unittest discover -s tests -p test_benchmark_v05.py -v
```

## Data and privacy

Do not submit private or sensitive text to external writing services. Keep
credentials and personal information out of the repository. The supplemental
spelling-pair file remains under source and reuse review and is not part of the
four-pillar score. The newly drafted v0.5 passage set is dedicated under
CC0-1.0, but its similarity and rights review must be completed before public
release.

## Legal limitations, fair use, and provider opt-out

- **Good-Faith Open Evaluation:** This benchmark is an independent, reproducible
  scientific test suite conducted in good faith without malice or bad-faith intent
  toward any evaluated product or commercial provider.
- **Fair-Use Commentary:** All evaluations, comparative metrics, and product names
  are presented under protected nominative fair use (15 U.S.C. Section 1125(c)(3))
  and fair-use commentary (17 U.S.C. Section 107).
- **Disclaimer of Reputational Liability:** Maintainers and contributors assume no
  legal liability or responsibility for any alleged harm to reputation, commercial
  standing, brand value, or financial outcomes resulting from these open tests.
  Anyone can independently inspect and execute the test suite offline.
- **Provider Opt-Out:** Providers who prefer not to have their products included in
  future benchmark cycles may submit an exclusion request via our
  [Provider opt-out issue template](.github/ISSUE_TEMPLATE/benchmark-opt-out.yml) and
  will be excluded from subsequent runs. We respectfully encourage providers to
  participate in the spirit of open scientific progress.

For complete details, see the
[Collection, Publication, and Legal Policy](documentation/submission-policy.md).

## License

The benchmark software and documentation are licensed under Apache-2.0; see
[LICENSE](LICENSE) and [NOTICE](NOTICE). The v0.5 passages and annotations are
separate dataset material dedicated under CC0-1.0; see
[benchmark_data/LICENSE.txt](benchmark_data/LICENSE.txt) and
[its scope notes](benchmark_data/README.md). These data terms do not cover
software, provider outputs, or third-party material.
