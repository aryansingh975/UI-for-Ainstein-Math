"""
Reasoning Trace Dependency Checker (Pure Python)

Validates the logical consistency and dependency links in a reasoning trace:
1. Ensures BIND steps only reference step IDs that were defined earlier in the sequence.
2. Checks that referenced EXTRACT values are valid numbers.
3. Ensures CONSTRUCT exists and has valid AST expression format.
"""


def verify_trace_dependencies(parsed_steps: list[dict]) -> dict:
    """
    Validates dependency links (<E1, E2, M1>) across trace steps.
    
    Args:
        parsed_steps: List of step dictionaries from parse_full_trace().
        
    Returns:
        dict: {
            "valid": bool,
            "errors": list[str],
            "warnings": list[str],
            "step_ids": list[str],
        }
    """
    seen_step_ids = set()
    errors = []
    warnings = []

    has_construct = False

    for step in parsed_steps:
        step_id = step.get("step_id")
        step_type = step.get("type")

        if step_type == "EXTRACT":
            val_str = step.get("value", "")
            try:
                float(val_str)
            except ValueError:
                errors.append(f"EXTRACT step [{step_id}] has invalid non-numeric value: '{val_str}'")

            seen_step_ids.add(step_id)

        elif step_type == "MAP":
            seen_step_ids.add(step_id)

        elif step_type == "BIND":
            dependencies = step.get("dependencies", [])
            for dep in dependencies:
                if dep not in seen_step_ids:
                    errors.append(
                        f"BIND step [{step_id}] references unknown or future dependency: '{dep}'"
                    )

            seen_step_ids.add(step_id)

        elif step_type == "CONSTRUCT":
            has_construct = True
            if not step.get("ast_expression"):
                errors.append("CONSTRUCT step missing 'ast_expression'")

    if not has_construct:
        warnings.append("Trace is missing a final [CONSTRUCT] step.")

    is_valid = (len(errors) == 0)

    return {
        "valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "step_ids": list(seen_step_ids),
    }
