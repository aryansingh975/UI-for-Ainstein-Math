// Solution graph for g08-hegp203-ex003 (generated from graph.json — do not hand-edit).
window.SOLUTION_GRAPHS = window.SOLUTION_GRAPHS || {};
window.SOLUTION_GRAPHS["g08-hegp203-ex003"] = {
  "graph_meta": {
    "graph_id": "sg-g08-hegp203-ex003",
    "problem_uuid": "g08-hegp203-ex003",
    "problem_text": "20 workers can lay a road in 4 days. How many days will 10 workers take to lay the same road?",
    "navigation_label": "Workers & Road (Inverse)",
    "problem_context": {
      "chapter": "8",
      "topic": "Inverse Proportion",
      "difficulty": "easy",
      "source": "g08-hegp203-ex003"
    },
    "graph_type": "directed_acyclic_graph",
    "version": "1.0.0",
    "description": "Two-method solution graph for an inverse proportion word problem involving workers and days to lay a road.",
    "created": "2026-10-12",
    "total_methods": 2,
    "total_nodes": 10,
    "total_edges": 10
  },
  "start_node": "start",
  "conclusion_node": "conclusion",
  "nodes": [
    {
      "id": "start",
      "type": "start",
      "label": "Problem Statement",
      "description": "20 workers can lay a road in 4 days. How many days will 10 workers take to lay the same road?",
      "prompt": "Read the problem carefully. What type of proportion do you see between workers and days?",
      "accept": [],
      "hints": [
        "Think about what happens to the number of days when you increase or decrease the number of workers.",
        "If fewer workers are doing the job, will it take more or fewer days?",
        "When one quantity increases and the other decreases, it is inverse proportion."
      ]
    },
    {
      "id": "given_extraction",
      "type": "extraction",
      "optional": false,
      "label": "Identify the Givens",
      "description": "Extract the known values from the problem.",
      "prompt": "What information is given in the problem?",
      "accept": [
        "20 workers, 4 days",
        "workers1 = 20, days1 = 4, workers2 = 10",
        "20 workers take 4 days, 10 workers are new",
        "number of workers: 20 and 10; days: 4",
        "20 workers in 4 days, 10 workers",
        "workers = 20, days = 4, new workers = 10"
      ],
      "hints": [
        "Look for numbers related to workers and days in the problem.",
        "There are two groups of workers mentioned — what are their counts?",
        "Given: 20 workers take 4 days, and we have a second group of 10 workers."
      ]
    },
    {
      "id": "goal_extraction",
      "type": "extraction",
      "optional": false,
      "label": "Identify the Goal",
      "description": "Determine what the problem is asking us to find.",
      "prompt": "What do we need to find?",
      "accept": [
        "number of days for 10 workers",
        "days taken by 10 workers",
        "how many days will 10 workers take",
        "days2",
        "time for 10 workers to lay the road",
        "days required for 10 workers"
      ],
      "hints": [
        "The question ends with '...how many days will 10 workers take?'",
        "We already know the days for 20 workers. What is unknown?",
        "We need to find the number of days 10 workers take to lay the same road."
      ]
    },
    {
      "id": "method1",
      "type": "method",
      "label": "Method 1: Inverse Proportion Formula",
      "description": "Use the constant product property of inverse proportion: workers × days = constant.",
      "prompt": "In inverse proportion, the product of the two quantities remains constant. What is the constant here?",
      "accept": [
        "workers × days = constant",
        "inverse proportion formula",
        "product is constant",
        "x1 × y1 = x2 × y2",
        "w1 × d1 = w2 × d2"
      ],
      "hints": [
        "In inverse proportion, as one value goes up, the other goes down, keeping their product the same.",
        "Multiply workers by days for the first case to find the constant.",
        "The formula is: workers₁ × days₁ = workers₂ × days₂."
      ]
    },
    {
      "id": "m1_step1",
      "type": "step",
      "label": "Calculate the Constant (Product)",
      "description": "Find the constant product: 20 × 4.",
      "prompt": "What is the product of workers and days in the first case?",
      "accept": [
        "80",
        "20 × 4 = 80",
        "constant = 80",
        "product = 80",
        "80 worker-days"
      ],
      "hints": [
        "Multiply the number of workers by the number of days for the first situation.",
        "20 × 4 = ?",
        "20 × 4 = 80. The constant is 80."
      ]
    },
    {
      "id": "m1_step2",
      "type": "step",
      "label": "Find Days for 10 Workers",
      "description": "Use the constant to find days2: 80 ÷ 10.",
      "prompt": "Using the constant 80, how many days will 10 workers take? (days2 = 80 ÷ 10)",
      "accept": [
        "8",
        "8 days",
        "80 ÷ 10 = 8",
        "days2 = 8",
        "eight days"
      ],
      "hints": [
        "Use the equation: 10 × days₂ = 80.",
        "Divide both sides by 10: days₂ = 80 ÷ 10.",
        "80 ÷ 10 = 8 days."
      ]
    },
    {
      "id": "method2",
      "type": "method",
      "label": "Method 2: Ratio Method",
      "description": "Use the ratio of workers to find the inverse ratio of days.",
      "prompt": "Set up the ratio of workers (old to new). What is the workers ratio?",
      "accept": [
        "ratio method",
        "workers ratio = 20:10",
        "20:10",
        "2:1",
        "workers ratio is 2 to 1"
      ],
      "hints": [
        "Compare the two worker counts as a ratio.",
        "The ratio of workers (original to new) is 20:10, which simplifies to 2:1.",
        "Workers ratio = 20:10 = 2:1."
      ]
    },
    {
      "id": "m2_step1",
      "type": "step",
      "label": "Find the Inverse Days Ratio",
      "description": "Since proportion is inverse, flip the workers ratio to get the days ratio.",
      "prompt": "Since it is inverse proportion, the days ratio is the inverse of the workers ratio. What is the days ratio?",
      "accept": [
        "1:2",
        "days ratio = 1:2",
        "inverse of 2:1 is 1:2",
        "flipped ratio is 1:2"
      ],
      "hints": [
        "Inverse proportion means the ratios are reciprocals of each other.",
        "Flip the workers ratio 2:1 to get the days ratio.",
        "Days ratio = 1:2 (the inverse of 2:1)."
      ]
    },
    {
      "id": "m2_step2",
      "type": "step",
      "label": "Calculate New Days",
      "description": "Apply the days ratio to find days2: 4 × 2 = 8.",
      "prompt": "The days ratio is 1:2, and original days = 4. What are the new days? (days2 = 4 × 2)",
      "accept": [
        "8",
        "8 days",
        "4 × 2 = 8",
        "days2 = 8",
        "eight days"
      ],
      "hints": [
        "If the days ratio is 1:2, then new days = original days × 2.",
        "Multiply 4 by 2 to get the new number of days.",
        "4 × 2 = 8 days."
      ]
    },
    {
      "id": "conclusion",
      "type": "conclusion",
      "label": "Final Answer",
      "description": "10 workers will take 8 days to lay the same road.",
      "prompt": "How many days will 10 workers take to lay the road?",
      "accept": [
        "8 days",
        "8",
        "eight days",
        "10 workers take 8 days",
        "the answer is 8 days",
        "days = 8"
      ],
      "hints": [
        "Both methods should give the same answer.",
        "Using either the product method or the ratio method, you arrive at the same result.",
        "10 workers will take 8 days to lay the same road."
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
      "from": "method1",
      "to": "m1_step1"
    },
    {
      "from": "m1_step1",
      "to": "m1_step2"
    },
    {
      "from": "m1_step2",
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
