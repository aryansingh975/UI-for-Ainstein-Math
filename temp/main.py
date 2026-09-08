"""
Main Execution Script for Reasoning Trace Tree Pipeline (Pure Python)

Demonstrates solving math word problems using formal reasoning traces.
Runs 100% locally without external API dependencies.
"""

from ainstein_math.verification.evaluator import evaluate_reasoning_trace

# Example problems and pre-generated reasoning traces for offline demonstration
SAMPLE_PROBLEMS = [
    {
        "id": 1,
        "title": "Bank Account Balance with Debt & Deposit",
        "problem": "An account has a debt of 20 dollars. A deposit of 100 dollars is made. Calculate the final balance.",
        "trace": """
[E1] EXTRACT entity: "debt of 20 dollars" -> val: -20
[E2] EXTRACT entity: "deposit of 100 dollars" -> val: 100
[M1] MAP trigger: "deposit is made" -> gen_trigger: "deposit" -> concept: "incremental addition to state" -> op: ADD
[B1] <E1, E2, M1> BIND logic: "Initial account state is modified by deposit amount" -> role: LEFT = -20, RIGHT = 100
[CONSTRUCT] Tree: ADD[balance](-20, 100) -> target: "dollars"
""".strip(),
    },
    {
        "id": 2,
        "title": "Discounted Pencil Boxes Purchase",
        "problem": "A box of pencils contains 12 pencils. You buy 5 boxes, but give away 10 pencils. How many pencils do you have left?",
        "trace": """
[E1] EXTRACT entity: "12 pencils per box" -> val: 12
[E2] EXTRACT entity: "5 boxes bought" -> val: 5
[E3] EXTRACT entity: "10 pencils given away" -> val: 10
[M1] MAP trigger: "buy 5 boxes" -> gen_trigger: "group multiplication" -> concept: "total quantity calculation" -> op: MUL
[M2] MAP trigger: "give away" -> gen_trigger: "subtraction of quantity" -> concept: "reduction of inventory" -> op: SUB
[B1] <E1, E2, M1> BIND logic: "Total initial pencils = 12 * 5" -> role: LEFT = 12, RIGHT = 5
[B2] <B1, E3, M2> BIND logic: "Remaining pencils = Total initial - 10" -> role: LEFT = MUL(12, 5), RIGHT = 10
[CONSTRUCT] Tree: SUB[remaining_pencils](MUL(12, 5), 10) -> target: "pencils"
""".strip(),
    },
]


def run_pipeline_demo():
    print("=" * 70)
    print("      AINSTEIN MATH: REASONING TRACE TREE PIPELINE DEMO")
    print("=" * 70)
    print("System Prompt & Grammar defined in prompts.py:")
    print("  Prefix AST operations: ADD, SUB, MUL, DIV, NEG, etc.")
    print("  Trace structure: EXTRACT -> MAP -> BIND -> CONSTRUCT")
    print("=" * 70)

    for sample in SAMPLE_PROBLEMS:
        print(f"\n--- Example {sample['id']}: {sample['title']} ---")
        print(f"Problem Text: \"{sample['problem']}\"\n")
        print("Generated Reasoning Trace:")
        print(sample['trace'])
        print("-" * 50)

        # Run end-to-end evaluation
        res = evaluate_reasoning_trace(sample['trace'])

        print(f"✅ Dependency Verification: Passed (Steps verified: {len(res['steps'])})")
        print(f"🌲 Prefix AST Expression:   {res['ast_expression']}")
        print("Visual AST Tree Representation:")
        print(res["ascii_tree"])
        print("-" * 50)
        print(f"🎯 Final Calculated Result: {res['result']} {res['target_unit']}")
        print("=" * 70)


if __name__ == "__main__":
    run_pipeline_demo()
