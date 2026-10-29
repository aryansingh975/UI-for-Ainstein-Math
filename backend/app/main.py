from __future__ import annotations

import json
import os
from contextlib import asynccontextmanager
from pathlib import Path
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1 import api_v1_router
from app.graph_loader import load_all_graphs

# Path to the root project directory containing index.html, styles.css, app.js
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Warm up the graph cache on server start."""
    load_all_graphs()
    yield


app = FastAPI(
    title="Ainstein Socratic Math Tutor API",
    version="1.0.0",
    description="Deterministic Socratic Math Tutor Backend with DAG traversal and step verification.",
    lifespan=lifespan,
)

# Enable CORS for local development and multi-client access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API v1 routes
app.include_router(api_v1_router)


# Jev Method Classification (OpenRouter + Deterministic Fallback)
METHODS = {
    "factoring": {"nodeId": "m1_factor", "description": "Factor the quadratic, then set each factor equal to zero."},
    "quadratic_formula": {"nodeId": "m2_formula", "description": "Use the quadratic formula."},
    "completing_the_square": {"nodeId": "m3_square", "description": "Complete the square."},
    "graphical": {"nodeId": "m4_graph", "description": "Graph the quadratic and read its x-intercepts."},
    "sum_and_product_of_roots": {"nodeId": "m5_vieta", "description": "Use the sum and product of the roots."},
    "trial_and_factor_theorem": {"nodeId": "m6_trial", "description": "Test possible roots and use the factor theorem."}
}


def _get_api_key() -> str:
    key = os.getenv("OPENROUTER_API_KEY", "")
    if not key:
        env_file = PROJECT_ROOT / ".env"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("OPENROUTER_API_KEY="):
                    key = line.split("=", 1)[1].strip()
                    break
    return key


@app.post("/api/jev/method")
async def jev_method_endpoint(req: dict):
    problem_id = req.get("problemId")
    student_work = str(req.get("studentWork", "")).strip()

    if not student_work:
        return {"status": "invalid_request", "message": "Student work required."}

    api_key = _get_api_key()
    if api_key:
        try:
            task = {
                "model": "jev",
                "state": {"problem": "Solve the quadratic equation x^2 - 5x + 6 = 0.", "student_work": student_work},
                "questions": {
                    "method": {
                        "type": "choice",
                        "question": "Which solution method is the student using?",
                        "options": {k: v["description"] for k, v in METHODS.items()}
                    },
                    "off_graph": {
                        "type": "noul",
                        "question": "Is the student using a solution method that is not listed in the method options?"
                    }
                }
            }
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={
                        "model": "typesafe/jev-router",
                        "messages": [
                            {"role": "system", "content": "Classify the method shown by the student work. Return JSON with method, confidence, off_graph."},
                            {"role": "user", "content": json.dumps(task)}
                        ],
                        "response_format": {
                            "type": "json_schema",
                            "json_schema": {
                                "name": "jev_method_classification",
                                "strict": True,
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "method": {"type": "string", "enum": list(METHODS.keys())},
                                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                                        "off_graph": {"type": "boolean"}
                                    },
                                    "required": ["method", "confidence", "off_graph"],
                                    "additionalProperties": False
                                }
                            }
                        },
                        "temperature": 0,
                        "max_tokens": 200
                    }
                )
                if res.status_code == 200:
                    data = res.json()
                    content = data["choices"][0]["message"]["content"]
                    parsed = json.loads(content)
                    if parsed.get("off_graph"):
                        return {"status": "off_graph", "confidence": parsed.get("confidence", 1.0)}
                    m_key = parsed.get("method")
                    if m_key in METHODS and parsed.get("confidence", 0) >= 0.7:
                        return {
                            "status": "selected",
                            "methodKey": m_key,
                            "methodId": METHODS[m_key]["nodeId"],
                            "confidence": parsed["confidence"]
                        }
                    return {"status": "uncertain"}
        except Exception:
            pass

    # Deterministic fallback if offline or no key
    sw_lower = student_work.lower()
    if any(k in sw_lower for k in ["factor", "(x-", "(x -", "(x+", "(x +"]):
        return {"status": "selected", "methodKey": "factoring", "methodId": "m1_factor", "confidence": 1.0}
    if any(k in sw_lower for k in ["formula", "sqrt", "b^2", "4ac", "+-", "±"]):
        return {"status": "selected", "methodKey": "quadratic_formula", "methodId": "m2_formula", "confidence": 1.0}
    if any(k in sw_lower for k in ["square", "(x-5/2)", "(x - 5/2)"]):
        return {"status": "selected", "methodKey": "completing_the_square", "methodId": "m3_square", "confidence": 1.0}

    return {"status": "uncertain"}


# Path to modern React frontend build, fallback to root if not built yet
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"
STATIC_DIR = FRONTEND_DIST if FRONTEND_DIST.exists() else PROJECT_ROOT


# Serve root index.html
@app.get("/", include_in_schema=False)
def serve_index():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "Ainstein Socratic Math Tutor API is running."}


# Mount static files so React bundled assets or root assets load seamlessly
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
