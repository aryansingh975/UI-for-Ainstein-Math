#!/usr/bin/env python3
"""Minimal interactive tutor for the atomic validation dataset.

The tutor is intentionally simple. It does not try to model the whole problem in
one large algorithm; instead, it asks the user for one atomic step at a time and
then passes that small step into the verification engine.

This makes the interaction easier to explain and easier to debug.
"""

import sys
from pathlib import Path

# -----------------------------------------------------------------------------
# Project setup
# -----------------------------------------------------------------------------
# When this file is launched directly, Python may not include the repository root
# on its import path. We add it manually so the project modules can be imported.
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Import the validator that interprets the current dataset in atomic node-based steps.
from ainstein_math.verification_engine import verification_engine


# -----------------------------------------------------------------------------
# Main interactive loop
# -----------------------------------------------------------------------------
def main() -> None:
    """Run a simple terminal session with the validator.

    The loop is deliberately small:
      1. show the initial question
      2. read one student input
      3. send the input to the verification engine
      4. show the tutor's reply
      5. stop when the problem is marked complete
    """
    engine = verification_engine()

    print("=" * 70)
    print("AINSTEIN MATH: ATOMIC TUTOR")
    print("=" * 70)
    print(engine.get_initial_prompt())
    print()

    while True:
        try:
            # Read a single atomic step from the student.
            student_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            # Gracefully handle terminal close or Ctrl+C.
            print("\nSession ended.")
            break

        if not student_input:
            # Ignore blank entries so the tutor does not get confused by empty input.
            continue

        if student_input.lower() in {"quit", "exit", "q"}:
            print("Goodbye!")
            break

        # Pass the single step to the verification engine for validation.
        result = engine.evaluate_turn(student_input)
        print(f"Tutor: {result['response']}")

        # Stop when the engine says the problem is complete.
        if result.get("completed"):
            print("\nProblem completed.")
            break


if __name__ == "__main__":
    main()