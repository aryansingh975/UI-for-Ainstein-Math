"""Scoring Metric Engine.

Pure mathematical functions that compute scalar similarity values in [0.0, 1.0]
between two token sets. Combines token-level weighted Jaccard with character
n-gram soft matching for typo resiliency and short-input collision prevention.
"""

from __future__ import annotations

try:
    from app.navigator.normalizer import normalize, to_token_set
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from app.navigator.normalizer import normalize, to_token_set


# ---------------------------------------------------------------------------
# Set-Similarity & N-Gram Metrics
# ---------------------------------------------------------------------------

def char_bigrams(word: str) -> set[str]:
    """Generate boundary-padded character bigrams for a word."""
    padded = f"^{word}$"
    return {padded[i : i + 2] for i in range(len(padded) - 1)}


def token_char_sim(t1: str, t2: str) -> float:
    """Compute character bigram Dice coefficient between two tokens.

    Returns 1.0 for exact equality. For tokens with length >= 3, computes
    the Sørensen-Dice coefficient over padded character bigrams.
    Enforces a strict minimum similarity cutoff of 0.70 to avoid accidental
    fuzzy collisions on distinct short words.
    """
    if t1 == t2:
        return 1.0
    # Guard against short tokens or drastic length divergence
    if len(t1) < 3 or len(t2) < 3 or abs(len(t1) - len(t2)) > 2:
        return 0.0
    b1 = char_bigrams(t1)
    b2 = char_bigrams(t2)
    dice = 2.0 * len(b1 & b2) / (len(b1) + len(b2))
    return dice if dice >= 0.70 else 0.0


def jaccard_similarity(set_a: frozenset[str], set_b: frozenset[str]) -> float:
    """Standard Jaccard similarity: |A ∩ B| / |A ∪ B|.

    Returns 0.0 if both sets are empty.
    """
    if not set_a and not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union)


def weighted_jaccard(set_a: frozenset[str], set_b: frozenset[str]) -> float:
    """Specificity-boosted Jaccard using token-length weights.

    Each token *t* contributes ``len(t)`` to the intersection and union sums::

        WJ(A, B) = Σ len(t) for t in A∩B  /  Σ len(t) for t in A∪B

    Longer, more specific tokens (e.g. "daughter") outweigh short tokens
    (e.g. "age"), directly implementing Specificity Weighting.

    Returns 0.0 if the weighted union is zero.
    """
    if not set_a and not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    weighted_union = sum(len(t) for t in union)
    if weighted_union == 0:
        return 0.0
    weighted_intersection = sum(len(t) for t in intersection)
    return weighted_intersection / weighted_union


# ---------------------------------------------------------------------------
# Exact Match
# ---------------------------------------------------------------------------

def exact_match(normalized_input: str, normalized_phrase: str) -> bool:
    """Check exact string equality between two already-normalized strings.

    This is the primary gate for Rule 1 (Exact Match Dominance) which
    short-circuits all fuzzy scoring.
    """
    return normalized_input == normalized_phrase


# ---------------------------------------------------------------------------
# Composite Scorer
# ---------------------------------------------------------------------------

