from __future__ import annotations

import re
from typing import Set

RELEVANT_WORDS: Set[str] = {
    # Structural / conversational words
    "i", "a", "an", "the", "and", "or", "so", "if", "then", "thus", "hence", "therefore",
    "is", "are", "am", "was", "were", "be", "been", "being", "do", "does", "did", "done",
    "can", "will", "would", "should", "shall", "may", "might", "must",
    "we", "us", "our", "you", "your", "my", "me", "it", "its", "they", "them", "their",
    "this", "that", "these", "those", "there", "here", "of", "to", "for", "with", "by",
    "in", "on", "at", "as", "from", "into", "both", "each", "per",
    "get", "got", "have", "has", "had", "give", "gives", "given", "use", "used", "using", "after",
    "check", "see", "find", "found", "try", "tries", "trying", "want", "wants", "let",
    "lets", "think", "okay", "ok", "yes", "no", "not", "now", "first", "next", "last",
    "final", "because", "since", "when", "make", "makes", "made", "means", "mean",
    "know", "known", "suppose", "supposed", "maybe", "please",
    "first", "second", "explain", "show", "calculate", "multiple",
    "equal", "equals", "same", "identical", "match", "matches", "matched", "matching",
    "ratio", "ratios", "proportional", "proportion", "proportions",
    "fraction", "fractions", "numerator", "denominator", "numerators", "denominators",
    "hcf", "gcd", "highest", "common", "factor", "factors", "factorization",
    "factorise", "factorize", "factorised", "factorized", "prime", "primes",
    "simplest", "simple", "simplify", "simplified", "simplifies", "simplifying",
    "cancel", "cancels", "canceled", "cancelled", "canceling", "cancelling",
    "reduce", "reduced", "reduces", "reducing", "reduction",
    "divide", "divided", "divides", "dividing", "division", "divisor", "dividend",
    "multiply", "multiplied", "multiplies", "multiplying", "multiplication",
    "times", "product", "products", "scale", "scaled", "scales", "scaling",
    "decimal", "decimals", "equivalent", "equivalence",
    "value", "values", "result", "results", "answer", "answers", "term", "terms",
    "number", "numbers", "step", "steps", "method", "methods", "approach", "over",
    "cross", "form", "side", "sides",
    "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
    "quarter", "quarters", "half", "halves", "third", "thirds",

    # Percentages & Finance
    "percent", "percentage", "percentages", "depreciation", "depreciates", "depreciate", "depreciated",
    "original", "bought", "buy", "cost", "price", "sale", "rate", "time", "annum", "year", "years", "amount",
    "interest", "principal", "discount", "markup", "profit", "loss", "gain",

    # Algebra & Word Problems
    "age", "ages", "daughter", "daughters", "mother", "mothers", "father", "son", "present", "future", "past",
    "ago", "hence", "older", "younger", "unit", "units", "part", "parts", "constant", "difference", "sum", "total",
    "equation", "let", "assume", "variable", "linear", "solve", "solved", "solving", "subtract", "subtracted", "subtracting",
    "add", "added", "adding", "addition", "subtraction"
}

MATH_INTENT: Set[str] = {
    "hcf", "gcd", "simplify", "simplified", "simplifies", "simplifying", "simplest",
    "cross", "multiply", "multiplied", "multiplication", "scale", "scaled", "scaling",
    "decimal", "decimals", "fraction", "fractions", "prime", "factorization",
    "factorize", "factorise", "equivalent", "reduce", "reduced", "reduction",
    "proportional", "proportion", "ratio", "ratios", "divide", "divided", "division",
    "equal", "equals", "same", "identical", "yes", "no", "not", "times", "product"
}


def has_irrelevant_words(normalized_input: str, normalized_accepted: str = "") -> bool:
    """Check if input contains off-topic words not recognized in RELEVANT_WORDS or accepted answer."""
    input_words = [w for w in re.split(r"[^a-z]+", normalized_input) if w]
    if not input_words:
        return False

    accepted_words = [w for w in re.split(r"[^a-z]+", normalized_accepted) if w]
    accepted_is_keyword = bool(re.match(r"^[a-z]+$", normalized_accepted)) and len(normalized_accepted) >= 3

    for word in input_words:
        if word in RELEVANT_WORDS:
            continue
        if any((len(aw) >= 3 and word.startswith(aw)) or (len(word) >= 3 and aw.startswith(word)) for aw in accepted_words):
            continue
        if accepted_is_keyword and word.startswith(normalized_accepted):
            continue
        return True

    return False

