# Project Idea

## Title
Method-Aware Math Tutor with Visual Solution Graphs

## Core Concept
Build an interactive learning app that helps students solve math problems step by step by recognizing the method they are using, giving route-specific hints, and visualizing the solution graph.

### Key idea
Instead of only checking whether the final answer is correct, the app tracks the student’s reasoning path and responds based on the method they are taking.

## Why This Is Strong
- Encourages conceptual understanding rather than answer-only solving
- Works well for word problems, fractions, ratios, proportions, and percentages
- Helps students learn from mistakes by identifying the wrong route or misconception
- Gives a visual map of valid solution paths
- Suitable for adaptive learning and tutoring workflows

## Product Vision
A student writes one step at a time. The app identifies which valid method they are using from their first step and then gives guidance based on that path. If the student has chosen a wrong interpretation or a common trap, the app points it out clearly.

## Main Features
### 1. Problem and Method Modeling
- Each problem has a set of valid solution methods
- Each method is broken into ordered steps
- Related methods share common first steps

### 2. Step-by-Step Tutor
- Student enters one step at a time
- App matches the step against possible routes
- App checks arithmetic and logic
- App responds with encouragement, hints, or correction

### 3. Misconception / Trap Detection
- Detect common wrong interpretations
- Highlight when the student has confused total vs. extra amount
- Warn when they are using the wrong ratio or reversed order
- Give targeted feedback rather than generic error messages

### 4. Visual Graphs
- Show all valid solution paths
- Highlight the route the student is currently following
- Show trap paths that lead to common mistakes
- Use a diagrammatic representation to make reasoning visible

### 5. Adaptive Help
- First hint: small nudge
- Second hint: stronger guidance
- Third hint: reveal next step or route

## Example Problem Types
- Fractions
- Ratios and proportions
- Percentages
- Missing value problems
- Word problems involving rates and scale
- Better-buy comparisons

## Technical Architecture
### Frontend
- Dashboard for choosing problem sets
- Input area for student steps
- Feedback panel and hint system
- Graph/visual route panel

### Backend
- Problem definition engine
- Step parser and validation
- Route classification engine
- Hint generation logic
- Session tracking

### Data Model
- Question
- Method
- Step
- Route
- Trap
- Student session

## MVP Scope
A first version can include:
- 3–5 problem types
- 2–4 methods per problem
- step detection for common first steps
- visual route graph
- hints and misconceptions

## Long-Term Vision
Turn this into a learning platform that supports:
- multiple grade levels
- different math domains
- personalized tutoring pathways
- teacher analytics
- progress reports and skill tracking

## Short Project Positioning Statement
An adaptive math reasoning tutor that helps students learn by following valid solution methods, not just by producing final answers.

## One-Line Summary
A method-aware, visual, step-by-step math tutor that recognizes student reasoning and gives targeted help along the correct solution path.

---

## 1. Current Status
Your current project is already a strong prototype and not a blank slate.

### What is already working
- A usable browser-based tutor interface
- A step-by-step student input flow
- LaTeX-style math input and preview
- A Proportional Reasoning chapter containing six Grade 8 problems
- A Grade 10 quadratic equation problem as the only current case using the separate method-selection layer
- Feedback messages for correct, wrong, irrelevant, and conclusion-based responses
- A solution graph / route-based engine that recognizes valid reasoning paths

### What this means
You are not missing the core idea. You already have the foundations of a method-aware tutor. The project is in the prototype stage, but it is a credible working prototype rather than just a mockup.

### Current implementation direction
The project now follows a chapter-based structure in which each textbook chapter stores its own problem graphs, and each graph is a concrete instance of a reusable generic route schema. In this structure, the tutor engine identifies the student’s active method by reading the first valid reasoning step and then locking to the matching route; the solution graph becomes the visual and pedagogical map for that route.

This is the standard model for the proportional reasoning chapter and most problems in the app. The separate method-selection layer is intentionally scoped only to the quadratic-equation problem and is not meant to be the general architecture for the entire chapter set.

