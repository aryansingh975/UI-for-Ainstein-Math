// Solution graph for g08-hegp201-ex-p19-q1 (generated from graph.json — do not hand-edit).
window.SOLUTION_GRAPHS = window.SOLUTION_GRAPHS || {};
window.SOLUTION_GRAPHS["g08-hegp201-ex-p19-q1"] = {
  "graph_meta": {
    "graph_id": "sg-3a1b2c4d-5e6f-7890-abcd-ef1234567890",
    "problem_uuid": "g08-hegp201-ex-p19-q1",
    "problem_text": "A shopkeeper buys a geometry box for ₹75 and sells it for ₹110. Find the profit and profit percentage.",
    "navigation_label": "Geometry Box Profit%",
    "problem_context": {
      "chapter": 9,
      "topic": "Percentages / Fractions in Disguise",
      "difficulty": "Easy",
      "subject": "Mathematics",
      "grade": 8
    },
    "graph_type": "directed_acyclic_graph",
    "version": "1.0.0",
    "description": "Solution graph for finding profit and profit percentage when CP and SP are given.",
    "created": "2026-10-12",
    "total_methods": 1,
    "total_nodes": 8,
    "total_edges": 7
  },
  "start_node": "start",
  "conclusion_node": "conclusion",
  "nodes": [
    {
      "id": "start",
      "type": "start",
      "label": "Problem Statement",
      "description": "A shopkeeper buys a geometry box for ₹75 and sells it for ₹110. Find the profit and profit percentage.",
      "prompt": "A shopkeeper buys a geometry box for ₹75 and sells it for ₹110. Find the profit and profit percentage. How will you begin solving this?",
      "accept": [],
      "hints": [
        "Think about what the shopkeeper paid versus what he received.",
        "Identify the Cost Price (CP) and Selling Price (SP) from the problem.",
        "CP is what was paid to buy (₹75) and SP is what was received on selling (₹110)."
      ]
    },
    {
      "id": "given_extraction",
      "type": "extraction",
      "optional": false,
      "label": "Extract Given Information",
      "description": "Identify CP and SP from the problem statement.",
      "prompt": "What information is given in the problem? State the Cost Price (CP) and Selling Price (SP).",
      "accept": [
        "CP = ₹75, SP = ₹110",
        "CP = 75, SP = 110",
        "Cost Price = 75, Selling Price = 110",
        "Cost Price = ₹75 and Selling Price = ₹110",
        "CP ₹75 SP ₹110",
        "Bought for 75, sold for 110"
      ],
      "hints": [
        "Read the problem carefully — two prices are mentioned.",
        "The price the shopkeeper pays is the Cost Price (CP), and the price he sells at is the Selling Price (SP).",
        "CP = ₹75 (buying price) and SP = ₹110 (selling price)."
      ]
    },
    {
      "id": "goal_extraction",
      "type": "extraction",
      "optional": false,
      "label": "Identify the Goal",
      "description": "Determine what needs to be found: profit amount and profit percentage.",
      "prompt": "What do we need to find in this problem?",
      "accept": [
        "Profit and profit percentage",
        "Profit and profit%",
        "Find profit and profit%",
        "Profit amount and profit percentage",
        "The profit and the profit percent",
        "How much profit and what percent profit"
      ],
      "hints": [
        "Re-read the last sentence of the problem.",
        "Two things need to be calculated here.",
        "We need to find: (1) Profit in rupees, and (2) Profit percentage."
      ]
    },
    {
      "id": "method1",
      "type": "method",
      "label": "Method 1: Profit % Formula",
      "description": "Use the standard profit formula: Profit = SP - CP, then Profit% = (Profit/CP) × 100.",
      "prompt": "We'll use the Profit Formula. What is the first formula needed to find profit?",
      "accept": [
        "Profit = SP - CP",
        "Profit = Selling Price - Cost Price",
        "SP minus CP",
        "110 - 75",
        "Subtract CP from SP"
      ],
      "hints": [
        "When SP > CP, the shopkeeper makes a profit.",
        "Profit is the extra money earned beyond the cost.",
        "Profit = SP − CP = 110 − 75."
      ]
    },
    {
      "id": "step1_profit",
      "type": "step",
      "label": "Calculate Profit",
      "description": "Subtract CP from SP to find the profit amount.",
      "prompt": "Calculate the profit: Profit = SP − CP = 110 − 75 = ?",
      "accept": [
        "₹35",
        "35",
        "Rs 35",
        "Profit = ₹35",
        "Profit = 35",
        "35 rupees",
        "The profit is ₹35"
      ],
      "hints": [
        "Simply subtract the buying price from the selling price.",
        "110 − 75 = ?",
        "Profit = 110 − 75 = ₹35."
      ]
    },
    {
      "id": "step2_profit_percent",
      "type": "step",
      "label": "Calculate Profit Percentage",
      "description": "Apply the formula: Profit% = (Profit ÷ CP) × 100.",
      "prompt": "Now calculate the Profit Percentage using: Profit% = (Profit ÷ CP) × 100. What is the answer?",
      "accept": [
        "46.67%",
        "46.67 percent",
        "46⅔%",
        "46.7%",
        "approximately 46.67%",
        "46.666...%",
        "Profit% = 46.67%",
        "46.67"
      ],
      "hints": [
        "Use the formula: Profit% = (Profit ÷ CP) × 100.",
        "Substitute: (35 ÷ 75) × 100 = ?",
        "35 ÷ 75 × 100 = 46.67% (rounded to 2 decimal places)."
      ]
    },
    {
      "id": "step3_verify",
      "type": "step",
      "label": "Verify and Summarise",
      "description": "State both results: Profit = ₹35 and Profit% ≈ 46.67%.",
      "prompt": "State the complete answer. What are the profit and profit percentage?",
      "accept": [
        "Profit = ₹35, Profit% = 46.67%",
        "Profit is ₹35 and Profit% is 46.67%",
        "₹35 profit and 46.67% profit percentage",
        "Profit ₹35, Profit% 46.67",
        "Profit = 35, Profit% ≈ 46.67",
        "35 rupees profit, 46.67 percent"
      ],
      "hints": [
        "Bring both calculated values together.",
        "You found Profit = ₹35 in the previous step, now combine with Profit%.",
        "Profit = ₹35 and Profit% = (35/75) × 100 ≈ 46.67%."
      ]
    },
    {
      "id": "conclusion",
      "type": "conclusion",
      "label": "Final Answer",
      "description": "The shopkeeper earns a profit of ₹35 and a profit percentage of approximately 46.67%.",
      "prompt": "What is the final answer for the profit and profit percentage?",
      "accept": [
        "Profit = ₹35, Profit% = 46.67%",
        "Profit is ₹35 and Profit% is 46.67%",
        "₹35 and 46.67%",
        "Profit ₹35 and profit percent 46.67",
        "35 rupees profit, 46.67 percent profit",
        "Profit = Rs 35, Profit% ≈ 46.67%"
      ],
      "hints": [
        "Recall: we subtracted CP from SP to get profit.",
        "Then we applied Profit% = (Profit/CP) × 100.",
        "Final Answer: Profit = ₹35 and Profit% ≈ 46.67%."
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
      "from": "method1",
      "to": "step1_profit"
    },
    {
      "from": "step1_profit",
      "to": "step2_profit_percent"
    },
    {
      "from": "step2_profit_percent",
      "to": "step3_verify"
    },
    {
      "from": "step3_verify",
      "to": "conclusion"
    }
  ]
};
