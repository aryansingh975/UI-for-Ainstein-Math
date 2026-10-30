# Socratic Math Tutor: UI Redesign, Method Discovery & Systemic Engine Audit

This document records the complete pedagogical discussion, architectural audit, and UI redesign plan discussed regarding the Socratic Math Tutor.

---

# Section 1: Is Problem 1 Isolated or Systemic Across All 32 Graphs?

### The Question:
> *"The Problem 1 ('proportional or not' premature completion) is quite specific for that particular problem. Don't you think there can be such problems in the other 31 problems too? Can the solution be systemic rather than specific?"*

### The Audit Findings Across All 32 Graphs:
**The user was 100% correct.** An automated audit of all 32 problem graphs in `solution_graph/` proved that premature conclusion leaks are an **architectural engine flaw**, not an isolated data issue:

| Chapter & Problem | Conclusion Node Accepts | The Collision Hazard |
| :--- | :--- | :--- |
| **Ch 7: Ratio & Proportion** (`ex001`, `ex002`, `ex004`) | `["proportional", "yes", "yes proportional"]` | During extraction or intermediate steps, if the student asks *"find whether proportional or not"*, the engine matches `"proportional"` as a substring and terminates the problem. |
| **Ch 11: Linear Equations & Age** (`g08-hegp206-age-q7`) | `["6", "6 years"]` | In given extraction, the question mentions 6 years. If the student writes *"given time is 6 years"*, it immediately triggers conclusion completion! |
| **Ch 8: Inverse Proportion** (`ex003`, `ex005`, `ex006`) | `["8"]`, `["12"]`, `["36"]`, `["8 days"]` | If a student in given extraction writes *"8 workers"* or *"12 pipes"*, the conclusion fires on turn 1! |
| **Ch 1 & 2: Powers & Roots** (`sqrt-324`, `cbrt-3375`, `p11-q1`) | `["18"]`, `["15"]`, `["8"]`, `["6"]` | Mentioning any factor or intermediate base in Step 1 prematurely marks the whole problem solved! |

### The Root Cause in the Backend Engine:
1. **Unconditional Conclusion Evaluation in `backend/app/engine/tutor_engine.py` (Line 398):**  
   `detect_conclusion()` is evaluated at Step 2 of `process_step` on *every single turn*—even when the student is in Pólya extraction or Step 1 of a multi-step calculation.
2. **Loose Substring Matching in `backend/app/engine/matcher.py` (Line 20):**  
   Single-word accepted answers (`"proportional"`, `"6"`) match any sentence where that word appears (`if normalized_accepted in normalized_input: return True`).

### The Systemic Universal Fix (0 Per-Problem JSON Edits):
* **Phase Gating (Extraction Lockdown):** Disable `detect_conclusion()` completely whenever `session.current_node_id` is an extraction node (`given_extraction` or `goal_extraction`).
* **Prerequisite DAG Completion Gate:** A conclusion verdict can only be emitted if all intermediate calculation steps in the active method chain have been validated in `session.trail`.
* **Strict Matcher for Conclusions:** Disable substring matching for conclusion nodes. Require exact phrase equality or explicit conclusion assertions; reject question/conditional clauses (`"whether"`, `"if"`, `"or not"`).

---

# Section 2: Autonomous Method Discovery (True Socratic Pedagogy)

### The Core Pedagogical Principle:
> *"The method discovery you're talking about—there is no such step. We expect the student to start with identifying givens and goals. After that, we expect the student to start with their mathematical calculation step directly. We should be the one who silently understands which method was going on. There should be NO multiple-choice menu or upfront spoon-feeding."*

### Why This is Pedagogically Superior:
* In traditional tutoring, students are not handed a menu: *"Do you want to solve by HCF, Cross-Multiplication, or Scaling?"*.
* Presenting options upfront ruins curiosity and cognitive effort.
* In true Socratic teaching:
  1. The student identifies **Givens and Goal** (Pólya Step 1: Understand the Problem).
  2. The student directly enters their **first mathematical step** (e.g. `HCF of 72 and 96 is 24` or `3 * 96 = 288`).
  3. The tutor's engine **silently and dynamically infers** which valid method the student is executing, validates the math, locks that method in the background, and prompts for the next step of that method.
  4. Scaffolding/hints are provided **only on demand** if the student explicitly says *"I don't know how to start"*.

---

# Section 3: Comprehensive Codebase Conflict Audit

An exhaustive audit of the codebase was conducted to identify everything currently opposing this autonomous method discovery idea:

### 1. Conflicts in the UI Visual Mockup (`ui_visual_mockup.html`):
* **Extra Milestone in Stepper:**  
  The progress bar showed: `[1. Givens & Goal] ── [2. Method Discovery] ── [3. Step 2: Divide] ── [4. Conclude]`.  
  *Correction:* Remove "Method Discovery". The stepper must only have: `[1. Givens & Goal] ── [2. Mathematical Calculations] ── [3. Conclusion]`.
