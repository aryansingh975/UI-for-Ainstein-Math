# Socratic Math Tutor: Pedagogical & Engine Fixes Log

This document tracks every pedagogical conflict, engine bug, and UX issue resolved in the Socratic Math Tutor. For every problem addressed, it documents:
1. **The Problem** (what was going wrong and why)
2. **Concrete Example** (student input and the broken behavior)
3. **How We Solved It** (exact engine, state machine, or API changes)
4. **How the Tutor Behaves Now** (verified before vs. after behavior)

---

## Fix 1: Eliminating the "Dead Prompt Gap" After Goal Extraction

* **Category:** Pedagogical State Machine & Prompt Flow
* **Files Modified:** `backend/app/api/v1/sessions.py`

### 1. The Problem
When a student finishes identifying the Givens and Goal (Pólya extraction phase), the solution graph DAG branches into multiple possible solution methods (e.g., Simplification, Cross-Multiplication, Decimal Comparison, etc.). Because it branches, `session.current_node_id` becomes `None` until a specific method is detected.

Previously, `sessions.py` checked:
```python
if active_id and active_id in node_map:
    next_prompt = cur.prompt
```
Because `active_id` was `None`, `next_prompt` was set to `None`. The tutor had no follow-up question or guidance for the student, and the UI input box fell back to a generic: *"Type your next step…"*. The student was left wondering what to do next.

### 2. Concrete Failing Example
* **Turn 1 (Given):** Student enters `"3:4 and 72:96"` $\to$ Tutor accepts given extraction.
* **Turn 2 (Goal):** Student enters `"whether the ratios are proportional"` $\to$ Tutor accepts goal extraction.
* **Tutor's next prompt:** `None` (Blank speech bubble / fallback placeholder).
* **The issue:** The tutor failed to prompt the student to begin their first calculation step.

### 3. How We Solved It
In `backend/app/api/v1/sessions.py`:
When `active_id` is `None`, the session is not completed, and no method is locked yet (`session.method_id is None`), the tutor now detects that extraction is satisfied and dynamically provides an encouraging, proactive calculation prompt:
```python
elif not active_id and not session.method_id:
    active_label = "Step 1"
    next_prompt = "Great! Now that we know what is given and what to find, what is your first step to solve this problem?"
```

### 4. How the Tutor Behaves Now
* **Turn 1:** Student identifies givens.
* **Turn 2:** Student identifies goal.
* **Tutor response:** *"Great! Now that we know what is given and what to find, what is your first step to solve this problem?"*
* The student is seamlessly transitioned from problem analysis directly into doing their first mathematical calculation, with zero dead air and no spoon-fed method menu.

---

## Fix 2: Phase Gating to Prevent Premature Conclusion Leaks (Systemic Fix)

* **Category:** Engine Architectural Integrity & Socratic Pedagogy
* **Files Modified:** `backend/app/engine/tutor_engine.py`

### 1. The Problem
In `backend/app/engine/tutor_engine.py`, `detect_conclusion()` was being evaluated unconditionally at Step 2 of `process_step` on *every single turn*. 

Because conclusion nodes in the solution graphs contain common English words (e.g., `"proportional"`, `"yes"`) or simple numbers that also appear in the problem statement (e.g., `"6"`, `"8"`, `"12"`), any sentence uttered by a student during early turns that included those words caused the engine to instantly declare the entire problem solved.

### 2. Concrete Failing Examples
* **Example A (Ratio & Proportion `g08-hegp107-ex001`):**  
  * **Tutor asks:** *"What do we need to determine in this problem?"*  
  * **Student types:** *"We need to find whether the ratios are proportional."*  
  * **Broken behavior:** Engine matched `"proportional"`, emitted `CONCLUSION_RIGHT`, and completed the session on Turn 1!
* **Example B (Age Word Problem `g08-hegp206-age-q7`):**  
  * **Problem statement:** Mentions a 6-year age difference.  
  * **Student types during extraction:** *"Given age is 6 years."*  
  * **Broken behavior:** Final answer is `6`. The engine matched `"6"`, emitted `CONCLUSION_RIGHT`, and finished the problem on Turn 1 before any algebra was written!

### 3. How We Solved It
We implemented two strict pedagogical gates in `tutor_engine.py`:
1. **Extraction Phase Lockdown:**  
   If the student is currently on an extraction node (`given_extraction` or `goal_extraction`), or if required extraction has not yet been satisfied, `detect_conclusion()` is completely disabled.
2. **Hypothesis / Question Clause Filter:**  
   If the student's text contains interrogative or hypothesis phrases (e.g., `"whether"`, `"if"`, `"find if"`, `"check if"`, `"to find"`), it is filtered out from triggering conclusion matches.
3. **Prerequisite Calculation Gate:**  
   Bare conclusion keywords (like `"proportional"` or standalone numbers) are only accepted as a conclusion if the student has already performed at least one verified mathematical calculation step in `session.trail`, or is explicitly positioned at the conclusion node.

### 4. How the Tutor Behaves Now
* When a student writes *"find whether the ratios are proportional"* during goal extraction, the tutor correctly accepts it as the **Goal** (`ACCEPT`), NOT the final conclusion.
* When a student mentions given quantities like `"6 years"` or `"8 workers"`, the engine records the given and continues teaching without premature termination.

---

## Fix 3: Prioritizing Real Mathematical Calculation Over Keyword Interception

* **Category:** Socratic Method Discovery
* **Files Modified:** `backend/app/engine/tutor_engine.py`

### 1. The Problem
In `backend/app/engine/tutor_engine.py`, the engine checked method keywords (`detect_method_keyword`) *before* searching for actual mathematical calculations (`find_global_step_match`).

When a student entered a calculation that happened to contain a method-related word (e.g., *"I will divide 72 and 96 by 24 to get 3 and 4"*), the keyword interceptor caught the word `"divide"`, set `approach_only=True`, and stopped. It did not validate or record the calculation `72/24=3`. The student had to type their math all over again on the next turn.

### 2. Concrete Failing Example
* **Student types:** *"divide 72 and 96 by 24"*
* **Broken behavior:** Engine caught `"divide"` $\to$ marked `approach_only=True` $\to$ did not advance the math step $\to$ turn wasted just setting the method name.

### 3. How We Solved It
We flipped the evaluation order in `tutor_engine.py`:
1. **First:** Evaluate `find_global_step_match`. If the student provided a valid mathematical calculation (e.g., `24`, `72/24=3`, `3 * 96 = 288`), validate the math immediately, record the step in `session.trail`, and silently lock the method.
2. **Second:** Fall back to `detect_method_keyword` *only* if the student wrote no checkable math and literally only mentioned a method name (e.g., *"cross multiplication"*).

### 4. How the Tutor Behaves Now
* When the student types their first calculation step directly (e.g., `"divide by 24"` or `"HCF is 24"`), the engine evaluates the math, records the step, silently locks the method, and advances to Step 2 in a single seamless turn.

---

## Fix 4: Natural Goal Phrasing & Conversational Vocabulary in Matcher

* **Category:** Student Experience & Natural Language Understanding
* **Files Modified:** `backend/app/engine/vocabulary.py`, `backend/app/engine/matcher.py`

### 1. The Problem
When answering the goal extraction question (*"What do we need to determine in this problem?"*), students naturally speak in full sentences, such as:
> *"We need to find whether the ratios are proportional."*

Previously, two separate engine hurdles blocked this:
1. Words like `"need"` and `"whether"` were missing from `RELEVANT_WORDS` in `vocabulary.py`, causing `has_irrelevant_words()` to flag honest student answers as `"GARBAGE"`.
2. In `matcher.py`, multi-word phrase matching required exact string equality, rejecting any student sentence that added conversational framing around the required goal phrase.

### 2. Concrete Failing Example
* **Tutor asks:** *"What do we need to determine?"*
* **Student types:** *"we need to find whether the ratios are proportional"*
* **Broken behavior:** Flagged as `"GARBAGE"` because `"need"` was considered irrelevant, and even if allowed, exact match failed because of the prefix `"we need to find"`.

### 3. How We Solved It
1. **Vocabulary Expansion:** Added conversational goal-framing words to `RELEVANT_WORDS`:  
   `"need"`, `"needs"`, `"needed"`, `"whether"`, `"determine"`, `"determines"`, `"determining"`, `"goal"`, `"goals"`, `"compare"`, `"comparing"`, `"comparison"`.
2. **Verbal Multi-Word Phrase Matching:** In `matcher.py`, added non-numeric multi-word phrase matching so that if a student embeds the accepted goal phrase within a conversational sentence, it is cleanly recognized and accepted.

