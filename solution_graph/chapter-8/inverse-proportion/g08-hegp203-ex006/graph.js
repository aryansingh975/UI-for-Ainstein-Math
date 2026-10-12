// Solution Graph for Ram takes 1 hour to cut vegetables. Shyam takes 1.5 hours to cut the same vegetables. How long will they take if they work together?
// Problem UUID: c3d4e5f6-a7b8-9012-cdef-123456789012
window.SOLUTION_GRAPHS = window.SOLUTION_GRAPHS || {};
window.SOLUTION_GRAPHS["c3d4e5f6-a7b8-9012-cdef-123456789012"] = {
    "graph_meta": {
        "graph_id": "sg-c3d4e5f6-a7b8-9012-cdef-123456789012",
        "problem_uuid": "c3d4e5f6-a7b8-9012-cdef-123456789012",
        "problem_text": "Ram takes 1 hour to cut vegetables. Shyam takes 1.5 hours to cut the same vegetables. How long will they take if they work together?",
        "navigation_label": "Ram and Shyam Together",
        "problem_context": {
            "chapter": "8",
            "topic": "Inverse Proportion",
            "difficulty": "hard",
            "source": "g08-hegp203-ex006"
        },
        "graph_type": "directed_acyclic_graph",
        "version": "1.0.0",
        "description": "Two-method solution graph for a combined work rate word problem involving Ram and Shyam cutting vegetables together.",
        "created": "2026-10-12",
        "total_methods": 2,
        "total_nodes": 14,
        "total_edges": 14
    },
    "start_node": "start",
    "conclusion_node": "conclusion",
    "nodes": [
        {
            "id": "start",
            "type": "start",
            "label": "Problem Statement",
            "description": "Ram takes 1 hour to cut vegetables. Shyam takes 1.5 hours to cut the same vegetables. How long will they take if they work together?",
            "prompt": "Read the problem carefully. What strategy can you use when two people work together?",
            "accept": [],
            "hints": [
                "When two people work together, their rates of work add up.",
                "Think about how much of the job each person completes per hour.",
                "To find the combined time, add their individual rates and take the reciprocal."
            ]
        },
        {
            "id": "given_extraction",
            "type": "extraction",
            "label": "Identify the Givens",
            "description": "Extract the known values from the problem.",
            "prompt": "What information is given in the problem?",
            "accept": [
                "Ram takes 1 hour, Shyam takes 1.5 hours",
                "Ram = 1 hr, Shyam = 1.5 hr",
                "Ram takes 1 hour; Shyam takes 1.5 hours for the same job",
                "time for Ram = 1 hour, time for Shyam = 3/2 hours",
                "Ram: 1 hour, Shyam: 90 minutes",
                "Ram 1hr Shyam 1.5hr"
            ],
            "hints": [
                "Look for the time each person takes to complete the job.",
                "Two people are mentioned — what are their individual times?",
                "Given: Ram takes 1 hour and Shyam takes 1.5 hours (or 3/2 hours) to cut the vegetables."
            ]
        },
        {
            "id": "goal_extraction",
            "type": "extraction",
            "label": "Identify the Goal",
            "description": "Determine what the problem is asking us to find.",
            "prompt": "What do we need to find?",
            "accept": [
                "time taken working together",
                "combined time",
                "how long if they work together",
                "time for both together",
                "joint time",
                "time when Ram and Shyam work together"
            ],
            "hints": [
                "The question asks how long the job takes when both work simultaneously.",
                "We want to find the combined time, not individual times.",
                "We need to find how many hours (or minutes) Ram and Shyam together take to cut the vegetables."
            ]
        },
        {
            "id": "method1",
            "type": "method",
            "label": "Method 1: Combined Rate Method",
            "description": "Add the individual work rates to get the combined rate, then find total time.",
            "prompt": "Find each person's work rate (fraction of job per hour). What is Ram's rate?",
            "accept": [
                "combined rate method",
                "work rate method",
                "add rates",
                "rate = 1/time",
                "Ram rate = 1 job per hour"
            ],
            "hints": [
                "Work rate = 1 ÷ time taken. This gives the fraction of the job done per hour.",
                "If Ram finishes in 1 hour, he does 1 full job per hour.",
                "Ram's rate = 1/1 = 1 job/hour. Now find Shyam's rate similarly."
            ]
        },
        {
            "id": "m1_step1",
            "type": "step",
            "label": "Find Individual Rates",
            "description": "Ram's rate = 1 job/hr; Shyam's rate = 1/1.5 = 2/3 job/hr.",
            "prompt": "What is Shyam's work rate? (rate = 1 ÷ 1.5)",
            "accept": [
                "2/3",
                "2/3 job per hour",
                "1/1.5 = 2/3",
                "Shyam rate = 2/3",
                "0.667 job per hour",
                "two-thirds job per hour"
            ],
            "hints": [
                "Shyam's rate = 1 ÷ time = 1 ÷ 1.5.",
                "1 ÷ 1.5 = 1 ÷ (3/2) = 2/3.",
                "Shyam's rate = 2/3 job per hour."
            ]
        },
        {
            "id": "m1_step2",
            "type": "step",
            "label": "Add the Rates",
            "description": "Combined rate = 1 + 2/3 = 5/3 job/hr.",
            "prompt": "What is the combined rate when both work together? (1 + 2/3 = ?)",
            "accept": [
                "5/3",
                "5/3 job per hour",
                "1 + 2/3 = 5/3",
                "combined rate = 5/3",
                "1.667 jobs per hour"
            ],
            "hints": [
                "Add Ram's rate and Shyam's rate.",
                "1 + 2/3 = 3/3 + 2/3 = 5/3.",
                "Combined rate = 5/3 jobs per hour."
            ]
        },
        {
            "id": "m1_step3",
            "type": "step",
            "label": "Calculate Combined Time",
            "description": "Time = 1 ÷ combined rate = 1 ÷ (5/3) = 3/5 hr = 36 minutes.",
            "prompt": "If combined rate is 5/3 job/hr, how long does 1 job take? (time = 1 ÷ 5/3)",
            "accept": [
                "3/5 hour",
                "36 minutes",
                "0.6 hours",
                "3/5 hr",
                "36 min",
                "1 ÷ (5/3) = 3/5",
                "36"
            ],
            "hints": [
                "Time = 1 ÷ rate.",
                "Time = 1 ÷ (5/3) = 3/5 hours.",
                "3/5 hours = 3/5 × 60 = 36 minutes."
            ]
        },
        {
            "id": "method2",
            "type": "method",
            "label": "Method 2: LCM Method",
            "description": "Use LCM of individual times to find work done in a common time frame.",
            "prompt": "Find the LCM of 1 hour and 1.5 hours (or 1 hr and 3/2 hr). Work with LCM = 3 hours as the reference period.",
            "accept": [
                "LCM method",
                "LCM of 1 and 1.5",
                "LCM = 3",
                "common time frame method",
                "LCM of times"
            ],
            "hints": [
                "Convert 1.5 hours to a fraction: 1.5 = 3/2. LCM of 1 and 3/2 hours.",
                "LCM of 1 and 3 (numerators with same denominator) is 3, so LCM = 3 hours.",
                "Use 3 hours as the reference: find how many jobs each person completes in 3 hours."
            ]
        },
        {
            "id": "m2_step1",
            "type": "step",
            "label": "Find Jobs Done in 3 Hours",
            "description": "In 3 hours: Ram does 3 jobs, Shyam does 2 jobs. Together = 5 jobs.",
            "prompt": "In 3 hours, how many jobs does Ram complete? How many does Shyam complete?",
            "accept": [
                "Ram = 3, Shyam = 2",
                "Ram does 3 jobs, Shyam does 2 jobs",
                "3 jobs and 2 jobs",
                "together 5 jobs in 3 hours",
                "Ram 3, Shyam 2, total 5"
            ],
            "hints": [
                "Ram takes 1 hour per job, so in 3 hours he does 3 ÷ 1 = 3 jobs.",
                "Shyam takes 1.5 hours per job, so in 3 hours he does 3 ÷ 1.5 = 2 jobs.",
                "Together they complete 3 + 2 = 5 jobs in 3 hours."
            ]
        },
        {
            "id": "m2_step2",
            "type": "step",
            "label": "Find Time for 1 Job Together",
            "description": "5 jobs in 3 hours → 1 job in 3/5 hours = 36 minutes.",
            "prompt": "If they do 5 jobs in 3 hours, how long does 1 job take? (time = 3/5 hours = ? minutes)",
            "accept": [
                "3/5 hour",
                "36 minutes",
                "3 ÷ 5 = 3/5 hr",
                "36 min",
                "0.6 hours",
                "36"
            ],
            "hints": [
                "Time for 1 job = total time ÷ number of jobs.",
                "Time = 3 hours ÷ 5 jobs = 3/5 hours.",
                "3/5 hours = 3/5 × 60 = 36 minutes."
            ]
        },
        {
            "id": "conclusion",
            "type": "conclusion",
            "label": "Final Answer",
            "description": "Ram and Shyam together will take 36 minutes (3/5 hour) to cut the vegetables.",
            "prompt": "How long will Ram and Shyam take to cut the vegetables if they work together?",
            "accept": [
                "36 minutes",
                "36 min",
                "3/5 hour",
                "0.6 hours",
                "36",
                "3/5 hr",
                "thirty-six minutes"
            ],
            "hints": [
                "Both methods should give the same result.",
                "Convert the fractional hour to minutes: 3/5 × 60 = 36.",
                "Ram and Shyam together will finish in 36 minutes (= 3/5 hour)."
            ]
        }
    ],
    "edges": [
        { "from": "start", "to": "given_extraction" },
        { "from": "given_extraction", "to": "goal_extraction" },
        { "from": "goal_extraction", "to": "method1" },
        { "from": "goal_extraction", "to": "method2" },
        { "from": "method1", "to": "m1_step1" },
        { "from": "m1_step1", "to": "m1_step2" },
        { "from": "m1_step2", "to": "m1_step3" },
        { "from": "m1_step3", "to": "conclusion" },
        { "from": "method2", "to": "m2_step1" },
        { "from": "m2_step1", "to": "m2_step2" },
        { "from": "m2_step2", "to": "conclusion" }
    ]
};