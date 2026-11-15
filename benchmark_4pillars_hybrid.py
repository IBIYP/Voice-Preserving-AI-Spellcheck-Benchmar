#!/usr/bin/env python3
"""
Open Spelling & Grammar Benchmark: v4.0 Quality and Diagnostic Evaluation
==========================================================================
Bad Character Scanner Codebase Inc. (BCSC) - Open Benchmark Working Group

A transparent empirical evaluation framework for spelling and grammar engines:
1. Spelling Accuracy (Orthography, severe dysgraphia, phonetic slips)
2. Grammar & Syntactic Accuracy (Agreement, tense harmony, punctuation)
3. Maintaining Writer's Voice (Dialect tolerance, slang, anti-over-editing)
4. Correction-Site Edit Diagnostic (standalone lexical diagnostic)
5. Quality Composite (weighted synthesis across the first three pillars)

Canadian spelling conventions (colour, honour, behaviour, analyse, catalogue)
are maintained throughout codebase comments.
"""

import hashlib
import math
import os
import sys
import json
import time

from text_matching import (
    VOICE_SCORING_REVISION,
    aggregate_writer_voice,
    contains_phrase,
    score_writer_voice,
)
from correction_site_diagnostic import score_correction_sites, score_target_accuracy

# Definition of the 10 blind unseen domain evaluation units
# Each unit has decoupled targets:
# - spelling_targets: pure orthographic slips
# - grammar_targets: syntax and grammatical agreements
# - voice_tokens: stylistic markers, slang, and authorial expressions
# - dialect_equivalents: acceptable regional/vernacular variants (multi-reference)
# - forbidden_rewrites: corporate/robotic paraphrases (over-editing)
# - hallucination_signatures: v3 legacy annotations; unused by v4 scoring