### 4. How the Tutor Behaves Now
* When a student types *"we need to find whether the ratios are proportional"*, the tutor warmly accepts it as the verified goal (`ACCEPT`), advances the state machine, and prompts for the first calculation step.


---

## Fix 5: Automatic Method Junction Bypass (Zero Breaking JSON Edits)

* **Category:** Solution Graph Handling & Method Routing
* **Files Modified:** `backend/app/engine/state_machine.py`, `backend/app/api/v1/sessions.py`

### 1. The Problem
All 32 `graph.json` files contain 78 method nodes (`m1_simplify`, `m2_formula`, `method1`, etc.) with hardcoded prompts like:
> *"Choose a method to solve this problem. You can simplify 72 : 96, cross multiply, scale, compare decimals, etc."*

These nodes were originally authored under the old assumption of forcing students to choose a method from a menu before performing calculations. If `session.current_node_id` or `successor_of` ever pointed to a method node, the tutor would output this menu prompt, directly opposing our pedagogical principle of autonomous silent method discovery.

### 2. Concrete Failing Example
* If a session transition landed on a method node (or if `successor_of` followed an incoming edge into a method node), `cur.prompt` was sent to the student:  
  *"Choose a method to solve this problem..."*
* This violated the core principle that students should never be spoon-fed a method menu or asked to name a method upfront.

### 3. How We Solved It
Without having to edit any of the 32 `graph.json` files:
1. In `state_machine.py`, `successor_of` was updated to treat method nodes strictly as internal routing junctions. If the successor node has `type == "method"`, it automatically bypasses it to `first_step_of(nxt, graph)`.
2. In `sessions.py`, `start_session` and `check_step` enforce that if `active_id` ever points to a method junction node, it is immediately bypassed to `first_step_of(active_id, graph)`.

### 4. How the Tutor Behaves Now
* The student **never** sees a "Choose a method" menu or prompt.
* Method nodes function purely as invisible internal DAG routing anchors.

---

## Fix 6: Universal Method Resolution Across Diverse Graph Naming Schemas

* **Category:** Solution Graph DAG Traversal & Method Inference
* **Files Modified:** `backend/app/engine/state_machine.py`, `backend/app/engine/tutor_engine.py`, `backend/app/api/v1/sessions.py`

### 1. The Problem
Across the 32 problem graphs, method nodes and step nodes used several different naming conventions:
* **Chapter 7 & 10:** Methods like `m1_simplify`, steps like `m1_s1`
* **Chapters 1, 2, 8, 11:** Methods like `method1`, steps like `m1_step1`
* **Chapter 9 (Percentages):** Methods like `method1`, steps like `step1_profit`, `step_si_calc`
* **Shared steps:** Steps like `shared_ratio_comparison`

The engine previously used a strict regex `r"^(m\d+)_"` to extract the method. This caused 3 major architectural flaws:
1. **0 out of 228 steps (0.0%)** could look up their method node in `node_map.get(session.method_id)` because `session.method_id` was `'m1'` while the node id in the graph was `'m1_simplify'` or `'method1'`. As a result, `method_label` was ALWAYS `None` in API responses!
2. For 12 steps in Percentages and Ratio Comparison (`step1_profit`, `shared_ratio_comparison`), `method_of` returned `None`, leaving `session.method_id` unlocked and breaking step progression scoring.
3. `method_chain("m1", graph)` returned `['m1']` (length 1) because `'m1'` was not an actual node in the graph, completely breaking subsequent step scoring (`ni > ci`).

### 2. Concrete Failing Examples
* **Ratio & Proportion (`ex001`):** Student enters `24`. Method 1 is detected, but API returns `method_label = None`. The UI cannot show the active strategy badge.
* **Percentages (`g08-hegp201-ex-p19-q1`):** Student enters profit calculation `35`. Step is accepted, but `method_id` is set to `None`, and `method_label` is `None`.
* **Powers & Roots (`g08-hegp101-cbrt-3375`):** Steps are `m1_step1` while method is `method1`. `get_method_node('m1', graph)` failed completely.

### 3. How We Solved It
1. **DAG Ancestry Resolution (`method_for_node`):**
   Instead of relying solely on regex, `method_for_node` traces incoming graph edges backwards. If a step node like `step1_profit` or `shared_ratio_comparison` is executed, it traverses up the DAG to find its parent method junction node (`method1` or `m1_simplify`).
