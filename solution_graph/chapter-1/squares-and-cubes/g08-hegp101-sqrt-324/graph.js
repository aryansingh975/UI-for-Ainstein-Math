// Solution graph for g08-hegp101-sqrt-324 (generated from graph.json — do not hand-edit).
window.SOLUTION_GRAPHS = window.SOLUTION_GRAPHS || {};
window.SOLUTION_GRAPHS["g08-hegp101-sqrt-324"] = {
  "graph_meta": {
    "graph_id": "sg-a1b2c3d4-e5f6-7890-abcd-ef1234567801",
    "problem_uuid": "g08-hegp101-sqrt-324",
    "problem_text": "Find the square root of 324 using prime factorisation.",
    "navigation_label": "√324 by Prime Factorisation",
    "problem_context": {},
    "graph_type": "directed_acyclic_graph",
    "version": "1.0.0",
    "description": "Two-method solution graph for finding √324: Method 1 uses prime factorisation and grouping into pairs; Method 2 uses estimation/verification.",
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
      "description": "Find the square root of 324 using prime factorisation.",
      "prompt": "Find the square root of 324 using prime factorisation. How would you begin?",
      "accept": [],
      "hints": [
        "Think about breaking 324 into its prime factors.",
        "Start dividing 324 by the smallest prime number that divides it evenly.",
        "324 is even, so start dividing by 2."
      ]
    },
    {
      "id": "given_extraction",
      "type": "extraction",
      "optional": true,
      "label": "Identify Given Information",
      "description": "Identify the number whose square root is to be found.",
      "prompt": "What number are we finding the square root of?",
      "accept": [
        "324",
        "the number 324",
        "324 is given",
        "we are given 324"
      ],
      "hints": [
        "Look at the problem statement carefully.",
        "The problem asks for the square root of a specific number.",
        "The given number is 324."
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
        "square root of 324",
        "√324",
        "sqrt(324)",
        "find √324",
        "the square root",
        "root of 324"
      ],
      "hints": [
        "Read the problem again — what are we solving for?",
        "We need to find a number that, when multiplied by itself, gives 324.",
        "We need to find √324."
      ]
    },
    {
      "id": "method1",
      "type": "method",
      "label": "Method 1: Prime Factorisation",
      "description": "Find √324 by expressing 324 as a product of prime factors and grouping them into pairs.",
      "prompt": "Which method will you use? Choose prime factorisation — what is your first step?",
      "accept": [
        "prime factorisation",
        "prime factorization",
        "factor tree",
        "divide by primes",
        "prime factors"
      ],
      "hints": [
        "Prime factorisation means writing the number as a product of prime numbers.",
        "Start dividing 324 by the smallest prime (2) repeatedly, then move to 3.",
        "Begin: 324 ÷ 2 = 162."
      ]
    },
    {
      "id": "m1_step1",
      "type": "step",
      "label": "Step 1: Divide by Primes",
      "description": "Repeatedly divide 324 by primes to get the full factorisation.",
      "prompt": "Divide 324 by prime numbers step by step. What is the prime factorisation of 324?",
      "accept": [
        "2² × 3⁴",
        "2^2 × 3^4",
        "2^2 x 3^4",
        "4 × 81",
        "2 squared times 3 to the 4th",
        "2² x 3⁴",
        "3⁴ × 2²",
        "324 = 2² × 3⁴"
      ],
      "hints": [
        "324 ÷ 2 = 162, 162 ÷ 2 = 81. Now 81 is odd — try dividing by 3.",
        "81 ÷ 3 = 27, 27 ÷ 3 = 9, 9 ÷ 3 = 3, 3 ÷ 3 = 1. You have used 2 twice and 3 four times.",
        "324 = 2² × 3⁴."
      ]
    },
    {
      "id": "m1_step2",
      "type": "step",
      "label": "Step 2: Group Factors into Pairs",
      "description": "Pair the prime factors and rewrite as a perfect square.",
      "prompt": "Now group the prime factors into pairs. What perfect square expression do you get?",
      "accept": [
        "(2 × 3²)²",
        "(2 × 9)²",
        "18²",
        "(18)²",
        "2² × (3²)²",
        "2^2 × 3^4 = (2 × 9)²",
        "(2×9)²"
      ],
      "hints": [
        "For a perfect square, every prime factor must appear in pairs (even exponent).",
        "Group 2² as (2)² and 3⁴ as (3²)². Then combine: (2 × 3²)².",
        "2² × 3⁴ = (2 × 9)² = 18²."
      ]
    },
    {
      "id": "m1_step3",
      "type": "step",
      "label": "Step 3: Take the Square Root",
      "description": "Extract the square root from the perfect square expression.",
      "prompt": "Given that 324 = 18², what is √324?",
      "accept": [
        "18",
        "√324 = 18",
        "the answer is 18",
        "18²=324 so √324=18"
      ],
      "hints": [
        "If a number equals x², then its square root is x.",
        "We found 324 = 18², so √324 = ?",
        "√324 = 18."
      ]
    },
    {
      "id": "method2",
      "type": "method",
      "label": "Method 2: Estimation & Verification",
      "description": "Estimate √324 by testing nearby perfect squares.",
      "prompt": "Use estimation: which two perfect squares is 324 between?",
      "accept": [
        "estimation",
        "guess and check",
        "trial and error",
        "between 17 and 19",
        "17² and 19²",
        "289 and 361"
      ],
      "hints": [
        "Think of integers whose squares are close to 324.",
        "Try 17² = 289 and 19² = 361. Where does 324 fall?",
        "324 is between 289 and 361, so try 18."
      ]
    },
    {
      "id": "m2_step1",
      "type": "step",
      "label": "Step 1: Test 18² = 324",
      "description": "Verify that 18² equals 324.",
      "prompt": "Calculate 18². Does it equal 324?",
      "accept": [
        "18² = 324",
        "18 × 18 = 324",
        "yes 18² = 324",
        "324",
        "18 squared is 324"
      ],
      "hints": [
        "Multiply 18 × 18.",
        "18 × 18 = 18 × 10 + 18 × 8 = 180 + 144 = 324.",
        "18² = 324, so √324 = 18 ✓"
      ]
    },
    {
      "id": "m2_step2",
      "type": "step",
      "label": "Step 2: Confirm √324 = 18",
      "description": "State the final answer from the estimation method.",
      "prompt": "Since 18² = 324, what is √324?",
      "accept": [
        "18",
        "√324 = 18",
        "the square root is 18",
        "18²=324 so √324=18"
      ],
      "hints": [
        "The square root of a number n² is n.",
        "We verified 18² = 324.",
        "√324 = 18."
      ]
    },
    {
      "id": "conclusion",
      "type": "conclusion",
      "label": "Final Answer",
      "description": "The square root of 324 is 18.",
      "prompt": "What is √324?",
      "accept": [
        "18",
        "√324 = 18",
        "the square root of 324 is 18",
        "18²=324",
        "answer is 18"
      ],
      "hints": [
        "Both methods should give the same answer.",
        "Using prime factorisation: 324 = 2² × 3⁴ = 18².",
        "√324 = 18."
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