UNSEEN_BENCHMARK_UNITS = [
    {
        "id": "H-01",
        "domain": "Urban Slang & Modern Banter",
        "input": "Yo that concert was straight fire no cap, but my freind lost his tickit at the entrence. We had to finagle our way past securty but it was to lit to miss.",
        "spelling_targets": {
            "freind": "friend",
            "tickit": "ticket",
            "entrence": "entrance",
            "securty": "security"
        },
        "grammar_targets": {
            "to lit": "too lit"
        },
        "voice_tokens": [
            "yo",
            "no cap",
            "finagle our way",
            "straight fire",
        ],
        "dialect_equivalents": {},
        "forbidden_rewrites": [
            "genuinely incredible",
            "negotiate our way past the security team",
            "far too exciting"
        ],
        "hallucination_signatures": {
            "BCorrect (FMM)": ["strait fire"],
            "LanguageTool API": [],
            "TextGears API": [],
            "DeepL Write": ["misplaced his ticket", "negotiate our way past the security team", "far too exciting"],
            "Sapling Grammar Checker": ["so that concert", "on cap"],
            "JSpell Free Web Checker": ["You that concert", "lost his tick"]
        }
    },
    {
        "id": "H-02",
        "domain": "Southern Gothic & Regional Cadence",
        "input": "Granddaddy sat on the porch rockin slow, watchin the crik rise after the floodin. He reckned the old barn wouldnt survive another downpoar.",
        "spelling_targets": {
            "floodin": "flooding",
            "reckned": "reckoned",
            "downpoar": "downpour"
        },
        "grammar_targets": {
            "wouldnt": "wouldn't"
        },
        "voice_tokens": [
            "rockin slow",
            "watchin the crik",
            "granddaddy",
            "old barn"
        ],
        "dialect_equivalents": {
            "rockin": ["rockin", "rocking"],
            "watchin": ["watchin", "watching"],
            "crik": ["crik", "creek", "crick"]
        },
        "forbidden_rewrites": [
            "grandfather was seated",
            "veranda",
            "observing the stream",
            "calculated that",
            "heavy rainstorm"
        ],
        "hallucination_signatures": {
            "BCorrect (FMM)": ["watch in the cri"],
            "LanguageTool API": ["watching the erik rise"],
            "TextGears API": [],
            "DeepL Write": ["heavy rainstorm", "my grandfather", "rocking slowly"],
            "Sapling Grammar Checker": [],
            "JSpell Free Web Checker": []
        }
    },
    {
        "id": "H-03",
        "domain": "Gritty Cyberpunk Tech-Noir",
        "input": "Neon reflected off the wet ashpalt. She jackd into the subnet, bypassed the firewal, and dumpd the encrypted payload before the ICE could trace her signel.",
        "spelling_targets": {
            "ashpalt": "asphalt",
            "firewal": "firewall",
            "signel": "signal"
        },
        "grammar_targets": {
            "jackd": "jacked",
            "dumpd": "dumped"
        },
        "voice_tokens": [
            "neon",
            "subnet",
            "ice",
            "encrypted payload"
        ],
        "dialect_equivalents": {},
        "forbidden_rewrites": [
            "connected to the network",
            "circumvented the security protocols",
            "extracted the confidential data",
            "counter-intrusion software"
        ],
        "hallucination_signatures": {
            "BCorrect (FMM)": [],
            "LanguageTool API": ["trace her signed", "she jack into"],
            "TextGears API": [],
            "DeepL Write": ["counter-intrusion software", "accessed the local network", "extracted the encrypted data"],
            "Sapling Grammar Checker": [],
            "JSpell Free Web Checker": ["dump the encrypted payload", "trace her signed"]
        }
    },
    {
        "id": "H-04",
        "domain": "Culinary & Sensory Critique",
        "input": "The roasted duck had increadible crispy skin, but the rasberry reduction was way to acidic. It totally overpowred the delicat flavor of the parsnips.",
        "spelling_targets": {
            "increadible": "incredible",
            "rasberry": "raspberry",
            "overpowred": "overpowered",
            "delicat": "delicate"
        },
        "grammar_targets": {
            "way to": "way too"
        },
        "voice_tokens": [
            "roasted duck",
            "crispy skin",
            "reduction",
            "parsnips",
            "totally"
        ],
        "dialect_equivalents": {
            "flavor": ["flavor", "flavour"]
        },
        "forbidden_rewrites": [
            "poultry exhibited commendable crispness",
            "excessively tart",
            "diminished the subtle qualities",
            "delicate taste"
        ],
        "hallucination_signatures": {
            "BCorrect (FMM)": [],
            "LanguageTool API": [],
            "TextGears API": [],
            "DeepL Write": ["featured wonderfully crispy skin", "proved excessively acidic", "completely masked"],
            "Sapling Grammar Checker": [],
            "JSpell Free Web Checker": []
        }
    },
    {
        "id": "H-05",
        "domain": "High-Entropy Severe Dysgraphia",
        "input": "Lass nite I dreemt of a spacship flying throu the stars with a giant roket boostr. We landd on a purpul planet with buble lakes and alien critturs that dancd joyfully. It felt so reel I cried wen my mom woak me up for skool!",
        "spelling_targets": {
            "lass nite": "last night",
            "dreemt": "dreamt",
            "spacship": "spaceship",
            "throu": "through",
            "roket": "rocket",
            "boostr": "booster",
            "purpul": "purple",
            "buble": "bubble",
            "critturs": "critters",
            "reel": "real",
            "wen": "when",
            "skool": "school"
        },
        "grammar_targets": {
            "landd": "landed",
            "dancd": "danced",
            "woak": "woke"
        },
        "voice_tokens": [
            "spaceship",
            "purple planet",
            "bubble lakes",
            "alien",
            "joyfully"
        ],
        "dialect_equivalents": {
            "dreamt": ["dreamt", "dreamed"]
        },
        "forbidden_rewrites": [
            "celestial spacecraft",
            "traveling across the cosmos",
            "violet world",
            "wept profusely"
        ],
        "hallucination_signatures": {
            "BCorrect (FMM)": ["mom work me up"],
            "LanguageTool API": ["flying thou the stars", "pursue planet", "up for stool"],
            "TextGears API": ["pupil planet", "bauble lakes", "up for skoal"],
            "DeepL Write": ["celestial spacecraft", "traveling across the cosmos", "violet world", "sparkling lakes"],
            "Sapling Grammar Checker": [],
            "JSpell Free Web Checker": [
                "niter", "rocket boosts", "purl planet", "cried ween",
                "mom wok", "for solo"
            ]
        }
    },
    {
        "id": "H-06",
        "domain": "Punchy SaaS Executive Pitch",
        "input": "Our cac dropped 40% mom, while arr hit a record high. The competishun is scramblin to match our feachures, but we move to fast.",
        "spelling_targets": {
            "competishun": "competition",
            "scramblin": "scrambling",
            "feachures": "features"
        },
        "grammar_targets": {
            "cac": "cac",
            "mom": "mom",
            "arr": "arr",
            "to fast": "too fast"
        },
        "voice_tokens": [
            "record high",
            "scrambling",
            "dropped 40% mom"
        ],
        "dialect_equivalents": {
            "cac": ["cac", "CAC"],
            "mom": ["mom", "MoM", "MOM"],
            "arr": ["arr", "ARR"]
        },
        "forbidden_rewrites": [
            "customer acquisition costs",
            "month-over-month",
            "annualized recurring revenue",
            "unmatched pace"
        ],
        "hallucination_signatures": {
            "BCorrect (FMM)": [],
            "LanguageTool API": [],
            "TextGears API": ["our vac dropped"],
            "DeepL Write": ["customer acquisition costs", "annualized recurring revenue", "unmatched pace"],
            "Sapling Grammar Checker": [],
            "JSpell Free Web Checker": ["Our ca dropped", "while AR hit", "our Peachtree"]
        }
    },
    {
        "id": "H-07",
        "domain": "Sports Locker-Room Kinetic Action",
        "input": "Coach drew up the play on the whitebord during the timout. We ran the pick and rool to perfecshun, nailed the threepointer at the buzer, and won the champinship!",
        "spelling_targets": {
            "whitebord": "whiteboard",
            "timout": "timeout",
            "rool": "roll",
            "perfecshun": "perfection",
            "buzer": "buzzer",
            "champinship": "championship"
        },
        "grammar_targets": {
            "threepointer": "three-pointer"
        },
        "voice_tokens": [
            "coach",
            "play",
            "pick and roll",
            "championship"
        ],
        "dialect_equivalents": {
            "three-pointer": ["three-pointer", "three pointer"]
        },
        "forbidden_rewrites": [
            "tactical sequence",
            "offensive maneuver",
            "decisive perimeter shot",
            "clinched the championship title"
        ],
        "hallucination_signatures": {
            "BCorrect (FMM)": ["at the buyer"],
            "LanguageTool API": ["pick and room", "at the buyer"],
            "TextGears API": ["pick and roil"],
            "DeepL Write": ["tactical sequence", "pick-and-roll maneuver impeccably", "decisive perimeter shot", "clinched the championship title"],
            "Sapling Grammar Checker": [],
            "JSpell Free Web Checker": ["to preference", "the thirteenth at"]
        }
    },
    {
        "id": "H-08",
        "domain": "Introspective Poetic Stream-of-Thought",
        "input": "Autumn leavs spiraled across the abandond trax. A quiet saddness hung in the air, neither bitter nor cruel, just the slow exhail of another dying year.",
        "spelling_targets": {
            "leavs": "leaves",
            "abandond": "abandoned",
            "trax": "tracks",
            "saddness": "sadness",
            "exhail": "exhale"
        },
        "grammar_targets": {},
        "voice_tokens": [
            "autumn leaves",
            "spiraled",
            "quiet sadness hung in the air",
            "neither bitter nor cruel",
            "dying year"
        ],
        "dialect_equivalents": {},
        "forbidden_rewrites": [
            "golden autumn foliage",
            "neglected rails",
            "subdued sorrow lingered",
            "closing season"
        ],
        "hallucination_signatures": {
            "BCorrect (FMM)": ["slow exiled of another dying year"],
            "LanguageTool API": ["autumn leave spiraled", "abandoned tax"],
            "TextGears API": ["abandoned Trax"],
            "DeepL Write": ["golden autumn foliage", "neglected rails", "subdued sorrow", "closing season"],
            "Sapling Grammar Checker": ["abandoned train tracks"],
            "JSpell Free Web Checker": ["across the abandon Tara"]
        }
    },
    {
        "id": "H-09",
        "domain": "Field Biology & Explorer Notes",
        "input": "Observd three speshimens of dendrobates tinctorius near the stream bed. The aposematik coloration was extreamly vibrant despite heavy canoppy shade.",
        "spelling_targets": {
            "speshimens": "specimens",
            "aposematik": "aposematic",
            "extreamly": "extremely",
            "canoppy": "canopy"
        },
        "grammar_targets": {
            "observd": "observed"
        },
        "voice_tokens": [
            "three specimens",
            "stream bed",
            "coloration",
            "heavy canopy shade"
        ],
        "dialect_equivalents": {
            "dendrobates tinctorius": ["dendrobates tinctorius", "dendrobates tinctorious"]
        },
        "forbidden_rewrites": [
            "researchers identified",
            "instances of the poison frog",
            "watercourse",
            "warning pigmentation"
        ],
        "hallucination_signatures": {
            "BCorrect (FMM)": [],
            "LanguageTool API": ["dendrites tinctorial"],
            "TextGears API": ["dendrites tinctures", "postmark coloration"],
            "DeepL Write": ["researchers identified", "instances of the poison frog", "watercourse", "dense overhead foliage"],
            "Sapling Grammar Checker": ["tintorius"],
            "JSpell Free Web Checker": [
                "Observe three", "tenderfoots", "tinctures", "Postmates coloration"
            ]
        }
    },
    {
        "id": "H-10",
        "domain": "Legal & Contractual Shorthand",
        "input": "Clause 4.2 govorns indemity obligashuns. Neither party shall be liabel for consequenshal damages arising from unintensional breach.",
        "spelling_targets": {
            "indemity": "indemnity",
            "obligashuns": "obligations",
            "liabel": "liable",
            "consequenshal": "consequential",
            "unintensional": "unintentional"
        },
        "grammar_targets": {
            "govorns": "governs"
        },
        "voice_tokens": [
            "clause 4.2",
            "neither party shall be",
            "consequential damages",
            "breach"
        ],
        "dialect_equivalents": {},
        "forbidden_rewrites": [
            "section 4.2 establishes",
            "under no circumstance will either signatory",
            "assume financial responsibility",
            "non-willful contractual default"
        ],
        "hallucination_signatures": {
            "BCorrect (FMM)": [],
            "LanguageTool API": ["neither party shall be label"],
            "TextGears API": ["neither party shall be label"],
            "DeepL Write": ["section 4.2 establishes", "under no circumstance", "assume financial responsibility"],
            "Sapling Grammar Checker": [],
            "JSpell Free Web Checker": []
        }
    }
]

ENGINES = [
    "BCorrect (FMM)",
    "LanguageTool API",
    "TextGears API",
    "DeepL Write",
    "Sapling Grammar Checker",
    "JSpell Free Web Checker",
    "Grammarly Free Grammar Checker",
]

COLLECTION_MODES = {
    "BCorrect (FMM)": "api",
    "LanguageTool API": "api",
    "TextGears API": "api",
    "DeepL Write": "not reported",
    "Sapling Grammar Checker": "web_demo",
    "JSpell Free Web Checker": "web_demo",
    "Grammarly Free Grammar Checker": "web_demo",
}

COLLECTION_LOCALES = {
    "BCorrect (FMM)": "not reported",
    "LanguageTool API": "en-US",
    "TextGears API": "en-US",
    "DeepL Write": "not reported",
    "Sapling Grammar Checker": "not reported",
    "JSpell Free Web Checker": "English (US)",
    "Grammarly Free Grammar Checker": "not reported",
}

TARGET_SCORING_REVISION = "aligned-correction-sites-v1"
GRAMMARLY_RESULTS_PATH = os.path.join(
    "raw_results", "grammarly_web_checker_outputs.json"
)


def _load_grammarly_runs(path=GRAMMARLY_RESULTS_PATH):
    with open(path, "r", encoding="utf-8") as file:
        results = json.load(file)
    if not isinstance(results, dict):
        raise ValueError("Grammarly web-checker results must be an object")

    metadata = results.get("metadata")
    if not isinstance(metadata, dict) or metadata.get("collection_mode") != "web_demo":
        raise ValueError("Grammarly results must identify web_demo collection mode")
    if metadata.get("status") != "complete for H-suite; no Blind-suite outputs collected":
        raise ValueError("Grammarly results must be marked complete for the H-suite")

    passages = results.get("four_pillar")
    if not isinstance(passages, dict):
        raise ValueError("Grammarly web-checker results are missing four_pillar outputs")
    expected_ids = {unit["id"] for unit in UNSEEN_BENCHMARK_UNITS}
    if set(passages) != expected_ids:
        missing = sorted(expected_ids - set(passages))
        unexpected = sorted(set(passages) - expected_ids)
        raise ValueError(
            f"Grammarly H-suite passage coverage mismatch; missing={missing}, "
            f"unexpected={unexpected}"
        )

    runs = {}
    for passage_id, result in passages.items():
        if not isinstance(result, dict) or not isinstance(result.get("text"), str) or not result["text"].strip():
            raise ValueError(f"Grammarly result is missing valid text for {passage_id}")
        if result.get("lat") is not None:
            raise ValueError(
                f"Grammarly latency must remain null for {passage_id}; "
                "web-demo latency was not measured"
            )
        runs[passage_id] = {"text": result["text"], "lat": None}
    return runs, metadata


