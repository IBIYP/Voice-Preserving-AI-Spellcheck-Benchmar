"""Load the current v0.4 Blind Suite data and reference-based diagnostic."""

from collections import Counter
import json
from pathlib import Path

DATA_PATH = (
    Path(__file__).resolve().parent
    / "Docs"
    / "private"
    / "benchmark"
    / "blind_suite_v4_data.json"
)
if not DATA_PATH.is_file():
    raise FileNotFoundError(
        "Private Blind Suite data are not included in the public repository. "
        f"Place the authorized local file at {DATA_PATH} to run the Blind evaluator."
    )
with DATA_PATH.open("r", encoding="utf-8") as file:
    _suite_data = json.load(file)
if _suite_data.get("benchmark_version") != "4.0":
    raise ValueError(f"{DATA_PATH} does not contain v0.4 Blind Suite data")

ENGINES = _suite_data["engines"]
GOLD_REFERENCES = _suite_data["gold_references"]
GROUND_TRUTH = _suite_data["ground_truth"]
del _suite_data


def extract_ngrams(tokens, n):
    return [tuple(tokens[index:index + n]) for index in range(len(tokens) - n + 1)]


def calculate_sari_keep(input_text, ref_text, hyp_text, max_n=3):
    """Calculate retained input n-gram overlap with the minimal-edit reference."""
    clean_texts = [
        text.lower()
        .replace(",", " ")
        .replace(".", " ")
        .replace("!", " ")
        .replace("?", " ")
        .split()
        for text in (input_text, ref_text, hyp_text)
    ]
    clean_input, clean_reference, clean_hypothesis = clean_texts
    f_scores = []
    for n in range(1, max_n + 1):
        input_ngrams = Counter(extract_ngrams(clean_input, n))
        reference_ngrams = Counter(extract_ngrams(clean_reference, n))
        hypothesis_ngrams = Counter(extract_ngrams(clean_hypothesis, n))
        numerator = sum(
            min(
                hypothesis_ngrams[gram],
                input_ngrams.get(gram, 0),
                reference_ngrams.get(gram, 0),
            )
            for gram in hypothesis_ngrams
        )
        precision_denominator = sum(
            min(hypothesis_ngrams[gram], input_ngrams.get(gram, 0))
            for gram in hypothesis_ngrams
        )
        recall_denominator = sum(
            min(input_ngrams[gram], reference_ngrams.get(gram, 0))
            for gram in input_ngrams
        )
        precision = numerator / precision_denominator if precision_denominator else 0.0
        recall = numerator / recall_denominator if recall_denominator else 0.0
        f_scores.append(
            (2.0 * precision * recall) / (precision + recall)
            if precision + recall
            else 0.0
        )
    return sum(f_scores) / len(f_scores) * 100.0
