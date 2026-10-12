// Standalone solution graph for NCERT Example 4 (teacher-to-student ratio comparison)
window.SOLUTION_GRAPHS = window.SOLUTION_GRAPHS || {};
window.SOLUTION_GRAPHS["g08-hegp107-ex004"] = {
  "graph_meta": {
    "graph_id": "sg-g08-hegp107-ex004",
    "problem_uuid": "g08-hegp107-ex004",
    "problem_text": "In my school, there are 5 teachers and 170 students. The ratio of teachers to students is 5 : 170. Count the number of teachers and students in your school. What is the ratio of teachers to students in your school? Is the teacher-to-student ratio in your school proportional to the one in my school?",
    "navigation_label": "Teachers and students ratio",
    "problem_context": { "first": [5, 170], "second": [10, 340] },
    "graph_type": "directed_acyclic_graph",
    "version": "1.0.0",
    "description": "Solution DAG for the school teacher-to-student ratio comparison. It shows that 5:170 and 10:340 both simplify to 1:34, so the ratios are proportional.",
    "created": "2026-10-11",
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
      "description": "Compare the teacher-to-student ratio in the school with the ratio 5:170.",
      "prompt": "Reduce the ratio 5:170 and compare it with the ratio in your school.",
      "accept": [],
      "hints": [
        "Write the ratio as teachers : students.",
        "Reduce both numbers by the same factor.",
        "Check whether the simplified ratio matches the school ratio."
      ]
    },
    {
      "id": "conclusion",
      "type": "conclusion",
      "label": "Final Conclusion",
      "description": "Yes, the ratios are proportional because both simplify to 1:34.",
      "prompt": "State whether the teacher-to-student ratios are proportional.",
      "accept": [
        "yes",
        "yes, they are proportional",
        "the ratios are proportional",
        "yes, both simplify to 1:34",
        "yes, 5:170 = 10:340 = 1:34",
        "proportional"
      ],
      "hints": [
        "5:170 simplifies to 1:34.",
        "10:340 also simplifies to 1:34.",
        "Since both ratios are the same, they are proportional."
      ]
    },
    {
      "id": "m1_simplify",
      "type": "method",
      "label": "Method 1: Simplify the ratio",
      "description": "Reduce the teacher-to-student ratio 5:170 to its simplest form.",
      "prompt": "Simplify 5:170.",
      "accept": ["simplify", "reduce", "1:34", "1 : 34"],
      "hints": [
        "Divide both numbers by 5.",
        "5 ÷ 5 = 1 and 170 ÷ 5 = 34.",
        "So the simplified ratio is 1:34."
      ]
    },
    {
      "id": "m1_s1",
      "type": "step",
      "label": "Reduce 5:170",
      "description": "5:170 simplifies to 1:34.",
      "prompt": "What is the simplest form of 5:170?",
      "accept": ["1:34", "1 : 34", "one to thirty-four", "5/170 = 1/34"],
      "hints": [
        "Both numbers are divisible by 5.",
        "5 ÷ 5 = 1 and 170 ÷ 5 = 34.",
        "The ratio is 1:34."
      ]
    },
    {
      "id": "m1_s2",
      "type": "step",
      "label": "Compare with another ratio",
      "description": "10:340 also reduces to 1:34, so the ratios are proportional.",
      "prompt": "If your school has 10 teachers and 340 students, what is the ratio?",
      "accept": ["10:340", "10 : 340", "10 to 340", "1:34"],
      "hints": [
        "10:340 divides by 10 to give 1:34.",
        "This is the same as the original ratio.",
        "So the ratios are proportional."
      ]
    },
    {
      "id": "m1_s3",
      "type": "step",
      "label": "Decide proportionality",
      "description": "Since 5:170 and 10:340 both simplify to 1:34, the teacher-to-student ratios are proportional.",
      "prompt": "Are the ratios proportional?",
      "accept": ["yes", "yes, proportional", "they are proportional", "the ratio is the same"],
      "hints": [
        "Both ratios simplify to 1:34.",
        "That means they are in the same proportion."
      ]
    }
  ],
  "edges": [
    { "from": "start", "to": "m1_simplify", "label": "Reduce the ratio" },
    { "from": "m1_simplify", "to": "m1_s1", "label": "Read simplified form" },
    { "from": "m1_s1", "to": "m1_s2", "label": "Compare with school ratio" },
    { "from": "m1_s2", "to": "m1_s3", "label": "Check proportionality" },
    { "from": "m1_s3", "to": "conclusion", "label": "State the answer" }
  ]
};
