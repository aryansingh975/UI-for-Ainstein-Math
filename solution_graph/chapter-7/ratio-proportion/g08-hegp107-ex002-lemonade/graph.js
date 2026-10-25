// Solution graph for g08-hegp107-ex002 (generated from graph.json — do not hand-edit).
window.SOLUTION_GRAPHS = window.SOLUTION_GRAPHS || {};
window.SOLUTION_GRAPHS["g08-hegp107-ex002"] = {
  "graph_meta": {
    "graph_id": "sg-g08-hegp107-ex002-lemonade",
    "problem_uuid": "g08-hegp107-ex002",
    "problem_text": "Kesang used 6 glasses of water and 10 spoons of sugar. She needs 18 more glasses of lemonade at the same sweetness. How many spoons of sugar are needed?",
    "navigation_label": "Kesang's lemonade",
    "problem_context": {
      "first": [
        6,
        10
      ],
      "second": [
        18,
        30
      ]
    },
    "graph_type": "directed_acyclic_graph",
    "version": "1.0.0",
    "description": "Standalone solution DAG for textbook Example 2. It interprets 18 more glasses as 18 additional glasses: 24 glasses and 40 spoons total, requiring 30 additional spoons.",
    "created": "2026-10-05",
    "total_methods": 4,
    "total_nodes": 24,
    "total_edges": 26
  },
  "start_node": "start",
  "conclusion_node": "conclusion",
  "nodes": [
    {
      "id": "goal_extraction",
      "type": "extraction",
      "optional": false,
      "label": "Identify the Goal",
      "description": "Identify the quantity or decision the problem asks for.",
      "prompt": "What do we need to find?",
      "accept": [
        "how many spoons of sugar are needed"
      ],
      "hints": [
        "State clearly what the question asks you to determine."
      ]
    },
    {
      "id": "given_extraction",
      "type": "extraction",
      "optional": false,
      "label": "Identify Given Information",
      "description": "Identify the facts and quantities provided in this word problem.",
      "prompt": "What information is given in the problem?",
      "accept": [
        "6 glasses of water, 10 spoons of sugar, and 18 more glasses of lemonade"
      ],
      "hints": [
        "Read the problem carefully and identify the quantities and relationships."
      ]
    },
    {
      "id": "start",
      "type": "start",
      "label": "Problem Statement",
      "description": "Kesang made 6 glasses of lemonade with 10 spoons of sugar. She needs 18 more glasses at the same sweetness.",
      "prompt": "How much sugar should Kesang use for 18 more glasses of lemonade at the same sweetness?",
      "accept": [],
      "hints": [
        "First account for the word more: 18 additional glasses are being made.",
        "The original 6 glasses plus 18 more makes 24 glasses altogether.",
        "The extra 18 glasses need 30 spoons; the 24 glasses need 40 spoons in total."
      ]
    },
    {
      "id": "conclusion",
      "type": "conclusion",
      "label": "Final Answer",
      "description": "Kesang adds 30 spoons for the additional 18 glasses, making 40 spoons for 24 glasses altogether.",
      "prompt": "State both amounts: how many spoons are added for the 18 more glasses, and how many spoons are used altogether?",
      "accept": [
        "30 additional spoons and 40 total",
        "30 spoons more, 40 spoons total",
        "30 more spoons; 40 in total",
        "30 spoons should be added; 40 total",
        "30 additional, 40 altogether",
        "40 total spoons, so add 30",
        "add 30 spoons"
      ],
      "hints": [
        "The full 24-glass batch uses 40 spoons.",
        "Kesang already used 10 spoons for the first 6 glasses.",
        "40 - 10 = 30 additional spoons."
      ]
    },
    {
      "id": "m1_unit_rate",
      "type": "method",
      "label": "Method 1: Unit Rate",
      "description": "Find the sugar needed per glass, then calculate for 24 glasses.",
      "prompt": "Choose a method. You can find the amount of sugar needed per glass.",
      "accept": [
        "unit rate",
        "per glass",
        "sugar per glass",
        "rate per glass"
      ],
      "hints": [
        "Find the total number of glasses, including the 18 more.",
        "Divide 10 spoons by 6 glasses.",
        "Use the per-glass rate for 24 glasses."
      ]
    },
    {
      "id": "m1_s1",
      "type": "step",
      "label": "Find total glasses",
      "description": "18 more than the original 6 glasses gives 24 glasses altogether.",
      "prompt": "How many glasses will Kesang make altogether?",
      "accept": [
        "24",
        "6+18=24",
        "6 + 18 = 24",
        "24 glasses"
      ],
      "hints": [
        "She already made 6 glasses.",
        "Add the 18 additional glasses.",
        "6 + 18 = 24 glasses."
      ]
    },
    {
      "id": "m1_s2",
      "type": "step",
      "label": "Find sugar per glass",
      "description": "10 spoons for 6 glasses is 10/6 = 5/3 spoons per glass.",
      "prompt": "How many spoons of sugar are used per glass?",
      "accept": [
        "5/3",
        "10/6",
        "1 2/3",
        "1.666 spoons per glass",
        "five thirds"
      ],
      "hints": [
        "Divide 10 spoons by 6 glasses.",
        "10/6 simplifies to 5/3.",
        "That is 1 2/3 spoons per glass."
      ]
    },
    {
      "id": "m1_s3",
      "type": "step",
      "label": "Find sugar for 24 glasses",
      "description": "24 x 5/3 = 40 spoons total.",
      "prompt": "At 5/3 spoons per glass, how much sugar is needed for 24 glasses altogether?",
      "accept": [
        "40",
        "40 spoons",
        "24*5/3=40",
        "24 x 5/3 = 40"
      ],
      "hints": [
        "Multiply the per-glass amount by 24.",
        "24 x 5/3 = 40.",
        "The full batch needs 40 spoons."
      ]
    },
    {
      "id": "m1_s4",
      "type": "step",
      "label": "Find additional sugar",
      "description": "Subtract the 10 spoons already used: 40 - 10 = 30 additional spoons.",
      "prompt": "If 40 spoons are needed altogether and 10 were already used, how many more spoons are needed?",
      "accept": [
        "30",
        "30 spoons",
        "40-10=30",
        "40 - 10 = 30",
        "30 more"
      ],
      "hints": [
        "The original batch already contains 10 spoons.",
        "Subtract 10 from the total 40.",
        "Kesang needs 30 more spoons."
      ]
    },
    {
      "id": "m2_scaling",
      "type": "method",
      "label": "Method 2: Proportional Scaling",
      "description": "Scale the original 6-glass recipe to 24 glasses by the same factor as the sugar.",
      "prompt": "Choose a method. You can use the same scale factor for glasses and sugar.",
      "accept": [
        "scale",
        "scaling",
        "common factor",
        "rule of three",
        "proportion"
      ],
      "hints": [
        "First include the 18 more glasses in the total.",
        "Find the factor that changes 6 glasses to 24.",
        "Multiply the 10 spoons by that same factor."
      ]
    },
    {
      "id": "m2_s1",
      "type": "step",
      "label": "Find total glasses",
      "description": "6 original glasses plus 18 more equals 24 glasses.",
      "prompt": "How many glasses are needed altogether?",
      "accept": [
        "24",
        "6+18=24",
        "6 + 18 = 24",
        "24 glasses"
      ],
      "hints": [
        "Add the original 6 and the 18 additional glasses.",
        "6 + 18 = 24.",
        "The total is 24 glasses."
      ]
    },
    {
      "id": "m2_s2",
      "type": "step",
      "label": "Find the scale factor",
      "description": "24/6 = 4, so the recipe is scaled by a factor of 4.",
      "prompt": "What factor changes 6 glasses into 24 glasses?",
      "accept": [
        "4",
        "24/6=4",
        "24 divided by 6 is 4",
        "multiply by 4"
      ],
      "hints": [
        "Divide the new total by the original amount.",
        "24 divided by 6 is 4.",
        "The scale factor is 4."
      ]
    },
    {
      "id": "m2_s3",
      "type": "step",
      "label": "Scale the sugar",
      "description": "10 x 4 = 40 spoons are needed for 24 glasses altogether.",
      "prompt": "Use the same factor of 4 for the sugar. How many spoons are needed altogether?",
      "accept": [
        "40",
        "40 spoons",
        "10*4=40",
        "10 x 4 = 40"
      ],
      "hints": [
        "Multiply the original 10 spoons by 4.",
        "10 x 4 = 40.",
        "The total amount is 40 spoons."
      ]
    },
    {
      "id": "m2_s4",
      "type": "step",
      "label": "Find additional sugar",
      "description": "40 total spoons minus the 10 already used leaves 30 additional spoons.",
      "prompt": "How many spoons must Kesang add beyond the original 10?",
      "accept": [
        "30",
        "30 spoons",
        "40-10=30",
        "40 - 10 = 30",
        "30 more"
      ],
      "hints": [
        "Subtract the original 10 spoons from 40.",
        "40 - 10 = 30.",
        "She adds 30 spoons."
      ]
    },
    {
      "id": "m3_equivalent_ratio",
      "type": "method",
      "label": "Method 3: Equivalent Ratios",
      "description": "Simplify the glasses-to-sugar ratio, then scale the equivalent ratio to 24 glasses.",
      "prompt": "Choose a method. You can simplify the ratio and build an equivalent ratio.",
      "accept": [
        "equivalent ratio",
        "simplify ratio",
        "simplification",
        "simplest ratio"
      ],
      "hints": [
        "The original ratio is 6:10.",
        "Simplify it to 3:5.",
        "Scale the glasses term from 3 to 24."
      ]
    },
    {
      "id": "m3_s1",
      "type": "step",
      "label": "Find total glasses",
      "description": "The target batch is 6 + 18 = 24 glasses.",
      "prompt": "What is the total number of glasses, including the 18 more?",
      "accept": [
        "24",
        "6+18=24",
        "6 + 18 = 24",
        "24 glasses"
      ],
      "hints": [
        "The original amount is 6 glasses.",
        "Add 18 more.",
        "The total is 24 glasses."
      ]
    },
    {
      "id": "m3_s2",
      "type": "step",
      "label": "Simplify the original ratio",
      "description": "6:10 simplifies to 3:5 by dividing both terms by 2.",
      "prompt": "What is 6:10 in simplest form?",
      "accept": [
        "3:5",
        "3 : 5",
        "6/10=3/5",
        "6/10 = 3/5"
      ],
      "hints": [
        "The HCF of 6 and 10 is 2.",
        "Divide both terms by 2.",
        "6:10 becomes 3:5."
      ]
    },
    {
      "id": "m3_s3",
      "type": "step",
      "label": "Build the equivalent ratio",
      "description": "3 scales to 24 by a factor of 8, so 5 scales to 40 spoons total.",
      "prompt": "If 3 parts correspond to 24 glasses, how many spoons correspond to 5 parts?",
      "accept": [
        "40",
        "40 spoons",
        "3:5=24:40",
        "24:40",
        "5*8=40"
      ],
      "hints": [
        "24 divided by 3 is 8.",
        "Multiply the sugar term 5 by 8.",
        "The total sugar is 40 spoons."
      ]
    },
    {
      "id": "m3_s4",
      "type": "step",
      "label": "Find additional sugar",
      "description": "Subtract the original 10 spoons from 40 total to get 30 more spoons.",
      "prompt": "How many more spoons are needed after the original 10?",
      "accept": [
        "30",
        "30 spoons",
        "40-10=30",
        "40 - 10 = 30",
        "30 more"
      ],
      "hints": [
        "The full batch uses 40 spoons.",
        "10 spoons were already used.",
        "40 - 10 = 30 additional spoons."
      ]
    },
    {
      "id": "m4_cross_multiply",
      "type": "method",
      "label": "Method 4: Cross Multiplication",
      "description": "Use the proportion 6:10::24:s to find the total sugar for 24 glasses.",
      "prompt": "Choose a method. You can set up a proportion and cross-multiply.",
      "accept": [
        "cross multiply",
        "cross multiplication",
        "cross products"
      ],
      "hints": [
        "First find the total number of glasses.",
        "Let s be the total spoons for 24 glasses.",
        "Set up 6:10::24:s."
      ]
    },
    {
      "id": "m4_s1",
      "type": "step",
      "label": "Find total glasses",
      "description": "6 original glasses plus 18 more equals 24 glasses altogether.",
      "prompt": "How many glasses will there be altogether?",
      "accept": [
        "24",
        "6+18=24",
        "6 + 18 = 24",
        "24 glasses"
      ],
      "hints": [
        "Add 6 and 18.",
        "6 + 18 = 24.",
        "There will be 24 glasses."
      ]
    },
    {
      "id": "m4_s2",
      "type": "step",
      "label": "Set up the proportion",
      "description": "Let s be total sugar: 6:10::24:s, or 6/10 = 24/s.",
      "prompt": "Set up a proportion for 6 glasses with 10 spoons and 24 glasses with s spoons.",
      "accept": [
        "6:10::24:s",
        "6/10=24/s",
        "6:10=24:s",
        "6 to 10 as 24 to s"
      ],
      "hints": [
        "Keep the glasses terms in the same position.",
        "Keep the sugar terms in the same position.",
        "The proportion is 6:10::24:s."
      ]
    },
    {
      "id": "m4_s3",
      "type": "step",
      "label": "Solve for total sugar",
      "description": "6s = 10 x 24 = 240, so s = 40 spoons total.",
      "prompt": "Solve the proportion to find s, the total spoons of sugar.",
      "accept": [
        "40",
        "40 spoons",
        "6s=240 so s=40",
        "6s = 240, s = 40",
        "s=40"
      ],
      "hints": [
        "Cross-multiply to get 6s = 240.",
        "Divide both sides by 6.",
        "s = 40 spoons total."
      ]
    },
    {
      "id": "m4_s4",
      "type": "step",
      "label": "Find additional sugar",
      "description": "40 total spoons minus 10 already used equals 30 additional spoons.",
      "prompt": "How much sugar should be added beyond the 10 spoons already used?",
      "accept": [
        "30",
        "30 spoons",
        "40-10=30",
        "40 - 10 = 30",
        "30 more"
      ],
      "hints": [
        "Subtract the original 10 spoons from 40.",
        "40 - 10 = 30.",
        "Add 30 more spoons."
      ]
    }
  ],
  "edges": [
    {
      "from": "m1_unit_rate",
      "to": "m1_s1",
      "label": "Find total glasses"
    },
    {
      "from": "m1_s1",
      "to": "m1_s2",
      "label": "Find unit rate"
    },
    {
      "from": "m1_s2",
      "to": "m1_s3",
      "label": "Scale rate to total glasses"
    },
    {
      "from": "m1_s3",
      "to": "m1_s4",
      "label": "Subtract original sugar"
    },
    {
      "from": "m1_s4",
      "to": "conclusion",
      "label": "State both amounts"
    },
    {
      "from": "m2_scaling",
      "to": "m2_s1",
      "label": "Find total glasses"
    },
    {
      "from": "m2_s1",
      "to": "m2_s2",
      "label": "Find scale factor"
    },
    {
      "from": "m2_s2",
      "to": "m2_s3",
      "label": "Scale sugar by the same factor"
    },
    {
      "from": "m2_s3",
      "to": "m2_s4",
      "label": "Subtract original sugar"
    },
    {
      "from": "m2_s4",
      "to": "conclusion",
      "label": "State both amounts"
    },
    {
      "from": "m3_equivalent_ratio",
      "to": "m3_s1",
      "label": "Find total glasses"
    },
    {
      "from": "m3_s1",
      "to": "m3_s2",
      "label": "Simplify original ratio"
    },
    {
      "from": "m3_s2",
      "to": "m3_s3",
      "label": "Build equivalent ratio"
    },
    {
      "from": "m3_s3",
      "to": "m3_s4",
      "label": "Subtract original sugar"
    },
    {
      "from": "m3_s4",
      "to": "conclusion",
      "label": "State both amounts"
    },
    {
      "from": "m4_cross_multiply",
      "to": "m4_s1",
      "label": "Find total glasses"
    },
    {
      "from": "m4_s1",
      "to": "m4_s2",
      "label": "Set up proportion"
    },
    {
      "from": "m4_s2",
      "to": "m4_s3",
      "label": "Solve for total sugar"
    },
    {
      "from": "m4_s3",
      "to": "m4_s4",
      "label": "Subtract original sugar"
    },
    {
      "from": "m4_s4",
      "to": "conclusion",
      "label": "State both amounts"
    },
    {
      "from": "start",
      "to": "given_extraction",
      "label": "Identify the given information"
    },
    {
      "from": "given_extraction",
      "to": "goal_extraction",
      "label": "Identify what to find"
    },
    {
      "from": "goal_extraction",
      "to": "m1_unit_rate",
      "label": "Choose a solution method"
    },
    {
      "from": "goal_extraction",
      "to": "m2_scaling",
      "label": "Choose a solution method"
    },
    {
      "from": "goal_extraction",
      "to": "m3_equivalent_ratio",
      "label": "Choose a solution method"
    },
    {
      "from": "goal_extraction",
      "to": "m4_cross_multiply",
      "label": "Choose a solution method"
    }
  ]
};
