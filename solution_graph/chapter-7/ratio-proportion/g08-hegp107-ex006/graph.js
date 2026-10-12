// Standalone solution graph for NCERT Example 6 (Neelima age ratio problem)
window.SOLUTION_GRAPHS = window.SOLUTION_GRAPHS || {};
window.SOLUTION_GRAPHS["g08-hegp107-ex006"] = {
  "graph_meta": {
    "graph_id": "sg-g08-hegp107-ex006",
    "problem_uuid": "g08-hegp107-ex006",
    "problem_text": "When Neelima was 3 years old, her mother was 30 years old. What was the ratio of Neelima's age to her mother's age? When Neelima is 12, what is the ratio of their ages? Would it remain the same?",
    "navigation_label": "Neelima's age ratios",
    "problem_context": { "first": [3, 30], "second": [12, 39] },
    "graph_type": "directed_acyclic_graph",
    "version": "1.0.0",
    "description": "Solution DAG for the age-ratio problem. It shows that 3:30 simplifies to 1:10, but 12:39 simplifies to 4:13, so the ratio does not remain the same when a common number is added to both quantities.",
    "created": "2026-10-07",
    "total_methods": 3,
    "total_nodes": 18,
    "total_edges": 18
  },
  "start_node": "start",
  "conclusion_node": "conclusion",
  "nodes": [
    {
      "id": "start",
      "type": "start",
      "label": "Problem Statement",
      "description": "Neelima and her mother are compared at ages 3 and 30 and then later at 12 and 39.",
      "prompt": "Find the ratio at age 3 and again at age 12. Does the ratio stay the same?",
      "accept": [],
      "hints": [
        "Write the ratio of Neelima's age to her mother's age at each stage.",
        "Simplify the ratios.",
        "Check whether adding the same number to both ages keeps the ratio unchanged."
      ]
    },
    {
      "id": "conclusion",
      "type": "conclusion",
      "label": "Final Conclusion",
      "description": "No, the ratio does not remain the same. 3:30 simplifies to 1:10, while 12:39 simplifies to 4:13.",
      "prompt": "State whether the ratio remains the same.",
      "accept": [
        "no",
        "no, it does not remain the same",
        "it changes",
        "not the same",
        "1:10 and 4:13 are different",
        "the ratio changes"
      ],
      "hints": [
        "3:30 simplifies to 1:10.",
        "12:39 simplifies to 4:13.",
        "Since 1:10 and 4:13 are not equal, the ratio changes."
      ]
    },
    {
      "id": "m1_simplify",
      "type": "method",
      "label": "Method 1: Simplify the age ratios",
      "description": "Simplify the boy's and mother's ages at both times to compare the ratios.",
      "prompt": "Simplify 3:30 and 12:39 to compare them.",
      "accept": ["simplify", "reduce", "find simplest form"],
      "hints": [
        "Divide 3 and 30 by 3.",
        "Divide 12 and 39 by 3.",
        "Compare the simplified ratios."
      ]
    },
    {
      "id": "m1_s1",
      "type": "step",
      "label": "Simplify 3:30",
      "description": "3:30 simplifies to 1:10.",
      "prompt": "Reduce 3:30 to its simplest form.",
      "accept": ["1:10", "1 : 10", "one to ten", "3/30=1/10"],
      "hints": [
        "Both numbers are divisible by 3.",
        "3 ÷ 3 = 1 and 30 ÷ 3 = 10.",
        "So the ratio is 1:10."
      ]
    },
    {
      "id": "m1_s2",
      "type": "step",
      "label": "Simplify 12:39",
      "description": "12:39 simplifies to 4:13.",
      "prompt": "Reduce 12:39 to its simplest form.",
      "accept": ["4:13", "4 : 13", "four to thirteen", "12/39=4/13"],
      "hints": [
        "Divide both numbers by 3.",
        "12 ÷ 3 = 4 and 39 ÷ 3 = 13.",
        "So the ratio is 4:13."
      ]
    },
    {
      "id": "m1_s3",
      "type": "step",
      "label": "Compare the ratios",
      "description": "1:10 and 4:13 are different, so the ratio does not stay the same.",
      "prompt": "Are 1:10 and 4:13 the same?",
      "accept": ["no", "not the same", "different", "1:10 is not 4:13"],
      "hints": [
        "1:10 and 4:13 are not equal.",
        "So the ratio changes over time."
      ]
    },
    {
      "id": "m2_addition",
      "type": "method",
      "label": "Method 2: Check the effect of adding a constant",
      "description": "See what happens when 9 years are added to both ages.",
      "prompt": "If 9 years are added to both ages, does the ratio stay proportional?",
      "accept": ["common difference", "add same number", "same number added"],
      "hints": [
        "Age 3 becomes 12, and age 30 becomes 39.",
        "A common addition changes the ratio.",
        "That is why the ratio is not the same."
      ]
    },
    {
      "id": "m2_s1",
      "type": "step",
      "label": "Add 9 years to both ages",
      "description": "3 + 9 = 12 and 30 + 9 = 39.",
      "prompt": "What are the ages nine years later?",
      "accept": ["12 and 39", "12, 39", "3+9=12 and 30+9=39"],
      "hints": [
        "Neelima is 12.",
        "Her mother is 39.",
        "The ages changed by the same amount, but the ratio is different."
      ]
    },
    {
      "id": "m2_s2",
      "type": "step",
      "label": "Recognize the ratio changed",
      "description": "12:39 is not the same as 3:30.",
      "prompt": "Why does the ratio not stay the same?",
      "accept": ["because adding the same number changes the ratio", "not proportional", "same shift does not preserve ratio"],
      "hints": [
        "Adding the same number to both terms does not preserve a ratio.",
        "The ratio changes because the quantities are not scaled by the same factor.",
        "So the ratio is not the same."
      ]
    },
    {
      "id": "m3_compare",
      "type": "method",
      "label": "Method 3: Compare the values directly",
      "description": "Compare the ratio values at the two ages to decide if they remain equal.",
      "prompt": "Check the value of the ratio at both points in time.",
      "accept": ["value", "compare", "check ratio value"],
      "hints": [
        "The first ratio value is 1/10.",
        "The second ratio value is 4/13.",
        "Since 1/10 ≠ 4/13, the ratio changes."
      ]
    },
    {
      "id": "m3_s1",
      "type": "step",
      "label": "First ratio value",
      "description": "3/30 = 1/10.",
      "prompt": "What is the value of 3:30?",
      "accept": ["1/10", "one tenth", "0.1"],
      "hints": [
        "3/30 simplifies to 1/10.",
        "The value is 0.1."
      ]
    },
    {
      "id": "m3_s2",
      "type": "step",
      "label": "Second ratio value",
      "description": "12/39 = 4/13.",
      "prompt": "What is the value of 12:39?",
      "accept": ["4/13", "four thirteenths", "0.307..."],
      "hints": [
        "Simplify 12:39 by dividing by 3.",
        "12 ÷ 3 = 4 and 39 ÷ 3 = 13.",
        "The value is 4/13."
      ]
    }
  ],
  "edges": [
    { "from": "start", "to": "m1_simplify", "label": "Simplify the age ratios" },
    { "from": "start", "to": "m2_addition", "label": "Check the effect of adding 9 years" },
    { "from": "start", "to": "m3_compare", "label": "Compare ratio values" },
    { "from": "m1_simplify", "to": "m1_s1", "label": "Simplify first ratio" },
    { "from": "m1_s1", "to": "m1_s2", "label": "Simplify second ratio" },
    { "from": "m1_s2", "to": "m1_s3", "label": "Compare simplified ratios" },
    { "from": "m1_s3", "to": "conclusion", "label": "Different ratios" },
    { "from": "m2_addition", "to": "m2_s1", "label": "Compute later ages" },
    { "from": "m2_s1", "to": "m2_s2", "label": "Reason about the change" },
    { "from": "m2_s2", "to": "conclusion", "label": "The ratio changes" },
    { "from": "m3_compare", "to": "m3_s1", "label": "Evaluate first ratio" },
    { "from": "m3_s1", "to": "m3_s2", "label": "Evaluate second ratio" },
    { "from": "m3_s2", "to": "conclusion", "label": "Different values" }
  ]
};
