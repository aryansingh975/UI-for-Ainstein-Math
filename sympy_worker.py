"""
sympy_worker.py — long-running SymPy process used by server.js.

Started once by sympyWorker.js. Reads one JSON request per line on stdin:
    {"id": 1, "student_work": "D = 25 - 24 = 1", "equation": "x**2 - 5*x + 6 = 0"}
and writes one JSON response per line on stdout:
    {"id": 1, "result": {...}}   or   {"id": 1, "error": "..."}

Keeping the process alive avoids paying SymPy's ~1 s import time on every request.
"""

import json
import sys

from sympy_validator import validate


def main() -> None:
    sys.stdout.write(json.dumps({"ready": True}) + "\n")
    sys.stdout.flush()
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        req_id = None
        try:
            req = json.loads(line)
            req_id = req.get("id")
            result = validate(str(req.get("student_work", "")), req.get("equation"))
            out = {"id": req_id, "result": result}
        except Exception as e:  # never crash the worker on one bad input
            out = {"id": req_id, "error": f"{type(e).__name__}: {e}"}
        sys.stdout.write(json.dumps(out, ensure_ascii=False) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
