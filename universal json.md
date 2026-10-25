# Universal Solution Graph Contract

**Status:** Canonical contract for every solution graph in `solution_graph/`.

This document defines the one structure used by every chapter and every new
problem. A problem may be a direct calculation or a contextual word problem,
but its graph file shape never changes.

## 1. Required files and folder layout

Each problem has one canonical folder:

```text
solution_graph/chapter-X/topic/problem-uuid/
  graph.json
  graph.js
  graph.svg
```

- `graph.json` is the portable source of truth.
- `graph.js` registers the exact same graph object in `window.SOLUTION_GRAPHS`.
- `graph.svg` is the visual representation for the same problem.

All three files must be co-located. `graph.js` must contain data equivalent to
`graph.json`; it must not be independently edited to a different graph.

## 2. Required root structure

Every `graph.json` must contain these fields:

```json
{
  "graph_meta": {},
  "start_node": "start",
  "conclusion_node": "conclusion",
  "nodes": [],
  "edges": []
}
```

`graph_meta` must contain:

```json
{
  "graph_id": "unique stable graph id",
  "problem_uuid": "unique stable problem id",
  "problem_text": "student-facing problem statement",
  "navigation_label": "short display title",
  "problem_context": {},
  "graph_type": "directed_acyclic_graph",
  "version": "semantic version string",
  "description": "graph summary",
  "created": "YYYY-MM-DD",
  "total_methods": 0,
  "total_nodes": 0,
  "total_edges": 0
}
```

The three total fields must equal the actual number of method nodes, nodes,
and edges in the graph.

## 3. Required node contract

Every node must contain:

```json
{
  "id": "unique node id",
  "type": "start | extraction | method | step | conclusion",
  "label": "short UI label",
  "description": "purpose of this node",
  "prompt": "student-facing tutor question",
  "accept": ["accepted response"],
  "hints": ["progressive hint"]
}
```

The graph must contain these fixed IDs:

| ID | Required type | Purpose |
|---|---|---|
| `start` | `start` | Entry point for the problem. |
| `given_extraction` | `extraction` | Identify relevant given information. |
| `goal_extraction` | `extraction` | Identify what the student must find. |
| `conclusion` | `conclusion` | Verify or state the final answer. |

Each extraction node must additionally declare either `"optional": true` or
`"optional": false`. Both extraction nodes for one problem must use the same
value. Additional metadata fields are allowed, but they cannot replace any
required field.

## 4. Extraction-path rules

Both extraction nodes always exist. The `optional` value controls graph
topology and future tutor-engine behavior.

### Required extraction

Use `"optional": false` when the problem is a word problem or needs students
to identify quantities, relationships, units, or the goal before solving.

```text
start -> given_extraction -> goal_extraction -> method
```

There must be no direct `start -> method` bypass edge.

### Optional extraction

Use `"optional": true` when the problem is direct and its givens and goal are
already obvious from the expression or equation.

Guided route:

```text
start -> given_extraction -> goal_extraction -> method
```

Required bypass route:

```text
start -> method
```

Every method that can be selected after `goal_extraction` must also be
available through a direct edge from `start`.

## 5. Edge rules

Every edge must contain valid `from` and `to` node IDs. The graph must be a
DAG, every node must be reachable from `start`, and `conclusion` must be
reachable from `start`.

## 6. Validation rules

Run the contract validator after any graph change:

```powershell
node test_universal_graph_structure.js
```

It checks JSON shape, required metadata, node IDs/types, extraction rules,
edge validity, reachability, metadata totals, co-located assets, and JSON/JS
synchronization. The command exits with a non-zero code until every violation
is fixed.

## 7. Minimal required-extraction example

```json
{
  "start_node": "start",
  "conclusion_node": "conclusion",
  "nodes": [
    { "id": "start", "type": "start" },
    { "id": "given_extraction", "type": "extraction", "optional": false },
    { "id": "goal_extraction", "type": "extraction", "optional": false },
    { "id": "method_system", "type": "method" },
    { "id": "step_1", "type": "step" },
    { "id": "conclusion", "type": "conclusion" }
  ],
  "edges": [
    { "from": "start", "to": "given_extraction" },
    { "from": "given_extraction", "to": "goal_extraction" },
    { "from": "goal_extraction", "to": "method_system" },
    { "from": "method_system", "to": "step_1" },
    { "from": "step_1", "to": "conclusion" }
  ]
}
```

`example_universal_structure.json` is the complete required-extraction
example. `example_universal_structure_optional_extraction.json` is the
complete optional-extraction example. Both illustrate the contract with
prompts, accepts, and hints.

`example_universal_structure_no_extraction.json` predates this contract. It
is a legacy reference only and must not be copied when creating or migrating
graphs.
