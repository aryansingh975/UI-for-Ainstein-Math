"""LLM Semantic Verifier (Qwen 3.5 via OpenRouter API).

Fallback verification engine for Given, Goal (To Find), and Step nodes
whenever the deterministic Socratic Navigator (SymPy -> Exact -> Jaccard)
cannot verify the student's phrasing or mathematical representation.

Note: Never runs network calls during pytest unless explicitly enabled via
AINSTEIN_ENABLE_LLM_VERIFIER=1 or mocked in tests.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.schemas.graph import Node

OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_QWEN_MODEL = "qwen/qwen3.5-flash-02-23"
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def get_openrouter_api_key() -> str:
    """Retrieve OPENROUTER_API_KEY from environment or project .env file."""
    key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if key:
        return key
    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if line.startswith("OPENROUTER_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def _should_call_remote_llm() -> bool:
    """Return True if an API key is available and remote LLM calls are allowed."""
    if os.getenv("PYTEST_CURRENT_TEST") and os.getenv("AINSTEIN_ENABLE_LLM_VERIFIER") != "1":
        return False
    return bool(get_openrouter_api_key())


def _post_openrouter(payload: Dict[str, Any], timeout: float = 8.0) -> Dict[str, Any]:
    """Send a chat completion request to OpenRouter and parse the JSON content."""
    api_key = get_openrouter_api_key()
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not configured")

    req = urllib.request.Request(
        OPENROUTER_CHAT_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://ainstein.local",
            "X-Title": "Ainstein Socratic Math Tutor",
        },
        data=json.dumps(payload).encode("utf-8"),
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
    data = json.loads(raw)
    content = data["choices"][0]["message"]["content"]
    return json.loads(content)


def verify_node_with_qwen(
    raw_input: str,
    node: Node,
    problem_text: str,
    node_role: str = "step",
) -> Optional[Dict[str, Any]]:
    """Verify whether raw_input semantically/mathematically satisfies a single node using Qwen 3.5.

    Returns {"accepted": True, "source": "qwen-3.5", "confidence": float, "reason": str}
    if verified, or None on uncertainty/rejection/failure.
    """
    if not raw_input or not raw_input.strip() or not _should_call_remote_llm():
        return None

    schema = {
        "type": "object",
        "properties": {
            "is_valid": {"type": "boolean"},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "reason": {"type": "string"},
        },
        "required": ["is_valid", "confidence", "reason"],
        "additionalProperties": False,
    }

    user_payload = {
        "problem_text": problem_text,
        "node_id": node.id,
        "node_role": node_role,
        "node_label": getattr(node, "label", "") or "",
        "node_description": getattr(node, "description", "") or "",
        "node_prompt": getattr(node, "prompt", "") or "",
        "accepted_examples": list(node.accept or [])[:8],
        "student_input": raw_input.strip(),
    }

    req_body = {
        "model": os.getenv("AINSTEIN_QWEN_MODEL", DEFAULT_QWEN_MODEL),
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a strict yet fair NCERT Mathematics Socratic step verifier. "
                    "Decide whether the student's input accurately and validly states the requested "
                    "node_role (given, goal, or mathematical step) for the given problem, even if phrased "
                    "in informal English or an equivalent algebraic form. "
                    "Do NOT mark wrong arithmetic, reversed ratios, or unrelated text as valid. "
                    "If the student jumped straight to a later calculation or final answer when the target "
                    "is an earlier step, only mark is_valid=true if it matches THIS specific target node."
                ),
            },
            {"role": "user", "content": json.dumps(user_payload)},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "qwen_node_verification",
                "strict": True,
                "schema": schema,
            },
        },
        "temperature": 0.0,
        "max_tokens": 180,
    }

    try:
        parsed = _post_openrouter(req_body)
        if parsed.get("is_valid") is True and float(parsed.get("confidence", 0.0)) >= 0.75:
            return {
                "accepted": True,
                "source": "qwen-3.5",
                "confidence": float(parsed.get("confidence", 0.0)),
                "reason": str(parsed.get("reason", "")),
            }
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError, ValueError, Exception):
        return None
    return None


def verify_candidates_with_qwen(
    raw_input: str,
    candidates: List[Node],
    problem_text: str,
) -> Optional[Tuple[Node, Dict[str, Any]]]:
    """Identify and verify which candidate step node (if any) raw_input fulfills using Qwen 3.5."""
    if not raw_input or not raw_input.strip() or not candidates or not _should_call_remote_llm():
        return None

    candidate_ids = [c.id for c in candidates]
    schema = {
        "type": "object",
        "properties": {
            "matched_node_id": {"type": ["string", "null"]},
            "is_valid": {"type": "boolean"},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "reason": {"type": "string"},
        },
        "required": ["matched_node_id", "is_valid", "confidence", "reason"],
        "additionalProperties": False,
    }

    candidate_summaries = [
        {
            "id": n.id,
            "label": getattr(n, "label", "") or "",
            "description": getattr(n, "description", "") or "",
            "accepted_examples": list(n.accept or [])[:5],
        }
        for n in candidates[:12]
    ]

    user_payload = {
        "problem_text": problem_text,
        "student_input": raw_input.strip(),
        "candidate_nodes": candidate_summaries,
    }

    req_body = {
        "model": os.getenv("AINSTEIN_QWEN_MODEL", DEFAULT_QWEN_MODEL),
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a strict NCERT Mathematics Socratic step matcher. "
                    "Given a student's step and candidate DAG step nodes, determine whether the student's "
                    "input accurately fulfills one specific candidate node. "
                    "If the math is wrong or unrelated, return is_valid=false and matched_node_id=null."
                ),
            },
            {"role": "user", "content": json.dumps(user_payload)},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "qwen_candidate_verification",
                "strict": True,
                "schema": schema,
            },
        },
        "temperature": 0.0,
        "max_tokens": 200,
    }

    try:
        parsed = _post_openrouter(req_body)
        nid = parsed.get("matched_node_id")
        if (
            parsed.get("is_valid") is True
            and float(parsed.get("confidence", 0.0)) >= 0.75
            and nid in candidate_ids
        ):
            matched_node = next(c for c in candidates if c.id == nid)
            return matched_node, {
                "accepted": True,
                "source": "qwen-3.5",
                "confidence": float(parsed.get("confidence", 0.0)),
                "reason": str(parsed.get("reason", "")),
            }
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError, ValueError, Exception):
        return None
    return None
