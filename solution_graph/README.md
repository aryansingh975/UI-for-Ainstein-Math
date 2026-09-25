# Solution Graph (DAG) — g08-hegp107-ex001

## Overview

This directory contains a **Directed Acyclic Graph (DAG)** that captures **all valid solution methods** for Problem 1:

> **Are the ratios 3 : 4 and 72 : 96 proportional?**

The purpose of this graph is to allow the Socratic tutor to **accept any valid solution path** without needing to store each solution method separately in the validation JSON file. Instead of hardcoding a single expected answer, the tutor can traverse this graph and validate student input against any node in the graph.

---

## Why a Solution Graph?

The current validation JSON (`class08-hegp107.validation.json`) only stores **one solution path** (simplification method). This means:

- A student who solves the problem via **cross multiplication** gets rejected.
- A student who solves via **decimal comparison** gets rejected.
- A student who solves via **scaling** gets rejected.

Storing every possible solution method in the JSON file would be:
- **Time-consuming** to author
- **Space-inefficient** (duplicate data)
- **Hard to maintain** (every change requires updating multiple entries)

The **solution graph** solves this by representing the problem's solution space as a DAG where:
- **Nodes** represent steps, methods, or conclusions
- **Edges** represent valid transitions between steps
- **Any path from `start` to `conclusion`** is a valid solution

---

## Graph Structure

```
                    ┌─────────────────────────────┐
                    │          START              │
                    │  "Are 3:4 and 72:96         │
                    │   proportional?"            │
                    └─────────────┬───────────────┘
                                  │
        ┌──────────┬──────────┬───┴────┬──────────┬──────────┬──────────┬──────────┐
        ▼          ▼          ▼        ▼          ▼          ▼          ▼          ▼
   ┌─────────┐ ┌─────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
   │ Method 1│ │ Method 2│ │Method 3│ │Method 4│ │Method 5│ │Method 6│ │Method 7│ │Method 8│
   │Simplify │ │Cross    │ │Scaling │ │Decimal │ │Fraction│ │Prime   │ │Equiv.  │ │Step-by-│
   │ (HCF)   │ │Multiply │ │        │ │Compare │ │Simplify│ │Factor  │ │Fraction│ │Step    │
   └────┬────┘ └────┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘
        │           │          │          │          │          │          │          │
        ▼           ▼          ▼          ▼          ▼          ▼          ▼          ▼
   ┌─────────────────────────────────────────────────────────────────────────────────────┐
   │                              CONCLUSION                                              │
   │                    "Yes, 3:4 and 72:96 are proportional"                             │
   └─────────────────────────────────────────────────────────────────────────────────────┘
```

Each method has its own sub-path of steps that lead to the conclusion.

---

## The 8 Solution Methods

| Method | ID | Description | Key Steps |
| :--- | :--- | :--- | :--- |
| **1. Simplification (HCF)** | `m1_simplify` | Find HCF of 72 and 96, divide both terms, compare with 3:4 | Find HCF → Divide → Compare |
| **2. Cross Multiplication** | `m2_cross_multiply` | Check if 3×96 = 4×72 | Set up → Compute 3×96 → Compute 4×72 → Compare |
| **3. Scaling** | `m3_scale` | Check if 3:4 scales to 72:96 by a common factor | Find factor → Verify second term → Conclude |
| **4. Decimal Comparison** | `m4_decimal` | Convert both ratios to decimals and compare | Convert 3:4 → Convert 72:96 → Compare |
| **5. Fraction Simplification** | `m5_fraction` | Write 72:96 as fraction, simplify, compare with 3/4 | Write fraction → Simplify → Compare |
| **6. Prime Factorization** | `m6_prime` | Factorize 72 and 96, cancel common factors | Factorize 72 → Factorize 96 → Cancel → Compare |
| **7. Equivalent Fraction** | `m7_equivalent` | Show 3:4 × 24 = 72:96 | Multiply by 24 → Recognize equivalence |
| **8. Step-by-Step Reduction** | `m8_reduce` | Reduce 72:96 step by step (÷2, ÷2, ÷2, ÷3) | 72:96 → 36:48 → 18:24 → 9:12 → 3:4 |

---

## Node Types

| Type | Description |
| :--- | :--- |
| `start` | The problem statement. Entry point of the graph. |
| `method` | A distinct solution method. The student chooses which method to use. |
| `step` | An intermediate step within a method. The student must complete each step. |
| `conclusion` | The final answer. All valid paths converge here. |

---

## Node Schema

Each node in the graph has the following structure:

```json
{
  "id": "unique-node-id",
  "type": "start | method | step | conclusion",
  "label": "Human-readable label",
  "description": "What this node represents",
  "prompt": "The question to ask the student at this node",
  "accept": ["list of accepted answers"],
  "hints": ["progressive hints for this node"]
}
```

---

## Edge Schema

Each edge represents a valid transition between nodes:

```json
{
  "from": "source-node-id",
  "to": "target-node-id",
  "label": "Description of the transition"
}
```

---

## How the Tutor Uses This Graph

1. **Start**: The tutor presents the problem and asks the student to begin.
2. **Method Selection**: The student's first response is matched against the `accept` lists of all `method` nodes. The tutor identifies which method the student is using.
3. **Step Progression**: The tutor guides the student through the steps of the selected method, validating each response against the current node's `accept` list.
4. **Conclusion**: Once all steps of a method are completed, the student reaches the `conclusion` node. The tutor confirms the final answer.

### Matching Logic

- The tutor checks the student's input against the `accept` array of the **current node**.
- If the input matches, the student advances to the next node in the path.
- If the input doesn't match, the tutor provides the next hint from the `hints` array.
- The tutor can also detect **method switching** — if the student's input matches a different method's `accept` list, the tutor can switch to that method's path.

---

## Files

| File | Description |
| :--- | :--- |
| `g08-hegp107-ex001.solution-graph.json` | The solution graph DAG data (38 nodes, 47 edges) |
| `g08-hegp107-ex001.solution-graph.svg` | Visual representation of the graph |
| `README.md` | This documentation |

---

## Extending to Other Problems

The same pattern can be extended to other problems in the dataset. For each problem:

1. Identify all valid solution methods.
2. Create a DAG with `start` → `method` nodes → `step` nodes → `conclusion`.
3. Add `accept` lists for each node covering common phrasings.
4. Add progressive `hints` for each node.

This approach scales efficiently because:
- Each method's steps are only stored **once**.
- New methods can be added without modifying existing ones.
- The tutor can accept any valid path without hardcoding.