def _stable_digest(value):
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _validate_cached_runs(raw_runs):
    if not isinstance(raw_runs, dict):
        raise ValueError("H-suite raw results must be an object keyed by passage ID")
    expected_ids = {unit["id"] for unit in UNSEEN_BENCHMARK_UNITS}
    if set(raw_runs) != expected_ids:
        missing = sorted(expected_ids - set(raw_runs))
        unexpected = sorted(set(raw_runs) - expected_ids)
        raise ValueError(
            f"H-suite passage coverage mismatch; missing={missing}, "
            f"unexpected={unexpected}"
        )
    for unit in UNSEEN_BENCHMARK_UNITS:
        passage_id = unit["id"]
        passage_runs = raw_runs.get(passage_id)
        if not isinstance(passage_runs, dict):
            raise ValueError(f"H-suite results are missing passage {passage_id}")
        for engine in ENGINES:
            engine_run = passage_runs.get(engine)
            if not isinstance(engine_run, dict) or not isinstance(
                engine_run.get("text"), str
            ):
                raise ValueError(
                    f"H-suite result is missing text for {engine} on {passage_id}"
                )


def _mean_recorded_latency(raw_runs, engine):
    latencies = []
    for unit in UNSEEN_BENCHMARK_UNITS:
        value = raw_runs[unit["id"]][engine].get("lat")
        if value is None:
            continue
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value < 0
        ):
            raise ValueError(f"Invalid latency for {engine} on {unit['id']}: {value}")
        latencies.append(value)
    average = round(sum(latencies) / len(latencies), 1) if latencies else None
    return average, len(latencies)


