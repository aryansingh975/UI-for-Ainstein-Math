// Solution Graph for Simplify m⁵n¹²/(mn)⁹ in exponential form.
// Problem UUID: g08-hegp102-ex-p26-q5v
window.SOLUTION_GRAPHS = window.SOLUTION_GRAPHS || {};
window.SOLUTION_GRAPHS["g08-hegp102-ex-p26-q5v"] = {
    "graph_meta": {
        "graph_id": "sg-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "problem_uuid": "g08-hegp102-ex-p26-q5v",
        "problem_text": "Simplify m⁵n¹²/(mn)⁹ in exponential form.",
        "navigation_label": "Simplify m⁵n¹²/(mn)⁹",
        "problem_context": {},
        "graph_type": "directed_acyclic_graph",
        "version": "1.0.0",
        "description": "Simplify the expression m⁵n¹²/(mn)⁹ using laws of exponents.",
        "created": "2026-10-12",
        "total_methods": 1,
        "total_nodes": 7,
        "total_edges": 6
    },
    "start_node": "start",
    "conclusion_node": "conclusion",
    "nodes": [
        {
            "id": "start",
            "type": "start",
            "label": "Problem Statement",
            "description": "Simplify m⁵n¹²/(mn)⁹ in exponential form.",
            "prompt": "How would you begin simplifying m⁵n¹²/(mn)⁹?",
            "accept": [],
            "hints": [
                "First, expand the denominator (mn)⁹.",
                "Then use the quotient rule for exponents.",
                "Remember: (ab)ⁿ = aⁿbⁿ and aᵐ/aⁿ = aᵐ⁻ⁿ."
            ]
        },
        {
            "id": "extraction",
            "type": "extraction",
            "label": "Identify the Expression",
            "description": "Identify the base and exponents in m⁵n¹²/(mn)⁹.",
            "prompt": "What is the simplified form of the denominator (mn)⁹?",
            "accept": [
                "mⁿ⁹",
                "m⁹n⁹",
                "(mn)⁹ = m⁹n⁹",
                "m to the 9, n to the 9"
            ],
            "hints": [
                "Apply the power of a product rule: (mn)⁹ = m⁹n⁹.",
                "So the expression becomes m⁵n¹²/(m⁹n⁹)."
            ]
        },
        {
            "id": "method1",
            "type": "method",
            "label": "Method 1: Quotient Rule",
            "description": "Apply the quotient rule for exponents: aᵐ/aⁿ = aᵐ⁻ⁿ separately for m and n.",
            "prompt": "After expanding the denominator, what rule applies to simplify m⁵/m⁹ and n¹²/n⁹?",
            "accept": [
                "quotient rule",
                "subtract exponents",
                "aᵐ/aⁿ = aᵐ⁻ⁿ",
                "subtract the exponents for each base"
            ],
            "hints": [
                "For like bases when dividing, subtract the exponents: m⁵/m⁹ = m⁵⁻⁹.",
                "Do this for both m and n bases separately."
            ]
        },
        {
            "id": "m1_step1",
            "type": "step",
            "label": "Simplify m Terms",
            "description": "Apply quotient rule to m: m⁵/m⁹ = m⁵⁻⁹ = m⁻⁴.",
            "prompt": "What is m⁵/m⁹ simplified?",
            "accept": [
                "m⁻⁴",
                "m^(-4)",
                "1/m⁴",
                "m to the negative 4"
            ],
            "hints": [
                "5 - 9 = -4, so m⁵/m⁹ = m⁻⁴.",
                "m⁻⁴ can also be written as 1/m⁴."
            ]
        },
        {
            "id": "m1_step2",
            "type": "step",
            "label": "Simplify n Terms",
            "description": "Apply quotient rule to n: n¹²/n⁹ = n¹²⁻⁹ = n³.",
            "prompt": "What is n¹²/n⁹ simplified?",
            "accept": [
                "n³",
                "n^3",
                "n cubed",
                "n to the 3"
            ],
            "hints": [
                "12 - 9 = 3, so n¹²/n⁹ = n³."
            ]
        },
        {
            "id": "m1_step3",
            "type": "step",
            "label": "Combine Results",
            "description": "Combine the simplified m and n terms: m⁻⁴n³.",
            "prompt": "What do you get when you combine m⁻⁴ and n³?",
            "accept": [
                "m⁻⁴n³",
                "n³/m⁴",
                "n^3/m^4",
                "n cubed over m to the 4"
            ],
            "hints": [
                "m⁻⁴n³ = n³/m⁴ (move the negative exponent to the denominator)."
            ]
        },
        {
            "id": "conclusion",
            "type": "conclusion",
            "label": "Final Answer",
            "description": "The simplified form is n³/m⁴.",
            "prompt": "What is the final simplified exponential form of m⁵n¹²/(mn)⁹?",
            "accept": [
                "n³/m⁴",
                "n^3/m^4",
                "n cubed over m to the 4",
                "the answer is n³/m⁴"
            ],
            "hints": [
                "Both methods lead to the same answer: n³/m⁴."
            ]
        }
    ],
    "edges": [
        { "from": "start", "to": "extraction" },
        { "from": "extraction", "to": "method1" },
        { "from": "start", "to": "method1" },
        { "from": "method1", "to": "m1_step1" },
        { "from": "m1_step1", "to": "m1_step2" },
        { "from": "m1_step2", "to": "m1_step3" },
        { "from": "m1_step3", "to": "conclusion" }
    ]
};