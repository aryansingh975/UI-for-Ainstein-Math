// Solution graph for g08-hegp107-ex010 (generated from graph.json — do not hand-edit).
window.SOLUTION_GRAPHS = window.SOLUTION_GRAPHS || {};
window.SOLUTION_GRAPHS["g08-hegp107-ex010"] = {
  "graph_meta": {
    "graph_id": "sg-g08-hegp107-ex010",
    "problem_uuid": "g08-hegp107-ex010",
    "problem_text": "A small farmer in Himachal Pradesh sells each 200 g packet of tea for ₹200. A large estate in Meghalaya sells each 1 kg packet of tea for ₹800. Are the weight-to-price ratios in both places proportional? Which tea is more expensive?",
    "navigation_label": "Tea cost comparison",
    "problem_context": {
      "first": [
        200,
        200
      ],
      "second": [
        1000,
        800
      ]
    },
    "graph_type": "directed_acyclic_graph",
    "version": "1.0.0",
    "description": "Solution DAG for comparing tea price ratios and identifying the more expensive tea.",
    "created": "2026-10-11",
    "total_methods": 2,
    "total_nodes": 11,
    "total_edges": 11
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
        "whether the ratios are proportional and which tea costs more"
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
        "200 g of tea costs ₹200 and 1 kg costs ₹800"
      ],
      "hints": [
        "Read the problem carefully and identify the quantities and relationships."
      ]
    },
    {
      "id": "start",
      "type": "start",
      "label": "Problem Statement",
      "description": "Compare the weight-to-price ratio for tea in Himachal Pradesh and Meghalaya and decide which tea is more expensive.",
      "prompt": "Write the weight-to-price ratios in the same units and compare them.",
      "accept": [],
      "hints": [
        "Use the same units for weight in both cases.",
        "200 g is one-fifth of 1 kg.",
        "Compare the simplified ratios or the cost for 1 kg."
      ]
    },
    {
      "id": "conclusion",
      "type": "conclusion",
      "label": "Final Conclusion",
      "description": "The tea from Himachal Pradesh is more expensive because 1 kg costs ₹1000, while Meghalaya costs ₹800.",
      "prompt": "State which tea is more expensive and justify it.",
      "accept": [
        "the tea from Himachal Pradesh is more expensive",
        "Himachal tea is more expensive",
        "the tea from Himachal is more expensive",
        "the Himachal tea is more expensive",
        "Himachal Pradesh tea is more expensive",
        "1 kg of Himachal tea costs ₹1000 and Meghalaya costs ₹800",
        "1 kg of tea from Himachal costs ₹1000, while Meghalaya costs ₹800",
        "the tea from Himachal Pradesh is more expensive because 1 kg costs ₹1000"
      ],
      "hints": [
        "Compare the cost for the same weight, such as 1 kg.",
        "The Himachal tea costs ₹1000 per kg, while the Meghalaya tea costs ₹800 per kg.",
        "So Himachal tea is more expensive."
      ]
    },
    {
      "id": "m1_compare",
      "type": "method",
      "label": "Method 1: Equivalent ratios",
      "description": "Express both tea prices using the same unit of weight and compare the ratios.",
      "prompt": "Write the weight-to-price ratios in equivalent simplified forms.",
      "accept": [
        "ratio",
        "compare ratio",
        "equivalent ratio",
        "simplify ratio",
        "weight to price ratio"
      ],
      "hints": [
        "For Himachal, 200 g : ₹200.",
        "For Meghalaya, 1000 g : ₹800.",
        "Simplify both ratios to compare them."
      ]
    },
    {
      "id": "m1_s1",
      "type": "step",
      "label": "Write the Himachal ratio",
      "description": "The Himachal ratio is 200 g : ₹200, which simplifies to 1 : 1.",
      "prompt": "What is the Himachal weight-to-price ratio?",
      "accept": [
        "200:200",
        "200 : 200",
        "200 g : 200",
        "200 : 200 = 1 : 1",
        "the ratio is 200:200",
        "200 : 200 in simplest form is 1 : 1"
      ],
      "hints": [
        "Divide both by 200.",
        "200 ÷ 200 = 1.",
        "So the simplified ratio is 1 : 1."
      ]
    },
    {
      "id": "m1_s2",
      "type": "step",
      "label": "Write the Meghalaya ratio",
      "description": "The Meghalaya ratio is 1000 g : ₹800, which simplifies to 5 : 4.",
      "prompt": "What is the Meghalaya weight-to-price ratio in the same units?",
      "accept": [
        "1000:800",
        "1000 : 800",
        "1000 g : 800",
        "1000 : 800 = 5 : 4",
        "the ratio is 1000:800",
        "1000 : 800 in simplest form is 5 : 4"
      ],
      "hints": [
        "Convert 1 kg into 1000 g.",
        "Then simplify 1000 : 800 by dividing both by 200.",
        "You get 5 : 4."
      ]
    },
    {
      "id": "m2_cost",
      "type": "method",
      "label": "Method 2: Cost for the same weight",
      "description": "Compare the cost of 1 kg of tea from both places to decide which is more expensive.",
      "prompt": "Find the cost of 1 kg of tea from each seller and compare them.",
      "accept": [
        "same weight",
        "cost for 1 kg",
        "per kg",
        "same amount",
        "compare price per kg"
      ],
      "hints": [
        "Take 1 kg as the common unit.",
        "200 g is one-fifth of 1 kg.",
        "Use the proportional relationship to find the cost of 1 kg."
      ]
    },
    {
      "id": "m2_s1",
      "type": "step",
      "label": "Convert 1 kg to grams",
      "description": "1 kg = 1000 g. This lets us compare the same amount of tea.",
      "prompt": "What is 1 kg in grams?",
      "accept": [
        "1 kg = 1000 g",
        "1 kilogram = 1000 grams",
        "1000 g",
        "1 kg is 1000 g"
      ],
      "hints": [
        "1 kilogram = 1000 grams.",
        "Use this to convert the weight for comparison."
      ]
    },
    {
      "id": "m2_s2",
      "type": "step",
      "label": "Find the cost of 1 kg from Himachal",
      "description": "If 200 g costs ₹200, then 1 kg costs ₹1000.",
      "prompt": "What is the price of 1 kg of Himachal tea?",
      "accept": [
        "1 kg costs ₹1000",
        "1 kilogram costs ₹1000",
        "₹1000",
        "200 g is 1/5 of 1 kg so x = 1000",
        "1/5 × x = 200",
        "x = 1000"
      ],
      "hints": [
        "200 g is 1/5 of 1 kg.",
        "So 1/5 × x = 200.",
        "Multiply both sides by 5 to get x = 1000."
      ]
    },
    {
      "id": "m2_s3",
      "type": "step",
      "label": "Compare the two prices",
      "description": "The same amount costs ₹1000 in Himachal and ₹800 in Meghalaya, so Himachal is more expensive.",
      "prompt": "Which tea is more expensive after comparing the same weight?",
      "accept": [
        "Himachal tea is more expensive",
        "the tea from Himachal Pradesh is more expensive",
        "₹1000 is more than ₹800",
        "1000 > 800",
        "1 kg in Himachal costs ₹1000 while Meghalaya costs ₹800"
      ],
      "hints": [
        "Compare ₹1000 and ₹800.",
        "Since ₹1000 > ₹800, Himachal tea is more expensive."
      ]
    }
  ],
  "edges": [
    {
      "from": "m1_compare",
      "to": "m1_s1",
      "label": "Himachal ratio"
    },
    {
      "from": "m1_s1",
      "to": "m1_s2",
      "label": "Meghalaya ratio"
    },
    {
      "from": "m1_s2",
      "to": "conclusion",
      "label": "State the answer"
    },
    {
      "from": "m2_cost",
      "to": "m2_s1",
      "label": "Convert 1 kg"
    },
    {
      "from": "m2_s1",
      "to": "m2_s2",
      "label": "Find 1 kg price"
    },
    {
      "from": "m2_s2",
      "to": "m2_s3",
      "label": "Compare prices"
    },
    {
      "from": "m2_s3",
      "to": "conclusion",
      "label": "Conclude"
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
      "to": "m1_compare",
      "label": "Choose a solution method"
    },
    {
      "from": "goal_extraction",
      "to": "m2_cost",
      "label": "Choose a solution method"
    }
  ]
};