def evaluate_unit(
    unit, output_text, locale=None, locale_spelling_targets=None
):
    """
    Evaluates an engine's output across the v4 benchmark metrics.

    Locale-specific spelling targets are optional so the v4.0 baseline remains
    unchanged; paired runs pass the target forms for the selected locale.
    """
    spelling_signatures = {}
    for source, target in unit["spelling_targets"].items():
        accepted = [target] if isinstance(target, str) else list(target)
        equivalents = unit.get("dialect_equivalents", {}).get(target, [])
        if isinstance(equivalents, str):
            equivalents = [equivalents]
        spelling_signatures[source] = list(dict.fromkeys(accepted + equivalents))

    if locale is not None:
        if locale not in ("en-US", "en-GB"):
            raise ValueError(f"Unsupported H-suite locale: {locale}")
        if not isinstance(locale_spelling_targets, dict):
            raise ValueError(
                f"Locale-specific spelling targets are required for {locale}"
            )
        for source, accepted in locale_spelling_targets.items():
            if not isinstance(source, str) or not isinstance(accepted, str):
                raise ValueError("Locale-specific spelling targets must map strings to strings")
            spelling_signatures[source] = [accepted]

    grammar_signatures = {}
    for source, target in unit["grammar_targets"].items():
        accepted = [target] if isinstance(target, str) else list(target)
        equivalents = unit.get("dialect_equivalents", {}).get(target, [])
        if isinstance(equivalents, str):
            equivalents = [equivalents]
        grammar_signatures[source] = list(dict.fromkeys(accepted + equivalents))

    # Pillar 1: Spelling Accuracy
    spelling_targets = score_target_accuracy(
        unit["input"],
        output_text,
        spelling_signatures,
        include_identity_only=locale is not None,
    )
    spelling_acc = spelling_targets["accuracy"]

    # Pillar 2: Grammar & Syntactic Accuracy
    grammar_targets = score_target_accuracy(
        unit["input"], output_text, grammar_signatures
    )
    grammar_acc = grammar_targets["accuracy"]

    # Pillar 3: Maintaining Writer's Voice
    voice_tokens = unit["voice_tokens"]
    voice_total = len(voice_tokens)
    voice_hits = 0
    for vt in voice_tokens:
        eq_list = unit.get("dialect_equivalents", {}).get(vt, [vt])
        if isinstance(eq_list, str):
            eq_list = [eq_list]
        if any(contains_phrase(output_text, eq) for eq in eq_list):
            voice_hits += 1
    vpr = (voice_hits / max(voice_total, 1)) * 100.0

    # Over-editing penalty
    forbidden = unit["forbidden_rewrites"]
    voice_metrics = score_writer_voice(
        unit["input"],
        output_text,
        unit["spelling_targets"],
        unit["grammar_targets"],
        voice_tokens,
        unit.get("dialect_equivalents", {}),
        forbidden,
    )
    voice_preservation_score = voice_metrics["score"]
    oer = min(100.0, voice_metrics["over_edit_count"] * 10.0)

    correction_diagnostic = score_correction_sites(
        unit["input"],
        output_text,
        [spelling_signatures, grammar_signatures],
        include_identity_only=locale is not None,
    )

    # The v4 diagnostic is reported separately until its interpretation is
    # validated; it does not contribute to the legacy composite.
    quality_composite = (
        (0.4375 * spelling_acc)
        + (0.3125 * grammar_acc)
        + (0.25 * voice_preservation_score)
    )

    return {
        "spelling_acc": round(spelling_acc, 2),
        "spelling_target_hits": spelling_targets["accepted_targets"],
        "spelling_target_count": spelling_targets["total_targets"],
        "grammar_acc": round(grammar_acc, 2),
        "grammar_target_hits": grammar_targets["accepted_targets"],
        "grammar_target_count": grammar_targets["total_targets"],
        "voice_preservation": round(voice_preservation_score, 2),
        "vpr": round(vpr, 2),
        "voice_precision": voice_metrics["precision"],
        "voice_recall": voice_metrics["recall"],
        "voice_lexical_f1": voice_metrics["lexical_f1"],
        "voice_marker_retention": voice_metrics["voice_marker_retention"],
        "voice_over_edit_count": voice_metrics["over_edit_count"],
        "oer": round(oer, 2),
        "correction_site_diagnostic": correction_diagnostic,
        "quality_composite": round(quality_composite, 2)
    }


