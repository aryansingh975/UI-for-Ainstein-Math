You are an expert Backend System Architect specialized in Natural Language Processing (NLP), String-Similarity metrics, and Pure Function pipeline designs.

### 🎯 Objective
Your task is to design a robust, deterministic, and completely **stateless** **Navigator Module** (V1) for the backend of a Socratic tutoring engine. 

### 🛑 Critical Architectural Constraint (V1 Boundary)
The navigator module is currently **entirely blind to the external system state**. It does not track user history, it does not know the "current" step, and it has no session memory. It acts as a pure function with exactly two inputs and one output:
*   **Input 1:** A Directed Acyclic Graph (DAG) in a JSON format.
*   **Input 2:** A raw `string` containing the user's input.
*   **Output:** A single matching `node` object from the input DAG, OR the fallback string: `"No node found"`.

#### Node Schema Reference:
```json
{
  "id": "goal_extraction",
  "type": "extraction",
  "optional": false,
  "label": "Identify the Goal",
  "description": "What does the problem ask us to find?",
  "prompt": "What do we need to find?",
  "accept": [
    "daughter's present age",
    "present age of daughter",
    "age of daughter",
    "find x",
    "daughter's age now",
    "how old is the daughter"
  ],
  "hints": [
    "Re-read the last sentence of the problem.",
    "The problem asks for the daughter's current age.",
    "We need to find the present age of the daughter."
  ]
}
```

### Prototypical Design Idea to Build Upon: 

Create a semantic_distance function that assigns to each node a scalar value between 0 and 1. 
The node with the greatest value is the node that is semantically the closest to the input string. And that is the node the navigator module returns. 

You must design a robust pipeline that replaces basic string matching with something that contains the following components:

1. **Deterministic Text Normalization Pipeline:**
 Before computing distances, both the input string and all phrases inside the "accept" array of the input DAG must pass through a strict sanitization function:
 
 - Lowercasing & Stripping: Convert all text to lowercase and remove trailing/leading whitespaces.
 
 - Article & Stopword Stripping: Remove high-frequency, low-meaning words like "a", "an", "the", 
    "is", "to", "what", "find". 
    For example, "find the daughter's age" transforms into a list ["daughter", "age"].
 
 - Symbol Standardisation: Convert algebraic indicators like "=", "equals", or "is equal to" into 
    a unified token (e.g., eq), and strip out non-mathematical punctuation.
 
2. **The Scoring Metric** 
 Instead of binary 1 or 0 string matching, use an overlap or token-based ratio metric. 
 One strong deterministic approach might be highly effective for this:

 - Jaccard Similarity: It calculates the ratio of the size of the intersection of two sets 
    to the size of their union. Mathematically, for two lists $A$ and $B$, it is expressed as:
    $J(A,B) = \frac{|A \cap B|}{|A \cup B|}$. 
    
    Example: 
    User Input ($A$): `"We are trying to find the daughter's present age"` $\rightarrow$ `{'age', 'daughter', 'present'}`
    
    Accept Phrase ($B$): `"daughter present age"` $\rightarrow$ `{'age', 'daughter', 'present'}`
    
    $$\text{Intersection} (A \cap B) = \{\text{'age', 'daughter', 'present'}\} \quad (\text{Size } = 3)$$
    $$\text{Union } (A \cup B) = \{\text{'age', 'daughter', 'present'}\} \quad (\text{Size } = 3)$$
    $$J(A, B) = \frac{3}{3} = 1.00 \text{ (100\% similarity)}$$

3. **Scoring Hierarchy:**
   - Multiple nodes might end up getting similar score, in that case we will need to establish a 
    clear scoring hierarchy. 

   - *Rule 1: Exact Match Dominance.* If an input exactly matches an element in a node's `accept` array post-normalization, it must win instantly, short-circuiting fuzzier matches elsewhere.

   - *Rule 2: Specificity Weighting.* Longer, highly specific phrase matches must rank higher than short, ambiguous single-word overlaps to prevent false positives.

4. **Threshold Guardrails:**
   - Enforce a strict mathematical distance/similarity threshold. If the highest scoring node fails to meet this threshold, the function must return `"No node found"`.

---

### 📈 Future Extensibility Note (Design For v2)
While V1 has only two inputs, V2 will later will take more inputs like the active step ID or graph-edge traversal history. 

* Ensure your module structure isolates the scoring logic so that an additional contextual weight parameter can be cleanly injected later without refactoring the base algorithms.

---


### 📋 Deliverables Required in Your Design Plan
Provide a comprehensive engineering design document covering:

1. **Pure Function Pipeline Architecture:** Structured data-flow showing how the raw string and DAG are processed side-by-side.

2. **The Scoring & Matching Algorithm:** Detail the exact mathematical formulas used to combine token-based similarity and character-based n-gram similarity into a single final score.

3. **Collision Resolution Strategy:** Explain how the engine cleanly differentiates between nodes when similar phrases or mathematical variables overlap across different steps without using state.

4. **Complete Code Prototype:** Provide clean, runnable Python code implementing `navigate_dag(dag_json, user_input, threshold)` handling all edge cases.