"""Deterministic Text Normalization Pipeline for Navigator v2.

Transforms raw input text and DAG accept phrases into canonical forms
for robust string matching, Jaccard similarity.
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
    # Conversational fillers
    "find", "finding", "what", "which", "how", "who", "where", "when", "why",
    "need", "want", "get", "got", "let", "lets", "try", "trying",
    "use", "using", "used", "think", "please", "tell", "show", "here", "there",
})

# Multi-character symbol phrases (longest first)
_SYMBOL_PHRASES: list[tuple[str, str]] = [
    ("is equal to", "eq"),
    ("equal to", "eq"),
    ("equals", "eq"),
    ("divided by", "div"),
    ("times", "mul"),
]

# Single character math operators
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
        1. Lowercase + strip whitespace.
        2. Strip possessives ('s and s') to prevent word divergence.
        3. Replace math phrases and symbols with canonical words.
        4. Preserve colon (ratio) as a distinct token or convert it cleanly.
        5. Strip remaining non-alphanumeric, non-space punctuation.
        6. Collapse repeated whitespace.
    """
    s = str(text).lower().strip()

    # Step 2: Strip possessives
    s = re.sub(r"['’]s\b", "", s)
    s = re.sub(r"s['’]\b", "s", s)

    # Step 3a: Multi-char symbol phrases
    for phrase, token in _SYMBOL_PHRASES:
        s = s.replace(phrase, f" {token} ")

    # Step 3b: Single-char symbols
    for char, token in _SYMBOL_CHARS.items():
        s = s.replace(char, f" {token} ")

    # Preserve ratios (e.g. 3:4 -> 3 4 or 3:4)
    # Convert ':' to space to treat ratio numbers as standard tokens
    s = s.replace(":", " ")

    # Step 4: Strip non-alphanumeric, non-space characters
    s = re.sub(r"[^a-z0-9 ]", "", s)

    # Step 5: Collapse whitespace
    s = re.sub(r"\s+", " ", s).strip()

    return s


def tokenize(text: str, remove_stopwords: bool = True) -> list[str]:
    """Split a pre-normalized string on whitespace and optionally remove stopwords.

    If stopword removal eliminates all tokens, returns the unfiltered tokens
    to prevent empty token sets on valid short inputs like "yes" or "is".
    """
    words = text.split()
    if not remove_stopwords:
        return words

    filtered = [w for w in words if w not in STOPWORDS]
    # Fallback to unfiltered tokens if all words were stopwords
    return filtered if filtered else words


def to_token_set(text: str, remove_stopwords: bool = True) -> frozenset[str]:
    """Convenience function: raw text -> normalize -> tokenize -> frozenset."""
    return frozenset(tokenize(normalize(text), remove_stopwords=remove_stopwords))
