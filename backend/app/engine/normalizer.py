from __future__ import annotations

import re


def normalize_text(value: str) -> str:
    """Normalize text for consistent mathematical matching.
    
    Strips currency symbols (₹, $), digit grouping commas (21,000 -> 21000),
    standardizes operators (×, ÷, *, /), and trims excess whitespace.
    """
    s = str(value).lower()
    s = re.sub(r"[\u20B9$]", "", s)
    s = re.sub(r"\brs\b\.?|\brupees?\b", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\s*:\s*", ":", s)
    s = re.sub(r"\s*×\s*", "*", s)
    s = re.sub(r"\bx\b", "*", s)
    s = re.sub(r"\s*÷\s*", "/", s)
    s = re.sub(r"\s*([*+/])\s*", r"\1", s)
    s = re.sub(r"\s*=\s*", "=", s)
    s = re.sub(r"\s*->\s*", "->", s)
    s = re.sub(r"[.,!;?]+$", "", s).strip()

    # Collapse commas between digits: "21,000" -> "21000", "19,950" -> "19950"
    while re.search(r"(\d),(\d)", s):
        s = re.sub(r"(\d),(\d)", r"\1\2", s)

    return s


def strip_connecting_words(text: str) -> str:
    """Strip extraneous connecting words from a student response."""
    pattern = r"\b(i|love|paris|the|a|an|and|is|are|so|then|therefore|hence|thus|we|can|get|have|has|of|to|for|it|that|this|my|me|you|your|with)\b"
    s = re.sub(pattern, " ", str(text), flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", s).strip()
