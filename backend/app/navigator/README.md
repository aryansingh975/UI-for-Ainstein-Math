# Ainstein — Socratic DAG Navigator (v2)

A lightweight, deterministic, session-aware DAG navigator designed for Socratic tutoring systems.

---

## Highlights

- **Zero External Runtime Dependencies**: Pure Python Standard Library (no numpy, scipy, scikit-learn, or torch required).
- **Deterministic Ranker Pipeline**:
  - **Rule 1: Exact Match Dominance**: Normalized string equality + canonical token set equivalence with score `1.0`.
  - **Fuzzy Composite Scoring**: Specificity-weighted Jaccard, character bigram Dice coefficient, and grounded input coverage.
  - **Threshold Gate**: `DEFAULT_THRESHOLD = 0.50` strict cutoff.
  - **Rule 2: Specificity Tie-Breaker**: Longest matching phrase token count wins ties.
- **DAG Path Reachability**: Enforces forward traversal along valid DAG paths via BFS.
- **Step-Jump Detection**: Detects when a student skips critical intermediate steps flagged with `importance: "yes"`.
- **Session & Path Narrowing**: Dynamically narrows candidate solution paths as the student navigates through multi-method problems.

---

## Installation

Install as a local editable package:
```bash
pip install -e .
```

Or copy the `navigator/` folder directly into your project.

---

## Quickstart

### 1. Interactive CLI

Launch the interactive terminal session on any solution graph:

```bash
# Run with a specific graph
python navigator/cli.py path/to/graph.json
```

### 2. Python API

```python
from navigator import Navigator

# Load a graph JSON file or dictionary
nav = Navigator("path/to/graph.json", threshold=0.5)

# Process a student's input
result = nav.process_input("200 g costs 200 rupees")

print(f"Status: {result.status}")           # FIRST_MATCH, ADVANCED, STEP_JUMP, INVALID_PATH, NO_MATCH
print(f"Message: {result.message}")
print(f"Current Node: {result.current_node_id}")
print(f"Trail: {result.trail}")
```

### 3. Graph Inspection Tool

Inspect and validate a DAG structure and precomputed solution paths:

```bash
python navigator/graph_loader.py path/to/graph.json
```

---

## Module Layout

```
navigator/
├── __init__.py         # Public exports (Navigator, load_dag, etc.)
├── cli.py              # Interactive terminal CLI runner
├── graph_loader.py     # Graph ingestion, validation, and DFS path enumeration
├── navigator.py        # Core Navigator engine & state machine
├── normalizer.py       # Math symbol mapping & tokenization
├── path_finder.py      # BFS reachability & intermediate importance detection
├── ranker.py           # Collision resolution & threshold gate
├── scorer.py           # Deterministic token math & character n-gram alignment
├── session.py          # Session history & active candidate paths manager
├── ARCHITECTURE.md     # In-depth architectural design blueprint
├── pyproject.toml      # Standard Python package specification
└── tests/              # Test suite (14 comprehensive tests)
```

---

## Running Tests

```bash
pytest navigator/tests
```
