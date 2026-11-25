"""Bridge between the Tutor Engine and the Socratic Navigator Ranker.

Provides unified single-pass node matching (Exact -> Weighted Jaccard >= 0.70)
with strict mathematical safety guards so fuzzy text similarity never approves
wrong numbers or incorrect equations.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from app.schemas.graph import Node


def _extract_numbers(text: str) -> List[float]:
    clean = re.sub(r"(?<=\d),(?=\d)", "", text or "")
    return [float(x) for x in re.findall(r"\d+(?:\.\d+)?", clean)]


def _numbers_compatible(raw_input: str, matched_phrase: str, allow_subset: bool = False) -> bool:
    """Prevent fuzzy Jaccard from accepting wrong numerical values or signs.

    When allow_subset=True (for extraction nodes), a single-fact statement like
    'Mother is 5 times her daughter's present age' may match a combined multi-fact
    phrase containing [5, 6, 3] as long as all numbers the student wrote exist in it.
    """
    in_nums = _extract_numbers(raw_input)
    ph_nums = _extract_numbers(matched_phrase)
    if not in_nums and not ph_nums:
        return True
    if allow_subset:
        if not in_nums:
            return True
        if not ph_nums:
            return False
        return all(any(abs(n - p) < 1e-6 for p in ph_nums) for n in in_nums)
    if bool(in_nums) != bool(ph_nums):
        return False
    # Every number written by the student must appear in the matched reference phrase
    return all(any(abs(n - p) < 1e-6 for p in ph_nums) for n in in_nums) and len(in_nums) == len(ph_nums)


def _node_to_dict(node: Node) -> Dict[str, Any]:
    return {
        "id": node.id,
        "type": node.type,
        "label": getattr(node, "label", "") or "",
        "accept": list(getattr(node, "accept", None) or []),
    }


def navigator_match_node(
    raw_input: str,
    node: Node,
    threshold: float = 0.70,
) -> Dict[str, Any]:
    """Score raw_input against node['accept'] using Navigator's ranker.

    Applies strict numerical and sign compatibility guards before accepting
    fuzzy Jaccard matches.
    """
    if not raw_input or not raw_input.strip():
        return {"accepted": False, "score": 0.0}

    accepts = getattr(node, "accept", None) or []
    if not accepts:
        return {"accepted": False, "score": 0.0}

    # Never allow fuzzy text matching to accept algebraic/arithmetic sign errors
    has_equation_ops = bool(re.search(r"[=+\-*/÷×^]", raw_input))

    try:
        from app.navigator.ranker import score_node
        score, match_type, best_phrase = score_node(raw_input, _node_to_dict(node))
    except Exception:
        return {"accepted": False, "score": 0.0}

    if match_type in ("EXACT_STRING_MATCH", "EXACT_TOKEN_MATCH") and score >= 1.0 - 1e-9:
        if has_equation_ops and not _numbers_compatible(raw_input, best_phrase):
            return {"accepted": False, "score": 0.0}
        return {
            "accepted": True,
            "score": float(score),
            "match_type": match_type,
            "source": "navigator_exact",
            "phrase": best_phrase,
        }

    # Fuzzy Jaccard path: enforce threshold AND strict number/operator safety
    if score >= threshold:
        if has_equation_ops:
            # Equations/arithmetic must be validated by SymPy or exact match, never fuzzy Jaccard alone
            return {"accepted": False, "score": float(score)}
        is_extraction = getattr(node, "type", None) == "extraction"
        if not _numbers_compatible(raw_input, best_phrase, allow_subset=is_extraction):
            return {"accepted": False, "score": float(score)}
        return {
            "accepted": True,
            "score": float(score),
            "match_type": match_type,
            "source": "navigator_jaccard",
            "phrase": best_phrase,
        }

    return {"accepted": False, "score": float(score)}


def navigator_resolve_nodes(
    raw_input: str,
    nodes: List[Node],
    threshold: float = 0.70,
) -> Optional[Tuple[Node, Dict[str, Any]]]:
    """Return the highest-scoring safe Navigator match across candidate nodes."""
    best_node: Optional[Node] = None
    best_res: Dict[str, Any] = {"accepted": False, "score": 0.0}

    for node in nodes:
        res = navigator_match_node(raw_input, node, threshold=threshold)
        if res.get("accepted") and res.get("score", 0.0) > best_res.get("score", 0.0):
            best_node = node
            best_res = res

    if best_node is not None:
        return best_node, best_res
    return None
