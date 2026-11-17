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

This benchmark is an open, honest, and independent scientific evaluation suite
conducted entirely in good faith. It carries zero malice, bias, or intent of
commercial disparagement toward any evaluated company, developer, or product.

All evaluations, published scorecards, and comparative analyses are conducted
strictly within the bounds of protected fair-use commentary, non-commercial
scientific research, and comparative critique under:
- **Nominative Fair Use** (15 U.S.C. Section 1125(c)(3)): Third-party product
  names, service marks, and trademarks are used exclusively to accurately
  identify the software being tested.
- **Fair Use Commentary and Analysis** (17 U.S.C. Section 107): The test
  suite provides open, reproducible critique and educational measurement of
  publicly available software tools.

Anyone can independently inspect, audit, and execute the test harness locally
to verify all published findings.

## Disclaimer of liability and reputational harm

This benchmark, its evaluation scripts, sample data, and published scores are
provided strictly on an "as is" and "as available" basis, without warranties of
any kind, express or implied.

Under no circumstances shall the benchmark maintainers, independent researchers,
or contributors be held legally liable or responsible for:
- Any direct, indirect, incidental, consequential, special, or punitive damages;
- Any alleged harm to reputation, brand equity, commercial standing, goodwill,
  revenue, profits, or business operations;
- Any purchasing, deployment, or software adoption decisions made by third parties
  based on benchmark data or published scorecards.

Benchmark results reflect objective, reproducible measurements under a defined,
publicly disclosed testing protocol. They represent opinion and comparative
analysis derived from deterministic evaluation code, not statements of absolute
fact regarding an engine's general fitness for every purpose.

## Provider opt-out procedure

The maintainers respect the autonomy of software creators. Any commercial
vendor, developer, or provider that does not want their tool or product
included in future benchmark runs may request exclusion at any time:

- Submit an exclusion request using the
  [Provider opt-out issue template](../.github/ISSUE_TEMPLATE/benchmark-opt-out.yml)
  or contact the maintainers via the public repository channels.
- Upon receiving a verified request, the named product will be excluded from all
  subsequent evaluation cycles and future published scorecards.

While the maintainers respectfully encourage providers to remain part of the
benchmark—in the collaborative spirit of open scientific inquiry, transparency,
and communal progress in natural language processing—participation in future
runs is never forced against an explicit opt-out request. Past published
results remain available as immutable, point-in-time historical records.