def run_comprehensive_benchmark():
    """
    Executes the 4-pillar benchmark evaluation across all engines and passages.
    """
    raw_results_path = os.path.join("raw_results", "unseen_10_domains_live_run.json")
    if not os.path.exists(raw_results_path):
        raise FileNotFoundError(f"Missing raw results at {raw_results_path}")

    with open(raw_results_path, "r", encoding="utf-8") as f:
        raw_runs = json.load(f)
    if not isinstance(raw_runs, dict):
        raise ValueError("H-suite raw results must be an object keyed by passage ID")

    jspell_path = os.path.join("raw_results", "jspell_web_checker_outputs.json")
    if not os.path.exists(jspell_path):
        raise FileNotFoundError(f"Missing JSpell web-checker results at {jspell_path}")
    with open(jspell_path, "r", encoding="utf-8") as f:
        jspell_runs = json.load(f).get("four_pillar")
    if not isinstance(jspell_runs, dict):
        raise ValueError("JSpell web-checker results are missing four_pillar outputs")
    for unit in UNSEEN_BENCHMARK_UNITS:
        passage_id = unit["id"]
        result = jspell_runs.get(passage_id)
        if not isinstance(result, dict) or not isinstance(result.get("text"), str):
            raise ValueError(f"JSpell web-checker result is missing {passage_id}")
        raw_runs.setdefault(passage_id, {})["JSpell Free Web Checker"] = {
            "text": result["text"],
            "lat": None
        }
    grammarly_runs, grammarly_metadata = _load_grammarly_runs()
    for passage_id, result in grammarly_runs.items():
        raw_runs.setdefault(passage_id, {})["Grammarly Free Grammar Checker"] = result
    _validate_cached_runs(raw_runs)

    results = {
        eng: {
            "spelling_target_hits": 0,
            "spelling_target_count": 0,
            "grammar_target_hits": 0,
            "grammar_target_count": 0,
            "voice_metrics": [],
            "correction_site_diagnostic": [],
        }
        for eng in ENGINES
    }
    per_passage_breakdown = []

    for unit in UNSEEN_BENCHMARK_UNITS:
        uid = unit["id"]
        unit_runs = raw_runs[uid]
        passage_entry = {"id": uid, "domain": unit["domain"], "scores": {}}

        for eng in ENGINES:
            eng_data = unit_runs[eng]
            out_text = eng_data["text"]
            eval_res = evaluate_unit(unit, out_text)

            results[eng]["spelling_target_hits"] += eval_res["spelling_target_hits"]
            results[eng]["spelling_target_count"] += eval_res["spelling_target_count"]
            results[eng]["grammar_target_hits"] += eval_res["grammar_target_hits"]
            results[eng]["grammar_target_count"] += eval_res["grammar_target_count"]
            results[eng]["voice_metrics"].append({
                "score": eval_res["voice_preservation"],
                "lexical_f1": eval_res["voice_lexical_f1"],
                "voice_marker_retention": eval_res["voice_marker_retention"],
                "over_edit_count": eval_res["voice_over_edit_count"],
            })
            results[eng]["correction_site_diagnostic"].append(
                eval_res["correction_site_diagnostic"]
            )
            passage_entry["scores"][eng] = {
                "text": out_text,
                "metrics": eval_res
            }

        per_passage_breakdown.append(passage_entry)

    summary = {}
    for eng in ENGINES:
        voice_summary = aggregate_writer_voice(results[eng]["voice_metrics"])
        spelling_target_count = results[eng]["spelling_target_count"]
        grammar_target_count = results[eng]["grammar_target_count"]
        spelling_accuracy = (
            round(results[eng]["spelling_target_hits"] / spelling_target_count * 100, 1)
            if spelling_target_count
            else 100.0
        )
        grammar_accuracy = (
            round(results[eng]["grammar_target_hits"] / grammar_target_count * 100, 1)
            if grammar_target_count
            else 100.0
        )
        diagnostic_sites = [
            site
            for passage in results[eng]["correction_site_diagnostic"]
            for site in passage["sites"]
        ]
        diagnostic_applicable = len(diagnostic_sites)
        diagnostic_unapproved = sum(
            site["classification"] == "unapproved_edit" for site in diagnostic_sites
        )
        diagnostic_unchanged = sum(
            site["classification"] == "unchanged" for site in diagnostic_sites
        )
        diagnostic_approved = sum(
            site["classification"] == "accepted_correction" for site in diagnostic_sites
        )
        diagnostic_rate = (
            round(diagnostic_unapproved / diagnostic_applicable * 100.0, 1)
            if diagnostic_applicable
            else None
        )
        quality_composite = round(
            (0.4375 * spelling_accuracy)
            + (0.3125 * grammar_accuracy)
            + (0.25 * voice_summary["score"]),
            1,
        )
        latency_ms, latency_samples = _mean_recorded_latency(raw_runs, eng)
        summary[eng] = {
            "spelling_accuracy": spelling_accuracy,
            "spelling_accepted_targets": results[eng]["spelling_target_hits"],
            "spelling_total_targets": spelling_target_count,
            "grammar_accuracy": grammar_accuracy,
            "grammar_accepted_targets": results[eng]["grammar_target_hits"],
            "grammar_total_targets": grammar_target_count,
            "voice_preservation": voice_summary["score"],
            "voice_lexical_f1": voice_summary["lexical_f1"],
            "voice_marker_retention": voice_summary["voice_marker_retention"],
            "voice_over_edit_count": voice_summary["over_edit_count"],
            "voice_over_edit_penalty": voice_summary["over_edit_penalty"],
            "correction_site_diagnostic": {
                "applicable_sites": diagnostic_applicable,
                "unchanged_sites": diagnostic_unchanged,
                "accepted_corrections": diagnostic_approved,
                "unapproved_edits": diagnostic_unapproved,
                "unapproved_edit_rate": diagnostic_rate,
            },
            "quality_composite": quality_composite,
            "latency_ms": latency_ms,
            "latency_samples": latency_samples,
        }

    for engine, engine_summary in summary.items():
        penalty_factor = 1.0 - engine_summary["voice_over_edit_penalty"] / 100.0
        for passage in per_passage_breakdown:
            metrics = passage["scores"][engine]["metrics"]
            metrics["voice_base_score"] = metrics["voice_preservation"]
            metrics["voice_over_edit_penalty"] = engine_summary["voice_over_edit_penalty"]
            metrics["voice_preservation"] = round(
                metrics["voice_base_score"] * penalty_factor, 2
            )
            metrics["quality_composite"] = round(
                (0.4375 * metrics["spelling_acc"])
                + (0.3125 * metrics["grammar_acc"])
                + (0.25 * metrics["voice_preservation"]),
                2,
            )

    # Save v4 output separately; the v3 artifact remains the historical record.
    dataset_digest = _stable_digest(
        [
            {
                key: unit[key]
                for key in (
                    "id",
                    "input",
                    "spelling_targets",
                    "grammar_targets",
                    "dialect_equivalents",
                )
                if key in unit
            }
            for unit in UNSEEN_BENCHMARK_UNITS
        ]
    )
    outputs_digest = _stable_digest(raw_runs)
    output_artifact = {
        "benchmark_metadata": {
            "title": "Open Spelling & Grammar Benchmark: v4.0",
            "version": "4.0",
            "voice_scoring_revision": VOICE_SCORING_REVISION,
            "target_scoring_revision": TARGET_SCORING_REVISION,
            "eval_date": "November 14, 2026",
            "locale_scope": (
                "Single-locale baseline; locale settings vary or are unreported. "
                "Paired en-US/en-GB results have not been collected."
            ),
            "run_id": f"h-suite-v4-{outputs_digest[:16]}",
            "dataset_sha256": dataset_digest,
            "cached_outputs_sha256": outputs_digest,
            "target_scoring_methodology_note": (
                "Accepted forms are matched at aligned annotated source sites. "
                "An unchanged source counts only when explicitly accepted; "
                "identity-only annotations are excluded. Target hits are pooled."
            ),
            "engine_run_metadata": {
                engine: {
                    "version": "not reported",
                    "source_run_id": "not recorded",
                    "collection_mode": COLLECTION_MODES[engine],
                    "locale": COLLECTION_LOCALES[engine],
                    **(
                        {
                            "source_url": grammarly_metadata.get("source_url"),
                            "collection_date": grammarly_metadata.get("collection_date"),
                            "selection_policy": grammarly_metadata.get("selection_policy"),
                        }
                        if engine == "Grammarly Free Grammar Checker"
                        else {}
                    ),
                }
                for engine in ENGINES
            },
            "latency_methodology": (
                "Arithmetic mean of non-null per-passage latencies recorded in "
                "the cached output log; null when no timing was recorded."
            ),
            "architecture": "3 weighted quality pillars + standalone correction-site diagnostic",
            "diagnostic_revision": "unapproved-correction-site-v1",
            "correction_site_diagnostic_note": (
                "Counts output edits at annotated spelling/grammar target sites "
                "that are not unchanged or one of the shared accepted forms. "
                "This deterministic lexical diagnostic is not a general "
                "hallucination or semantic-correctness rate."
            ),
            "weights": {
                "pillar_1_spelling": "43.75%",
                "pillar_2_grammar": "31.25%",
                "pillar_3_voice": "25%",
                "correction_site_diagnostic": "reported separately"
            }
        },
        "engine_summary": summary,
        "passages": per_passage_breakdown
    }

    out_json_path = os.path.join("raw_results", "blind_4pillars_eval_run_v4.json")
    with open(out_json_path, "w", encoding="utf-8") as f:
        json.dump(output_artifact, f, indent=2)
    print(f"Saved H-suite v4 evaluation results to {out_json_path}")

    return summary