def score_phrase(input_text: str, accept_phrase: str) -> float:
    """Compute a composite similarity score for a single (input, phrase) pair.

    Pipeline:
        1. Normalize both strings.
        2. Rule 1 Check: If ``exact_match`` -> return 1.0 immediately.
        3. Rule 1 Extension: If canonical token sets are identical (e.g., fluff
           words successfully stripped) -> return 1.0.
        4. Short Input Guardrail (Bug Vector 2): If the input is a single short
           token (len <= 2), disable character n-grams and require exact token
           containment, scaled by phrase length so it cannot match complex
           expressions like "x + 20 = 40".
        5. Typo Resiliency & Specificity Blend (Bug Vector 3): Compute token-level
           soft alignment via character bigrams, weighted Jaccard, and input
           coverage.

    Args:
        input_text:    The raw user input string.
        accept_phrase: One raw element from a node's ``accept`` array.

    Returns:
        A float in [0.0, 1.0]. 1.0 indicates a perfect / exact match.
    """
    norm_input = normalize(input_text)
    norm_phrase = normalize(accept_phrase)

    # Rule 1: Exact Match Dominance
    if exact_match(norm_input, norm_phrase):
        return 1.0

    tokens_a = to_token_set(input_text)
    tokens_b = to_token_set(accept_phrase)

    if not tokens_a or not tokens_b:
        return 0.0

    # Rule 1 Extension: Pure token set equivalence (fluff-stripped exact match)
    if tokens_a == tokens_b:
        return 1.0

    # Bug Vector 2: Short Input Guardrail
    # If input is a short token (e.g. 'x', 'y', '2'), require exact token equality
    # and strictly prevent matching multi-token phrases via partial overlap.
    is_short_input = (len(tokens_a) == 1 and max(len(t) for t in tokens_a) <= 2) or len(norm_input) <= 2
    if is_short_input:
        single_tok = next(iter(tokens_a)) if tokens_a else norm_input
        if single_tok not in tokens_b:
            return 0.0
        # Strict Jaccard: 1 / |tokens_b| (e.g., 'x' vs 'x' = 1.0; 'x' vs 'x + 20 = 40' = 0.20)
        return 1.0 / len(tokens_b)

    # Bug Vector 3: Character N-Gram Soft Token Matching
    w_a = {t: len(t) for t in tokens_a}
    w_b = {t: len(t) for t in tokens_b}

    match_a = {ta: max((token_char_sim(ta, tb) for tb in tokens_b), default=0.0) for ta in tokens_a}
    match_b = {tb: max((token_char_sim(tb, ta) for ta in tokens_a), default=0.0) for tb in tokens_b}

    inter_w = (sum(w_a[ta] * match_a[ta] for ta in tokens_a) + sum(w_b[tb] * match_b[tb] for tb in tokens_b)) / 2.0
    total_w = sum(w_a.values()) + sum(w_b.values())
    union_w = total_w - inter_w
    jaccard = inter_w / union_w if union_w > 0 else 0.0

    # Input coverage (how much of the user's intent is grounded in the accept phrase)
    cov_input = sum(w_a[ta] * match_a[ta] for ta in tokens_a) / sum(w_a.values())

    # Blend: 40% weighted Jaccard + 60% grounded input coverage
    final_score = 0.4 * jaccard + 0.6 * (cov_input * max(match_a.values(), default=0.0))

    return min(1.0, final_score)


# ---------------------------------------------------------------------------
# Terminal Test Bench (Interactive & CLI)
# ---------------------------------------------------------------------------

def explain_score(input_text: str, accept_phrase: str) -> None:
    """Print a detailed breakdown of scoring between two strings."""
    norm_input = normalize(input_text)
    norm_phrase = normalize(accept_phrase)
    tokens_input = sorted(to_token_set(input_text))
    tokens_phrase = sorted(to_token_set(accept_phrase))
    score = score_phrase(input_text, accept_phrase)

    print("-" * 65)
    print(f"String 1 (Input):   {input_text!r}")
    print(f"  Normalized:       {norm_input!r}")
    print(f"  Tokens:           {tokens_input}")
    print(f"String 2 (Accept):  {accept_phrase!r}")
    print(f"  Normalized:       {norm_phrase!r}")
    print(f"  Tokens:           {tokens_phrase}")
    print("-" * 65)

    if exact_match(norm_input, norm_phrase):
        match_type = "Exact Normalized String Match (Rule 1 Dominance)"
    elif frozenset(tokens_input) == frozenset(tokens_phrase) and tokens_input:
        match_type = "Identical Token Set Match"
    else:
        match_type = "Fuzzy N-Gram & Weighted Jaccard Blend"

    print(f"Match Type:  {match_type}")
    print(f"Final Score: {score:.4f} ({score * 100:.1f}%)")
    print("-" * 65)


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        prog="scorer",
        description="Test and debug similarity scoring between two strings.",
    )
    parser.add_argument("str1", nargs="?", type=str, default=None, help="First string (e.g. user input)")
    parser.add_argument("str2", nargs="?", type=str, default=None, help="Second string (e.g. accept phrase)")

    args = parser.parse_args()

    # Mode 1: One-shot CLI arguments passed directly
    if args.str1 is not None and args.str2 is not None:
        explain_score(args.str1, args.str2)
        sys.exit(0)

    # Mode 2: Interactive REPL bench
    print("=" * 65)
    print("NAVIGATOR SCORER — INTERACTIVE TWO-STRING TEST BENCH")
    print("Compare student input against an accept phrase and inspect score.")
    print("Type 'exit', 'quit', or press Ctrl+C to stop.")
    print("=" * 65)

    while True:
        try:
            s1 = input("\nEnter String 1 (Input)   : ").strip()
            if s1.lower() in ("exit", "quit", "q"):
                print("Exiting scorer.")
                break
            if not s1:
                continue

            s2 = input("Enter String 2 (Accept)  : ").strip()
            if s2.lower() in ("exit", "quit", "q"):
                print("Exiting scorer.")
                break
            if not s2:
                continue

            explain_score(s1, s2)
        except (KeyboardInterrupt, EOFError):
            print("\nExiting scorer.")
            break
