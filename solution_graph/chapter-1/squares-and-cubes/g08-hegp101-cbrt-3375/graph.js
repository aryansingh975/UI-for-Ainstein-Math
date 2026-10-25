// Solution graph for g08-hegp101-cbrt-3375 (generated from graph.json — do not hand-edit).
window.SOLUTION_GRAPHS = window.SOLUTION_GRAPHS || {};
window.SOLUTION_GRAPHS["g08-hegp101-cbrt-3375"] = {
  "graph_meta": {
    "graph_id": "sg-b2c3d4e5-f6a7-8901-bcde-fa2345678902",
    "problem_uuid": "g08-hegp101-cbrt-3375",
    "problem_text": "Find the cube root of 3375 using prime factorisation.",
    "navigation_label": "∛3375 by Prime Factorisation",
    "problem_context": {},
    "graph_type": "directed_acyclic_graph",
    "version": "1.0.0",
    "description": "Two-method solution graph for finding ∛3375: Method 1 uses prime factorisation and grouping into triples; Method 2 uses estimation/verification.",
    "created": "2026-10-12",
    "total_methods": 2,
    "total_nodes": 11,
    "total_edges": 13
  },
  "start_node": "start",
  "conclusion_node": "conclusion",
  "nodes": [
    {
      "id": "start",
      "type": "start",
      "label": "Problem Statement",
      "description": "Find the cube root of 3375 using prime factorisation.",
      "prompt": "Find the cube root of 3375 using prime factorisation. How would you begin?",
      "accept": [],
      "hints": [
        "Think about breaking 3375 into its prime factors.",
        "Start dividing 3375 by the smallest prime that divides it evenly.",
        "3375 ends in 5, so it is divisible by 5 — but also check 3: 3+3+7+5=18, divisible by 3."
      ]
    },
    {
      "id": "given_extraction",
      "type": "extraction",
      "optional": true,
      "label": "Identify Given Information",
      "description": "Identify the number whose cube root is to be found.",
      "prompt": "What number are we finding the cube root of?",
      "accept": [
        "3375",
        "the number 3375",
        "3375 is given",
        "we are given 3375"
      ],
      "hints": [
        "Look at the problem statement.",
        "The problem asks for the cube root of a specific number.",
        "The given number is 3375."
      ]
    },
    {
      "id": "goal_extraction",
      "type": "extraction",
      "optional": true,
      "label": "Identify the Goal",
      "description": "State what we need to find.",
      "prompt": "What do we need to find?",
      "accept": [
        "cube root of 3375",
        "∛3375",
        "cbrt(3375)",
        "find ∛3375",
        "the cube root",
        "root of 3375"
      ],
      "hints": [
        "Read the problem — what are we solving for?",
        "We need a number that, when cubed, gives 3375.",
        "We need to find ∛3375."
      ]
    },
    {
      "id": "method1",
      "type": "method",
      "label": "Method 1: Prime Factorisation",
      "description": "Find ∛3375 by expressing 3375 as a product of prime factors and grouping them into triples.",
      "prompt": "Choose prime factorisation. What is your first step to factorise 3375?",
      "accept": [
        "prime factorisation",
        "prime factorization",
        "factor tree",
        "divide by primes",
        "prime factors",
        "divide by 3",
        "divide by 5"
      ],
      "hints": [
        "Prime factorisation: write the number as a product of primes.",
        "Check divisibility by 3 first: 3+3+7+5=18, so 3375 ÷ 3 = 1125.",
        "Start: 3375 ÷ 3 = 1125."
      ]
    },
    {
      "id": "m1_step1",
      "type": "step",
      "label": "Step 1: Divide by Primes",
      "description": "Repeatedly divide 3375 by primes to get the full prime factorisation.",
      "prompt": "Divide 3375 by primes step by step. What is the prime factorisation of 3375?",
      "accept": [
        "3³ × 5³",
        "3^3 × 5^3",
        "3^3 x 5^3",
        "27 × 125",
        "3 cubed times 5 cubed",
        "5³ × 3³",
        "3375 = 3³ × 5³"
      ],
      "hints": [
        "3375 ÷ 3 = 1125, 1125 ÷ 3 = 375, 375 ÷ 3 = 125. Now try dividing 125 by 5.",
        "125 ÷ 5 = 25, 25 ÷ 5 = 5, 5 ÷ 5 = 1. You used 3 three times and 5 three times.",
        "3375 = 3³ × 5³."
      ]
    },
    {
      "id": "m1_step2",
      "type": "step",
      "label": "Step 2: Group Factors into Triples",
      "description": "Group the prime factors into triples and rewrite as a perfect cube.",
      "prompt": "Group the prime factors into triples. What perfect cube expression do you get?",
      "accept": [
        "(3 × 5)³",
        "(15)³",
        "15³",
        "3³ × 5³ = (3×5)³",
        "(3×5)^3",
        "15 cubed"
      ],
      "hints": [
        "For a perfect cube, every prime factor must appear in groups of three.",
        "3³ × 5³ can be combined using the rule (a × b)³ = a³ × b³.",
        "3³ × 5³ = (3 × 5)³ = 15³."
      ]
    },
    {
      "id": "m1_step3",
      "type": "step",
      "label": "Step 3: Take the Cube Root",
      "description": "Extract the cube root from the perfect cube expression.",
      "prompt": "Given that 3375 = 15³, what is ∛3375?",
      "accept": [
        "15",
        "∛3375 = 15",
        "the answer is 15",
        "15³=3375 so ∛3375=15"
      ],
      "hints": [
        "If a number equals x³, then its cube root is x.",
        "We found 3375 = 15³, so ∛3375 = ?",
        "∛3375 = 15."
      ]
    },
    {
      "id": "method2",
      "type": "method",
      "label": "Method 2: Estimation & Verification",
      "description": "Estimate ∛3375 by testing nearby perfect cubes.",
      "prompt": "Use estimation: what are some perfect cubes near 3375?",
      "accept": [
        "estimation",
        "guess and check",
        "trial and error",
        "10 cubed",
        "15 cubed",
        "1000 and 3375"
      ],
      "hints": [
        "Think of integers whose cubes are close to 3375.",
        "10³ = 1000 and 20³ = 8000. Try numbers between 10 and 20.",
        "Try 15: 15³ = 15 × 15 × 15."
      ]
    },
    {
      "id": "m2_step1",
      "type": "step",
      "label": "Step 1: Test 15³ = 3375",
      "description": "Verify that 15³ equals 3375.",
      "prompt": "Calculate 15³. Does it equal 3375?",
      "accept": [
        "15³ = 3375",
        "15 × 15 × 15 = 3375",
        "yes 15³ = 3375",
        "3375",
        "15 cubed is 3375"
      ],
      "hints": [
        "Multiply 15 × 15 first, then multiply by 15 again.",
        "15 × 15 = 225; 225 × 15 = 3375.",
        "15³ = 3375, so ∛3375 = 15 ✓"
      ]
    },
    {
      "id": "m2_step2",
      "type": "step",
      "label": "Step 2: Confirm ∛3375 = 15",
      "description": "State the final answer from the estimation method.",
      "prompt": "Since 15³ = 3375, what is ∛3375?",
      "accept": [
        "15",
        "∛3375 = 15",
        "the cube root is 15",
        "15³=3375 so ∛3375=15"
      ],
      "hints": [
        "The cube root of n³ is n.",
        "We verified 15³ = 3375.",
        "∛3375 = 15."
      ]
    },
    {
      "id": "conclusion",
      "type": "conclusion",
      "label": "Final Answer",
      "description": "The cube root of 3375 is 15.",
      "prompt": "What is ∛3375?",
      "accept": [
        "15",
        "∛3375 = 15",
        "the cube root of 3375 is 15",
        "15³=3375",
        "answer is 15"
      ],
      "hints": [
        "Both methods should give the same answer.",
        "Using prime factorisation: 3375 = 3³ × 5³ = 15³.",
        "∛3375 = 15."
      ]
    }
  ],
  "edges": [
    {
      "from": "start",
      "to": "given_extraction"
    },
    {
      "from": "given_extraction",
      "to": "goal_extraction"
    },
    {
      "from": "goal_extraction",
      "to": "method1"
    },
    {
      "from": "goal_extraction",
      "to": "method2"
    },
    {
      "from": "start",
      "to": "method1"
    },
    {
      "from": "start",
      "to": "method2"
    },
    {
      "from": "method1",
      "to": "m1_step1"
    },
    {
      "from": "m1_step1",
      "to": "m1_step2"
    },
    {
      "from": "m1_step2",
      "to": "m1_step3"
    },
    {
      "from": "m1_step3",
      "to": "conclusion"
    },
    {
      "from": "method2",
      "to": "m2_step1"
    },
    {
      "from": "m2_step1",
      "to": "m2_step2"
    },
    {
      "from": "m2_step2",
      "to": "conclusion"
    }
  ]
};