The proportional reasoning chapter has been organized into a chapter folder model, and it now includes the new ratio-proportion example graph for Example 12, which was validated in the live UI as a working tutor problem.

### Reality check
The current app supports several problem-specific graphs, but the six proportional-reasoning problems still have separate definitions and are not yet powered by one reusable chapter model.

---

## 2. Missing Features Compared to the Product Vision
The gap is not in the concept; the gap is in productization and scale.

### Missing from the current project
- Multiple problem types instead of one focused example
- A reusable problem catalog and dataset structure
- Multiple valid methods for each problem, not just a single hardcoded flow
- Broader route classification over larger math domains
- Student progress tracking across sessions
- A persistence layer for saved work and analytics
- Adaptive learning logic beyond one-off feedback
- Teacher/admin dashboard or learning insights
- A generalized backend for storing methods, problems, and student states

### Main gap in one sentence
The project is strong as a tutor demo, but still weak as a full learning platform.

---

## 3. Priority Order to Build
Build in this order to avoid creating a bigger, fragile system too early.

### Priority 1: Generalize the problem schema
Create a structured way to define:
- problem id
- problem text
- concepts involved
- valid methods
- step sequences
- traps / misconceptions

This is the foundation for expanding beyond one example.

### Priority 2: Make the tutor engine reusable
Refactor the current logic so it works for many problems instead of only one ratio problem. The goal is to separate:
- problem definitions
- step validation rules
- route matching
- hint generation
- feedback logic

### Priority 3: Add multiple problem sets
Add 3 to 5 problem types in the first phase, such as:
- ratios and proportions
- fractions
- percentages
- simplification problems
- missing value problems

### Priority 4: Build student learning flow
Add:
- progress tracking
- hints by stage
- encouragement loops
- incorrect route detection
- completion states

### Priority 5: Add the product layer
Then add:
- dashboard navigation
- chapter/grade structure
- progress analytics
- teacher-facing reports
- saved sessions

---

## 4. Exact Roadmap
A practical roadmap for this project.

### Phase 1: Prototype hardening
- Keep the current UI and tutor functionality
- Convert the problem logic into a reusable schema
- Define a generic step model and route model
- Validate the current example using the generalized model

### Phase 2: Multi-problem extension
- Add 3-5 problem templates
- Define valid methods for each one
- Create route graphs for each problem
- Add hint generation and trap handling across them

### Phase 3: Student learning experience
- Add a study dashboard
- Add chapter selection and problem progression
- Add progress tracking and completion states
- Add adaptive hints based on repeated wrong steps

### Phase 4: Product-ready platform
- Add backend persistence
- Add user accounts or local session saving
- Add analytics and lesson outcomes
- Add teacher/coach view and problem insights

### Phase 5: Scale to real classroom use
- Support multiple grades and topics
- Expand beyond arithmetic into algebra and reasoning-based tasks
- Add curriculum mapping and assessment alignment

---

## 5. Generic Proportional-Reasoning Solver

### Goal
The Proportional Reasoning chapter should teach one reusable set of ideas across its six problems instead of maintaining six unrelated solution engines. The student should still see the original problem, and the tutor should still give steps that fit that problem. Reuse should happen in the underlying problem model, graph templates, and validators.

The goal is not to place every literal sentence and every numeric answer into one enormous graph. A large merged graph would contain many overlapping steps, make route selection ambiguous, and be difficult to maintain. A better design is a **master graph template** with shared reasoning patterns and problem-specific data supplied separately.

### The Six Current Problems
The chapter contains several related but mathematically distinct situations:

1. **Ratio equivalence: 3:4 and 72:96**
	Decide whether two ratios represent the same relationship. The tutor can guide students to simplify, scale, convert to fractions, or compare cross-products.

2. **Lemonade: 6 glasses use 10 spoons; make 18 more glasses**
	Use the same-sweetness rate to find the sugar needed. The problem definition must state whether the requested answer means sugar for the additional 18 glasses or sugar for the full batch. The words “more” and “total” must not be treated as interchangeable.

