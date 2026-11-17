# Collection, Publication, and Legal Policy

The v0.5 protocol is under review. Do not collect or submit outputs for an
official v0.5 run until the inputs and controls have been reviewed and the
protocol has been explicitly frozen.

## What may be evaluated

Spelling checkers, grammar tools, writing assistants, APIs, web interfaces,
and local libraries may be considered. A run must use the same frozen 20
paired inputs and ten controls for every engine. Locale must not be forced;
record the provider's default or automatic-detection behavior.

The benchmark does not request API keys. If a local collection requires a
credential, the collector must use their own key and must not commit, attach,
or share it.

## Required collection record

Record the protocol version and digest, UTC freeze and collection timestamps,
engine/provider, reported product version (or `not reported`), route, source
URL, locale setting, exact input hashes, suggestion/recheck policy, and
latency method. Use `null` for unmeasured latency. A complete run is required
for scoring; do not silently omit unavailable engines or passages.

## Privacy and publication

Do not submit private customer text, credentials, or confidential material.
Only collect and publish text that may be shared under the relevant provider
terms and data rights. Review raw outputs and provenance before publication.
The benchmark is not legal advice and does not guarantee that third-party
content may be redistributed.

Published results must identify the exact protocol and collection route.
Product names identify evaluated systems and do not imply endorsement or
sponsorship.

## Score interpretation and limitations

The four pillars are equally weighted. Negative-control hits apply only to
predefined exact patterns. Unclassified changes are not labeled
hallucinations, and the negative-control score is not a general hallucination
rate or semantic-fidelity measure.

Scores represent deterministic measurements under a specific, reproducible
test harness. They do not constitute an exhaustive evaluation of all commercial
features, interactive workflows, or full generative capabilities of evaluated
systems.

## Good faith, fair use, and commentary

This benchmark is an open and honest project run in good faith. We have no
motive of bad faith, and we do not intend to harm or disparage any company,
developer, or product.

This benchmark is not intended to represent or serve any one company or
organization. We hope every tested provider will eventually help review and
shape it, and we invite all providers and researchers to share input and
feedback.

We believe our tests, scorecards, and comparisons are protected fair-use
commentary and public review:
- **Nominative Fair Use** (15 U.S.C. Section 1125(c)(3)): We mention third-party
  product names and trademarks solely to identify the tools we test.
- **Fair Use Commentary** (17 U.S.C. Section 107): We provide open,
  reproducible commentary and educational testing on publicly available tools.

Anyone can download the code, inspect every line, and run the benchmark offline
to verify our results.

## Disclaimer of liability and reputational harm

This benchmark, its scripts, sample data, and published scores are provided on
an "as is" basis without any warranties.

To the extent the law allows, the maintainers accept no liability for:
- Any direct, indirect, incidental, or consequential damages;
- Any alleged harm to reputation, brand image, commercial standing, sales, or
  business operations;
- Any purchasing or software adoption choices made by third parties based on our
  scores.

Our results are objective, reproducible numbers from a specific test harness.
They represent fair commentary and comparative analysis based on open code, not
absolute statements about how a tool performs in every real-world scenario.

## Provider opt-out procedure

We respect software creators. If any company or developer does not want their
tool included in future benchmark runs, they can ask to be removed:

- Open a request using the
  [Provider opt-out issue template](../.github/ISSUE_TEMPLATE/benchmark-opt-out.yml)
  or reach out through the repository.
- Once verified, we will exclude that tool from all future evaluation rounds.

We ask providers to stay so that the public has honest, open data, but we will
never force a provider to participate against their wishes. Past published
results stay up as historical records.
