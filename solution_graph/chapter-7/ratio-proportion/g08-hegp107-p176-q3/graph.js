// Solution graph for NCERT Figure it Out Q3 (g08-hegp107-p176-q3)
window.SOLUTION_GRAPHS = window.SOLUTION_GRAPHS || {};
window.SOLUTION_GRAPHS["g08-hegp107-p176-q3"] = {
  "graph_meta": {
    "graph_id": "sg-g08-hegp107-p176-q3",
    "problem_uuid": "g08-hegp107-p176-q3",
    "problem_text": "The area of Delhi is 1,484 sq. km and the area of Mumbai is 550 sq. km. The population of Delhi is approximately 30 million and that of Mumbai is 20 million people. Which city is more crowded? Why do you say so?",
    "navigation_label": "Population density comparison",
    "problem_context": { "delhi_area": 1484, "delhi_pop": 30000000, "mumbai_area": 550, "mumbai_pop": 20000000 },
    "graph_type": "directed_acyclic_graph",
    "version": "1.0.0",
    "description": "Solution DAG for comparing the population densities of Delhi and Mumbai and identifying the more crowded city.",
    "created": "2026-10-11",
    "total_methods": 1,
    "total_nodes": 6,
    "total_edges": 5
  },
  "start_node": "start",
  "conclusion_node": "conclusion",
  "nodes": [
    {
      "id": "start",
      "type": "start",
      "label": "Problem Statement",
      "description": "Compare the two cities by population per square kilometre.",
      "prompt": "Find the density of each city and compare them.",
      "accept": [],
      "hints": [
        "Population density means people per square kilometre.",
        "Delhi density = population ÷ area.",
        "Mumbai density = population ÷ area."
      ]
    },
    {
      "id": "conclusion",
      "type": "conclusion",
      "label": "Final Conclusion",
      "description": "Mumbai is more crowded because it has about 36,364 people per sq km, while Delhi has about 20,216 people per sq km.",
      "prompt": "State which city is more crowded and why.",
      "accept": [
        "Mumbai is more crowded",
        "mumbai",
        "mumbai is more crowded because it has more people per square kilometre",
        "mumbai 36364 vs delhi 20216",
        "mumbai has higher density",
        "delhi is less crowded"
      ],
      "hints": [
        "Mumbai density ≈ 36,364 people/sq km.",
        "Delhi density ≈ 20,216 people/sq km.",
        "Since 36,364 > 20,216, Mumbai is more crowded."
      ]
    },
    {
      "id": "m1_density",
      "type": "method",
      "label": "Method 1: Compute population density",
      "description": "Divide each city's population by its area to compare the people per sq km.",
      "prompt": "Calculate the density for Delhi and Mumbai.",
      "accept": [
        "divide population by area",
        "population density",
        "calculate density",
        "compare per sq km"
      ],
      "hints": [
        "Delhi = 30,000,000 ÷ 1,484.",
        "Mumbai = 20,000,000 ÷ 550.",
        "Compare the two results."
      ]
    },
    {
      "id": "m1_s1",
      "type": "step",
      "label": "Compute Delhi density",
      "description": "30,000,000 ÷ 1,484 ≈ 20,216 people per sq km.",
      "prompt": "What is Delhi's population density?",
      "accept": [
        "20216",
        "20216 people per sq km",
        "delhi 20216",
        "30,000,000/1484 ≈ 20,216"
      ],
      "hints": [
        "30,000,000 ÷ 1,484 ≈ 20,216.",
        "Delhi is about 20,216 people per square kilometre."
      ]
    },
    {
      "id": "m1_s2",
      "type": "step",
      "label": "Compute Mumbai density",
      "description": "20,000,000 ÷ 550 ≈ 36,364 people per sq km.",
      "prompt": "What is Mumbai's population density?",
      "accept": [
        "36364",
        "36364 people per sq km",
        "mumbai 36364",
        "20,000,000/550 ≈ 36,364"
      ],
      "hints": [
        "20,000,000 ÷ 550 ≈ 36,364.",
        "Mumbai is about 36,364 people per square kilometre."
      ]
    }
  ],
  "edges": [
    { "from": "start", "to": "m1_density", "label": "Compute density" },
    { "from": "m1_density", "to": "m1_s1", "label": "Delhi density" },
    { "from": "m1_s1", "to": "m1_s2", "label": "Mumbai density" },
    { "from": "m1_s2", "to": "conclusion", "label": "Compare densities" }
  ]
};