3. **Ratio equivalence: 6:8 and 72:96**
	This uses the same ratio-comparison template as Problem 1, but with different values. It is a useful test that the graph is parameterized rather than tied to 3, 4, 72, and 96.

4. **Compound wall: 60 feet with 3 bags; 40 feet with 2 bags**
	Compare cement-per-foot or feet-per-bag for the two walls, then decide whether the rates are equal. The quantities and units matter: the tutor must compare like rates in the same orientation.

5. **Age ratio: a 3-year-old and a 30-year-old, then 12 years later**
	This is the important exception. Both ages increase by the same additive amount; their ratio does not stay constant. The tutor should help students distinguish equal additive changes from equal multiplicative scaling.

6. **Rice: 15 kg for 120 students; find the amount for 80 students**
	Find a scale factor or a per-student rate, then apply it to the new number of students. The result should retain the correct unit, kilograms.

These examples share proportional-reasoning concepts, but not all share the same invariant. The graph must represent direct proportion, ratio comparison, and the age-ratio exception explicitly.

### Recommended Architecture: Data + Templates + Validators
Separate the problem into three parts:

- **Problem instance:** The student-facing prompt, quantities, names, units, requested unknown, problem family, and any interpretation notes.
- **Graph template:** Reusable nodes and route shapes for the relevant family of reasoning problems. Node steps use variable names rather than fixed values from one exercise.
- **Deterministic validators:** Small mathematical checks that calculate or compare values from the problem instance and the student's current claim.

The selected problem determines which graph template and methods are available. The graph template supplies the step sequence. The validator checks the math using the selected problem's actual values. This avoids copying a whole graph just to change a number.

### Example Problem Definition
An instance should describe the math without embedding a completed solution path in its prose. For example, a scaling problem could be represented conceptually as:

```json
{
  "id": "rice-for-80-students",
  "family": "direct-proportion",
  "quantities": [
	 { "name": "students", "value": 120, "unit": "students" },
	 { "name": "rice", "value": 15, "unit": "kg" }
  ],
  "target": { "name": "students", "value": 80, "unit": "students" },
  "unknown": { "name": "rice", "unit": "kg" },
  "invariant": "rice_per_student_is_constant",
  "graphTemplate": "direct-scaling"
}
```

The exact schema should be finalized against all six exercises before migrating the existing graphs. Some prompts, especially the lemonade and age questions, need additional fields for wording or time interpretation.

### Shared Graph Shape
A reusable graph can follow this overall flow:

1. **Interpret the question:** Identify the quantities, units, known values, and requested value or comparison.
2. **Identify the relationship:** Determine whether the quantities scale together, whether two rates should be compared, or whether an additive change means the ratio will change.
3. **Select a solution method:** Offer only methods valid for this problem family.
4. **Work through method-specific steps:** Use variable-based graph nodes instantiated with this problem's values.
5. **Check the invariant:** For example, compare equivalent ratios, verify a scale factor, or check that units and direction are consistent.
6. **State and verify the conclusion:** Compare the student's result with a deterministic calculation and the requested answer type.

The graph can share conceptual nodes while branching into method-specific paths. For example, ratio equivalence may allow simplification, equivalent-ratio scaling, fraction comparison, or cross multiplication. A direct-scaling problem may allow unit rate or scale factor. The age problem should not offer a direct-proportion route as though the ratio stays fixed; instead, it should expose the equal-addition reasoning and check the changed ratio.

### Route Selection in This Chapter
The selected problem already identifies its family and gives the valid methods. For most problems in the app, the tutor selects the student's active route by matching the first valid reasoning step against the methods available for that problem. The separate method-selection layer is intentionally used only for the quadratic-equation problem; the remaining chapter problems continue to use the standard graph-based tutor flow.

After a route is selected:

