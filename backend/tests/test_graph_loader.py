from pathlib import Path
import pytest
from app.graph_loader import find_graph_files, load_all_graphs, get_graph, list_problems


def test_finds_all_32_graph_files():
    files = find_graph_files()
    assert len(files) == 32, f"Expected 32 graph.json files, found {len(files)}"


def test_loads_all_32_graphs_through_pydantic():
    graphs = load_all_graphs(force_reload=True)
    assert len(graphs) == 32, f"Expected 32 parsed graphs, got {len(graphs)}"

    for uuid, graph in graphs.items():
        assert graph.graph_meta.problem_uuid == uuid
        assert graph.graph_meta.problem_text.strip() != ""
        assert len(graph.nodes) > 0
        assert len(graph.edges) > 0


def test_universal_graph_invariants():
    graphs = load_all_graphs()

    for uuid, graph in graphs.items():
        node_map = {node.id: node for node in graph.nodes}

        # 1. Start and conclusion nodes exist
        assert graph.start_node in node_map, f"[{uuid}] start_node '{graph.start_node}' missing from nodes"
        assert graph.conclusion_node in node_map, f"[{uuid}] conclusion_node '{graph.conclusion_node}' missing from nodes"

        # 2. Required extraction nodes exist
        assert "given_extraction" in node_map, f"[{uuid}] 'given_extraction' node missing"
        assert "goal_extraction" in node_map, f"[{uuid}] 'goal_extraction' node missing"

        # 3. All edges connect existing nodes
        for edge in graph.edges:
            assert edge.from_node in node_map, f"[{uuid}] Edge source '{edge.from_node}' does not exist"
            assert edge.to_node in node_map, f"[{uuid}] Edge target '{edge.to_node}' does not exist"

        # 4. At least one method node exists
        methods = [n for n in graph.nodes if n.type == "method"]
        assert len(methods) >= 1, f"[{uuid}] Must have at least 1 method node"

        # 5. Conclusion reachability via BFS from start_node
        outgoing = {}
        for edge in graph.edges:
            outgoing.setdefault(edge.from_node, []).append(edge.to_node)

        visited = set()
        queue = [graph.start_node]
        while queue:
            cur = queue.pop(0)
            if cur not in visited:
                visited.add(cur)
                for nxt in outgoing.get(cur, []):
                    if nxt not in visited:
                        queue.append(nxt)

        assert graph.conclusion_node in visited, f"[{uuid}] conclusion_node '{graph.conclusion_node}' is unreachable from start!"


def test_get_graph_and_list_problems():
    graphs = load_all_graphs()
    first_uuid = list(graphs.keys())[0]

    graph = get_graph(first_uuid)
    assert graph is not None
    assert graph.graph_meta.problem_uuid == first_uuid

    problem_list = list_problems()
    assert len(problem_list) == 32
    assert any(p["problem_uuid"] == first_uuid for p in problem_list)

