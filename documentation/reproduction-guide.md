# Reproduce and Check the v0.5 Draft

The evaluator uses cached outputs only; it never queries a provider. The
checked-in protocol is deliberately a draft, so a scoring attempt will be
rejected until it is reviewed and explicitly frozen. No output cache is
included or collected.

## Requirements

Python 3.9 or later. The scorer uses the standard library and the repository's
local matching modules; it does not require network access or provider
credentials.

## Validate the draft

Run the focused tests:

```bash
python -m unittest discover -s tests -p test_benchmark_v05.py -v
```

The tests cover manifest completeness, exact control classification, equal
weights, locale-specific spelling, cache completeness, input hashes, forced
locale rejection, and the requirement that control freeze precede collection.

## Score a future run

After review, freeze the protocol by updating its status and version identifier.
Collect a complete cache at `raw_results/v0.5_anchor_runs.json` using the schema
described in [`../raw_results/README.md`](../raw_results/README.md). Then run:

```bash
python benchmark_v05.py
```

The evaluator requires the cache's protocol digest to match the frozen
manifest. It also checks all 20 sample IDs, identical engine coverage, nonempty
outputs, input hashes, UTC freeze/collection timestamps, engine provenance,
and automatic or unset locale settings. It writes the score artifact only
after all checks pass.

Do not score outputs collected under another protocol, or outputs collected
before the controls were frozen, as v0.5 results.