- Lock the session to that method's graph route.
- Pass the student's original response into the deterministic tutor engine so valid work already shown can be recognized.
- Validate every subsequent step with deterministic graph matching and mathematical checks.
- Ask the student to clarify if the method is genuinely unclear or outside the available graph routes.

Only the methods valid for the selected problem family should be considered. For example, an off-graph result for an age-ratio problem should not silently start a direct-scaling route.

### Current Solution Graphs vs. Shared Question Schema
The existing solution graphs and the proposed shared schema solve different parts of the problem. They should be connected, not treated as competing formats.

| Aspect | Current solution graph | Shared question schema |
| --- | --- | --- |
| Main purpose | Describes the routes and step nodes the tutor follows for one specific problem. | Describes reusable questions, inputs, methods, and student actions in a shared step language. |
| Typical contents | Start, method, step, and conclusion nodes; edges; accepted responses; hints; problem-specific values. | Skill/core/applied question definitions; quantities; outputs; primitive operations; `all`, `choose`, `use`, and other composable steps. |
| Strengths | Already works with the current tutor; easy to inspect one problem's route; explicit hints and accepted steps; good as a test baseline. | Reuses shared reasoning; parameterizes values; supports calls between questions; can generate classifier trees and diagrams from one source. |
| Tradeoffs | Similar steps and logic can be duplicated across problem files; edits may need to be repeated; large graphs can become difficult to maintain. | Requires a schema validator, builder, and more authoring discipline; errors in the schema or builder can affect many generated outputs; problem-specific exceptions need explicit modeling. |

The proposed schema is best understood as an **authoring source**. Its step definitions describe the student's mathematical actions. A builder can turn those definitions into generated first-step trees for classification and diagrams that follow the shared graph grammar. A generated graph, or a closely related runtime representation, can then provide the route and next-step behavior expected by the tutor.

This means the current graphs do not have to be discarded. Initially, they are valuable as working examples and regression fixtures. During migration, generated routes can be compared with the existing graphs for accepted steps, traps, hints, and final answers. The existing files should only be replaced after the generated behavior has parity for all six problems.

### How the Tree, the Schema, and the Tutor Work Together
Each component has a distinct responsibility:

1. **Problem schema selects the context:** The selected problem supplies its quantities, units, target, family, valid methods, and any interpretation notes. This prevents methods that do not apply to that problem from being offered.
2. **The route selector identifies the intended method:** The tutor receives the student response and the valid methods for this problem. It returns a method classification; it does not decide whether the work is mathematically correct or choose values for the student.
3. **The generated tree matches the written step:** Once a method route is selected, the classifier tree helps map the actual student expression to a valid step and its expected operands or operation. It can also support deterministic matching and expose ambiguous cases.
4. **The runtime graph controls tutoring flow:** The matching graph route supplies the next step, hint, trap, or conclusion. Student progress remains attached to that route.
5. **Deterministic validators check correctness:** Primitive operations and problem-specific validators calculate results and check relationships, units, ratio order, and requested quantities. The selected route label alone never makes a step correct.

The tree should not silently compete with the route selector as a second method detector. In the intended design, the route selector chooses the student's method, while the tree classifies the student's written action within that route. If the route selector is uncertain, the tutor should ask for clarification rather than let an unrelated tree match silently switch methods. A deterministic tree result can be used as a consistency check, for diagnostics, or as a future fallback if that behavior is deliberately designed and tested.

### End-to-End Example
For the rice problem, the problem instance supplies 120 students, 15 kg of rice, and a target of 80 students. Its valid methods might include unit rate and scale factor. If a student writes, “I will divide 15 by 120 to find rice per student,” the route selector identifies the unit-rate method. The generated tree recognizes the divide operation and its operands as the first step on that route. The deterministic validator calculates 15 ÷ 120, checks the units, and the runtime graph presents the next step. If the student instead divides 120 by 15, the route selector may still identify a rate approach, but deterministic matching must flag that the written operation does not match the expected quantity or route.

