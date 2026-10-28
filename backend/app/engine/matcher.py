from __future__ import annotations

import re
from typing import List
from app.engine.normalizer import normalize_text, strip_connecting_words
from app.engine.vocabulary import has_irrelevant_words


def matches_accept(raw_input: str, accepted_answer: str) -> bool:
    """Matches a raw student input against an accepted answer string."""
    normalized_input = normalize_text(raw_input)
    normalized_accepted = normalize_text(accepted_answer)

    if normalized_input == normalized_accepted:
        return True

    if has_irrelevant_words(normalized_input, normalized_accepted):
        return False

    # Single-word keyword matching
    if re.match(r"^[a-z]+$", normalized_accepted) and len(normalized_accepted) >= 3:
        if normalized_accepted in normalized_input:
            return True
        input_words = normalized_input.split(" ")
        for word in input_words:
            if word.startswith(normalized_accepted):
                return True

    # Numeric match with optional context words (e.g. "hcf is 24" -> "24")
    if re.match(r"^[\d.]*$", normalized_accepted) and len(normalized_accepted) > 0:
        input_numbers = re.findall(r"\d+(?:\.\d+)?", normalized_input)
        if normalized_input == normalized_accepted:
            return True
        if input_numbers and len(input_numbers) == 1 and input_numbers[0] == normalized_accepted:
            words = normalized_input.split(" ")
            if len(words) <= 3:
                non_numeric = [w for w in words if not re.match(r"^\d+(?:\.\d+)?$", w)]
                if all(len(w) <= 6 for w in non_numeric):
                    return True
        return False

    # Strict ratio equality
    if re.match(r"^\d+:\d+$", normalized_accepted):
        return normalized_input == normalized_accepted

    # Strict fraction equality
    if re.match(r"^\d+/\d+$", normalized_accepted):
        return normalized_input == normalized_accepted

    # Multi-number expressions with matching operators (e.g. "72/24=3 and 96/24=4")
    input_numbers = re.findall(r"\d+(?:\.\d+)?", normalized_input)
    accepted_numbers = re.findall(r"\d+(?:\.\d+)?", normalized_accepted)
    if accepted_numbers and len(accepted_numbers) > 1 and input_numbers:
        if ",".join(input_numbers) != ",".join(accepted_numbers):
            return False
        accepted_has_op = bool(re.search(r"[/*=÷×]", normalized_accepted))
        if not accepted_has_op:
            return False
        has_op = bool(re.search(r"[/*=÷×]", normalized_input))
        if not has_op:
            return False
        return True

    # Phrasing with connecting words stripped
    if re.search(r"[a-z]", normalized_accepted):
        stripped = normalize_text(strip_connecting_words(raw_input))
        if stripped == normalized_accepted:
            return True

    return False


def matches_accept_any(raw_input: str, accepts: List[str]) -> bool:
    """Check if raw input matches any of the accepted strings."""
    return any(matches_accept(raw_input, a) for a in (accepts or []))

