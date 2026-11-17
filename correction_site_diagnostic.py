"""Deterministic diagnostics for edits at annotated correction sites."""

import difflib
import re


def _tokens(text):
    return re.findall(r"[^\W_]+(?:['\u2019][^\W_]+)?", text.casefold(), flags=re.UNICODE)


def _find_occurrences(tokens, phrase):
    width = len(phrase)
    if not width:
        return []
    return [
        start
        for start in range(len(tokens) - width + 1)
        if tokens[start : start + width] == phrase
    ]


def _output_alignment(input_tokens, output_tokens):
    alignment = {}
    matcher = difflib.SequenceMatcher(
        None, input_tokens, output_tokens, autojunk=False
    )
    for tag, input_start, input_end, output_start, output_end in matcher.get_opcodes():
        if tag == "equal":
            for offset in range(input_end - input_start):
                alignment[input_start + offset] = (
                    output_start + offset,
                    output_start + offset + 1,
                )
        elif tag == "replace":
            input_width = input_end - input_start
            output_width = output_end - output_start
            for offset in range(input_width):
                mapped_start = output_start + (offset * output_width // input_width)
                mapped_end = (
                    output_start
                    + ((offset + 1) * output_width + input_width - 1) // input_width
                )
                if mapped_start == mapped_end and output_width:
                    mapped_start = min(mapped_start, output_end - 1)
                    mapped_end = mapped_start + 1
                alignment[input_start + offset] = (mapped_start, mapped_end)
        elif tag == "delete":
            for index in range(input_start, input_end):
                alignment[index] = (output_start, output_start)
    return alignment


def score_correction_sites(
    input_text, output_text, target_maps, include_identity_only=False
):
    """Count unapproved edits at shared, annotated correction sites.

    ``target_maps`` is an iterable of mappings from source phrases to one or
    more accepted output phrases. The source phrase itself is always accepted
    as an unchanged result. This diagnostic only examines annotated sites; it
    does not judge semantic correctness elsewhere in the passage.
    """
    input_tokens = _tokens(input_text)
    output_tokens = _tokens(output_text)
    sites = {}

    for target_map in target_maps:
        if not isinstance(target_map, dict):
            raise TypeError("Each target map must be a dictionary")
        for source, accepted in target_map.items():
            source_tokens = _tokens(source)
            if not source_tokens:
                raise ValueError("Correction-site source phrases cannot be empty")
            if isinstance(accepted, str):
                accepted = [accepted]
            if not isinstance(accepted, (list, tuple, set)):
                raise TypeError("Accepted correction forms must be strings or a sequence")

            accepted_forms = {tuple(source_tokens)}
            for form in accepted:
                if not isinstance(form, str):
                    raise TypeError("Accepted correction forms must be strings")
                tokens = _tokens(form)
                if tokens:
                    accepted_forms.add(tuple(tokens))
            if accepted_forms == {tuple(source_tokens)} and not include_identity_only:
                continue

            for start in _find_occurrences(input_tokens, source_tokens):
                key = (start, start + len(source_tokens))
                sites.setdefault(key, set()).update(accepted_forms)

    alignment = _output_alignment(input_tokens, output_tokens)
    aligned_sites = []
    for (start, end), accepted_forms in sorted(sites.items()):
        intervals = [alignment[index] for index in range(start, end) if index in alignment]
        if intervals:
            output_start = min(interval[0] for interval in intervals)
            output_end = max(interval[1] for interval in intervals)
            output_positions = set(range(output_start, output_end))
        else:
            output_positions = set()
        aligned_sites.append(
            (start, end, accepted_forms, output_positions)
        )

    decisions = []
    for index, (start, end, accepted_forms, output_positions) in enumerate(aligned_sites):
        overlapping_positions = set()
        for other_index, (_, _, _, other_positions) in enumerate(aligned_sites):
            if other_index != index:
                overlapping_positions.update(output_positions & other_positions)
        site_positions = sorted(output_positions - overlapping_positions)
        observed = tuple(output_tokens[position] for position in site_positions)
        if observed == tuple(input_tokens[start:end]):
            classification = "unchanged"
        elif observed in accepted_forms:
            classification = "accepted_correction"
        else:
            classification = "unapproved_edit"

        decisions.append(
            {
                "source": " ".join(input_tokens[start:end]),
                "observed": " ".join(observed),
                "classification": classification,
            }
        )

    applicable = len(decisions)
    unapproved = sum(
        decision["classification"] == "unapproved_edit" for decision in decisions
    )
    unchanged = sum(
        decision["classification"] == "unchanged" for decision in decisions
    )
    accepted_edits = sum(
        decision["classification"] == "accepted_correction"
        for decision in decisions
    )
    return {
        "applicable_sites": applicable,
        "unchanged_sites": unchanged,
        "accepted_corrections": accepted_edits,
        "unapproved_edits": unapproved,
        "unapproved_edit_rate": (
            round(unapproved / applicable * 100.0, 1) if applicable else None
        ),
        "sites": decisions,
    }


def score_target_accuracy(
    input_text, output_text, targets, include_identity_only=False
):
    """Score accepted output forms aligned to their annotated source sites."""
    input_tokens = _tokens(input_text)
    if not isinstance(targets, dict):
        raise TypeError("Targets must be a dictionary")

    for source, accepted in targets.items():
        source_tokens = _tokens(source)
        if not source_tokens:
            raise ValueError("Correction target source phrases cannot be empty")
        if not _find_occurrences(input_tokens, source_tokens):
            raise ValueError(f"Correction target source not found in input: {source}")
        if isinstance(accepted, str):
            accepted = [accepted]
        if not isinstance(accepted, (list, tuple, set)):
            raise TypeError("Accepted correction forms must be strings or a sequence")
        if any(not isinstance(form, str) for form in accepted):
            raise TypeError("Accepted correction forms must be strings")

    sites = score_correction_sites(
        input_text,
        output_text,
        [targets],
        include_identity_only=include_identity_only,
    )
    source_is_accepted = set()
    for source, accepted in targets.items():
        source_tokens = _tokens(source)
        accepted = [accepted] if isinstance(accepted, str) else accepted
        if any(_tokens(form) == source_tokens for form in accepted):
            source_is_accepted.add(" ".join(source_tokens))
    accepted_unchanged = sum(
        site["classification"] == "unchanged"
        and site["source"] in source_is_accepted
        for site in sites["sites"]
    )
    total = sites["applicable_sites"]
    accepted_targets = sites["accepted_corrections"] + accepted_unchanged
    return {
        "accepted_targets": accepted_targets,
        "total_targets": total,
        "accuracy": (
            round(accepted_targets / total * 100.0, 2) if total else 100.0
        ),
    }