### Benefits for This Project
- **Less duplicated authoring:** Ratio-equivalence problems can share a core question and differ primarily in input values.
- **Consistent representations:** Trees and diagrams come from the same step definitions, reducing drift between what the classifier accepts and what the graph displays.
- **Reusable applied problems:** Story problems can map their quantities to core questions and translate the core result back into the story's requested answer.
- **Safer method selection:** The tutor sees only the methods valid for the selected question, while the deterministic engine remains responsible for correctness.
- **Easier expansion:** New exercises can reuse existing skills and core questions rather than requiring a separately hand-built graph for every variation.
- **Preserved problem-specific reasoning:** Explicit fields and branches can model the lemonade additional-versus-total distinction and the age-ratio additive-change exception.

### Main Risks and Mitigations
- **The builder becomes a critical dependency:** Validate schema files, report errors with question and step IDs, and test generated trees and diagrams in automation.
- **Abstraction hides special cases:** Keep family-specific invariants, units, traps, and interpretation notes explicit in the problem definition rather than relying on vague prose.
- **Route selector and the tree disagree:** Treat the route selector as the method detector and the tree as the step matcher; log disagreement for review and ask the student to clarify instead of silently changing routes.
- **Generated behavior regresses existing problems:** Keep the six current graphs as golden fixtures until each generated route passes equivalent route, arithmetic, trap, and conclusion tests.
- **A generic graph accepts mathematically true but irrelevant work:** Validators must check relevance to the selected problem and current graph node, not only whether an expression is arithmetically true.

### Migration Plan
1. **Record reference behavior:** Keep the six existing graph definitions and their accepted solution routes as the baseline. Record the expected answer, units, valid methods, and known traps for each problem.
2. **Classify the six instances:** Assign each problem a family and write down its invariant. Explicitly document the lemonade “additional versus total” distinction and the age problem's additive change.
3. **Define and validate the shared schema:** Agree on question fields, step operations, variable naming, call behavior, output mapping, and validation rules before writing many question files.
4. **Build the generator in small outputs:** First generate and test a classifier tree for one simple ratio question; next generate its diagram and runtime route representation from the same steps.
5. **Build parameterized validators:** Implement and test ratio equality, rate comparison, direct scaling, unit consistency, and additive age changes independently from UI wording.
6. **Connect the route selector to generated valid methods:** Supply methods from the selected question, map the selected method to its generated route, and keep tree matching and deterministic validation responsible for written steps and correctness.
7. **Build one template at a time:** Start with ratio equivalence, then direct scaling and rate comparison. Add the age-ratio exception as its own family or branch, not as a forced direct-proportion route.
8. **Run old and generated behavior side by side in tests:** For each of the six problem instances, compare classification, accepted steps, rejected claims, intermediate values, hints, traps, and final conclusions.
9. **Switch the chapter to generated templates only after parity:** Keep the old graphs available as regression fixtures until the generated version passes the complete set of tests.

### Success Criteria
The generic chapter solver is ready when:

- All six existing problems load from structured problem instances.
- Each problem offers only valid solution methods.
- Multiple valid methods reach the correct conclusion through graph routes.
- Incorrect arithmetic and incorrect interpretations are rejected, even when the route selector identifies the intended method correctly.
- Units, ratio order, and requested quantities are handled correctly.
- The lemonade question distinguishes additional from total sugar.
- The age example correctly shows that equal additions do not preserve the ratio.
- Existing problem-specific tests continue to pass against the generic templates.

---

## Final Assessment
This project is already a valid prototype of a method-aware tutoring system. The biggest weakness is not the idea itself, but the fact that the project is still focused on a single problem and has not yet been generalized into a learning platform.

### Best strategic conclusion
Do not abandon the current tutor. Instead, turn it into a reusable engine first, then scale the UI and product layer around it.

### Best product positioning
A step-aware math tutor that teaches through reasoning paths, not just final answers.

### Final short version
The project is already strong at the tutoring-engine prototype stage; it now needs generalization, multi-problem expansion, and product-level learning workflow to become the full vision described in this idea file.
