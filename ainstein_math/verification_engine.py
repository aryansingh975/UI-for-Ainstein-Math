"""Verify student replies using the dataset class08_test-problem_validation.json."""

import difflib
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

# -----------------------------------------------------------------------------
# Configuration and dataset loading
# -----------------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
DATASET = "dataset/class08_test-problem_validation.json"

STOP_WORDS = {
    "the", "a", "an", "is", "are", "and", "or", "to", "in", "it", "of",
    "for", "on", "at", "by", "with", "so", "ok", "okay", "um", "uh",
    "just", "well", "then", "be", "do", "i"
}


class VerifyEngine:
    """Interpret student replies using validation_data from the dataset.

    The engine follows the repository's node-based validation format with
    robust multi-layered filtering:
      1. Noise & Incomplete input detection (rejects 'the', 'a', 'ok', etc.)
      2. Irrelevant true arithmetic detection (catches '3+4=7', '2+2=4', etc.)
      3. Targeted arithmetic error hints (catches '3*96=200', etc.)
      4. Method-aware progression for cross-multiplication, simplification, and scaling.
    """

    # -------------------------------------------------------------------------
    # Constructor and state setup
    # -------------------------------------------------------------------------
    def __init__(self, dataset_path: str = DATASET):
        path = Path(dataset_path)
        if not path.is_absolute():
            path = ROOT_DIR / dataset_path

        with open(path, "r", encoding="utf-8") as fh:
            self.dataset = json.load(fh)

        self.validation_data = self.dataset.get("validation_data", {})
        self.solution_nodes = self.validation_data.get("solution_nodes", [])
        self.givens = self.validation_data.get("givens", [])
        self.goals = self.validation_data.get("goals", [])
        self.answer = self.validation_data.get("answer", {})
        self.methods = {m["id"]: m for m in self.validation_data.get("methods", [])}
        self.nodes_by_id = {node["id"]: node for node in self.solution_nodes}

        # Runtime state
        self.completed_nodes: Set[str] = set()
        self.established_facts: Set[str] = set()
        self.history: List[Dict[str, Any]] = []
        self.active_method: Optional[str] = None
        self.is_completed = False

    # -------------------------------------------------------------------------
    # Reset logic
    # -------------------------------------------------------------------------
    def reset(self) -> None:
        """Return the engine to its initial state for a fresh run."""
        self.completed_nodes.clear()
        self.established_facts.clear()
        self.history.clear()
        self.active_method = None
        self.is_completed = False

    # -------------------------------------------------------------------------
    # Dataset-level helpers & Text Normalization
    # -------------------------------------------------------------------------
    def get_initial_prompt(self) -> str:
        """Return the question text along with the tutor's initial question."""
        q_text = self.dataset.get("question_text", "Are the ratios proportional?")
        first_node = self._next_node()
        prompt = first_node.get("prompt", "What quantities are given in the problem?") if first_node else ""
        return (
            f"Problem Statement:\n"
            f"  {q_text}\n\n"
            f"Tutor:\n"
            f"  {prompt}"
        )

    def _normalize(self, text: str) -> str:
        """Standardize text so comparisons are not sensitive to spacing or symbols."""
        if text is None:
            return ""

        cleaned = text.lower().strip()
        cleaned = cleaned.replace("×", "x").replace("*", "x")
        cleaned = cleaned.replace("−", "-")
        cleaned = cleaned.replace("÷", "/")
        # Normalize whitespace around operators and colons
        cleaned = re.sub(r"\s*:\s*", ":", cleaned)
        cleaned = re.sub(r"\s*/\s*", "/", cleaned)
        cleaned = re.sub(r"\s*=\s*", "=", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned

    def _has_keyword(self, text: str, target: str, cutoff: float = 0.78) -> bool:
        """Check if text contains target word or a common student typo of it (e.g. 'proprtional')."""
        words = re.findall(r"[a-z]+", text.lower())
        target_lower = target.lower()
        for w in words:
            if w == target_lower or target_lower in w:
                return True
            # Check prefix alignment or difflib similarity for typos
            if len(w) >= 4 and len(target_lower) >= 4:
                if w.startswith(target_lower[:3]):
                    if difflib.SequenceMatcher(None, w, target_lower).ratio() >= cutoff:
                        return True
                elif difflib.SequenceMatcher(None, w, target_lower).ratio() >= cutoff:
                    return True
        return False

    def _is_noise_or_incomplete(self, text: str) -> bool:
        """Identify if the input is mere noise, single stop-words, or lacks content."""
        raw = text.strip().lower()
        # Check if contains any digits or math operators
        has_math = bool(re.search(r"[\d\+\-\*\/x×÷\:=]", raw))
        if has_math:
            return False

        # Check domain-relevant keywords
        domain_keywords = {
            "ratio", "ratios", "proportion", "proportional", "cross",
            "multiply", "multiplication", "simplify", "simplest", "scaling",
            "scale", "factor", "product", "products", "equal", "unequal",
            "divide", "division", "hcf", "gcd", "yes", "no", "extremes", "means"
        }
        words = set(re.findall(r"\b[a-z]+\b", raw))
        if words & domain_keywords:
            return False

        # If all words are stop words or length is too short
        non_stop = [w for w in words if w not in STOP_WORDS]
        return len(non_stop) == 0

    def _check_irrelevant_true_claim(self, text: str) -> Optional[str]:
        """Detect mathematically true claims that are irrelevant to comparing 3:4 and 72:96."""
        normalized = self._normalize(text)
        # Match standard binary arithmetic equality: A op B = C
        match = re.search(r"(\d+(?:\.\d+)?)\s*([\+\-\*x\/])\s*(\d+(?:\.\d+)?)\s*=\s*(\d+(?:\.\d+)?)", normalized)
        if match:
            a, op, b, c = float(match.group(1)), match.group(2), float(match.group(3)), float(match.group(4))
            is_true = False
            if op == "+":
                is_true = abs((a + b) - c) < 1e-6
            elif op == "-":
                is_true = abs((a - b) - c) < 1e-6
            elif op in ("*", "x"):
                is_true = abs((a * b) - c) < 1e-6
            elif op == "/":
                is_true = b != 0 and abs((a / b) - c) < 1e-6

            if is_true:
                # Check if this arithmetic is relevant to the problem
                pair = {a, b}
                relevant_pairs = [
                    {3, 96}, {4, 72},  # Cross multiplication
                    {72, 24}, {96, 24}, # Simplification by HCF
                    {3, 24}, {4, 24},  # Scaling
                ]
                is_relevant_math = any(pair == rp for rp in relevant_pairs)
                if not is_relevant_math or op in ("+", "-"):
                    return (
                        f"While {int(a) if a.is_integer() else a} {op} {int(b) if b.is_integer() else b} = "
                        f"{int(c) if c.is_integer() else c} is mathematically correct, "
                        "it is not relevant to determining if the ratios 3:4 and 72:96 are proportional."
                    )
        return None

    def _check_arithmetic_error(self, text: str) -> Optional[str]:
        """Detect on-topic calculations with arithmetic errors and provide a targeted hint."""
        normalized = self._normalize(text)
        # Check cross product calculation errors: 3 * 96 != 288
        m3_96 = re.search(r"3\s*(?:x|\*)\s*96\s*=\s*(\d+)", normalized)
        if m3_96 and int(m3_96.group(1)) != 288:
            return f"You are on the right track, but check your multiplication: 3 × 96 is 288, not {m3_96.group(1)}."

        m4_72 = re.search(r"4\s*(?:x|\*)\s*72\s*=\s*(\d+)", normalized)
        if m4_72 and int(m4_72.group(1)) != 288:
            return f"You are on the right track, but check your multiplication: 4 × 72 is 288, not {m4_72.group(1)}."

        # Check simplification errors: 72:96 != 3:4
        m_sim = re.search(r"72\s*[:\/]\s*96\s*(?:simplifies to|=|is)\s*(\d+)\s*[:\/]\s*(\d+)", normalized)
        if m_sim:
            n1, n2 = int(m_sim.group(1)), int(m_sim.group(2))
            if (n1, n2) != (3, 4):
                return f"Check your simplification: dividing 72 and 96 by their HCF (24) gives 3:4, not {n1}:{n2}."

        return None

    def _matches_any(self, text: str, candidates: List[str]) -> bool:
        """Check whether the student's text contains an accepted candidate phrasing.

        Directional matching: The candidate must be matched by the text,
        avoiding false positives from small single-word substrings like 'the'.
        """
        normalized_text = self._normalize(text)
        for candidate in candidates:
            normalized_candidate = self._normalize(candidate)
            if normalized_candidate in normalized_text:
                return True
        return False

    def _record_node(self, node: Dict[str, Any]) -> None:
        """Mark a node complete and add its established facts to the engine state."""
        node_id = node["id"]
        self.completed_nodes.add(node_id)

        for fact in node.get("establishes", []):
            self.established_facts.add(fact)

        self.history.append({
            "node_id": node_id,
            "operation": node.get("operation"),
            "facts": list(node.get("establishes", [])),
        })

    def _next_node(self) -> Optional[Dict[str, Any]]:
        """Return the next unfinished solution node along the active method's path."""
        # If a method has been selected, follow that method's specific path
        if self.active_method and self.active_method in self.methods:
            method_path = self.methods[self.active_method]["path"]
            for node_id in method_path:
                if node_id not in self.completed_nodes:
                    return self.nodes_by_id.get(node_id)
            return None

        # Before method selection, proceed through initial extraction nodes
        for node in self.solution_nodes:
            if node["id"] not in self.completed_nodes:
                return node
        return None

    # -------------------------------------------------------------------------
    # Method detection helpers
    # -------------------------------------------------------------------------
    def _method_from_text(self, text: str) -> Optional[str]:
        """Infer which method the student is choosing."""
        lower = self._normalize(text)

        if "cross" in lower and ("multi" in lower or "product" in lower or "cross" in lower):
            return "cross_multiplication"

        if "simplif" in lower or "reduce" in lower or "divide" in lower or "hcf" in lower:
            return "simplification"

        if "scale" in lower or "multipl" in lower or "factor" in lower:
            return "scaling"

        return None

    # -------------------------------------------------------------------------
    # Node-specific evaluators
    # -------------------------------------------------------------------------
    def _evaluate_node_001(self, text: str) -> Dict[str, Any]:
        """Handle the 'identify_givens' node with entity coverage verification."""
        node = self.nodes_by_id["node_001"]
        normalized = self._normalize(text)

        has_r1 = ("3:4" in normalized) or ("3/4" in normalized) or ("3 to 4" in normalized)
        has_r2 = ("72:96" in normalized) or ("72/96" in normalized) or ("72 to 96" in normalized)

        # Partial coverage hint
        if has_r1 and not has_r2:
            return {
                "verdict": "partial_givens",
                "node_id": node["id"],
                "response": "You identified the first ratio (3:4). What is the second ratio given in the problem?",
                "completed": False,
                "facts": sorted(self.established_facts),
            }
        if has_r2 and not has_r1:
            return {
                "verdict": "partial_givens",
                "node_id": node["id"],
                "response": "You identified the second ratio (72:96). What is the first ratio given in the problem?",
                "completed": False,
                "facts": sorted(self.established_facts),
            }

        if (has_r1 and has_r2) or self._matches_any(text, node["accept"]):
            self._record_node(node)
            return {
                "verdict": "atomic_step_accepted",
                "node_id": node["id"],
                "response": "Correct: the givens are the two ratios, 3:4 and 72:96.",
                "completed": False,
                "facts": sorted(self.established_facts),
            }

        return {
            "verdict": "waiting_for_atomic_step",
            "node_id": node["id"],
            "response": node["prompt"],
            "completed": False,
            "facts": sorted(self.established_facts),
        }

    def _evaluate_node_002(self, text: str) -> Dict[str, Any]:
        """Handle the 'identify_goals' node."""
        node = self.nodes_by_id["node_002"]
        normalized = self._normalize(text)

        has_proportional = (
            ("proport" in normalized)
            or self._has_keyword(normalized, "proportional")
            or self._has_keyword(normalized, "proportion")
        )
        has_equal = ("equal" in normalized) and ("ratio" in normalized or "both" in normalized)

        if has_proportional or has_equal or self._matches_any(text, node["accept"]):
            self._record_node(node)
            return {
                "verdict": "atomic_step_accepted",
                "node_id": node["id"],
                "response": "Correct: the goal is to decide whether the two ratios are proportional.",
                "completed": False,
                "facts": sorted(self.established_facts),
            }

        return {
            "verdict": "waiting_for_atomic_step",
            "node_id": node["id"],
            "response": node["prompt"],
            "completed": False,
            "facts": sorted(self.established_facts),
        }

    def _evaluate_node_003(self, text: str) -> Dict[str, Any]:
        """Handle the method-selection node."""
        node = self.nodes_by_id["node_003"]
        method = self._method_from_text(text)

        if method in {"cross_multiplication", "simplification", "scaling"}:
            self.active_method = method
            self._record_node(node)
            return {
                "verdict": "atomic_step_accepted",
                "node_id": node["id"],
                "method": method,
                "response": "Method selected: " + method.replace("_", " ") + ".",
                "completed": False,
                "facts": sorted(self.established_facts),
            }

        return {
            "verdict": "waiting_for_atomic_step",
            "node_id": node["id"],
            "response": node["prompt"],
            "completed": False,
            "facts": sorted(self.established_facts),
        }

    def _evaluate_node_crs_mul_001(self, text: str) -> Dict[str, Any]:
        """Handle the cross-multiplication computation node."""
        node = self.nodes_by_id["node_crs-mul_001"]
        normalized = self._normalize(text)

        has_3_96 = ("3x96" in normalized) or ("3*96" in normalized) or ("3 96" in normalized)
        has_4_72 = ("4x72" in normalized) or ("4*72" in normalized) or ("4 72" in normalized)
        has_288 = "288" in normalized

        if has_288 or (has_3_96 and has_4_72) or self._matches_any(text, node["accept"]):
            self._record_node(node)
            return {
                "verdict": "atomic_step_accepted",
                "node_id": node["id"],
                "response": "Correct: 3 × 96 = 288 and 4 × 72 = 288.",
                "completed": False,
                "facts": sorted(self.established_facts),
            }

        return {
            "verdict": "waiting_for_atomic_step",
            "node_id": node["id"],
            "response": node["prompt"],
            "completed": False,
            "facts": sorted(self.established_facts),
        }

    def _evaluate_node_crs_mul_002(self, text: str) -> Dict[str, Any]:
        """Handle the final conclusion for the cross-multiplication route."""
        node = self.nodes_by_id["node_crs-mul_002"]
        normalized = self._normalize(text)

        has_prop = ("proport" in normalized) or self._has_keyword(normalized, "proportional") or self._has_keyword(normalized, "proportion")
        is_affirmative_proportional = has_prop and ("not" not in normalized) and ("unequal" not in normalized)
        is_direct_yes = normalized in {"yes", "true", "correct"}

        if self._matches_any(text, node["accept"]) or is_affirmative_proportional or is_direct_yes:
            self._record_node(node)
            self.is_completed = True
            return {
                "verdict": "atomic_step_accepted",
                "node_id": node["id"],
                "response": "Conclusion: the ratios are proportional because the cross products are equal.",
                "completed": True,
                "facts": sorted(self.established_facts),
            }

        return {
            "verdict": "waiting_for_atomic_step",
            "node_id": node["id"],
            "response": node["prompt"],
            "completed": False,
            "facts": sorted(self.established_facts),
        }

    def _evaluate_node_sim_001(self, text: str) -> Dict[str, Any]:
        """Handle the simplification computation node for the ratio 72:96."""
        node = self.nodes_by_id["node_sim_001"]
        normalized = self._normalize(text)

        has_72_96 = ("72:96" in normalized) or ("72/96" in normalized) or ("72 96" in normalized)
        has_3_4 = ("3:4" in normalized) or ("3/4" in normalized) or ("3 4" in normalized)
        has_simplify = any(w in normalized for w in ["simpl", "divide", "reduce", "24", "hcf"])
        has_3_4 = ("3:4" in normalized) or ("3/4" in normalized) or ("3 to 4" in normalized) or ("3 : 4" in normalized)

        # Catch partial reductions with a helpful pedagogical hint
        partial_simplifications = ["6:8", "6/8", "9:12", "9/12", "18:24", "18/24", "36:48", "36/48"]
        if any(p in normalized for p in partial_simplifications) and not has_3_4:
            return {
                "verdict": "partial_simplification",
                "node_id": node["id"],
                "response": "That is a valid reduction, but can you simplify it further to its simplest form?",
                "completed": False,
                "facts": sorted(self.established_facts),
            }

        if has_3_4 or self._matches_any(text, node["accept"]):
            self._record_node(node)
            return {
                "verdict": "atomic_step_accepted",
                "node_id": node["id"],
                "response": "Correct: 72:96 simplifies to 3:4 by dividing by 24.",
                "response": "Correct: 72:96 simplifies to 3:4 by dividing both terms by 24 (their HCF).",
                "completed": False,
                "facts": sorted(self.established_facts),
            }

        return {
            "verdict": "waiting_for_atomic_step",
            "node_id": node["id"],
            "response": node["prompt"],
            "completed": False,
            "facts": sorted(self.established_facts),
        }

    def _evaluate_node_sim_002(self, text: str) -> Dict[str, Any]:
        """Handle the final conclusion for the simplification route."""
        node = self.nodes_by_id["node_sim_002"]
        normalized = self._normalize(text)

        has_prop = ("proport" in normalized) or self._has_keyword(normalized, "proportional") or self._has_keyword(normalized, "proportion")
        is_affirmative_proportional = has_prop and ("not" not in normalized) and ("unequal" not in normalized)
        is_direct_yes = normalized in {"yes", "true", "correct"}

        if self._matches_any(text, node["accept"]) or is_affirmative_proportional or is_direct_yes:
            self._record_node(node)
            self.is_completed = True
            return {
                "verdict": "atomic_step_accepted",
                "node_id": node["id"],
                "response": "Conclusion: both ratios simplify to 3:4, so they are proportional.",
                "completed": True,
                "facts": sorted(self.established_facts),
            }

        return {
            "verdict": "waiting_for_atomic_step",
            "node_id": node["id"],
            "response": node["prompt"],
            "completed": False,
            "facts": sorted(self.established_facts),
        }

    def _evaluate_node_scale_001(self, text: str) -> Dict[str, Any]:
        """Handle the scaling computation node."""
        node = self.nodes_by_id["node_scale_001"]
        normalized = self._normalize(text)

        has_3_24 = ("3x24" in normalized) or ("3*24" in normalized) or ("3 24" in normalized)
        has_4_24 = ("4x24" in normalized) or ("4*24" in normalized) or ("4 24" in normalized)
        has_scale = any(w in normalized for w in ["scale", "multipl", "factor", "24"])
        has_24 = "24" in normalized

        if (has_3_24 and has_4_24) or has_24 or self._matches_any(text, node["accept"]):
            self._record_node(node)
            return {
                "verdict": "atomic_step_accepted",
                "node_id": node["id"],
                "response": "Correct: multiplying 3 and 4 by 24 gives 72 and 96.",
                "completed": False,
                "facts": sorted(self.established_facts),
            }

        return {
            "verdict": "waiting_for_atomic_step",
            "node_id": node["id"],
            "response": node["prompt"],
            "completed": False,
            "facts": sorted(self.established_facts),
        }

    def _evaluate_node_scale_002(self, text: str) -> Dict[str, Any]:
        """Handle the final conclusion for the scaling route."""
        node = self.nodes_by_id["node_scale_002"]
        normalized = self._normalize(text)

        has_prop = ("proport" in normalized) or self._has_keyword(normalized, "proportional") or self._has_keyword(normalized, "proportion")
        is_affirmative_proportional = has_prop and ("not" not in normalized) and ("unequal" not in normalized)
        is_direct_yes = normalized in {"yes", "true", "correct"}

        if self._matches_any(text, node["accept"]) or is_affirmative_proportional or is_direct_yes:
            self._record_node(node)
            self.is_completed = True
            return {
                "verdict": "atomic_step_accepted",
                "node_id": node["id"],
                "response": "Conclusion: the ratios are proportional because one is a scaled version of the other.",
                "completed": True,
                "facts": sorted(self.established_facts),
            }

        return {
            "verdict": "waiting_for_atomic_step",
            "node_id": node["id"],
            "response": node["prompt"],
            "completed": False,
            "facts": sorted(self.established_facts),
        }

    # -------------------------------------------------------------------------
    # Main evaluation loop
    # -------------------------------------------------------------------------
    def evaluate_turn(self, student_input: str) -> Dict[str, Any]:
        """Process one student input against the next incomplete dataset node."""
        text = (student_input or "").strip()

        if not text:
            return {
                "verdict": "empty_input",
                "response": "Please enter a short atomic step.",
                "completed": False,
                "facts": sorted(self.established_facts),
            }

        if self.is_completed:
            return {
                "verdict": "completed",
                "response": "This problem is already complete.",
                "completed": True,
                "facts": sorted(self.established_facts),
            }

        # ─── Filter 1: Noise & Incomplete input check (e.g. "the", "a", "and") ───
        if self._is_noise_or_incomplete(text):
            cur_node = self._next_node()
            prompt = f"\n\nTutor: {cur_node['prompt']}" if cur_node and "prompt" in cur_node else ""
            return {
                "verdict": "noise_or_incomplete",
                "response": f"'{text}' is not a mathematical step or clear response.{prompt}",
                "completed": False,
                "facts": sorted(self.established_facts),
            }

        # ─── Filter 2: Irrelevant true arithmetic check (e.g. "3 + 4 = 7") ───
        irrelevant_msg = self._check_irrelevant_true_claim(text)
        if irrelevant_msg:
            cur_node = self._next_node()
            prompt = f"\n\nTutor: {cur_node['prompt']}" if cur_node and "prompt" in cur_node else ""
            return {
                "verdict": "irrelevant_true",
                "response": f"{irrelevant_msg}{prompt}",
                "completed": False,
                "facts": sorted(self.established_facts),
            }

        # ─── Filter 3: Targeted arithmetic error check (e.g. "3 * 96 = 200") ───
        arith_err_msg = self._check_arithmetic_error(text)
        if arith_err_msg:
            cur_node = self._next_node()
            prompt = f"\n\nTutor: {cur_node['prompt']}" if cur_node and "prompt" in cur_node else ""
            return {
                "verdict": "arithmetic_error",
                "response": f"{arith_err_msg}{prompt}",
                "completed": False,
                "facts": sorted(self.established_facts),
            }

        # ─── Filter 4: Dispatch to current node evaluator ───
        next_node = self._next_node()
        if next_node is None:
            self.is_completed = True
            return {
                "verdict": "completed",
                "response": "All solution nodes are complete. The problem is solved.",
                "completed": True,
                "facts": sorted(self.established_facts),
            }

        node_id = next_node["id"]
        dispatch = {
            "node_001": self._evaluate_node_001,
            "node_002": self._evaluate_node_002,
            "node_003": self._evaluate_node_003,
            "node_crs-mul_001": self._evaluate_node_crs_mul_001,
            "node_crs-mul_002": self._evaluate_node_crs_mul_002,
            "node_sim_001": self._evaluate_node_sim_001,
            "node_sim_002": self._evaluate_node_sim_002,
            "node_scale_001": self._evaluate_node_scale_001,
            "node_scale_002": self._evaluate_node_scale_002,
        }

        handler = dispatch.get(node_id)
        if handler is None:
            return {
                "verdict": "unsupported_node",
                "response": f"No handler is defined for node {node_id}.",
                "completed": False,
                "facts": sorted(self.established_facts),
            }

        result = handler(text)

        # When a step is accepted and problem is not yet done, append the next question
        if result.get("verdict") == "atomic_step_accepted" and not result.get("completed"):
            upcoming_node = self._next_node()
            if upcoming_node and "prompt" in upcoming_node:
                result["response"] = f"{result['response']}\n\nTutor: {upcoming_node['prompt']}"

        return result


# Minimal public alias kept only for compatibility with direct module imports.
verification_engine = VerifyEngine
