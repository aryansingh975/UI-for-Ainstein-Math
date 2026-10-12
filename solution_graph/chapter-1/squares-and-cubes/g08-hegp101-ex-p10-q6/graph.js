// Solution Graph for Perfect Square from 9408
// Problem UUID: g08-hegp101-ex-p10-q6
window.SOLUTION_GRAPHS = window.SOLUTION_GRAPHS || {};
window.SOLUTION_GRAPHS["g08-hegp101-ex-p10-q6"] = {
    "graph_meta": {
        "graph_id": "sg-c3d4e5f6-a7b8-9012-cdef-ab3456789003",
        "problem_uuid": "g08-hegp101-ex-p10-q6",
        "problem_text": "Find the smallest number by which 9408 must be multiplied so that the product is a perfect square. Also find the square root of that product.",
        "navigation_label": "Perfect Square from 9408",
        "problem_context": {},
        "graph_type": "directed_acyclic_graph",
        "version": "1.0.0",
        "description": "Single-method solution graph: prime factorise 9408, identify unpaired prime factors, multiply by the missing factor to get a perfect square, then find the square root of the product.",
        "created": "2026-10-12",
        "total_methods": 1,
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
            "description": "Find the smallest multiplier for 9408 to make it a perfect square, and find the square root of the result.",
            "prompt": "Find the smallest number by which 9408 must be multiplied so that the product is a perfect square. Also find the square root of that product. How would you begin?",
            "accept": [],
            "hints": [
                "A perfect square has all prime factors appearing an even number of times.",
                "Start by finding the prime factorisation of 9408.",
                "Divide 9408 by 2 repeatedly, then continue with the remaining odd number."
            ]
        },
        {
            "id": "given_extraction",
            "type": "extraction",
            "optional": true,
            "label": "Identify Given Information",
            "description": "Identify the given number and what we need to make it.",
            "prompt": "What is the given number, and what must we make it?",
            "accept": ["9408 must be made a perfect square", "9408, make it a perfect square", "given 9408", "the number is 9408"],
            "hints": [
                "Look at the problem statement for the given number.",
                "We have 9408 and need to make it a perfect square by multiplication.",
                "Given: 9408. Goal: find the smallest multiplier to make it a perfect square."
            ]
        },
        {
            "id": "goal_extraction",
            "type": "extraction",
            "optional": true,
            "label": "Identify the Goal",
            "description": "State the two-part goal: find the multiplier and find the square root.",
            "prompt": "What are the two things we need to find?",
            "accept": ["smallest multiplier and square root of product", "the multiplier and \u221a of the product", "find multiplier and square root", "two things: multiplier and square root"],
            "hints": [
                "The problem has two parts.",
                "Part 1: What is the smallest number to multiply 9408 by?",
                "Part 1: smallest multiplier. Part 2: \u221a(9408 \u00d7 multiplier)."
            ]
        },
        {
            "id": "method1",
            "type": "method",
            "label": "Method 1: Prime Factorisation & Pairing",
            "description": "Factorise 9408, identify unpaired prime factors, then multiply to complete all pairs.",
            "prompt": "Use prime factorisation. What is your first step to factorise 9408?",
            "accept": ["prime factorisation", "prime factorization", "factor 9408", "divide by 2", "prime factors of 9408"],
            "hints": [
                "9408 is even, so start dividing by 2.",
                "Keep dividing by 2 until you get an odd number.",
                "9408 \u00f7 2 = 4704. Continue dividing by 2."
            ]
        },
        {
            "id": "m1_step1",
            "type": "step",
            "label": "Step 1: Prime Factorise 9408",
            "description": "Divide 9408 by primes to get its full prime factorisation.",
            "prompt": "Divide 9408 by prime numbers step by step. What is the prime factorisation of 9408?",
            "accept": ["2\u2076 \u00d7 3 \u00d7 7\u00b2", "2^6 \u00d7 3 \u00d7 7^2", "2^6 x 3 x 7^2", "64 \u00d7 3 \u00d7 49", "2\u2076 \u00d7 3\u00b9 \u00d7 7\u00b2", "9408 = 2\u2076 \u00d7 3 \u00d7 7\u00b2"],
            "hints": [
                "9408 \u00f7 2 = 4704, \u00f72 = 2352, \u00f72 = 1176, \u00f72 = 588, \u00f72 = 294, \u00f72 = 147. Now 147 is odd.",
                "147 = 3 \u00d7 49 = 3 \u00d7 7\u00b2. So 9408 = 2\u2076 \u00d7 3 \u00d7 7\u00b2.",
                "9408 = 2\u2076 \u00d7 3\u00b9 \u00d7 7\u00b2."
            ]
        },
        {
            "id": "m1_step2",
            "type": "step",
            "label": "Step 2: Identify Unpaired Factors",
            "description": "Find which prime factors have odd exponents (unpaired).",
            "prompt": "Look at the exponents in 9408 = 2\u2076 \u00d7 3\u00b9 \u00d7 7\u00b2. Which prime factor is unpaired (has an odd exponent)?",
            "accept": ["3", "3 is unpaired", "3 has odd exponent", "the factor 3", "3 appears once", "3\u00b9"],
            "hints": [
                "For a perfect square, all exponents must be even.",
                "Check each exponent: 2\u2076 (even \u2713), 3\u00b9 (odd \u2717), 7\u00b2 (even \u2713).",
                "The factor 3 appears only once (odd exponent), so it is unpaired."
            ]
        },
        {
            "id": "m1_step3",
            "type": "step",
            "label": "Step 3: Find the Smallest Multiplier",
            "description": "Identify the smallest number needed to pair all factors.",
            "prompt": "To make all exponents even, what is the smallest number you must multiply 9408 by?",
            "accept": ["3", "multiply by 3", "the multiplier is 3", "smallest number is 3", "3 is the answer"],
            "hints": [
                "We need to add one more factor of 3 to make its exponent even (1 \u2192 2).",
                "Multiplying by 3 gives 9408 \u00d7 3 = 2\u2076 \u00d7 3\u00b2 \u00d7 7\u00b2, where all exponents are even.",
                "The smallest multiplier is 3."
            ]
        },
        {
            "id": "m1_step4",
            "type": "step",
            "label": "Step 4: Find the Product",
            "description": "Multiply 9408 by 3 and express the product as a perfect square.",
            "prompt": "Calculate 9408 \u00d7 3. What is the result, and how can you express it as a perfect square?",
            "accept": ["28224", "9408 \u00d7 3 = 28224", "28224 = 2\u2076 \u00d7 3\u00b2 \u00d7 7\u00b2", "(2\u00b3 \u00d7 3 \u00d7 7)\u00b2", "168\u00b2", "28224 = 168\u00b2"],
            "hints": [
                "9408 \u00d7 3 = 28224.",
                "28224 = 2\u2076 \u00d7 3\u00b2 \u00d7 7\u00b2 = (2\u00b3)\u00b2 \u00d7 3\u00b2 \u00d7 7\u00b2 = (2\u00b3 \u00d7 3 \u00d7 7)\u00b2.",
                "28224 = 168\u00b2."
            ]
        },
        {
            "id": "m1_step5",
            "type": "step",
            "label": "Step 5: Find the Square Root of the Product",
            "description": "Take the square root of 28224.",
            "prompt": "Find \u221a28224. Use the factorisation 28224 = 2\u2076 \u00d7 3\u00b2 \u00d7 7\u00b2.",
            "accept": ["168", "\u221a28224 = 168", "2\u00b3 \u00d7 3 \u00d7 7 = 168", "8 \u00d7 21 = 168", "8 \u00d7 3 \u00d7 7 = 168"],
            "hints": [
                "\u221a(2\u2076 \u00d7 3\u00b2 \u00d7 7\u00b2) = 2\u00b3 \u00d7 3 \u00d7 7.",
                "2\u00b3 = 8, so \u221a28224 = 8 \u00d7 3 \u00d7 7.",
                "8 \u00d7 3 \u00d7 7 = 8 \u00d7 21 = 168. So \u221a28224 = 168."
            ]
        },
        {
            "id": "conclusion",
            "type": "conclusion",
            "label": "Final Answer",
            "description": "The smallest multiplier is 3, and the square root of the product (28224) is 168.",
            "prompt": "State both answers: the smallest multiplier for 9408 and the square root of the resulting product.",
            "accept": ["multiply by 3; \u221a28224 = 168", "3 and 168", "multiplier is 3, square root is 168", "3; 168", "smallest number is 3 and square root is 168", "answer: 3 and 168"],
            "hints": [
                "There are two parts to the answer.",
                "The multiplier is the unpaired prime factor you identified.",
                "Multiply by 3; the product is 28224 and its square root is 168."
            ]
        }
    ],
    "edges": [
        { "from": "start", "to": "given_extraction" },
        { "from": "given_extraction", "to": "goal_extraction" },
        { "from": "goal_extraction", "to": "method1" },
        { "from": "start", "to": "method1" },
        { "from": "method1", "to": "m1_step1" },
        { "from": "m1_step1", "to": "m1_step2" },
        { "from": "m1_step2", "to": "m1_step3" },
        { "from": "m1_step3", "to": "m1_step4" },
        { "from": "m1_step4", "to": "m1_step5" },
        { "from": "m1_step5", "to": "conclusion" }
    ]
};
