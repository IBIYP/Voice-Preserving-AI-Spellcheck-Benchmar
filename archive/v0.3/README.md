# Archived v0.3 Results

This directory preserves the public v0.3 score artifacts and original raw
web-checker captures. The active benchmark release is v0.4; v0.3 scoring code,
annotations, and scorecards are not used by the current evaluators.

The v0.3 H-suite scores use a four-pillar hybrid meta-score (35% spelling,
25% grammar, 20% voice, and 20% exploratory engine-specific signature
diagnostic). That diagnostic is not a general hallucination rate. The v0.4
H-suite uses a different three-pillar quality composite and a separate
correction-site diagnostic. These metrics are not comparable.

| File | Contents |
| :--- | :--- |
| `blind_4pillars_eval_run.json` | v0.3 H-suite result artifact and legacy score summary |
| `blind_v3_official_scoreboard.json` | v0.3 Blind-suite scorecard |
| `blind_v3_sapling_outputs.json` | Sapling Blind-suite web-demo output records |
| `jspell_web_checker_outputs.json` | Original combined JSpell H-suite and Blind-suite capture |

Superseded v0.3 evaluator code, its tests, historical progress charts, and
submission instructions are retained under `legacy/` for reference only. They
are not used by the current benchmark. The internal character scanner is kept
only in the ignored local `Docs/archive/` directory and is not part of this
public archive.

The v0.4 Blind evaluator reuses the archived Sapling and JSpell Blind-suite
output text as raw inputs, but scores those outputs under v0.4 annotations and
rules. The v0.4 H-suite JSpell outputs are split into
`raw_results/jspell_web_checker_outputs.json`; their text records are unchanged
from the original combined capture archived here.

Both available H-suite artifacts are dated November 14, 2026. No verified
pre-November 2026 measured H-suite snapshots are available. Earlier illustrative
trend estimates were removed and are not represented as measured results.
