from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from app.schemas.graph import SolutionGraph, Node


class Session:
    def __init__(self, current_node_id: Optional[str] = None):
        self.trail: List[Dict[str, Any]] = []
        self.history: List[Dict[str, Any]] = []
        self.current_node_id: Optional[str] = current_node_id
        self.method_id: Optional[str] = None
        self.fail_streak: int = 0
        self.completed: bool = False
        self.raw_input: Optional[str] = None


def new_session(graph: SolutionGraph) -> Session:
    """Create a new session respecting required Pólya extraction."""
    initial_node_id: Optional[str] = None
    node_map = {n.id: n for n in graph.nodes}
    given_ext = node_map.get("given_extraction")
    if given_ext and given_ext.optional is False:
        initial_node_id = "given_extraction"
    return Session(current_node_id=initial_node_id)


def method_of(node_id: Optional[str]) -> Optional[str]:
    """Extract method prefix (e.g. 'm1' from 'm1_step1' or 'method1' from 'method1_s1')."""
    if not node_id:
        return None
    m = re.match(r"^(m\d+)_", str(node_id))
    if m:
        return m.group(1)
    m2 = re.match(r"^(method\d+)", str(node_id))
    if m2:
        return m2.group(1)
    return None


def method_for_node(node_id: Optional[str], graph: Optional[SolutionGraph] = None) -> Optional[str]:
    """Determine method identifier for a given node id using prefix or DAG ancestry."""
    if not node_id:
        return None
    m = method_of(node_id)
    if m:
        return m
    if graph:
        node_map = {n.id: n for n in graph.nodes}
        cur = node_map.get(node_id)
        if cur and cur.type == "method":
            return method_of(cur.id) or cur.id
        visited = set()
        queue = [node_id]
        while queue:
            curr_id = queue.pop(0)
            if curr_id in visited:
                continue
            visited.add(curr_id)
            for e in graph.edges:
                if e.to_node == curr_id:
                    parent_node = node_map.get(e.from_node)
                    if parent_node and parent_node.type == "method":
                        return method_of(parent_node.id) or parent_node.id
                    if parent_node and parent_node.type == "step":
                        queue.append(parent_node.id)
    return None


def method_index_of(node_id: Optional[str]) -> Optional[str]:
    """Extract numeric method index (e.g. '1' from 'm1', 'method1', or 'm1_s1')."""
    if not node_id:
        return None
    m = re.search(r"(?:m|method)(\d+)", str(node_id))
    return m.group(1) if m else None


def get_method_node(method_id: Optional[str], graph: Optional[SolutionGraph]) -> Optional[Node]:
    """Retrieve the method junction Node object from graph by id or method prefix."""
    if not method_id or not graph:
        return None
    node_map = {n.id: n for n in graph.nodes}
    direct = node_map.get(method_id)
    if direct and direct.type == "method":
        return direct
    idx = method_index_of(method_id)
    return next(
        (
            n for n in graph.nodes
            if n.type == "method"
            and (
                n.id == method_id
                or method_of(n.id) == method_id
                or n.id.startswith(f"{method_id}_")
                or (idx and method_index_of(n.id) == idx)
                or method_for_node(n.id, graph) == method_id
            )
        ),
        None,
    )


def successor_of(node_id: Optional[str], graph: SolutionGraph) -> Optional[str]:
    """Find the next DAG node. goal_extraction branches so it returns None.
    Bypasses internal method junction nodes directly to their first calculation step."""
    if not node_id:
        return None
    if node_id == "goal_extraction":
        return None
    edges = [e for e in graph.edges if e.from_node == node_id]
    if not edges:
        return graph.conclusion_node
    nxt = edges[0].to_node
    node_map = {n.id: n for n in graph.nodes}
    if nxt in node_map and node_map[nxt].type == "method":
        return first_step_of(nxt, graph)
    return nxt


def first_step_of(method_id: str, graph: SolutionGraph) -> str:
    """Get the first calculation step node of a method."""
    mn = get_method_node(method_id, graph)
    src: Optional[str] = mn.id if mn else method_id

    if not src:
        return graph.conclusion_node
    edges = [e for e in graph.edges if e.from_node == src]
    return edges[0].to_node if edges else graph.conclusion_node


def method_chain(method_id: str, graph: SolutionGraph) -> List[str]:
    """Return the sequential chain of node IDs for a method."""
    mn = get_method_node(method_id, graph)
    start_id = mn.id if mn else method_id
    chain: List[str] = []
    cur: Optional[str] = start_id
    seen = set()
    while cur and cur not in seen:
        seen.add(cur)
        chain.append(cur)
        cur = successor_of(cur, graph)
        if cur == graph.conclusion_node:
            break
    return chain


def has_completed_required_extraction(session: Session, graph: SolutionGraph) -> bool:
    """Check if required Pólya extractions have been satisfied in order."""
    node_map = {n.id: n for n in graph.nodes}
    given_ext = node_map.get("given_extraction")
    goal_ext = node_map.get("goal_extraction")
    if not given_ext or not goal_ext:
        return True
    if given_ext.optional is not False or goal_ext.optional is not False:
        return True

    given_idx = -1
    goal_idx = -1
    for i, t in enumerate(session.trail):
        if t.get("nodeId") == "given_extraction":
            given_idx = i
        if t.get("nodeId") == "goal_extraction":
            goal_idx = i
    return given_idx >= 0 and goal_idx > given_idx


def begin_method(session: Session, method_node_id: str, graph: SolutionGraph) -> bool:
    """Explicitly lock in a method."""
    node_map = {n.id: n for n in graph.nodes}
    node = node_map.get(method_node_id)
    if not session or session.completed or session.method_id or not node or node.type != "method":
        return False

    if not has_completed_required_extraction(session, graph):
        return False

    first_step = first_step_of(method_node_id, graph)
    if first_step == graph.conclusion_node:
        return False

    session.method_id = method_of(method_node_id) or method_node_id
    session.current_node_id = first_step
    return True


def apply_result(session: Session, result: Any, graph: SolutionGraph) -> Session:
    """Advance session state based on step evaluation verdict."""
    verdict = result.verdict
    if verdict == "ACCEPT":
        session.fail_streak = 0
        if result.approach_only:
            session.method_id = method_of(result.method_id) or result.method_id
            session.current_node_id = first_step_of(session.method_id, graph)
        else:
            session.trail.append({
                "input": result.parsed.raw,
                "nodeId": result.node_id,
                "methodId": result.method_id
            })
            if result.method_id:
                session.method_id = result.method_id
            session.current_node_id = successor_of(result.node_id, graph)
    elif verdict == "WRONG_CLAIM":
        session.fail_streak += 1
    elif verdict == "CONCLUSION_RIGHT":
        session.completed = True

    return session


def hint_for(session: Session, graph: SolutionGraph, node_id: Optional[str] = None) -> Optional[str]:
    """Retrieve cyclic hint for a node based on the student's fail streak."""
    target_id = node_id or session.current_node_id
    if not target_id:
        return None
    node_map = {n.id: n for n in graph.nodes}
    node = node_map.get(target_id)
    if node and node.hints:
        idx = session.fail_streak % len(node.hints)
        return node.hints[idx]
    return None

