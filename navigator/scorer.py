"""Scoring Engine for Navigator v2 (powered by v1 Deterministic Scorer).

Computes exact string match, token set equivalence, short-input guardrails,
and specificity-weighted Jaccard with character n-gram soft alignment.
Completely deterministic; pure string/token math without embeddings or cosine similarity.
"""

from __future__ import annotations

try:
    from .normalizer import normalize, to_token_set
except ImportError:
    from normalizer import normalize, to_token_set


def char_bigrams(word: str) -> set[str]:
    """Generate boundary-padded character bigrams for a word."""
    padded = f"^{word}$"
    return {padded[i : i + 2] for i in range(len(padded) - 1)}


def token_char_sim(t1: str, t2: str) -> float:
    """Compute character bigram Dice coefficient between two tokens.

    Returns 1.0 for exact equality. Supports prefix matches and character bigram
    Dice coefficient for typo resiliency. Enforces a strict minimum similarity
    cutoff of 0.70 to avoid accidental fuzzy collisions on distinct short words.
    """
    if t1 == t2:
        return 1.0

    # Prefix match if both tokens are sufficiently long (e.g. 'simplif' vs 'simplify')
    if len(t1) >= 4 and len(t2) >= 4 and (t1.startswith(t2) or t2.startswith(t1)):
        return 0.85

    # Guard against short tokens or drastic length divergence
    if len(t1) < 3 or len(t2) < 3 or abs(len(t1) - len(t2)) > 3:
        return 0.0

    b1 = char_bigrams(t1)
    b2 = char_bigrams(t2)
    dice = 2.0 * len(b1 & b2) / (len(b1) + len(b2))
    return dice if dice >= 0.70 else 0.0


def exact_match(normalized_input: str, normalized_phrase: str) -> bool:
    """Check exact string equality between two already-normalized strings."""
    return normalized_input == normalized_phrase and bool(normalized_input)


def jaccard_similarity(tokens_a: frozenset[str], tokens_b: frozenset[str]) -> float:
    """Standard Jaccard similarity: |A ∩ B| / |A ∪ B|."""
    if not tokens_a and not tokens_b:
        return 0.0
    if tokens_a == tokens_b:
        return 1.0
    inter = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return len(inter) / len(union) if union else 0.0


def weighted_jaccard(tokens_a: frozenset[str], tokens_b: frozenset[str]) -> float:
    """Specificity-boosted Jaccard using token-length weights."""
    if not tokens_a and not tokens_b:
        return 0.0
    inter = tokens_a & tokens_b
    union = tokens_a | tokens_b
    weighted_union = sum(len(t) for t in union)
    if weighted_union == 0:
        return 0.0
    weighted_inter = sum(len(t) for t in inter)
    return weighted_inter / weighted_union


def score_phrase(input_text: str, accept_phrase: str) -> tuple[float, str]:
    """Score a single input string against an accept phrase.

    Pipeline:
        1. Normalize both strings.
        2. Rule 1 Check: Exact string match -> 1.0 immediately.
        3. Rule 1 Extension: Identical token set (fluff words stripped) -> 1.0.
        4. Short Input Guardrail: If input is a short token (len <= 2), require
           exact token containment, scaled by phrase length so it cannot falsely
           match complex multi-token expressions.
        5. Typo Resiliency & Specificity Blend: Token-level soft alignment via
           character bigrams, weighted Jaccard, and grounded input coverage.

    Returns:
        (score, match_type) where score is in [0.0, 1.0].
    """
    norm_input = normalize(input_text)
    norm_phrase = normalize(accept_phrase)

    # 1. Exact string match (Rule 1: Exact Match Dominance)
    if exact_match(norm_input, norm_phrase):
        return 1.0, "EXACT_STRING_MATCH"

    tokens_a = to_token_set(input_text)
    tokens_b = to_token_set(accept_phrase)

    if not tokens_a or not tokens_b:
        return 0.0, "NO_TOKENS"

    # 2. Pure token set equivalence (fluff-stripped exact match)
    if tokens_a == tokens_b:
        return 1.0, "EXACT_TOKEN_MATCH"

    # 3. Short Input Guardrail
    is_short_input = (len(tokens_a) == 1 and max(len(t) for t in tokens_a) <= 2) or len(norm_input) <= 2
    if is_short_input:
        single_tok = next(iter(tokens_a)) if tokens_a else norm_input
        if single_tok not in tokens_b:
            return 0.0, "SHORT_INPUT_MISMATCH"
        # Strict Jaccard: 1 / |tokens_b| (e.g. 'x' vs 'x' = 1.0; 'x' vs 'x + 20 = 40' = 0.20)
        return 1.0 / len(tokens_b), "SHORT_INPUT_GUARDRAIL"

    # 4. Character N-Gram Soft Token Alignment & Weighted Jaccard
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

    return min(1.0, final_score), "FUZZY_WEIGHTED_JACCARD"
