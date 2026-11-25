"""Method Identification Waterfall Engine.

STRICT SCOPE BOUNDARY:
Local JEV and Global JEV are strictly and exclusively for Method Identification.
They NEVER validate mathematical correctness or grade student steps.

Waterfall order:
  1. Socratic Navigator (step-node match or method-node match)
  2. Local JEV (offline method_classifier.classify_graph)
  3. Global JEV (OpenRouter typesafe/jev-router API call)
  4. None (caller triggers Socratic prompt asking the student which method to use)
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional

from app.schemas.graph import SolutionGraph
from app.engine.method_classifier import classify_graph
from app.engine.navigator_bridge import navigator_resolve_nodes
from app.engine.llm_verifier import _post_openrouter, get_openrouter_api_key

GLOBAL_JEV_MODEL = "typesafe/jev-router"


def _should_call_global_jev() -> bool:
    if os.getenv("PYTEST_CURRENT_TEST") and os.getenv("AINSTEIN_ENABLE_GLOBAL_JEV") != "1":
        return False
    return bool(get_openrouter_api_key())


def classify_method_global_jev(raw_input: str, graph: SolutionGraph) -> Optional[Dict[str, Any]]:
    """Call Global JEV via OpenRouter strictly to identify which solution method the student intends."""
    if not raw_input or not raw_input.strip() or not _should_call_global_jev():
        return None

    method_nodes = [n for n in graph.nodes if n.type == "method"]
    if not method_nodes:
        return None

    method_ids = [m.id for m in method_nodes]
    method_catalog = [
        {
            "method_id": m.id,
            "label": getattr(m, "label", "") or m.id,
            "description": getattr(m, "description", "") or "",
            "examples": list(getattr(m, "accept", None) or [])[:5],
        }
        for m in method_nodes
    ]

    schema = {
        "type": "object",
        "properties": {
            "status": {"type": "string", "enum": ["selected", "uncertain"]},
            "method_id": {"type": ["string", "null"]},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "reason": {"type": "string"},
        },
        "required": ["status", "method_id", "confidence", "reason"],
        "additionalProperties": False,
    }

    payload = {
        "problem_text": (graph.graph_meta and graph.graph_meta.problem_text) or "",
        "available_methods": method_catalog,
        "student_input": raw_input.strip(),
    }

    req_body = {
        "model": os.getenv("AINSTEIN_GLOBAL_JEV_MODEL", GLOBAL_JEV_MODEL),
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are Jev, a strict mathematical approach classifier. "
                    "Your ONLY job is to identify WHICH solution method from available_methods the student "
                    "is declaring or intending to use. Do NOT grade correctness. "
                    "If the student's statement is ambiguous, unrelated, or just a bare final answer, "
                    "return status='uncertain' and method_id=null."
                ),
            },
            {"role": "user", "content": json.dumps(payload)},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "global_jev_method_identification",
                "strict": True,
                "schema": schema,
            },
        },
        "temperature": 0.0,
        "max_tokens": 180,
    }

    try:
        res = _post_openrouter(req_body)
        mid = res.get("method_id")
        if (
            res.get("status") == "selected"
            and mid in method_ids
            and float(res.get("confidence", 0.0)) >= 0.70
        ):
            return {
                "method_id": mid,
                "source": "global_jev",
                "confidence": float(res.get("confidence", 0.0)),
                "reason": str(res.get("reason", "")),
            }
    except Exception:
        return None
    return None


def resolve_method_waterfall(raw_input: str, graph: SolutionGraph) -> Optional[Dict[str, Any]]:
    """Run the Method Identification Waterfall (Navigator Method Nodes -> Local JEV -> Global JEV).

    Note: Step-node identification (e.g. matching 'm1_step1' -> 'method1') already happens
    upstream in Socratic Navigator & Qwen step matching before this fallback is reached.
    """
    method_nodes = [n for n in graph.nodes if n.type == "method"]
    if not method_nodes:
        return None
    valid_method_ids = {m.id for m in method_nodes}

    # Tier 1b: Navigator Jaccard/Exact match against method declaration nodes
    nav_match = navigator_resolve_nodes(raw_input, method_nodes, threshold=0.70)
    if nav_match:
        m_node, m_res = nav_match
        return {
            "method_id": m_node.id,
            "source": m_res.get("source", "navigator"),
            "confidence": float(m_res.get("score", 1.0)),
        }

    # Tier 2: Local JEV (offline heuristic classifier)
    try:
        local_res = classify_graph(graph, raw_input)
        local_mid = local_res.get("methodId") or local_res.get("methodKey")
        if local_res.get("status") == "selected" and local_mid in valid_method_ids:
            return {
                "method_id": local_mid,
                "source": "local_jev",
                "confidence": float(local_res.get("confidence", 0.75)),
            }
    except Exception:
        pass

    # Tier 3: Global JEV via OpenRouter API (only if input contains words/intent)
    if re.search(r"[a-zA-Z]{2,}", raw_input or ""):
        global_res = classify_method_global_jev(raw_input, graph)
        if global_res:
            return global_res

    return None
