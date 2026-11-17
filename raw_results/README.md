# Raw Results

The v0.5 protocol is not frozen. This directory contains no v0.5 engine
outputs or scorecards, and no new provider calls have been made for it.

See the [protocol and freeze requirements](../documentation/benchmark-v0.5-draft.md)
before collecting anything. Do not copy outputs from another test method into
a v0.5 cache.

## Future cache contract

The future `v0.5_anchor_runs.json` cache must have:

- `metadata.status`: `"complete"`;
- `protocol_version` and `protocol_sha256`, matching the frozen manifest;
- `locale_mode`: `"automatic"`;
- `control_set_frozen_at_utc` and `collection_started_at_utc`, both timezone-
  aware UTC timestamps, with collection strictly after freeze;
- `engine_metadata`, keyed by engine, with `product_version`, `collection_route`,
  `source_url`, and `locale_setting` (`"auto-detect"` or `"not-set"`);
- `outputs`, keyed by all 20 sample IDs (`V05-01-en-US` through `V05-10-en-GB`),
  each with the exact input's SHA-256 and one non-empty output per engine;
- optional `latency_ms`, recorded only when actually measured (otherwise
  `null`).

Every engine in a run must have output for every sample. Missing, extra, or
changed inputs are errors; the scorer does not fill gaps or substitute another
locale. Preserve the exact submitted text and output where publication is
permitted. Record unreported version or route information explicitly rather
than estimating it.

## Privacy and external data

Do not include credentials, private customer text, or other sensitive material
in public result files. Submit only inputs and outputs that may be published.
The former spelling-pair panel has not been cleared for redistribution and is
not part of the v0.5 four-pillar score; see
[`../documentation/research-and-tooling-provenance.md`](../documentation/research-and-tooling-provenance.md).
