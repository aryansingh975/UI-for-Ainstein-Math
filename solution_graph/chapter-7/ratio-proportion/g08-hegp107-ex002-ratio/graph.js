// Standalone solution graph for the 6:8 vs 72:96 proportionality check
// Embedded as JS to avoid file:// fetch restrictions
window.SOLUTION_GRAPHS = window.SOLUTION_GRAPHS || {};
window.SOLUTION_GRAPHS["g08-hegp107-ex002-ratio"] = {
  "graph_meta": {
    "graph_id": "sg-g08-hegp107-ex002-ratio",
    "problem_uuid": "g08-hegp107-ex002-ratio",
    "problem_text": "Are the ratios 6 : 8 and 72 : 96 proportional?",
    "navigation_label": "Ratios 6:8 and 72:96",
    "problem_context": { "first": [6, 8], "second": [72, 96] },
    "graph_type": "directed_acyclic_graph",
    "version": "1.0.0",
    "description": "Standalone solution DAG for the 6:8 and 72:96 proportionality problem. The reduction-based methods explicitly operate on both ratios before comparing their simplified forms.",
    "created": "2026-10-01",
    "total_methods": 8,
    "total_nodes": 38,
    "total_edges": 44
  },
  "start_node": "start",
  "conclusion_node": "conclusion",
  "nodes": [
    {
      "id": "start",
      "type": "start",
      "label": "Problem Statement",
      "description": "Are the ratios 6 : 8 and 72 : 96 proportional?",
      "prompt": "Are the ratios 6 : 8 and 72 : 96 proportional? Explain your reasoning.",
      "accept": [],
      "hints": [
        "You can test whether both ratios have the same value.",
        "Try simplifying both ratios or use another valid method.",
        "Methods include simplification, cross multiplication, scaling, and decimal comparison."
      ]
    },
    {
      "id": "conclusion",
      "type": "conclusion",
      "label": "Final Conclusion",
      "description": "Yes, 6 : 8 and 72 : 96 are proportional.",
      "prompt": "State your conclusion: Are 6 : 8 and 72 : 96 proportional?",
      "accept": [
        "yes",
        "yes they are proportional",
        "they are proportional",
        "proportional",
        "yes proportional",
        "6:8 and 72:96 are proportional",
        "yes, proportional"
      ],
      "hints": [
        "Both ratios represent the same relationship.",
        "Both ratios simplify to 3 : 4.",
        "Yes, they are proportional."
      ]
    },
    {
      "id": "m1_simplify",
      "type": "method",
      "label": "Method 1: Simplification (HCF)",
      "description": "Find the HCF and simplify each ratio independently, then compare the results.",
      "prompt": "Choose a method. You can find the HCF and simplify both ratios.",
      "accept": ["simplif", "hcf", "highest common factor", "reduce", "reduc", "simplest form", "divide"],
      "hints": [
        "Start by simplifying 6 : 8.",
        "Then find the HCF of 72 and 96.",
        "Compare the simplified form of each ratio."
      ]
    },
    {
      "id": "m1_s1",
      "type": "step",
      "label": "Find HCF of 6 and 8",
      "description": "The HCF of 6 and 8 is 2.",
      "prompt": "What is the HCF of 6 and 8?",
      "accept": ["2", "hcf is 2", "hcf = 2", "highest common factor is 2", "gcd is 2", "gcd = 2"],
      "hints": ["List the factors of 6 and 8.", "Their common factors are 1 and 2.", "The HCF is 2."]
    },
    {
      "id": "m1_s2",
      "type": "step",
      "label": "Simplify 6 : 8",
      "description": "Divide both terms of 6 : 8 by 2 to get 3 : 4.",
      "prompt": "Divide both terms of 6 : 8 by 2. What ratio do you get?",
      "accept": ["3:4", "3 : 4", "6/2=3 and 8/2=4", "6/2 = 3, 8/2 = 4", "3 to 4"],
      "hints": ["6 divided by 2 is 3.", "8 divided by 2 is 4.", "So 6 : 8 simplifies to 3 : 4."]
    },
    {
      "id": "m1_s3",
      "type": "step",
      "label": "Find HCF of 72 and 96",
      "description": "The HCF of 72 and 96 is 24.",
      "prompt": "What is the HCF of 72 and 96?",
      "accept": ["24", "hcf is 24", "hcf = 24", "highest common factor is 24", "gcd is 24", "gcd = 24"],
      "hints": ["Find the common factors of 72 and 96.", "24 divides both numbers.", "The HCF is 24."]
    },
    {
      "id": "m1_s4",
      "type": "step",
      "label": "Simplify 72 : 96",
      "description": "Divide both terms of 72 : 96 by 24 to get 3 : 4.",
      "prompt": "Divide both terms of 72 : 96 by 24. What ratio do you get?",
      "accept": ["3:4", "3 : 4", "72/24=3 and 96/24=4", "72/24 = 3, 96/24 = 4", "3 to 4"],
      "hints": ["72 divided by 24 is 3.", "96 divided by 24 is 4.", "So 72 : 96 simplifies to 3 : 4."]
    },
    {
      "id": "m2_fraction",
      "type": "method",
      "label": "Method 2: Fraction Simplification",
      "description": "Write both ratios as fractions, simplify each fraction, and compare.",
      "prompt": "Choose a method. You can write both ratios as fractions and simplify them.",
      "accept": ["fraction", "simplify fraction", "fractions", "write as fractions"],
      "hints": ["Write 6 : 8 as 6/8.", "Write 72 : 96 as 72/96.", "Simplify both fractions and compare them."]
    },
    {
      "id": "m2_s1",
      "type": "step",
      "label": "Write both ratios as fractions",
      "description": "The ratios can be written as 6/8 and 72/96.",
      "prompt": "Write both ratios as fractions.",
      "accept": ["6/8 and 72/96", "6/8, 72/96", "6 over 8 and 72 over 96"],
      "hints": ["Write the first ratio as numerator over denominator.", "Do the same for the second ratio.", "The fractions are 6/8 and 72/96."]
    },
    {
      "id": "m2_s2",
      "type": "step",
      "label": "Simplify 6/8",
      "description": "6/8 simplifies to 3/4 by dividing the numerator and denominator by 2.",
      "prompt": "What is 6/8 in simplest form?",
      "accept": ["3/4", "3 over 4", "6/8=3/4", "6/8 = 3/4"],
      "hints": ["The HCF of 6 and 8 is 2.", "Divide the numerator and denominator by 2.", "6/8 = 3/4."]
    },
    {
      "id": "m2_s3",
      "type": "step",
      "label": "Simplify 72/96",
      "description": "72/96 simplifies to 3/4 by dividing the numerator and denominator by 24.",
      "prompt": "What is 72/96 in simplest form?",
      "accept": ["3/4", "3 over 4", "72/96=3/4", "72/96 = 3/4"],
      "hints": ["The HCF of 72 and 96 is 24.", "Divide the numerator and denominator by 24.", "72/96 = 3/4."]
    },
    {
      "id": "m3_prime",
      "type": "method",
      "label": "Method 3: Prime Factorization",
      "description": "Factorize both terms in both ratios, simplify each ratio, and compare.",
      "prompt": "Choose a method. You can use prime factorization on both ratios.",
      "accept": ["prime", "factorization", "prime factor", "factorize", "factorise"],
      "hints": ["Factorize 6 and 8.", "Factorize 72 and 96.", "Cancel common prime factors in each ratio."]
    },
    {
      "id": "m3_s1",
      "type": "step",
      "label": "Factorize 6 and 8",
      "description": "6 = 2 x 3 and 8 = 2^3, so 6 : 8 simplifies to 3 : 4.",
      "prompt": "What are the prime factorizations of 6 and 8?",
      "accept": ["6=2*3 and 8=2^3", "6 = 2 x 3 and 8 = 2^3", "6 is 2 times 3 and 8 is 2 cubed"],
      "hints": ["6 = 2 x 3.", "8 = 2 x 2 x 2 = 2^3.", "Cancel one factor of 2 from both terms of 6/8."]
    },
    {
      "id": "m3_s2",
      "type": "step",
      "label": "Factorize 72 and 96",
      "description": "72 = 2^3 x 3^2 and 96 = 2^5 x 3.",
      "prompt": "What are the prime factorizations of 72 and 96?",
      "accept": ["72=2^3*3^2 and 96=2^5*3", "72 = 2^3 x 3^2 and 96 = 2^5 x 3"],
      "hints": ["72 = 8 x 9 = 2^3 x 3^2.", "96 = 32 x 3 = 2^5 x 3.", "Now cancel common factors."]
    },
    {
      "id": "m3_s3",
      "type": "step",
      "label": "Simplify both factored ratios",
      "description": "Cancel common factors in each ratio; both simplify to 3/4.",
      "prompt": "After canceling common factors, what does each ratio simplify to?",
      "accept": ["3/4 and 3/4", "3:4 and 3:4", "both simplify to 3/4", "both are 3/4"],
      "hints": ["For 6/8, cancel one factor of 2.", "For 72/96, cancel 2^3 and 3.", "Both fractions simplify to 3/4."]
    },
    {
      "id": "m4_reduce",
      "type": "method",
      "label": "Method 4: Step-by-Step Reduction",
      "description": "Reduce 6 : 8 and 72 : 96 independently until both reach 3 : 4.",
      "prompt": "Choose a method. Reduce both ratios step by step.",
      "accept": ["reduce step by step", "step by step reduction", "stepwise reduction"],
      "hints": ["First reduce 6 : 8 by dividing both terms by 2.", "Then reduce 72 : 96 using common factors.", "Compare the final ratios."]
    },
    {
      "id": "m4_s1",
      "type": "step",
      "label": "Reduce 6 : 8 to 3 : 4",
      "description": "Divide both terms of 6 : 8 by 2 to get 3 : 4.",
      "prompt": "Divide both terms of 6 : 8 by 2. What ratio do you get?",
      "accept": ["3:4", "3 : 4", "6/2=3 and 8/2=4", "3 to 4"],
      "hints": ["6 divided by 2 is 3.", "8 divided by 2 is 4.", "The first ratio becomes 3 : 4."]
    },
    {
      "id": "m4_s2",
      "type": "step",
      "label": "Reduce 72 : 96 to 36 : 48",
      "description": "Divide both terms of 72 : 96 by 2 to get 36 : 48.",
      "prompt": "Divide both terms of 72 : 96 by 2. What ratio do you get?",
      "accept": ["36:48", "36 : 48", "36 to 48", "36/48"],
      "hints": ["72 divided by 2 is 36.", "96 divided by 2 is 48.", "The ratio becomes 36 : 48."]
    },
    {
      "id": "m4_s3",
      "type": "step",
      "label": "Reduce 36 : 48 to 18 : 24",
      "description": "Divide both terms of 36 : 48 by 2 to get 18 : 24.",
      "prompt": "Divide both terms of 36 : 48 by 2. What ratio do you get?",
      "accept": ["18:24", "18 : 24", "18 to 24", "18/24"],
      "hints": ["36 divided by 2 is 18.", "48 divided by 2 is 24.", "The ratio becomes 18 : 24."]
    },
    {
      "id": "m4_s4",
      "type": "step",
      "label": "Reduce 18 : 24 to 9 : 12",
      "description": "Divide both terms of 18 : 24 by 2 to get 9 : 12.",
      "prompt": "Divide both terms of 18 : 24 by 2. What ratio do you get?",
      "accept": ["9:12", "9 : 12", "9 to 12", "9/12"],
      "hints": ["18 divided by 2 is 9.", "24 divided by 2 is 12.", "The ratio becomes 9 : 12."]
    },
    {
      "id": "m4_s5",
      "type": "step",
      "label": "Reduce 9 : 12 to 3 : 4",
      "description": "Divide both terms of 9 : 12 by 3 to get 3 : 4.",
      "prompt": "Divide both terms of 9 : 12 by 3. What ratio do you get?",
      "accept": ["3:4", "3 : 4", "3 to 4", "3/4"],
      "hints": ["9 divided by 3 is 3.", "12 divided by 3 is 4.", "The second ratio is now in simplest form: 3 : 4."]
    },
    {
      "id": "shared_ratio_comparison",
      "type": "step",
      "label": "Compare the simplified ratios",
      "description": "Both original ratios simplify to 3 : 4, so they are equivalent.",
      "prompt": "Do the two simplified ratios match? Show the comparison.",
      "accept": ["3:4=3:4", "3/4=3/4", "3:4 equals 3:4", "3/4 equals 3/4", "both ratios simplify to 3:4", "both are 3:4", "they match", "equal", "same"],
      "hints": ["The first ratio simplifies to 3 : 4.", "The second ratio also simplifies to 3 : 4.", "Since the simplified ratios are equal, the original ratios are proportional."]
    },
    {
      "id": "m5_cross_multiply",
      "type": "method",
      "label": "Method 5: Cross Multiplication",
      "description": "Compare 6 x 96 with 8 x 72. Equal cross products mean the ratios are proportional.",
      "prompt": "Choose a method. You can cross multiply the ratios.",
      "accept": ["cross multiply", "cross multiplication", "cross product"],
      "hints": ["For 6 : 8 and 72 : 96, compare 6 x 96 and 8 x 72.", "Calculate both products.", "Check whether the products are equal."]
    },
    {
      "id": "m5_s1",
      "type": "step",
      "label": "Set up cross multiplication",
      "description": "The cross products are 6 x 96 and 8 x 72.",
      "prompt": "What two products do you compare when cross multiplying 6 : 8 and 72 : 96?",
      "accept": ["6*96 and 8*72", "6 x 96 and 8 x 72", "6*96=8*72", "6 x 96 = 8 x 72"],
      "hints": ["Multiply the first term of the first ratio by the second term of the second.", "Multiply the second term of the first ratio by the first term of the second.", "Compare 6 x 96 and 8 x 72."]
    },
    {
      "id": "m5_s2",
      "type": "step",
      "label": "Compute 6 x 96",
      "description": "6 x 96 = 576.",
      "prompt": "What is 6 x 96?",
      "accept": ["576", "6*96=576", "6 x 96 = 576", "6 times 96 is 576"],
      "hints": ["6 x 100 = 600.", "Subtract 6 x 4 = 24.", "600 - 24 = 576."]
    },
    {
      "id": "m5_s3",
      "type": "step",
      "label": "Compute 8 x 72",
      "description": "8 x 72 = 576.",
      "prompt": "What is 8 x 72?",
      "accept": ["576", "8*72=576", "8 x 72 = 576", "8 times 72 is 576"],
      "hints": ["8 x 70 = 560.", "8 x 2 = 16.", "560 + 16 = 576."]
    },
    {
      "id": "m5_s4",
      "type": "step",
      "label": "Compare cross products",
      "description": "Both cross products are 576, so the ratios are proportional.",
      "prompt": "Are the cross products equal? What does that tell you?",
      "accept": ["576=576", "576 = 576", "equal", "they are equal", "both are 576", "6*96=8*72=576"],
      "hints": ["6 x 96 = 576.", "8 x 72 = 576.", "Equal cross products show the ratios are proportional."]
    },
    {
      "id": "m6_scale",
      "type": "method",
      "label": "Method 6: Scaling",
      "description": "Scale 6 : 8 by a common factor and verify that it becomes 72 : 96.",
      "prompt": "Choose a method. Check whether one ratio can be scaled to the other.",
      "accept": ["scale", "scaling", "multiply by", "common factor"],
      "hints": ["Find the factor that changes 6 into 72.", "Apply the same factor to 8.", "Check whether the result is 96."]
    },
    {
      "id": "m6_s1",
      "type": "step",
      "label": "Find the scale factor",
      "description": "The factor that changes 6 to 72 is 12.",
      "prompt": "What number do you multiply 6 by to get 72?",
      "accept": ["12", "6*12=72", "6 x 12 = 72", "multiply by 12", "factor is 12"],
      "hints": ["Divide 72 by 6.", "72 divided by 6 is 12.", "The scale factor is 12."]
    },
    {
      "id": "m6_s2",
      "type": "step",
      "label": "Verify the second term",
      "description": "8 x 12 = 96, so the same factor works for the second term.",
      "prompt": "Does multiplying 8 by 12 give 96?",
      "accept": ["yes", "8*12=96", "8 x 12 = 96", "yes 8*12=96", "yes 8 x 12 = 96"],
      "hints": ["Calculate 8 x 12.", "8 x 12 = 96.", "The same factor works for both terms."]
    },
    {
      "id": "m6_s3",
      "type": "step",
      "label": "Conclude from scaling",
      "description": "Both terms of 6 : 8 are multiplied by 12 to get 72 : 96.",
      "prompt": "What can you conclude when both terms are multiplied by the same factor?",
      "accept": ["proportional", "equivalent", "same factor", "6:8=72:96", "they are proportional"],
      "hints": ["6 x 12 = 72 and 8 x 12 = 96.", "Both terms were scaled by 12.", "The ratios are equivalent and proportional."]
    },
    {
      "id": "m7_decimal",
      "type": "method",
      "label": "Method 7: Decimal Comparison",
      "description": "Convert each ratio to a decimal and compare the values.",
      "prompt": "Choose a method. Convert both ratios to decimals and compare them.",
      "accept": ["decimal", "decimal comparison", "convert to decimal"],
      "hints": ["Divide 6 by 8.", "Divide 72 by 96.", "Compare the decimal answers."]
    },
    {
      "id": "m7_s1",
      "type": "step",
      "label": "Convert 6 : 8 to a decimal",
      "description": "6 divided by 8 is 0.75.",
      "prompt": "What is 6 divided by 8 as a decimal?",
      "accept": ["0.75", "6/8=0.75", "6/8 = 0.75", "three quarters"],
      "hints": ["Simplify 6/8 to 3/4.", "3 divided by 4 is 0.75.", "So 6/8 = 0.75."]
    },
    {
      "id": "m7_s2",
      "type": "step",
      "label": "Convert 72 : 96 to a decimal",
      "description": "72 divided by 96 is 0.75.",
      "prompt": "What is 72 divided by 96 as a decimal?",
      "accept": ["0.75", "72/96=0.75", "72/96 = 0.75", "72 divided by 96 is 0.75"],
      "hints": ["Simplify 72/96 to 3/4.", "3 divided by 4 is 0.75.", "So 72/96 = 0.75."]
    },
    {
      "id": "m7_s3",
      "type": "step",
      "label": "Compare decimal values",
      "description": "Both ratios equal 0.75, so they are proportional.",
      "prompt": "Are the decimal values equal? What does this tell you?",
      "accept": ["0.75=0.75", "0.75 = 0.75", "equal", "same", "both 0.75", "they are equal"],
      "hints": ["6/8 = 0.75.", "72/96 = 0.75.", "Since both values are equal, the ratios are proportional."]
    },
    {
      "id": "m8_equivalent",
      "type": "method",
      "label": "Method 8: Equivalent Ratio",
      "description": "Multiply both terms of 6 : 8 by 12 to obtain 72 : 96.",
      "prompt": "Choose a method. Show that one ratio can be transformed into the other by multiplying both terms by the same number.",
      "accept": ["equivalent", "equivalent ratio", "multiply both terms", "scale 6:8"],
      "hints": ["Find a common factor that changes 6 into 72.", "Multiply both terms of 6 : 8 by 12.", "Check that the result is 72 : 96."]
    },
    {
      "id": "m8_s1",
      "type": "step",
      "label": "Multiply 6 : 8 by 12",
      "description": "6 x 12 = 72 and 8 x 12 = 96.",
      "prompt": "What ratio do you get when you multiply both terms of 6 : 8 by 12?",
      "accept": ["72:96", "72 : 96", "6*12=72 and 8*12=96", "6 x 12 = 72 and 8 x 12 = 96", "72 and 96"],
      "hints": ["6 x 12 = 72.", "8 x 12 = 96.", "The resulting ratio is 72 : 96."]
    },
    {
      "id": "m8_s2",
      "type": "step",
      "label": "Recognize equivalent ratios",
      "description": "Multiplying both terms of 6 : 8 by 12 gives 72 : 96, so the ratios are equivalent and proportional.",
      "prompt": "Since both terms were multiplied by 12 to get the second ratio, what can you conclude?",
      "accept": ["proportional", "equivalent", "same ratio", "6:8=72:96", "they are proportional"],
      "hints": ["Both terms were multiplied by the same number.", "This gives an equivalent ratio.", "Equivalent ratios are proportional."]
    }
  ],
  "edges": [
    {"from": "start", "to": "m1_simplify", "label": "Method 1: Simplification"},
    {"from": "start", "to": "m2_fraction", "label": "Method 2: Fraction Simplification"},
    {"from": "start", "to": "m3_prime", "label": "Method 3: Prime Factorization"},
    {"from": "start", "to": "m4_reduce", "label": "Method 4: Step-by-Step Reduction"},
    {"from": "start", "to": "m5_cross_multiply", "label": "Method 5: Cross Multiplication"},
    {"from": "start", "to": "m6_scale", "label": "Method 6: Scaling"},
    {"from": "start", "to": "m7_decimal", "label": "Method 7: Decimal Comparison"},
    {"from": "start", "to": "m8_equivalent", "label": "Method 8: Equivalent Ratio"},
    {"from": "m1_simplify", "to": "m1_s1", "label": "Find HCF of first ratio"},
    {"from": "m1_s1", "to": "m1_s2", "label": "Simplify first ratio"},
    {"from": "m1_s2", "to": "m1_s3", "label": "Find HCF of second ratio"},
    {"from": "m1_s3", "to": "m1_s4", "label": "Simplify second ratio"},
    {"from": "m1_s4", "to": "shared_ratio_comparison", "label": "Compare simplified ratios"},
    {"from": "m2_fraction", "to": "m2_s1", "label": "Write both fractions"},
    {"from": "m2_s1", "to": "m2_s2", "label": "Simplify first fraction"},
    {"from": "m2_s2", "to": "m2_s3", "label": "Simplify second fraction"},
    {"from": "m2_s3", "to": "shared_ratio_comparison", "label": "Compare simplified fractions"},
    {"from": "m3_prime", "to": "m3_s1", "label": "Factorize first ratio"},
    {"from": "m3_s1", "to": "m3_s2", "label": "Factorize second ratio"},
    {"from": "m3_s2", "to": "m3_s3", "label": "Simplify both ratios"},
    {"from": "m3_s3", "to": "shared_ratio_comparison", "label": "Compare simplified ratios"},
    {"from": "m4_reduce", "to": "m4_s1", "label": "Reduce first ratio"},
    {"from": "m4_s1", "to": "m4_s2", "label": "Reduce second ratio"},
    {"from": "m4_s2", "to": "m4_s3", "label": "Divide by 2"},
    {"from": "m4_s3", "to": "m4_s4", "label": "Divide by 2"},
    {"from": "m4_s4", "to": "m4_s5", "label": "Divide by 3"},
    {"from": "m4_s5", "to": "shared_ratio_comparison", "label": "Compare simplified ratios"},
    {"from": "shared_ratio_comparison", "to": "conclusion", "label": "Proportional"},
    {"from": "m5_cross_multiply", "to": "m5_s1", "label": "Set up cross multiplication"},
    {"from": "m5_s1", "to": "m5_s2", "label": "Compute first product"},
    {"from": "m5_s2", "to": "m5_s3", "label": "Compute second product"},
    {"from": "m5_s3", "to": "m5_s4", "label": "Compare products"},
    {"from": "m5_s4", "to": "conclusion", "label": "Proportional"},
    {"from": "m6_scale", "to": "m6_s1", "label": "Find scaling factor"},
    {"from": "m6_s1", "to": "m6_s2", "label": "Verify second term"},
    {"from": "m6_s2", "to": "m6_s3", "label": "Same factor"},
    {"from": "m6_s3", "to": "conclusion", "label": "Proportional"},
    {"from": "m7_decimal", "to": "m7_s1", "label": "Convert first ratio"},
    {"from": "m7_s1", "to": "m7_s2", "label": "Convert second ratio"},
    {"from": "m7_s2", "to": "m7_s3", "label": "Compare decimal values"},
    {"from": "m7_s3", "to": "conclusion", "label": "Proportional"},
    {"from": "m8_equivalent", "to": "m8_s1", "label": "Multiply first ratio by 12"},
    {"from": "m8_s1", "to": "m8_s2", "label": "Recognize equivalence"},
    {"from": "m8_s2", "to": "conclusion", "label": "Proportional"}
  ]
};
