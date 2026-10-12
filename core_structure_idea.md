# Core Structure & Pedagogical Architecture Idea

## 1. Executive Summary & Core Design Philosophy

This document outlines the core architecture for problem representation, solution graphs (DAGs), and student interaction within Ainstein.

The central design goal is to balance two critical requirements:
1. **Pedagogical Empathy:** In mathematics—particularly contextual word problems—students frequently struggle not with arithmetic, but with *understanding the problem*: identifying what quantities are given and clarifying the target goal. The tutor must support this extraction phase.
2. **Database & Schema Uniformity:** All problem solution graphs in the database must adhere to **one identical, consistent JSON schema**. Rather than creating fragmented schemas for "word problems" versus "direct calculations", optionality is modeled natively through graph topology (edges) and node attributes.

---

## 2. Pedagogical Foundation: Pólya's 4-Stage Framework

Our solution graphs reflect George Pólya's classical problem-solving framework (*How to Solve It*):

```text
┌─────────────────────────────────────────────────────────────┐
│ 1. Understand the Problem (Extract Givens & Clarify Target) │
└──────────────────────────────┬──────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Devise a Plan (Select Method / Strategy)                 │
└──────────────────────────────┬──────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Carry Out the Plan (Step-by-step Mathematical Execution) │
└──────────────────────────────┬──────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Look Back & Conclude (Evaluate Reasonableness / Check)   │
└─────────────────────────────────────────────────────────────┘
```

In human tutoring:
- **Novice or struggling students** benefit immensely from scaffolding at Stage 1 (*"What information did the problem give us?"*).
- **Advanced or confident students** often perform Stage 1 mentally and immediately begin executing Stage 2 or 3 (*"20 × 4 = 80 total worker-days"*). A rigid tutor that demands they write out obvious givens creates friction; an intelligent tutor accepts their leap.

---

## 3. Problem Archetypes

Across our Grade 8 and Grade 10 curricula, problems naturally fall into two cognitive archetypes:

| Dimension | Contextual Word Problems | Direct Symbolic / Calculation Problems |
| :--- | :--- | :--- |
| **Examples** | • "20 workers take 4 days... how many days for 10?"<br>• "Mother is 5 times her daughter's age..."<br>• "Shopkeeper buys for ₹75 and sells for ₹110..." | • "Simplify and write in exponential form: $2^{-4} \times 2^7$"<br>• "Find $\sqrt{324}$ using prime factorisation"<br>• "Solve the quadratic equation $x^2 - 5x + 6 = 0$" |
| **Extraction Need** | **High / Essential.** The mathematical model is buried inside English narrative. | **Low / Implicit.** The problem statement *is* the mathematical expression. |
| **Givens / Goals Phase** | **Enforced or Recommended.** Scaffolding helps students avoid misreading numbers. | **Optional / Bypassable.** Forcing students to state the base/powers feels robotic. |

---

## 4. Unified Solution Graph Schema (Database Uniformity)

Every problem in `solution_graph/` follows the exact same schema. There are **no separate file structures** for word problems vs. direct calculations.

### Standard Problem Schema Specification

