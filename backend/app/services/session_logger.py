from __future__ import annotations

import json
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Base logs directory: backend/logs/
LOGS_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
SESSIONS_DIR = LOGS_DIR / "sessions"
ERRORS_FILE = LOGS_DIR / "errors.jsonl"
ALL_TURNS_FILE = LOGS_DIR / "all_turns.jsonl"

_file_lock = threading.Lock()


def _ensure_dirs() -> None:
    """Ensure the logging directories exist."""
    try:
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.warning(f"Failed to create logs directory: {e}")


def init_session_log(session_id: str, problem_meta: Dict[str, Any]) -> None:
    """Create a new session replay JSON file when a problem session begins."""
    try:
        _ensure_dirs()
        now = datetime.now().isoformat()
        session_file = SESSIONS_DIR / f"{session_id}.json"

        data = {
            "session_id": session_id,
            "started_at": now,
            "updated_at": now,
            "problem_id": problem_meta.get("problem_id", ""),
            "problem_title": problem_meta.get("problem_title", ""),
            "chapter": problem_meta.get("chapter", ""),
            "topic": problem_meta.get("topic", ""),
            "grade": problem_meta.get("grade"),
            "completed": False,
            "total_turns": 0,
            "mistakes_count": 0,
            "conversation": [],
        }

        with _file_lock:
            with open(session_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.warning(f"Error initializing session log for {session_id}: {e}")


def log_turn(
    session_id: str,
    turn_record: Dict[str, Any],
    completed: bool = False,
    problem_id: str = "",
) -> None:
    """Log a student turn: update session JSON and append to event/error streams."""
    try:
        _ensure_dirs()
        now = datetime.now().isoformat()
        session_file = SESSIONS_DIR / f"{session_id}.json"

        record_with_time = {
            "timestamp": now,
            **turn_record,
        }

        with _file_lock:
            # 1. Update session JSON file
            session_data = None
            if session_file.exists():
                try:
                    with open(session_file, "r", encoding="utf-8") as f:
                        session_data = json.load(f)
                except Exception:
                    session_data = None

            if not session_data:
                session_data = {
                    "session_id": session_id,
                    "started_at": now,
                    "problem_id": problem_id,
                    "completed": completed,
                    "total_turns": 0,
                    "mistakes_count": 0,
                    "conversation": [],
                }

            session_data["updated_at"] = now
            session_data["completed"] = completed
            session_data["total_turns"] = len(session_data["conversation"]) + 1
            if not turn_record.get("is_correct", False):
                session_data["mistakes_count"] = session_data.get("mistakes_count", 0) + 1

            session_data["conversation"].append(record_with_time)

            with open(session_file, "w", encoding="utf-8") as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)

            # 2. Append to all_turns.jsonl
            all_turns_entry = {
                "timestamp": now,
                "session_id": session_id,
                "problem_id": problem_id or session_data.get("problem_id", ""),
                **turn_record,
            }
            with open(ALL_TURNS_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(all_turns_entry, ensure_ascii=False) + "\n")

            # 3. If mistake / unparsed / wrong claim, append to errors.jsonl
            if not turn_record.get("is_correct", False):
                error_entry = {
                    "timestamp": now,
                    "session_id": session_id,
                    "problem_id": problem_id or session_data.get("problem_id", ""),
                    "turn": turn_record.get("turn"),
                    "input": turn_record.get("input"),
                    "verdict": turn_record.get("verdict"),
                    "active_node_id": turn_record.get("node_id"),
                    "active_label": turn_record.get("label"),
                    "feedback": turn_record.get("feedback"),
                    "explanation": turn_record.get("explanation"),
                    "hint": turn_record.get("hint"),
                }
                with open(ERRORS_FILE, "a", encoding="utf-8") as f:
                    f.write(json.dumps(error_entry, ensure_ascii=False) + "\n")

    except Exception as e:
        logger.warning(f"Error logging turn for session {session_id}: {e}")


def log_session_reset(session_id: str) -> None:
    """Record that a session was reset."""
    try:
        session_file = SESSIONS_DIR / f"{session_id}.json"
        if not session_file.exists():
            return

        with _file_lock:
            with open(session_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            data["reset_at"] = datetime.now().isoformat()
            with open(session_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.warning(f"Error logging reset for session {session_id}: {e}")

