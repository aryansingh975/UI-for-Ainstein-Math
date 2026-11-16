"""
CLI Runner for Jev Step Classification Lab.
Supports both interactive terminal testing and automated batch test suites.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure scratch directory can import jev_engine
sys.path.insert(0, str(Path(__file__).resolve().parent))
from jev_engine import classify_student_input, load_method_1_context

STEP_NAMES = {
    "m1_step1": "Step 1: Express Mother as 5x",
    "m1_step2": "Step 2: Express Ages After 6 Years (x+6, 5x+6)",
    "m1_step3": "Step 3: Form and Solve Equation (5x+6 = 3(x+6) -> x=6)",
    "m1_step4": "Step 4: State Daughter's Present Age (6 years)",
    "off_step": "Off-Step / Unrecognized"
}

TEST_CASES = [
    {
        "input": "mother is 5x",
        "expected_node": "m1_step1",
        "expected_completeness": "complete",
        "description": "Standard Step 1 formulation"
    },
    {
        "input": "5x",
        "expected_node": "m1_step1",
        "expected_completeness": "complete",
        "description": "Minimal single-expression Step 1"
    },
    {
        "input": "in 6 years mother will be 5x + 6",
        "expected_node": "m1_step2",
        "expected_completeness": "partial",
        "description": "Partial Step 2 (mother only, missing daughter)"
    },
    {
        "input": "daughter is x+6 and mother is 5x+6",
        "expected_node": "m1_step2",
        "expected_completeness": "complete",
        "description": "Complete paired Step 2"
    },
    {
        "input": "5x + 6 = 3(x + 6)",
        "expected_node": "m1_step3",
        "expected_completeness": "complete",
        "description": "Initial equation setup in Step 3"
    },
    {
        "input": "2x = 12",
        "expected_node": "m1_step3",
        "expected_completeness": "partial",
        "description": "Intermediate algebraic reduction in Step 3 (equation simplified, but not yet solved for x)"
    },
    {
        "input": "x = 6",
        "expected_node": "m1_step3",
        "expected_completeness": "complete",
        "description": "Equation solved for x"
    },
    {
        "input": "daughter is 6 years old",
        "expected_node": "m1_step4",
        "expected_completeness": "complete",
        "description": "Final contextual answer with units"
    },
    {
        "input": "mother is 5x now, so in 6 years she is 5x+6 and daughter is x+6",
        "expected_node": "m1_step2",
        "expected_completeness": "clubbed_multi_step",
        "description": "Clubbed Step 1 & Step 2 in one turn"
    },
    {
        "input": "I like playing soccer after school",
        "expected_node": "off_step",
        "expected_completeness": "off_track",
        "description": "Unrelated off-track sentence"
    }
]


def print_banner():
    ctx = load_method_1_context()
    print("=" * 76)
    print("  AINSTEIN JEV STEP CLASSIFICATION LAB (ISOLATED TERMINAL PROTOTYPE)")
    print("=" * 76)
    print(f" Problem: {ctx['problem_text']}")
    print(f" Locked:  {ctx['method_name']}")
    print(" Steps in Method 1:")
    for nid, desc in ctx["method_steps"].items():
        print(f"   • [{nid}] {desc}")
    print("=" * 76)


def format_result(res: dict, student_input: str):
    print("\n" + "-" * 76)
    print(f"  STUDENT INPUT: \"{student_input}\"")
    print("-" * 76)
    if not res.get("success"):
        print(f"  [ERROR]: {res.get('error')}")
        return

    node_id = res.get("target_step_node", "off_step")
    node_name = STEP_NAMES.get(node_id, node_id)
    completeness = res.get("completeness", "").upper()
    confidence = res.get("confidence", 0)

    print("  [GENERAL CLASSIFICATION WIDGETS]")
    print(f"    1. Has Numerical Values : {'YES' if res.get('has_numerical_values') else 'NO'}")
    print(f"    2. Has Variables (x)    : {'YES' if res.get('has_variables') else 'NO'}")
    print(f"    3. Operation / Structure: {res.get('operation_type', 'none').upper()}")
    print(f"    4. Completeness Status  : {completeness}")
    if res.get("missing_elements"):
        print(f"       -> Missing Element   : {res.get('missing_elements')}")

    print("\n  [JEV STEP-NODE RESOLUTION]")
    print(f"    Target Node : [{node_id}] {node_name}")
    print(f"    Confidence  : {confidence * 100:.1f}%")
    print(f"    Rationale   : {res.get('explanation')}")

    print("\n  [SOCRATIC TUTOR ACTION]")
    if node_id == "off_step":
        print("    -> Socratic Response: \"Let's stay focused on the problem. What can we write for the mother's age?\"")
    elif completeness == "PARTIAL":
        print(f"    -> Socratic Guidance: \"Good progress! But you still need: {res.get('missing_elements')}\"")
    elif completeness == "CLUBBED_MULTI_STEP":
        print("    -> Socratic Action: Automatically advance BOTH steps in the notebook paper!")
    else:
        print(f"    -> Socratic Action: Verified! Mark [{node_id}] complete on notebook paper and advance.")
    print("-" * 76)


def run_batch_tests():
    print_banner()
    print("\nRunning Automated Test Suite (10 Diverse Inputs)...\n")
    passed = 0
    total = len(TEST_CASES)

    for i, tc in enumerate(TEST_CASES, start=1):
        print(f"Test #{i:02d}: \"{tc['input']}\" ({tc['description']})")
        res = classify_student_input(tc["input"])
        if not res.get("success"):
            print(f"  FAILED with API error: {res.get('error')}\n")
            continue

        target = res.get("target_step_node")
        comp = res.get("completeness")
        
        node_ok = target == tc["expected_node"]
        comp_ok = comp == tc["expected_completeness"]

        status = "PASSED" if (node_ok and comp_ok) else "MISMATCH"
        if status == "PASSED":
            passed += 1
            print(f"  -> [{status}] Matched: {target} | Completeness: {comp} | Conf: {res.get('confidence')}")
        else:
            print(f"  -> [{status}] Expected: node={tc['expected_node']}, comp={tc['expected_completeness']}")
            print(f"              Got:      node={target}, comp={comp}")
            print(f"              Reason:   {res.get('explanation')}")
        print()

    print("=" * 76)
    print(f"  FINAL SCORECARD: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("=" * 76)


def run_interactive():
    print_banner()
    print("\nInteractive Mode Active. Type any student response to classify.")
    print("Type 'test' to run the batch suite, or 'q' to quit.\n")

    while True:
        try:
            user_in = input("Student Input > ").strip()
            if not user_in:
                continue
            if user_in.lower() in ("q", "quit", "exit"):
                print("Exiting Jev Step Lab. Goodbye!")
                break
            if user_in.lower() == "test":
                run_batch_tests()
                continue

            print("Evaluating general widgets via Jev...")
            res = classify_student_input(user_in)
            format_result(res, user_in)
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--batch":
        run_batch_tests()
    else:
        run_interactive()