```json
{
  "graph_meta": {
    "graph_id": "sg-g08-hegp102-ex-p11-q1",
    "problem_uuid": "g08-hegp102-ex-p11-q1",
    "chapter": "Chapter 2 - Power Play",
    "problem_type": "direct_calculation",
    "problem_text": "Simplify and write the answer in exponential form: 2^-4 × 2^7.",
    "version": "1.0.0"
  },
  "givens": [
    { "symbol": "base", "value": "2", "description": "common base" },
    { "symbol": "powers", "value": "[-4, 7]", "description": "exponents" }
  ],
  "goals": [
    { "symbol": "result", "description": "simplified exponential expression" }
  ],
  "start_node": "start",
  "conclusion_node": "conclusion",
  "nodes": [
    {
      "id": "start",
      "type": "start",
      "label": "Problem Statement",
      "prompt": "Simplify 2^-4 × 2^7 using the laws of exponents."
    },
    {
      "id": "node_givens",
      "type": "extraction",
      "optional": true,
      "label": "Identify Base & Powers",
      "prompt": "What base and powers are given in this expression?",
      "accept": [
        "base 2 with powers -4 and 7",
        "base is 2 and exponents are -4 and 7"
      ]
    },
    {
      "id": "m1_product_rule",
      "type": "computation",
      "label": "Apply Exponent Product Law",
      "prompt": "Apply the product rule: a^m × a^n = a^(m+n).",
      "accept": [
        "2^(-4+7)",
        "2^3",
        "8"
      ]
    },
    {
      "id": "conclusion",
      "type": "conclusion",
      "label": "Final Answer",
      "prompt": "State the final simplified exponential form.",
      "accept": [
        "2^3",
        "8",
        "the answer is 2^3"
      ]
    }
  ],
  "edges": [
    { "from": "start", "to": "node_givens" },
    { "from": "node_givens", "to": "m1_product_rule" },
    { "from": "start", "to": "m1_product_rule", "type": "direct_leap" },
    { "from": "m1_product_rule", "to": "conclusion" }
  ]
}
```

---

## 5. Modeling Optionality in the Graph Engine

To maintain database uniformity without penalizing students who bypass basic extraction steps, the engine uses two complementary mechanisms:

### A. Graph Topology (Direct Leap Edges)
In the graph edges:
- `start -> node_givens -> node_goal -> methods` (the guided scaffolding path)
- `start -> methods` (the direct leap edge)

If a student enters an answer matching `m1_product_rule` directly from `start`:
- The engine traverses the direct leap edge immediately.
- `node_givens` and `node_goal` are silently marked as satisfied/bypassed.
- The student is never scolded with *"You forgot to tell me the givens first!"*.

If a struggling student types the givens or asks for help:
- The engine matches `node_givens` and provides conversational scaffolding.

### B. The Node Attribute (`"optional": true`)
Extraction nodes can carry the flag `"optional": true`:
- If an upcoming step is marked `"optional": true`, and the student provides an answer that satisfies a downstream computational node, the engine auto-advances through the optional node without triggering a failure.

---

## 6. UI Interaction & Socratic Scaffolding Experience

The UI adapts its guidance based on problem type while using the exact same underlying rendering engine:

1. **Proactive Tutor Guidance:**
   - Instead of a blank textarea with no direction, the tutor explicitly displays its guiding question above the input:
     - *Word Problem:* `"Tutor: Before calculating, what are the known quantities in this problem?"`
     - *Direct Problem:* `"Tutor: How can we apply the exponent rules to simplify this expression?"`
2. **Context-Aware Scaffolding:**
   - When a student writes `"I don't know"` or makes an arithmetic blunder in a word problem, the tutor's first hint doesn't reveal the math—it prompts them to extract the givens:
     - *"Let's take it one step at a time. How many workers were originally assigned, and how many days did they take?"*
3. **Structured Entity Representation:**
   - For word problems, the UI can optionally render lightweight chips (`Given: ...`, `To Find: ...`) that ground the problem without altering the JSON contract.

---

## 7. Concrete Architectural Benefits

1. **Single Universal Parser:** Both `tutor-engine.js` (browser) and `verification_engine.py` (Python terminal tutor) use one unified parsing and evaluation pipeline.
2. **Consistent Automated Testing:** The test suite (`test_solution_graph.js`) validates every single problem against the same schema rules (unique node IDs, reachability from `start` to `conclusion`, valid edges).
3. **Adaptive Pedagogy:** Advanced students move quickly; developing students receive supportive scaffolding.
4. **Scalability:** Adding new chapters (Exponents, Algebra Play, Commercial Math, Roots) requires zero changes to the underlying graph engine.

