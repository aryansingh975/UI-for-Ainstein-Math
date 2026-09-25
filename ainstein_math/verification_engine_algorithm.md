# Verification Engine Algorithm

## Purpose

The verification engine validates a student response in a very explicit, step-by-step way.

It does not parse the whole conversation at once. Instead, it follows a fixed sequence of atomic validation nodes. Each node represents one small fact or action in the solution, such as:

- identifying the givens
- identifying the goal
- choosing a method
- computing
- concluding that the ratios are proportional

The engine checks whether the student input matches the current node before moving to the next node.

---

## High-level idea

The engine behaves like an intelligent state machine with a multi-layered evaluation pipeline:

1. **Layer 1 (Noise & Incomplete Filter)**: Discards pure stop words (like `"the"`, `"and"`, `"a"`) or inputs without mathematical/domain tokens.
2. **Layer 2 (Relevance & Truth Filter)**: Detects mathematically true but problem-irrelevant statements (like `"3 + 4 = 7"` or `"2 + 2 = 4"`) and gently redirects the student.
3. **Layer 3 (Arithmetic Diagnostics)**: Catches on-topic calculation slips (like `"3 * 96 = 200"`) and gives targeted feedback.
4. **Layer 4 (Method-Aware Node Progression)**: Follows the student's chosen path (cross-multiplication, simplification, or scaling) rather than enforcing a rigid linear list.
5. **Layer 5 (Entity Coverage Matching)**: Verifies that required entities (e.g. both ratios $3:4$ and $72:96$) are present, giving scaffolding hints if only one is mentioned.
6. **Layer 6 (Needs-Help Hint Ladder)**: Detects stuck replies like `"i don't know"` or `"help"` and escalates supportive hints (nudge -> specific pointer -> worked example) instead of repeating the question.

This keeps the logic robust, pedagogically helpful, and easy to explain.

---

## Data layout

The dataset is expected to contain a structure like this:

- `question_text`: the original problem statement
- `validation_data`
  - `solution_nodes`: ordered list of node definitions
  - each node has fields such as:
    - `id`
    - `operation`
    - `accept`
    - `prompt`
    - `establishes`

Each node is a single step in the solution path.

---

## Initialization

The constructor performs setup when a `VerifyEngine` object is created:

```python
ROOT_DIR = Path(__file__).resolve().parent.parent
DATASET = "dataset/class08_test-problem_validation.json"
```

This gives the engine a stable project root and the default dataset file.

Then in `__init__`: 

```python
path = Path(dataset_path)
if not path.is_absolute():
    path = ROOT_DIR / dataset_path
```

This makes sure the dataset path works even if the code is launched from a different directory.

After that, the engine loads the dataset JSON and stores:

- `self.dataset`
- `self.validation_data`
- `self.solution_nodes`
- `self.nodes_by_id`

It also creates runtime state variables:

- `self.completed_nodes`
- `self.established_facts`
- `self.history`
- `self.active_method`
- `self.is_completed`

These fields track the current progress of the validation process.

---

## Node progression

The engine determines the next required step using:

```python
def _next_node(self):
    for node in self.solution_nodes:
        if node["id"] not in self.completed_nodes:
            return node
    return None
```

This is a linear progression model:

- it scans the ordered node list
- it returns the first unfinished node
- when all nodes are done, it stops

So the engine enforces a strict sequence of solution steps.

---

## Text normalization

Before comparing student text, the engine normalizes it:

```python
cleaned = text.lower().strip()
cleaned = cleaned.replace("×", "x")
cleaned = cleaned.replace("−", "-")
cleaned = re.sub(r"\s+", " ", cleaned)
```

This reduces formatting differences such as:

- `3 x 96 = 288`
- `3×96=288`
- `3*96=288`

All are treated in a more uniform way for matching.

---

## Matching accepted phrases

The engine checks whether the student's answer matches any accepted phrase for the current node:

```python
def _matches_any(self, text, candidates):
    text_norm = self._normalize(text)
    for candidate in candidates:
        cand_norm = self._normalize(candidate)
        if cand_norm in text_norm or text_norm in cand_norm:
            return True
    return False
```

This is a simple substring-based comparison after normalization.

It is intentionally weak and interpretable:

