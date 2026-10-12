// Solution graph for NCERT Figure it Out Q1 (g08-hegp107-p176-q1)
window.SOLUTION_GRAPHS = window.SOLUTION_GRAPHS || {};
window.SOLUTION_GRAPHS["g08-hegp107-p176-q1"] = {
  "graph_meta": {
    "graph_id": "sg-g08-hegp107-p176-q1",
    "problem_uuid": "g08-hegp107-p176-q1",
    "problem_text": "Anagh mixes 600 mL of orange juice with 900 mL of apple juice to make a fruit drink. Write the ratio of orange juice to apple juice in its simplest form.",
    "navigation_label": "Orange to apple juice ratio",
    "problem_context": { "orange": 600, "apple": 900 },
    "graph_type": "directed_acyclic_graph",
    "version": "1.0.0",
    "description": "Solution DAG for simplifying the ratio 600 : 900 to 2 : 3 using the HCF.",
    "created": "2026-10-11",
    "total_methods": 1,
    "total_nodes": 6,
    "total_edges": 5
  },
  "start_node": "start",
  "conclusion_node": "conclusion",
  "nodes": [
    {
      "id": "start",
      "type": "start",
      "label": "Problem Statement",
      "description": "The ratio is 600 : 900. Find the simplest form.",
      "prompt": "Write the ratio 600 : 900 in simplest form.",
      "accept": [],
      "hints": [
        "Divide both numbers by their common factor.",
        "The HCF of 600 and 900 is 300.",
        "600 / 300 = 2 and 900 / 300 = 3."
      ]
    },
    {
      "id": "conclusion",
      "type": "conclusion",
      "label": "Final Conclusion",
      "description": "The simplest form of 600 : 900 is 2 : 3.",
      "prompt": "State the ratio in its simplest form.",
      "accept": [
        "2:3",
        "2 : 3",
        "2 to 3",
        "the ratio is 2:3",
        "orange to apple is 2:3",
        "2/3",
        "the simplest form is 2:3"
      ],
      "hints": [
        "Divide both 600 and 900 by 300.",
        "The result is 2 : 3.",
        "So the ratio is 2 : 3."
      ]
    },
    {
      "id": "m1_simplify",
      "type": "method",
      "label": "Method 1: Simplify by HCF",
      "description": "Find the HCF of 600 and 900 and divide both terms by it.",
      "prompt": "Use the HCF to simplify the ratio.",
      "accept": [
        "simplify",
        "hcf",
        "highest common factor",
        "divide by 300",
        "reduce"
      ],
      "hints": [
        "The common factor is 300.",
        "600 ÷ 300 = 2.",
        "900 ÷ 300 = 3."
      ]
    },
    {
      "id": "m1_s1",
      "type": "step",
      "label": "Find the HCF",
      "description": "The HCF of 600 and 900 is 300.",
      "prompt": "What is the HCF of 600 and 900?",
      "accept": [
        "300",
        "hcf is 300",
        "hcf = 300",
        "highest common factor is 300",
        "gcd is 300"
      ],
      "hints": [
        "600 = 2 × 2 × 2 × 3 × 5 × 5",
        "900 = 2 × 2 × 3 × 3 × 5 × 5",
        "The greatest common factor is 300."
      ]
    },
    {
      "id": "m1_s2",
      "type": "step",
      "label": "Divide by the HCF",
      "description": "600 ÷ 300 = 2 and 900 ÷ 300 = 3.",
      "prompt": "Divide both terms by 300. What do you get?",
      "accept": [
        "600/300=2 and 900/300=3",
        "600 ÷ 300 = 2 and 900 ÷ 300 = 3",
        "2 and 3",
        "600 divided by 300 is 2, 900 divided by 300 is 3"
      ],
      "hints": [
        "600 ÷ 300 = 2",
        "900 ÷ 300 = 3",
        "So the ratio becomes 2 : 3."
      ]
    }
  ],
  "edges": [
    { "from": "start", "to": "m1_simplify", "label": "Use HCF" },
    { "from": "m1_simplify", "to": "m1_s1", "label": "Find common factor" },
    { "from": "m1_s1", "to": "m1_s2", "label": "Reduce ratio" },
    { "from": "m1_s2", "to": "conclusion", "label": "Final ratio" }
  ]
};
