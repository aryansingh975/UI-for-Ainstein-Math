// Solution Graph for 4a + 16 = 36. Solve for a and find the four consecutive numbers starting at a.
// Problem UUID: g08-hegp206-grid-eq
window.SOLUTION_GRAPHS = window.SOLUTION_GRAPHS || {};
window.SOLUTION_GRAPHS["g08-hegp206-grid-eq"] = {
    "graph_meta": {
        "graph_id": "sg-3f8a1c2d-4b5e-6f7a-8c9d-0e1f2a3b4c5d",
        "problem_uuid": "g08-hegp206-grid-eq",
        "problem_text": "4a + 16 = 36. Solve for a and find the four consecutive numbers starting at a.",
        "navigation_label": "4a+16=36 Grid Problem",
        "problem_context": {
            "topic": "Linear Equations",
            "chapter": "Chapter 11 – Algebra Play",
            "difficulty": "Easy",
            "grade": 8
        },
        "graph_type": "directed_acyclic_graph",
        "version": "1.0.0",
        "description": "Solve the linear equation 4a + 16 = 36 for a, then list the four consecutive integers starting at a. Two solution paths: algebraic method and trial/guess-and-check.",
        "created": "2026-10-12",
        "total_methods": 2,
        "total_nodes": 11,
        "total_edges": 12
    },
    "start_node": "start",
    "conclusion_node": "conclusion",
    "nodes": [
        {
            "id": "start",
            "type": "start",
            "label": "Problem Statement",
            "description": "4a + 16 = 36. Solve for a and find the four consecutive numbers starting at a.",
            "prompt": "We have the equation 4a + 16 = 36. How would you like to solve it?",
            "accept": [],
            "hints": [
                "We need to find the value of 'a' that makes the equation true.",
                "You can isolate 'a' by moving numbers to one side, or try guessing a value.",
                "Start by choosing a method: solve it algebraically or guess-and-check."
            ]
        },
        {
            "id": "method1",
            "type": "method",
            "label": "Method 1: Solve the Equation Algebraically",
            "description": "Isolate the variable a step-by-step using inverse operations.",
            "prompt": "We'll solve 4a + 16 = 36 by isolating a. What is the first step?",
            "accept": [
                "subtract 16 from both sides",
                "move 16 to the other side",
                "subtract 16",
                "4a = 36 - 16",
                "4a = 20",
                "isolate 4a"
            ],
            "hints": [
                "To isolate the term with 'a', we need to remove the constant from the left side.",
                "Subtract 16 from both sides of the equation.",
                "4a + 16 − 16 = 36 − 16, which gives 4a = 20."
            ]
        },
        {
            "id": "m1_step1",
            "type": "step",
            "label": "Subtract 16 from Both Sides",
            "description": "4a + 16 − 16 = 36 − 16 → 4a = 20",
            "prompt": "After subtracting 16 from both sides we get 4a = 20. What is the next step to find a?",
            "accept": [
                "divide both sides by 4",
                "divide by 4",
                "4a ÷ 4 = 20 ÷ 4",
                "a = 20 ÷ 4",
                "a = 5",
                "divide 20 by 4"
            ],
            "hints": [
                "We now have 4a = 20. We need to get 'a' alone.",
                "Divide both sides by the coefficient of a, which is 4.",
                "4a ÷ 4 = 20 ÷ 4, so a = 5."
            ]
        },
        {
            "id": "m1_step2",
            "type": "step",
            "label": "Divide Both Sides by 4",
            "description": "4a ÷ 4 = 20 ÷ 4 → a = 5",
            "prompt": "We found a = 5. Now list the four consecutive numbers starting at a = 5.",
            "accept": [
                "5, 6, 7, 8",
                "5 6 7 8",
                "a=5, a+1=6, a+2=7, a+3=8",
                "five, six, seven, eight",
                "5 and 6 and 7 and 8"
            ],
            "hints": [
                "Consecutive numbers follow one after another without gaps.",
                "If the first number is 5, the next three are 5+1, 5+2, 5+3.",
                "The four consecutive numbers are 5, 6, 7, 8."
            ]
        },
        {
            "id": "m1_step3",
            "type": "step",
            "label": "List Four Consecutive Numbers",
            "description": "Starting at a = 5: the four consecutive numbers are 5, 6, 7, 8.",
            "prompt": "Great! The four consecutive numbers are 5, 6, 7, 8. Can you verify that a = 5 satisfies the original equation 4a + 16 = 36?",
            "accept": [
                "4(5) + 16 = 36",
                "20 + 16 = 36",
                "36 = 36",
                "yes it checks out",
                "verified",
                "yes",
                "correct"
            ],
            "hints": [
                "Substitute a = 5 back into 4a + 16 = 36.",
                "Calculate 4 × 5 + 16 = 20 + 16.",
                "20 + 16 = 36 ✓. The solution is verified."
            ]
        },
        {
            "id": "method2",
            "type": "method",
            "label": "Method 2: Trial / Guess and Check",
            "description": "Guess a value for a, substitute into the equation, and check if both sides balance.",
            "prompt": "We'll guess a value for a and test it in 4a + 16 = 36. What value would you try first?",
            "accept": [
                "try a = 5",
                "a = 5",
                "guess 5",
                "5",
                "try 5"
            ],
            "hints": [
                "Pick a value you think might work. Think: 4 times what, plus 16, equals 36?",
                "The right side minus 16 is 20. What divided by 4 gives 20? That's your guess.",
                "Try a = 5: 4(5) + 16 = 20 + 16 = 36. ✓"
            ]
        },
        {
            "id": "m2_step1",
            "type": "step",
            "label": "Test a = 5 in the Equation",
            "description": "Substitute a = 5: 4(5) + 16 = 20 + 16 = 36 ✓",
            "prompt": "a = 5 works! 4(5) + 16 = 36 ✓. Now list the four consecutive numbers starting at 5.",
            "accept": [
                "5, 6, 7, 8",
                "5 6 7 8",
                "five six seven eight",
                "5 and then 6 7 8",
                "a=5, a+1=6, a+2=7, a+3=8"
            ],
            "hints": [
                "We confirmed a = 5. Now we need four numbers in a row starting at 5.",
                "Add 0, 1, 2, 3 to the starting number to get consecutive integers.",
                "The four consecutive numbers are 5, 6, 7, 8."
            ]
        },
        {
            "id": "m2_step2",
            "type": "step",
            "label": "List Four Consecutive Numbers (Method 2)",
            "description": "Starting at a = 5: consecutive numbers are 5, 6, 7, 8.",
            "prompt": "The four consecutive numbers are 5, 6, 7, 8. What is the final answer?",
            "accept": [
                "a = 5, numbers are 5 6 7 8",
                "a equals 5 and numbers are 5, 6, 7, 8",
                "5, 6, 7, 8",
                "a=5",
                "five six seven eight"
            ],
            "hints": [
                "State the value of a and the four consecutive numbers.",
                "a = 5 satisfies the equation, and the numbers start at 5.",
                "a = 5; the four consecutive numbers are 5, 6, 7, 8."
            ]
        },
        {
            "id": "conclusion",
            "type": "conclusion",
            "label": "Final Answer",
            "description": "a = 5; the four consecutive numbers starting at a are 5, 6, 7, 8.",
            "prompt": "What is the final answer?",
            "accept": [
                "a = 5",
                "a equals 5",
                "5, 6, 7, 8",
                "a = 5 and the numbers are 5, 6, 7, 8",
                "five six seven eight",
                "a=5; 5,6,7,8",
                "the four consecutive numbers are 5 6 7 8"
            ],
            "hints": [
                "We solved 4a + 16 = 36 to find a.",
                "a = 5, and consecutive numbers starting at 5 are found by adding 0, 1, 2, 3.",
                "a = 5; the four consecutive numbers are 5, 6, 7, 8."
            ]
        }
    ],
    "edges": [
        { "from": "start", "to": "method1" },
        { "from": "start", "to": "method2" },
        { "from": "method1", "to": "m1_step1" },
        { "from": "m1_step1", "to": "m1_step2" },
        { "from": "m1_step2", "to": "m1_step3" },
        { "from": "m1_step3", "to": "conclusion" },
        { "from": "method2", "to": "m2_step1" },
        { "from": "m2_step1", "to": "m2_step2" },
        { "from": "m2_step2", "to": "conclusion" }
    ]
};