def print_scorecard(summary):
    """
    Renders the v4 quality metrics and standalone diagnostic.
    """
    print("\n" + "=" * 124)
    print("OPEN SPELLING & GRAMMAR BENCHMARK v4.0: QUALITY + CORRECTION-SITE DIAGNOSTIC")
    print("=" * 124)
    print(f"{'Engine':<34} | {'P1: Spell':<10} | {'P2: Gram':<10} | {'P3: Voice':<10} | {'Unapproved edits':<18} | {'Quality':<10} | {'Latency':<8}")
    print("-" * 124)
    for eng in sorted(summary.keys(), key=lambda x: summary[x]["quality_composite"], reverse=True):
        s = summary[eng]
        lat_str = f"~{s['latency_ms']} ms" if s["latency_ms"] is not None else "n/a"
        diagnostic = s["correction_site_diagnostic"]
        rate = (
            f"{diagnostic['unapproved_edits']}/{diagnostic['applicable_sites']} "
            f"({diagnostic['unapproved_edit_rate']:.1f}%)"
            if diagnostic["unapproved_edit_rate"] is not None
            else "n/a"
        )
        print(f"{eng:<34} | {s['spelling_accuracy']:>8.1f}% | {s['grammar_accuracy']:>8.1f}% | {s['voice_preservation']:>8.1f}% | {rate:>18} | {s['quality_composite']:>8.1f}% | {lat_str:>8}")
    print("=" * 124)
    print("Quality composite weights: 43.75% Spelling, 31.25% Grammar, 25% Voice Preservation")
    print("Crowns:")
    print("  * Best Spelling & Dysgraphia:   " + max(summary.items(), key=lambda x: x[1]["spelling_accuracy"])[0])
    print("  * Best Grammar & Syntax:       " + max(summary.items(), key=lambda x: x[1]["grammar_accuracy"])[0])
    print("  * Best Voice Preservation:     " + max(summary.items(), key=lambda x: x[1]["voice_preservation"])[0])
    print("  * Correction-site diagnostic is standalone; no winner is reported.")
    measured_latency = [
        (name, result["latency_ms"])
        for name, result in summary.items()
        if result["latency_ms"] is not None
    ]
    fastest = min(measured_latency, key=lambda x: x[1]) if measured_latency else None
    fastest_label = (
        f"{fastest[0]} (~{fastest[1]} ms, "
        f"{summary[fastest[0]]['latency_samples']} samples)"
        if fastest
        else "n/a"
    )
    print("  * Lowest recorded REST latency: " + fastest_label)
    if any(result["latency_ms"] is None for result in summary.values()):
        print("  * Web-demo latency:            not measured")
    print("  * Overall Quality Leader:     " + max(summary.items(), key=lambda x: x[1]["quality_composite"])[0])
    print("=" * 124 + "\n")


if __name__ == "__main__":
    summary = run_comprehensive_benchmark()
    if summary:
        print_scorecard(summary)
