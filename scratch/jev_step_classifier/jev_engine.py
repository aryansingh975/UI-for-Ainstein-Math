"""
Jev Step Classifier Engine (Standalone Lab)
Connects to OpenRouter Jev router to evaluate general classification widgets
and map student inputs to specific step nodes in Method 1.
"""
from __future__ import annotations

import json
import os
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any, Dict, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def get_api_key() -> str:
    """Retrieve OPENROUTER_API_KEY from environment or .env file."""
    key = os.getenv("OPENROUTER_API_KEY", "")
    if key:
        return key
    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("OPENROUTER_API_KEY="):
                return line.split("=", 1)[1].strip()
    return ""


def load_method_1_context() -> Dict[str, Any]:
    """Load the Age Problem graph and extract Method 1 nodes."""
    graph_path = PROJECT_ROOT / "solution_graph" / "chapter-11" / "algebra-play" / "g08-hegp206-age-q7" / "graph.json"
    if not graph_path.exists():
        raise FileNotFoundError(f"Graph file not found at: {graph_path}")

    with open(graph_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    problem_text = data.get("graph_meta", {}).get("problem_text", "")
    
    # Extract only Method 1 step nodes
    method_1_steps: Dict[str, str] = {}
    for node in data.get("nodes", []):
        if node.get("id", "").startswith("m1_step"):
            method_1_steps[node["id"]] = f"{node.get('label')}: {node.get('description')}"

    return {
        "problem_text": problem_text,
        "method_name": "Method 1: Linear Equation (Daughter = x)",
        "method_steps": method_1_steps
    }


def classify_student_input(student_input: str) -> Dict[str, Any]:
    """
    Executes the 5 General Classification Widgets via Jev:
    1. has_numerical_values (bool)
    2. has_variables (bool)
    3. operation_type (choice)
    4. completeness (complete, partial, clubbed_multi_step, off_track)
    5. target_step_node (m1_step1, m1_step2, m1_step3, m1_step4, off_step)
    """
    api_key = get_api_key()
    if not api_key:
        return {
            "error": "OPENROUTER_API_KEY not found in .env file.",
            "success": False
        }

    ctx = load_method_1_context()

    prompt_payload = {
        "model": "jev",
        "state": {
            "problem": ctx["problem_text"],
            "active_method": ctx["method_name"],
            "method_steps": ctx["method_steps"],
            "student_input": student_input.strip()
        },
        "general_classification_widgets": {
            "has_numerical_values": {
                "type": "boolean",
                "question": "Does the student input contain specific numerical values?"
            },
            "has_variables": {
                "type": "boolean",
                "question": "Does the student input contain algebraic variables (e.g., x)?"
            },
            "operation_type": {
                "type": "choice",
                "options": ["none", "arithmetic", "algebraic_expression", "equation_solving", "final_answer"],
                "question": "What mathematical structure or operation does this input represent?"
            },
            "completeness": {
                "type": "choice",
                "options": ["complete", "partial", "clubbed_multi_step", "off_track"],
                "question": (
                    "Completeness definition relative to the target step:\n"
                    "- 'complete': The input fully answers what the target step asks (e.g., for m1_step1: '5x' or 'mother = 5x'; for m1_step2: both x+6 and 5x+6; for m1_step3: setting up the equation, simplifying, or giving x=6; for m1_step4: daughter's age is 6).\n"
                    "- 'partial': Only part of the required step is present (e.g. in m1_step2, only giving one person's age instead of both).\n"
                    "- 'clubbed_multi_step': The input covers content spanning across more than one step node (e.g. contains both Step 1 '5x' and Step 2 'x+6, 5x+6').\n"
                    "- 'off_track': Input does not belong to any valid step node."
                )
            },
            "target_step_node": {
                "type": "choice",
                "options": ["m1_step1", "m1_step2", "m1_step3", "m1_step4", "off_step"],
                "question": "Which step node in Method 1 does this input primarily belong to or advance?"
            }
        }
    }

    schema = {
        "type": "object",
        "properties": {
            "has_numerical_values": {"type": "boolean"},
            "has_variables": {"type": "boolean"},
            "operation_type": {
                "type": "string",
                "enum": ["none", "arithmetic", "algebraic_expression", "equation_solving", "final_answer"]
            },
            "completeness": {
                "type": "string",
                "enum": ["complete", "partial", "clubbed_multi_step", "off_track"]
            },
            "target_step_node": {
                "type": "string",
                "enum": ["m1_step1", "m1_step2", "m1_step3", "m1_step4", "off_step"]
            },
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "missing_elements": {
                "type": "string",
                "description": "If partial, specify what is missing. Otherwise empty string."
            },
            "explanation": {
                "type": "string",
                "description": "Brief pedagogical rationale explaining why this step node was selected."
            }
        },
        "required": [
            "has_numerical_values",
            "has_variables",
            "operation_type",
            "completeness",
            "target_step_node",
            "confidence",
            "missing_elements",
            "explanation"
        ],
        "additionalProperties": False
    }

    req_body = {
        "model": "typesafe/jev-router",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are Jev, a high-precision mathematical step and widget classifier. "
                    "Analyze the student input against the Method 1 step nodes. "
                    "Classify each general widget question accurately and return strictly valid JSON conforming to the schema."
                )
            },
            {"role": "user", "content": json.dumps(prompt_payload)}
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "jev_general_widgets_classification",
                "strict": True,
                "schema": schema
            }
        },
        "temperature": 0.0,
        "max_tokens": 300
    }

    data_bytes = json.dumps(req_body).encode("utf-8")
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        data=data_bytes
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw_response = resp.read().decode("utf-8")
            res_json = json.loads(raw_response)
            content = res_json["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            parsed["success"] = True
            return parsed
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8") if e.fp else str(e)
        return {"success": False, "error": f"HTTPError {e.code}: {err_msg}"}
    except Exception as e:
        return {"success": False, "error": str(e)}