- it accepts close textual matches
- it avoids over-complicating the validation logic

---

## Recording a completed node

Once a node is accepted, the engine records it:

```python
def _record_node(self, node):
    node_id = node["id"]
    self.completed_nodes.add(node_id)

    for fact in node.get("establishes", []):
        self.established_facts.add(fact)

    self.history.append({
        "node_id": node_id,
        "operation": node.get("operation"),
        "facts": list(node.get("establishes", [])),
    })
```

This does two things:

1. marks the node as completed
2. adds the node’s established facts into the engine’s current belief state

This allows the engine to track the reasoning path and the facts it has already accepted.

---

## Method selection logic

The engine also tries to infer which solving method the student is using:

```python
def _method_from_text(self, text):
    text_norm = self._normalize(text)
    if "cross" in text_norm and ("multi" in text_norm or "product" in text_norm):
        return "cross_multiplication"
    if "simplif" in text_norm or "reduce" in text_norm or "divide" in text_norm or "hcf" in text_norm:
        return "simplification"
    if "scale" in text_norm or "multipl" in text_norm or "factor" in text_norm:
        return "scaling"
    return None
```

This is a lightweight keyword-based classifier. It decides whether the student is choosing a cross-multiplication, simplification, or scaling path.

---

## Atomic node evaluators

Each valid method branch has specific node handlers, such as:

- `_evaluate_node_001`
- `_evaluate_node_002`
- `_evaluate_node_003`
- `_evaluate_node_crs_mul_001`
- `_evaluate_node_crs_mul_002`
- `_evaluate_node_sim_001`
- `_evaluate_node_sim_002`
- `_evaluate_node_scale_001`
- `_evaluate_node_scale_002`

Each function follows this pattern:

1. look up the relevant node in `self.nodes_by_id`
2. check the student input against `node["accept"]`
3. optionally compare key numeric or symbolic fragments
4. if matched, call `_record_node(node)`
5. return a success verdict and a response message

For example, the cross-multiplication node checks whether the text contains the relevant multiplication facts such as:

- `3*96`
- `4*72`
- `288`

If those are present, the engine accepts the node.

---

## Main dispatcher

The central function is:

```python
def evaluate_turn(self, student_input):
    text = (student_input or "").strip()
    ...
    next_node = self._next_node()
    ...
    handler = dispatch.get(node_id)
    return handler(text)
```

This does the final orchestration:

- ignore empty input
- do nothing if the problem is already complete
- find the next node
- dispatch to the correct node evaluator
- return the verdict

This makes the engine a straightforward finite-state validator.

---

## Needs-help hint ladder

When the student replies with a stuck expression (`"i don't know"`, `"idk"`, `"help"`, `"i'm confused"`, ...), the engine answers supportively instead of repeating the question:

```python
# ─── Filter 1: Needs-help detection ───
if tutor_hints.is_stuck_expression(text):
    return self._handle_needs_help()
self.stuck_streak = 0  # any non-stuck reply restarts the ladder
```

`_handle_needs_help` escalates through three levels for the current node:

1. **Level 1 (nudge)**: re-frames what the node is asking.
2. **Level 2 (specific pointer)**: names the quantities or operations involved.
3. **Level 3 (worked example)**: shows the full step.

The streak counts consecutive stuck replies and resets whenever the student sends any other reply or completes a node with help. For most nodes the level-3 reveal records the node as **assisted** (`assisted_step_completed`) and moves on, so a struggling student is never blocked. Conclusion nodes never auto-complete: the reveal shows the reasoning and asks the student to type the final answer themselves.

Hint content lives in `tutor_hints.py` inside this package (original wording; only the progressive-ladder idea is shared with the solution-graph assets).

---

## Why the algorithm is useful here

This design is useful because it is:

- explicit
- easy to read
- easy to debug
- aligned with a dataset-driven educational workflow
- safe for atomic validation in a tutoring context

It prioritizes transparency over complex parsing or inference.

---

## Summary

The verification engine is a rule-based, node-by-node validator:

- the dataset defines the ordered solution steps
- the engine tracks which steps are complete
- the student input is normalized and matched against the current node
- accepted steps advance the state
- the process stops when the solution is complete

This is a deliberate, minimal, and interpretable design for validating a structured mathematical reasoning workflow.

