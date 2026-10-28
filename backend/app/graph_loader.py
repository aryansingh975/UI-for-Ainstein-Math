from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from app.schemas.graph import SolutionGraph

# Global cache of loaded solution graphs: problem_uuid -> SolutionGraph
_GRAPH_CACHE: Dict[str, SolutionGraph] = {}

# Default solution graph root relative to this file
_DEFAULT_ROOT = Path(__file__).resolve().parent.parent.parent / "solution_graph"


def find_graph_files(root_dir: Optional[Path] = None) -> List[Path]:
    """Recursively search for all graph.json files."""
    root = root_dir or _DEFAULT_ROOT
    if not root.exists():
        return []
    return sorted(list(root.glob("**/graph.json")))


def load_all_graphs(root_dir: Optional[Path] = None, force_reload: bool = False) -> Dict[str, SolutionGraph]:
    """Load and validate all graph.json files into memory."""
    global _GRAPH_CACHE
    if _GRAPH_CACHE and not force_reload:
        return _GRAPH_CACHE

    loaded: Dict[str, SolutionGraph] = {}
    graph_files = find_graph_files(root_dir)

    for file_path in graph_files:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        graph = SolutionGraph.model_validate(data)
        uuid = graph.graph_meta.problem_uuid
        loaded[uuid] = graph

    _GRAPH_CACHE = loaded
    return _GRAPH_CACHE


def get_graph(problem_uuid: str) -> Optional[SolutionGraph]:
    """Retrieve a solution graph by problem UUID."""
    if not _GRAPH_CACHE:
        load_all_graphs()
    return _GRAPH_CACHE.get(problem_uuid)


def list_problems() -> List[Dict[str, str]]:
    """List summary information for all loaded problems."""
    if not _GRAPH_CACHE:
        load_all_graphs()
    
    result = []
    for uuid, graph in _GRAPH_CACHE.items():
        meta = graph.graph_meta
        ctx = meta.problem_context or {}
        result.append({
            "problem_uuid": uuid,
            "navigation_label": meta.navigation_label or uuid,
            "problem_text": meta.problem_text,
            "chapter": str(ctx.get("chapter", "")),
            "topic": str(ctx.get("topic", "")),
            "grade": str(ctx.get("grade", ""))
        })
    return result