* **Tab 2 Title:**  
  Tab 2 was titled *"Method Discovery"*, implying a visible UI phase.

### 2. Conflicts in the Solution Graph JSONs (`solution_graph/**/graph.json`):
* **Explicit Method Prompts:**  
  In all 32 graphs, nodes like `m1_simplify`, `m2_fraction`, etc., contain hardcoded prompts:  
  `"prompt": "Choose a method to solve this problem. You can simplify 72 : 96, cross multiply, scale, compare decimals, etc."`
* **Graph Edges from Goal Extraction:**  
  Edges from `goal_extraction` lead to `m1_simplify` with label: `"Choose a solution method"`.
* **Keyword Matching on Method Nodes:**  
  Method nodes have accept lists looking for strings like `["simplif", "hcf", "cross multiply"]` rather than actual mathematical calculations.

### 3. Conflicts in the Backend Engine (`backend/app/engine/` & `sessions.py`):
* **The "Dead Prompt Gap" After Goal Extraction:**  
  When `goal_extraction` finishes, `successor_of("goal_extraction", graph)` returns `None` (because the DAG branches into multiple methods).  
  In `backend/app/api/v1/sessions.py` lines 101–113, because `current_node_id` is `None`, `next_prompt` is set to `None`.  
  The frontend falls back to a generic: *"Type your next step…"*.  
  *Correction:* Right after goal extraction is satisfied, the tutor should explicitly prompt:  
  *"Great! Now that we know what is given and what to find, start with your first calculation step to solve it."*
* **`detect_method_keyword` Interceptor (`tutor_engine.py` Line 458):**  
  The engine intercepts standalone words like `"simplify"` and consumes a turn setting `approach_only: True` without advancing math.

### 4. Conflicts in the Current Frontend UI (`frontend/src/`):
* **`Method: None` Badge in `WorkspacePanel.jsx`:**  
  Before the first step is taken, the header displays `Method: None`. This confuses students into thinking they forgot to select a method from a menu.  
  *Correction:* Hide the method indicator until a calculation step is validated, or display the active step label (`Step 1: Simplify 72:96`).

### Verification of Existing Engine Capabilities:
The backend engine's mathematical resolver (`find_global_step_match` in `tutor_engine.py` line 463) **already supports silent inference**!  
A live test through the engine verified:
```
Turn 1: "3:4 and 72:96"                       -> ACCEPT (goal_extraction)
Turn 2: "whether the ratios are proportional" -> ACCEPT (current_node: None)
Turn 3: "24"                                  -> ACCEPT (node_id: m1_s1, method: m1, current_node: m1_s2)
```
When the student typed `"24"`, the engine silently inferred Method 1 (HCF) and locked the DAG without requiring any method name or menu selection.

---

# Section 4: Proposed UI Architecture (Split-Screen Modern View)

### Key Improvements:
1. **Two-Column Split Layout (Desktop):**
   * **Left Panel (Sticky Problem Reference):**
     * Problem statement with crisp typography.
     * **Identified Information Tracker:** Real-time checklist of verified givens and goals.
     * **Discovered Strategy Roadmap:** Dynamically displays the steps of whichever method the student begins calculating.
   * **Right Panel (Conversational Socratic Stream):**
     * Messenger-style speech bubbles (Ainstein 🦉 on left, Student 👤 on right).
     * Typing indicator (*"Ainstein is analyzing your step..."*).
     * Input dock pinned to the bottom with contextual helper chips.
2. **Live Mathematical LaTeX Preview:**
   * Instant rendered preview ($\frac{72}{24} = 3 \text{ and } \frac{96}{24} = 4$) appears live above the input box as the student types.
3. **Milestone Stepper:**
   * Clean 3-stage progress:  
     $$\text{1. Identify Givens \& Goal} \longrightarrow \text{2. Mathematical Steps} \longrightarrow \text{3. Final Conclusion}$$
4. **Celebratory Victory Summary:**
   * On completion, a clean verified proof summary recaps the entire solution with a *"Next Problem ➔"* button.

### Interactive Mockup Location:
The interactive visual prototype is saved in your project root at:  
👉 **`ui_visual_mockup.html`**  
*(Open in any browser: Chrome, Edge, or Brave to view all interactive screens).*

---

# Section 5: Alignment & Implementation Roadmap

When you decide to proceed with implementation, the changes will follow this clean order:

1. **State Machine & Prompting (`sessions.py` & `state_machine.py`):**
   * Fill the dead-prompt gap after goal extraction with an encouraging calculation prompt.
   * Prevent conclusion leaks during extraction phase (universal Problem 1 fix).
2. **Engine Method Resolution (`tutor_engine.py`):**
   * Ensure `find_global_step_match` seamlessly locks `session.method_id` from the student's first mathematical input across all 32 problems.
3. **UI Modernization (`frontend/src/`):**
   * Implement the 2-column split layout.
   * Remove `Method: None` badge.
   * Add the live KaTeX math preview.

