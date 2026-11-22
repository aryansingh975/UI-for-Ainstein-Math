"""
Deterministic Text Normalization Pipeline.

Transforms raw text into canonical token sets for set-arithmetic scoring.
Every comparison in the navigator module operates on the output of this file.
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

STOPWORDS: frozenset[str] = frozenset({
    # Articles & determiners
    "a", "an", "the",
    # Pronouns
    "i", "me", "my", "we", "us", "our", "you", "your",
    "it", "its", "he", "she", "they", "them", "their",
    "this", "that", "these", "those",
    # Auxiliary / modal verbs
    "is", "are", "was", "were", "am", "be", "been", "being",
    "do", "does", "did", "has", "have", "had",
    "can", "could", "will", "would", "should", "shall", "may", "might", "must",
    # Prepositions & conjunctions
    "of", "to", "for", "with", "by", "in", "on", "at", "from",
    "and", "or", "but", "so", "if", "then",
    # High-frequency conversational & intent fillers
    "find", "finding", "what", "which", "how", "who", "where", "when", "why",
    "need", "want", "get", "got", "let", "lets", "try", "trying",
    "use", "using", "used", "think", "please", "tell", "show", "here", "there",
})

# Multi-char phrases MUST be checked before single-char symbols.
_SYMBOL_PHRASES: list[tuple[str, str]] = [
    ("is equal to", "eq"),
    ("equal to", "eq"),
    ("equals", "eq"),
    ("divided by", "div"),
    ("times", "mul"),
]

_SYMBOL_CHARS: dict[str, str] = {
    "=": "eq",
    "+": "plus",
    "-": "minus",
    "×": "mul",
    "*": "mul",
    "÷": "div",
    "/": "div",
}


# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------

def normalize(text: str) -> str:
    """Normalize raw text into a canonical lowercase string.

    Steps:
        1. Lowercase + strip leading/trailing whitespace.
        2. Strip possessive suffixes ('s and s') to prevent word divergence: (e.g., "daughter's" -> "daughter").
        3. Replace multi-character symbol phrases, then single-character symbols.
        4. Strip remaining non-alphanumeric, non-space punctuation.
        5. Collapse whitespace to single spaces.

    Does NOT remove stopwords — that is handled by ``tokenize``.
    """
    s = str(text).lower().strip()

    # Step 2: Strip possessives before punctuation stripping
    s = re.sub(r"['’]s\b", "", s)
    s = re.sub(r"s['’]\b", "s", s)

    # Step 3a: Multi-char symbol phrases (longest first)
    for phrase, token in _SYMBOL_PHRASES:
        s = s.replace(phrase, f" {token} ")

    # Step 3b: Single-char symbols
    for char, token in _SYMBOL_CHARS.items():
        s = s.replace(char, f" {token} ")

    # Step 4: Strip non-alphanumeric, non-space characters
    s = re.sub(r"[^a-z0-9 ]", "", s)

    # Step 5: Collapse whitespace
    s = re.sub(r"\s+", " ", s).strip()

    return s


def tokenize(text: str) -> list[str]:
    """Split a pre-normalized string on whitespace and remove stopwords.

    Args:
        text: A string that has already been passed through ``normalize``.

    Returns:
        Ordered list of content-bearing tokens.
    """
    return [w for w in text.split() if w not in STOPWORDS]


def to_token_set(text: str) -> frozenset[str]:
    """Full pipeline: raw text -> normalize -> tokenize -> frozenset.

    This is the single convenience function the rest of the module calls
    to obtain the canonical token representation of any string.
    """
    return frozenset(tokenize(normalize(text)))


if __name__ == "__main__":

    text = input("Enter your text: ")

    print("\nOriginal text:")
    print(text)

    normalized = normalize(text)
    print("\nAfter normalization:")
    print(normalized)

    tokens = tokenize(normalized)
    print("\nAfter tokenization:")
    print(tokens)

    token_set = to_token_set(text)
    print("\nFinal token set:")
    print(token_set)
    print()