// Solution Graph (g08-lin-word-ex001)
// Embedded as JS to avoid file:// fetch restrictions
// 4 methods for the pens-and-notebooks word problem: substitution and elimination share step 1.
window.SOLUTION_GRAPHS = window.SOLUTION_GRAPHS || {};
window.SOLUTION_GRAPHS["g08-lin-word-ex001"] = {
  "graph_meta": {
    "graph_id": "sg-g08-lin-word-ex001",
    "problem_uuid": "g08-lin-word-ex001",
    "problem_text": "Riya goes to a stationery shop. Pens cost ₹5 each and notebooks cost ₹12 each. She buys 10 items in total and pays ₹78. How many pens and how many notebooks did she buy?",
    "equation": "5*(10 - x) + 12*x = 78",
    "variable": "x",
    "system": {
      "variables": {
        "p": "number of pens",
        "n": "number of notebooks"
      },
      "equations": [
        "p + n = 10",
        "5*p + 12*n = 78"
      ],
      "solution": {
        "p": 6,
        "n": 4
      },
      "note": "One-variable form above uses x = number of notebooks (so x = 4). The current SymPy checker uses 'equation'; 'system' is for two-variable checking."
    },
    "use_jev": true,
    "graph_type": "directed_acyclic_graph",
    "version": "1.0.0",
    "description": "Solution DAG for the pens-and-notebooks word problem — four valid methods: one variable, substitution, elimination, trial and error. Substitution and elimination share step 1 (writing the two equations) and differ from step 2. The tutor accepts any path through this graph as a valid solution.",
    "created": "2026-10-22",
    "total_methods": 4,
    "total_nodes": 24,
    "total_edges": 27
  },
  "start_node": "start",
  "conclusion_node": "conclusion",
  "nodes": [
    {
      "id": "start",
      "type": "start",
      "label": "Problem Statement",
      "description": "Riya goes to a stationery shop. Pens cost ₹5 each and notebooks cost ₹12 each. She buys 10 items in total and pays ₹78. How many pens and how many notebooks did she buy?",
      "prompt": "Read the problem. How many pens and how many notebooks did Riya buy?",
      "accept": [],
      "hints": [
        "Two things are unknown: the number of pens and the number of notebooks.",
        "Use the total number of items (10) and the total cost (₹78).",
        "You can use one variable, two variables (substitution or elimination), or trial and error."
      ]
    },
    {
      "id": "conclusion",
      "type": "conclusion",
      "label": "Final Conclusion",
      "description": "Riya bought 6 pens and 4 notebooks.",
      "prompt": "State your final answer: how many pens and how many notebooks?",
      "accept": [
        "6 pens and 4 notebooks",
        "6 pens, 4 notebooks",
        "4 notebooks and 6 pens",
        "p = 6, n = 4",
        "p = 6 and n = 4",
        "n = 4, p = 6",
        "pens = 6, notebooks = 4",
        "6 pens 4 notebooks",
        "she bought 6 pens and 4 notebooks"
      ],
      "hints": [
        "Check the count: 6 + 4 = 10.",
        "Check the cost: 6 × 5 + 4 × 12 = 30 + 48 = 78.",
        "6 pens and 4 notebooks."
      ]
    },
    {
      "id": "m1_one_var",
      "type": "method",
      "label": "Method 1: One Variable",
      "description": "Let the number of notebooks be x, so the number of pens is 10 − x. Write one equation for the total cost and solve it.",
      "prompt": "Choose a method to solve this problem.",
      "accept": [
        "one variable",
        "let x",
        "10 - x",
        "10 − x",
        "single variable"
      ],
      "hints": [
        "Use only one unknown: let notebooks = x.",
        "Then pens = 10 − x.",
        "Total cost: 5(10 − x) + 12x = 78."
      ],
      "jev_description": "One variable. Steps: (1) let notebooks = x so pens = 10 - x, (2) one equation 5(10 - x) + 12x = 78, (3) 50 + 7x = 78, (4) 7x = 28 so x = 4, (5) pens = 10 - 4 = 6. Identified by using a single letter (x) and writing the other quantity as 10 - x from the start."
    },
    {
      "id": "m1_s1",
      "type": "step",
      "label": "Define the variable",
      "description": "Let notebooks = x. Then pens = 10 − x.",
      "prompt": "Choose a variable for one quantity. How do you write the other quantity?",
      "accept": [
        "notebooks = x, pens = 10 - x",
        "pens = 10 - x",
        "pens = 10 − x",
        "10 - x pens",
        "10 − x"
      ],
      "hints": [
        "Let the number of notebooks be x.",
        "There are 10 items in total.",
        "So pens = 10 − x."
      ]
    },
    {
      "id": "m1_s2",
      "type": "step",
      "label": "Write the cost equation",
      "description": "5(10 − x) + 12x = 78",
      "prompt": "Write an equation for the total cost of ₹78.",
      "accept": [
        "5(10 - x) + 12x = 78",
        "5(10 − x) + 12x = 78",
        "5*(10-x)+12x=78"
      ],
      "hints": [
        "Cost of pens = 5 × (10 − x).",
        "Cost of notebooks = 12 × x.",
        "5(10 − x) + 12x = 78"
      ]
    },
    {
      "id": "m1_s3",
      "type": "step",
      "label": "Expand and simplify",
      "description": "50 − 5x + 12x = 78, so 50 + 7x = 78.",
      "prompt": "Expand the bracket and combine like terms. What do you get?",
      "accept": [
        "50 + 7x = 78",
        "50 - 5x + 12x = 78",
        "50 − 5x + 12x = 78"
      ],
      "hints": [
        "5 × 10 = 50 and 5 × (−x) = −5x.",
        "−5x + 12x = 7x.",
        "50 + 7x = 78"
      ]
    },
    {
      "id": "m1_s4",
      "type": "step",
      "label": "Solve for x",
      "description": "7x = 78 − 50 = 28, so x = 4.",
      "prompt": "Solve 50 + 7x = 78. What is x?",
      "accept": [
        "7x = 28",
        "x = 4",
        "7x = 28, x = 4"
      ],
      "hints": [
        "Subtract 50 from both sides: 7x = 28.",
        "Divide by 7.",
        "x = 4"
      ]
    },
    {
      "id": "m1_s5",
      "type": "step",
      "label": "Find the number of pens",
      "description": "Pens = 10 − 4 = 6.",
      "prompt": "Notebooks = 4. How many pens?",
      "accept": [
        "10 - 4 = 6",
        "10 − 4 = 6",
        "pens = 6",
        "6 pens"
      ],
      "hints": [
        "Pens = 10 − x.",
        "x = 4.",
        "10 − 4 = 6"
      ]
    },
    {
      "id": "m2_substitution",
      "type": "method",
      "label": "Method 2: Substitution",
      "description": "Write two equations (p + n = 10 and 5p + 12n = 78), make p the subject of the first (p = 10 − n), and substitute it into the second.",
      "prompt": "Choose a method to solve this problem.",
      "accept": [
        "substitution",
        "substitute",
        "p = 10 - n",
        "p = 10 − n"
      ],
      "hints": [
        "Write two equations.",
        "From p + n = 10, get p = 10 − n.",
        "Put p = 10 − n into 5p + 12n = 78."
      ],
      "jev_description": "Substitution with two variables. Steps: (1) p + n = 10 and 5p + 12n = 78, (2) rearrange the first: p = 10 - n, (3) substitute: 5(10 - n) + 12n = 78, (4) 7n = 28 so n = 4, (5) p = 6. Step 1 is the same as elimination; step 2 (making one variable the subject, p = 10 - n) is what identifies substitution."
    },
    {
      "id": "m2_s1",
      "type": "step",
      "label": "Write two equations",
      "description": "Let pens = p and notebooks = n. Then p + n = 10 and 5p + 12n = 78.",
      "prompt": "Use two variables. Write one equation for the number of items and one for the cost.",
      "accept": [
        "p + n = 10 and 5p + 12n = 78",
        "p + n = 10, 5p + 12n = 78",
        "p+n=10, 5p+12n=78",
        "p + n = 10",
        "5p + 12n = 78"
      ],
      "hints": [
        "Let pens = p and notebooks = n.",
        "Items: p + n = 10.",
        "Cost: 5p + 12n = 78."
      ]
    },
    {
      "id": "m2_s2",
      "type": "step",
      "label": "Make p the subject",
      "description": "From p + n = 10: p = 10 − n.",
      "prompt": "Rearrange p + n = 10 to make p the subject.",
      "accept": [
        "p = 10 - n",
        "p = 10 − n",
        "p=10-n"
      ],
      "hints": [
        "Subtract n from both sides.",
        "p = 10 − n",
        "Now substitute this into the cost equation."
      ]
    },
    {
      "id": "m2_s3",
      "type": "step",
      "label": "Substitute",
      "description": "5(10 − n) + 12n = 78",
      "prompt": "Substitute p = 10 − n into 5p + 12n = 78.",
      "accept": [
        "5(10 - n) + 12n = 78",
        "5(10 − n) + 12n = 78",
        "50 - 5n + 12n = 78",
        "50 + 7n = 78"
      ],
      "hints": [
        "Replace p with (10 − n).",
        "5(10 − n) + 12n = 78",
        "50 + 7n = 78"
      ]
    },
    {
      "id": "m2_s4",
      "type": "step",
      "label": "Solve for n",
      "description": "50 + 7n = 78, so 7n = 28 and n = 4.",
      "prompt": "Solve for n.",
      "accept": [
        "7n = 28",
        "n = 4",
        "7n = 28, n = 4"
      ],
      "hints": [
        "50 + 7n = 78",
        "7n = 28",
        "n = 4"
      ]
    },
    {
      "id": "m2_s5",
      "type": "step",
      "label": "Find p",
      "description": "p = 10 − 4 = 6.",
      "prompt": "Use p = 10 − n. What is p?",
      "accept": [
        "p = 6",
        "p = 10 - 4 = 6",
        "p = 10 − 4 = 6"
      ],
      "hints": [
        "p = 10 − n",
        "n = 4",
        "p = 6"
      ]
    },
    {
      "id": "m3_elimination",
      "type": "method",
      "label": "Method 3: Elimination",
      "description": "Write two equations (p + n = 10 and 5p + 12n = 78), multiply the first by 5 so the p terms match, then subtract to eliminate p.",
      "prompt": "Choose a method to solve this problem.",
      "accept": [
        "elimination",
        "eliminate",
        "multiply by 5",
        "5p + 5n = 50",
        "subtract the equations"
      ],
      "hints": [
        "Write two equations.",
        "Multiply p + n = 10 by 5: 5p + 5n = 50.",
        "Subtract from 5p + 12n = 78."
      ],
      "jev_description": "Elimination with two variables. Steps: (1) p + n = 10 and 5p + 12n = 78, (2) multiply the first equation by 5: 5p + 5n = 50, (3) subtract the equations: 7n = 28, (4) n = 4, (5) p = 6. Step 1 is the same as substitution; step 2 (multiplying a whole equation to match coefficients, 5p + 5n = 50) is what identifies elimination."
    },
    {
      "id": "m3_s1",
      "type": "step",
      "label": "Write two equations",
      "description": "Let pens = p and notebooks = n. Then p + n = 10 and 5p + 12n = 78.",
      "prompt": "Use two variables. Write one equation for the number of items and one for the cost.",
      "accept": [
        "p + n = 10 and 5p + 12n = 78",
        "p + n = 10, 5p + 12n = 78",
        "p+n=10, 5p+12n=78",
        "p + n = 10",
        "5p + 12n = 78"
      ],
      "hints": [
        "Let pens = p and notebooks = n.",
        "Items: p + n = 10.",
        "Cost: 5p + 12n = 78."
      ]
    },
    {
      "id": "m3_s2",
      "type": "step",
      "label": "Multiply the first equation by 5",
      "description": "5(p + n) = 5 × 10, so 5p + 5n = 50.",
      "prompt": "Multiply p + n = 10 by 5 so the p terms match.",
      "accept": [
        "5p + 5n = 50",
        "5p+5n=50"
      ],
      "hints": [
        "Multiply every term by 5.",
        "5 × p + 5 × n = 5 × 10.",
        "5p + 5n = 50"
      ]
    },
    {
      "id": "m3_s3",
      "type": "step",
      "label": "Subtract to eliminate p",
      "description": "(5p + 12n) − (5p + 5n) = 78 − 50, so 7n = 28.",
      "prompt": "Subtract 5p + 5n = 50 from 5p + 12n = 78. What do you get?",
      "accept": [
        "7n = 28",
        "12n - 5n = 78 - 50",
        "12n − 5n = 78 − 50"
      ],
      "hints": [
        "5p − 5p = 0, so p disappears.",
        "12n − 5n = 7n and 78 − 50 = 28.",
        "7n = 28"
      ]
    },
    {
      "id": "m3_s4",
      "type": "step",
      "label": "Solve for n",
      "description": "n = 28 ÷ 7 = 4.",
      "prompt": "Solve 7n = 28.",
      "accept": [
        "n = 4",
        "28/7 = 4",
        "28 ÷ 7 = 4"
      ],
      "hints": [
        "Divide both sides by 7.",
        "28 ÷ 7 = 4",
        "n = 4"
      ]
    },
    {
      "id": "m3_s5",
      "type": "step",
      "label": "Find p",
      "description": "p + 4 = 10, so p = 6.",
      "prompt": "Put n = 4 into p + n = 10. What is p?",
      "accept": [
        "p = 6",
        "p + 4 = 10",
        "p = 10 - 4 = 6",
        "p = 10 − 4 = 6"
      ],
      "hints": [
        "p + n = 10",
        "p + 4 = 10",
        "p = 6"
      ]
    },
    {
      "id": "m4_trial",
      "type": "method",
      "label": "Method 4: Trial and Error",
      "description": "Try different numbers of notebooks (the rest are pens) and calculate the total cost until it equals ₹78.",
      "prompt": "Choose a method to solve this problem.",
      "accept": [
        "trial",
        "try",
        "guess",
        "table",
        "check each"
      ],
      "hints": [
        "Pick a number of notebooks; the rest of the 10 items are pens.",
        "Work out the total cost.",
        "Keep trying until the cost is ₹78."
      ],
      "jev_description": "Trial and error. Pick a number of notebooks, the rest of the 10 items are pens, and compute the cost: 2 notebooks, 8 pens: 40 + 24 = 64; 3 notebooks, 7 pens: 35 + 36 = 71; 4 notebooks, 6 pens: 30 + 48 = 78. Identified by plugging in numbers and computing totals, with no letters or equations."
    },
    {
      "id": "m4_s1",
      "type": "step",
      "label": "Try 2 notebooks",
      "description": "2 notebooks and 8 pens: 8 × 5 + 2 × 12 = 40 + 24 = 64. Not 78.",
      "prompt": "Try 2 notebooks (and 8 pens). What is the total cost?",
      "accept": [
        "40 + 24 = 64",
        "8 × 5 + 2 × 12 = 64",
        "8*5 + 2*12 = 64",
        "64"
      ],
      "hints": [
        "8 pens × ₹5 = ₹40.",
        "2 notebooks × ₹12 = ₹24.",
        "40 + 24 = 64, too low."
      ]
    },
    {
      "id": "m4_s2",
      "type": "step",
      "label": "Try 3 notebooks",
      "description": "3 notebooks and 7 pens: 7 × 5 + 3 × 12 = 35 + 36 = 71. Not 78.",
      "prompt": "Try 3 notebooks (and 7 pens). What is the total cost?",
      "accept": [
        "35 + 36 = 71",
        "7 × 5 + 3 × 12 = 71",
        "7*5 + 3*12 = 71",
        "71"
      ],
      "hints": [
        "7 pens × ₹5 = ₹35.",
        "3 notebooks × ₹12 = ₹36.",
        "35 + 36 = 71, still too low."
      ]
    },
    {
      "id": "m4_s3",
      "type": "step",
      "label": "Try 4 notebooks",
      "description": "4 notebooks and 6 pens: 6 × 5 + 4 × 12 = 30 + 48 = 78. Correct!",
      "prompt": "Try 4 notebooks (and 6 pens). What is the total cost?",
      "accept": [
        "30 + 48 = 78",
        "6 × 5 + 4 × 12 = 78",
        "6*5 + 4*12 = 78",
        "78"
      ],
      "hints": [
        "6 pens × ₹5 = ₹30.",
        "4 notebooks × ₹12 = ₹48.",
        "30 + 48 = 78 ✓"
      ]
    }
  ],
  "edges": [
    {
      "from": "start",
      "to": "m1_one_var",
      "label": "Method 1: One Variable"
    },
    {
      "from": "m1_one_var",
      "to": "m1_s1",
      "label": "Define x"
    },
    {
      "from": "m1_s1",
      "to": "m1_s2",
      "label": "Cost equation"
    },
    {
      "from": "m1_s2",
      "to": "m1_s3",
      "label": "Simplify"
    },
    {
      "from": "m1_s3",
      "to": "m1_s4",
      "label": "Solve"
    },
    {
      "from": "m1_s4",
      "to": "m1_s5",
      "label": "Pens"
    },
    {
      "from": "m1_s5",
      "to": "conclusion",
      "label": "6 pens, 4 notebooks"
    },
    {
      "from": "start",
      "to": "m2_substitution",
      "label": "Method 2: Substitution"
    },
    {
      "from": "m2_substitution",
      "to": "m2_s1",
      "label": "Two equations"
    },
    {
      "from": "m2_s1",
      "to": "m2_s2",
      "label": "Rearrange"
    },
    {
      "from": "m2_s2",
      "to": "m2_s3",
      "label": "Substitute"
    },
    {
      "from": "m2_s3",
      "to": "m2_s4",
      "label": "Solve"
    },
    {
      "from": "m2_s4",
      "to": "m2_s5",
      "label": "Find p"
    },
    {
      "from": "m2_s5",
      "to": "conclusion",
      "label": "6 pens, 4 notebooks"
    },
    {
      "from": "start",
      "to": "m3_elimination",
      "label": "Method 3: Elimination"
    },
    {
      "from": "m3_elimination",
      "to": "m3_s1",
      "label": "Two equations"
    },
    {
      "from": "m3_s1",
      "to": "m3_s2",
      "label": "Multiply by 5"
    },
    {
      "from": "m3_s2",
      "to": "m3_s3",
      "label": "Subtract"
    },
    {
      "from": "m3_s3",
      "to": "m3_s4",
      "label": "Solve"
    },
    {
      "from": "m3_s4",
      "to": "m3_s5",
      "label": "Find p"
    },
    {
      "from": "m3_s5",
      "to": "conclusion",
      "label": "6 pens, 4 notebooks"
    },
    {
      "from": "start",
      "to": "m4_trial",
      "label": "Method 4: Trial and Error"
    },
    {
      "from": "m4_trial",
      "to": "m4_s1",
      "label": "Try 2"
    },
    {
      "from": "m4_s1",
      "to": "m4_s2",
      "label": "Try 3"
    },
    {
      "from": "m4_s2",
      "to": "m4_s3",
      "label": "Try 4"
    },
    {
      "from": "m4_trial",
      "to": "m4_s3",
      "label": "Try 4 directly"
    },
    {
      "from": "m4_s3",
      "to": "conclusion",
      "label": "6 pens, 4 notebooks"
    }
  ]
};
