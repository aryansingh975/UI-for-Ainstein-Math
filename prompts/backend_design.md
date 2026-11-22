Role of the Engine

The engine answers one question: given this raw student input, what happened? It turns text into a verdict, and it does not decide what happens next in the session. Three responsibilities need to stay separate:

Interpret: turn raw text into mathematical claims.
Evaluate: decide whether each claim is true, and whether it matches the DAG.
Decide the next action: choose validate, probe, hint, clarify, or advance.

The existing backend merges all three into tutor_engine.py, which returns a verdict and feedback text. Your new algorithm needs them split.

backend/
├── app/
│   ├── api/          # HTTP routes: start, step, reset
│   ├── engine/       # Evaluation: normalize, evaluate, claims, verdicts
│   ├── navigator/    # DAG traversal: cursor, locator, trail, lifecycle
│   ├── schemas/      # Request, response, and session data models
│   └── services/     # Session storage and logging
├── graphs/           # Solution DAG files, one per problem
└── tests/

Proposed Layered Structure

app/engine/
├── normalizer.py      # Stage 1: clean text, standardize symbols       (pure)
├── vocabulary.py      # Stage 2: detect math intent                   (pure)
├── evaluator.py       # Stage 3a: compute arithmetic, gcd, lcm        (pure)
├── claims.py          # Stage 3b: split LHS/RHS, check truth          (pure)
├── matcher.py         # Stage 4: match claims to node phrases/values  (pure)
├── tutor_engine.py    # Stage 5: pick the verdict (evaluation only)   (pure)
├── action_selector.py # Stage 6: verdict + context → next action      (pure)
└── types.py           # Verdict, Evaluation, Action, StepResult


Architectural Issues to Resolve

1. Matching is duplicated. matcher.py in the engine and _match_node in navigator/locator.py both decide whether a claim matches a node. They will drift apart. Pick one owner. I recommend matcher.py owns the matching logic, and the locator calls it.

2. Evaluation and feedback are mixed. The current tree returns feedback strings such as “That’s correct! But before we conclude...”. That couples pedagogy to presentation and makes the rules hard to test. Return a structured reason code instead, such as EARLY_CONCLUSION_NO_WORK. Text can then come from the DAG node’s prompts and hints, which is where your hint ladder lives anyway.

3. The decision tree is order-dependent: 
Rule 2 (early conclusion) runs before rule 3 (wrong claim), so a student who writes “yes, 3 × 96 = 287” gets the early-conclusion message and never hears about the arithmetic error. 
The order is probably right for pedagogy, but it should be a deliberate, documented decision, not an accident of code layout. 
Write the priority list as data, so it can be reviewed and tested as a table.

4. Verdict and action are conflated: 
The current ACCEPT, WRONG_CLAIM, and so on describe what happened. 
Your new algorithm also needs what to do about it, and that depends on hint level, attempt count, and whether the student is stuck. 
Keeping these in one enum forces every new action into the verdict list. action_selector.py solves this.

5. The engine needs context it doesn’t have. action_selector needs the number of failed attempts on this node and the hint level already given. Those come from the session, so the engine must receive a read-only snapshot of the session, not the session itself. Otherwise purity breaks.

6. Each stage needs a defined output type. The pipeline only works if every stage returns a typed value. Define these in types.py before writing any stage: