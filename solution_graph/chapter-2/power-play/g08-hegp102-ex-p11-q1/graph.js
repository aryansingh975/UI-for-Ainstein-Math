// Solution Graph for Problem: Simplify 2⁻⁴ × 2⁷
// Problem UUID: g08-hegp102-ex-p11-q1
// Chapter 2: Power Play
window.SOLUTION_GRAPHS = window.SOLUTION_GRAPHS || {};
window.SOLUTION_GRAPHS["g08-hegp102-ex-p11-q1"] = {
  "graph_meta": {
    "graph_id": "sg-g08-hegp102-ex-p11-q1",
    "problem_uuid": "g08-hegp102-ex-p11-q1",
    "problem_text": "Simplify: 2⁻⁴ × 2⁷",
    "navigation_label": "2⁻⁴ × 2⁷",
    "problem_context": {},
    "graph_type": "directed_acyclic_graph",
    "version": "1.0.0",
    "description": "Simplify the expression 2⁻⁴ × 2⁷ using laws of exponents or by expanding.",
    "created": "2026-10-12",
    "total_methods": 2,
    "total_nodes": 10,
    "total_edges": 12
  },
  "start_node": "start",
  "conclusion_node": "conclusion",
  "nodes": [
    {
      "id": "given_extraction",
      "type": "extraction",
      "optional": true,
      "label": "Identify Base and Powers",
      "description": "Identify the common base and exponents in the expression.",
      "prompt": "What base and exponents are given?",
      "accept": [
        "base 2 with powers -4 and 7",
        "base 2, exponents -4 and 7",
        "2 to the power -4 and 2 to the power 7"
      ],
      "hints": [
        "Both factors have the same base, 2."
      ]
    },
    {
      "id": "goal_extraction",
      "type": "extraction",
      "optional": true,
      "label": "Identify the Goal",
      "description": "Identify the required simplified form.",
      "prompt": "What do we need to do?",
      "accept": [
        "simplify the expression",
        "simplify",
        "find the simplified exponential form"
      ],
      "hints": [
        "The instruction is to simplify the product of powers."
      ]
    },
    {
      "id": "start",
      "type": "start",
      "label": "Problem Statement",
      "description": "Simplify 2⁻⁴ × 2⁷",
      "prompt": "How would you begin simplifying 2⁻⁴ × 2⁷?",
      "accept": [],
      "hints": [
        "Notice that both terms have the same base (2).",
        "When the bases are the same, there is a multiplication law of exponents you can apply.",
        "Try adding the exponents: −4 + 7."
      ]
    },
    {
      "id": "method1",
      "type": "method",
      "label": "Method 1: Product Rule",
      "description": "Use the Product Rule: aᵐ × aⁿ = aᵐ⁺ⁿ to add the exponents.",
      "prompt": "What law of exponents applies when you multiply two powers with the same base?",
      "accept": [
        "product rule",
        "add the exponents",
        "aᵐ × aⁿ = aᵐ⁺ⁿ",
        "when multiplying same base add exponents",
        "product of powers rule",
        "multiply same base add powers"
      ],
      "hints": [
        "Think about what happens to the exponents when you multiply same-base powers.",
        "The Product Rule says: aᵐ × aⁿ = aᵐ⁺ⁿ.",
        "Add the exponents: 2⁻⁴ × 2⁷ = 2^(−4+7)."
      ]
    },
    {
      "id": "m1_step1",
      "type": "step",
      "label": "Add the Exponents",
      "description": "Apply the product rule: 2⁻⁴ × 2⁷ = 2^(−4+7) = 2³.",
      "prompt": "What is −4 + 7? Write the result as a power of 2.",
      "accept": [
        "2³",
        "2^3",
        "-4+7=3, so 2³",
        "the exponent is 3",
        "2 to the power 3",
        "2 cubed",
        "exponent sum is 3"
      ],
      "hints": [
        "Add the two exponents: −4 and 7.",
        "−4 + 7 = 3.",
        "So the result is 2³."
      ]
    },
    {
      "id": "m1_step2",
      "type": "step",
      "label": "Evaluate 2³",
      "description": "Calculate 2³ = 2 × 2 × 2 = 8.",
      "prompt": "What is the value of 2³?",
      "accept": [
        "8",
        "2³ = 8",
        "2 cubed is 8",
        "8 (two cubed)",
        "the answer is 8"
      ],
      "hints": [
        "Expand 2³ as a repeated multiplication.",
        "2 × 2 × 2 = ?",
        "2³ = 8."
      ]
    },
    {
      "id": "method2",
      "type": "method",
      "label": "Method 2: Expand & Cancel",
      "description": "Convert 2⁻⁴ to a fraction, expand 2⁷, then divide.",
      "prompt": "How can you rewrite 2⁻⁴ as a fraction?",
      "accept": [
        "1/2⁴",
        "1/16",
        "2⁻⁴ = 1/16",
        "negative exponent means reciprocal",
        "flip to get 1 over 2 to the 4",
        "1 divided by 16"
      ],
      "hints": [
        "A negative exponent means take the reciprocal.",
        "2⁻⁴ = 1 / 2⁴.",
        "2⁻⁴ = 1/16."
      ]
    },
    {
      "id": "m2_step1",
      "type": "step",
      "label": "Expand 2⁷",
      "description": "Calculate 2⁷ = 128.",
      "prompt": "What is the value of 2⁷?",
      "accept": [
        "128",
        "2⁷ = 128",
        "2 to the 7 is 128",
        "one hundred twenty eight"
      ],
      "hints": [
        "Multiply 2 by itself 7 times.",
        "2⁶ = 64, so 2⁷ = 64 × 2.",
        "2⁷ = 128."
      ]
    },
    {
      "id": "m2_step2",
      "type": "step",
      "label": "Divide 128 ÷ 16",
      "description": "1/16 × 128 = 128/16 = 8.",
      "prompt": "What is 128 ÷ 16?",
      "accept": [
        "8",
        "128/16 = 8",
        "128 divided by 16 equals 8",
        "the quotient is 8"
      ],
      "hints": [
        "You have (1/16) × 128 = 128 ÷ 16.",
        "Think: 16 × 8 = 128.",
        "128 ÷ 16 = 8."
      ]
    },
    {
      "id": "conclusion",
      "type": "conclusion",
      "label": "Final Answer",
      "description": "2⁻⁴ × 2⁷ = 8",
      "prompt": "What is the simplified value of 2⁻⁴ × 2⁷?",
      "accept": [
        "8",
        "the answer is 8",
        "simplified form is 8",
        "equals 8"
      ],
      "hints": [
        "Both methods lead to the same answer.",
        "You should have 2³ or its computed value.",
        "2⁻⁴ × 2⁷ = 2³ = 8."
      ]
    }
  ],
  "edges": [
    { "from": "start", "to": "method1" },
    { "from": "start", "to": "method2" },
    { "from": "method1", "to": "m1_step1" },
    { "from": "m1_step1", "to": "m1_step2" },
    { "from": "m1_step2", "to": "conclusion" },
    { "from": "method2", "to": "m2_step1" },
    { "from": "m2_step1", "to": "m2_step2" },
    { "from": "m2_step2", "to": "conclusion" },
    { "from": "start", "to": "given_extraction", "label": "Identify the given information" },
    { "from": "given_extraction", "to": "goal_extraction", "label": "Identify what to find" },
    { "from": "goal_extraction", "to": "method1", "label": "Choose a solution method" },
    { "from": "goal_extraction", "to": "method2", "label": "Choose a solution method" }
  ]
};