2. **Numeric Index & Flexible Lookup (`get_method_node`):**
   Added `method_index_of` to normalize `m1`, `method1`, and `m1_...` to index `1`. `get_method_node` now resolves the method junction node with 100.0% accuracy across all 32 graphs (verified on all 228 steps).
3. **Full Chain Traversal (`method_chain`):**
   `method_chain` now begins from the true method junction node (`mn.id`), properly constructing the full sequence of steps (e.g. `['m1_simplify', 'm1_s1', 'm1_s2', 'm1_s3', 'shared_ratio_comparison']`) so that progress scoring (`ni > ci`) functions accurately.

### 4. How the Tutor Behaves Now
* In every chapter (Ratio & Proportion, Powers & Roots, Percentages, Quadratic Equations, Linear Equations/Age), whenever a student enters an initial calculation, the tutor silently infers the correct method, records the step, and returns the human-readable method label (e.g. `"Method 1: Simplification (HCF)"`, `"Method 1: Profit % Formula"`, `"Method 1: Prime Factorisation"`).

---

## Fix 7: Elimination of "Method: None" UI Confusion & Dynamic Strategy Badge

* **Category:** Frontend UI & Pedagogical Transparency
* **Files Modified:** `frontend/src/App.jsx`, `frontend/src/components/WorkspacePanel.jsx`, `frontend/src/styles.css`

### 1. The Problem
In the live React UI, before any calculation was entered, the workspace header previously rendered an empty or blank method indicator (`· ` or `Method: None`). This misled students into thinking they had forgotten to select a method from a dropdown or menu before beginning.

### 2. Concrete Failing Example
* On problem start and during extraction turns 1 and 2, the header displayed an empty or ambiguous method indicator.
* Once the student entered their first calculation, it suddenly populated, reinforcing the mistaken impression that a method was supposed to have been chosen from a menu earlier.

### 3. How We Solved It
1. **Extraction Silence:** In `App.jsx`, `methodIndicator` remains completely hidden (`null`) during the extraction phase and before any mathematical calculation step is taken.
2. **Dynamic Strategy Pill:** Immediately upon the first mathematical calculation step being validated, `methodIndicator` renders an elegant recognized strategy badge:  
   `🎯 Method 1: Simplification (HCF)`
3. **Dedicated Styling:** Added `.method-pill` in `frontend/src/styles.css` with a soft emerald background, subtle border, and bold typography.
4. **Context-Aware Step Header:** During extraction, `stepLabel` explicitly reflects problem understanding (`Identify Givens & Goal`); after extraction completes, it cleanly transitions to `Step 1` for the student's first calculation.

### 4. How the Tutor Behaves Now
* During Givens and Goal extraction, no method badge is shown.
* As soon as the student enters their first mathematical step (e.g., `"24"` or `"35"`), the green pill badge `🎯 Method 1: Simplification (HCF)` appears, confirming to the student that Ainstein recognized their approach and is following along.

---

## Fix 8: 3-Stage Socratic Milestone Stepper in Visual Prototype

* **Category:** UI Mockup Alignment
* **Files Modified:** `ui_visual_mockup.html`

### 1. The Problem
In `ui_visual_mockup.html`, the milestone progress bar originally contained 4 separate milestones:  
`[✓ 1. Identify Givens & Goal] ── [✓ 2. Method Discovery] ── [⚡ 3. Step 2: Divide by HCF] ── [4. Final Conclusion]`

Having "Method Discovery" as milestone 2 explicitly contradicted the core principle that there is no separate student-facing method discovery step. Additionally, Tab 2 was titled `2. Socratic Method Discovery`.

### 2. Concrete Failing Example
* Reviewing the visual mockup presented "Method Discovery" as an explicit milestone between understanding the problem and calculating, giving the impression of a mandatory method selection phase.

### 3. How We Solved It
1. **3-Stage Milestone Stepper:** Consolidated the stepper bar into 3 true Socratic stages:  
   `[✓ 1. Understand Problem (Givens & Goal)] ── [⚡ 2. Mathematical Steps] ── [3. Final Conclusion]`
2. **Tab Renaming:** Renamed Tab 2 from `2. Socratic Method Discovery` to `2. Autonomous Strategy Recognition` to clearly convey that strategy recognition is an autonomous background capability of the tutor, not an upfront student hurdle.

### 4. How the Tutor Behaves Now
* The visual prototype and the live application are 100% harmonized: students understand the problem $\to$ immediately begin calculating $\to$ conclude.
