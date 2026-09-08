"""
Reasoning Trace Line Parser (Pure Python)

This module parses natural language reasoning trace lines into structured Python dictionaries.
It avoids external parsing libraries, using fundamental Python string manipulation methods:
- str.find() to locate sub-strings or delimiters
- str.split() to break strings into lists
- str.strip() to clean up leading/trailing whitespace
- String slicing (e.g., line[start:end]) to isolate tokens
"""

from enum import Enum


class TraceStepType(str, Enum):
    """Enumeration of reasoning trace step types."""
    EXTRACT = "EXTRACT"
    MAP = "MAP"
    BIND = "BIND"
    CONSTRUCT = "CONSTRUCT"


def classify_trace_line(line: str) -> TraceStepType:
    """
    Classify a trace line into its step type by inspecting the command keyword prefix.
    
    Args:
        line: A single line from the reasoning trace.
        
    Returns:
        TraceStepType: The classified step type (EXTRACT, MAP, BIND, CONSTRUCT).
        
    Raises:
        ValueError: If the line doesn't contain a recognized keyword.
    """
    clean_line = line.strip()

    # 1. Skip step ID bracket [ID] if present
    close_bracket = clean_line.find("]")
    if close_bracket != -1:
        after_id = clean_line[close_bracket + 1:].strip()
    else:
        after_id = clean_line

    # 2. Skip dependency angle brackets <dep1, dep2> if present
    if after_id.startswith("<"):
        close_angle = after_id.find(">")
        if close_angle != -1:
            after_id = after_id[close_angle + 1:].strip()

    # 3. Check exact command keyword prefix (case-sensitive)
    if after_id.startswith("EXTRACT"):
        return TraceStepType.EXTRACT
    elif after_id.startswith("MAP"):
        return TraceStepType.MAP
    elif after_id.startswith("BIND"):
        return TraceStepType.BIND
    elif after_id.startswith("CONSTRUCT") or clean_line.startswith("[CONSTRUCT]"):
        return TraceStepType.CONSTRUCT
    else:
        raise ValueError(f"Unrecognized trace line: '{clean_line}'")


def parse_extract_line(line: str) -> dict:
    """
    Parse an EXTRACT trace line.
    
    Format:
        [<id>] EXTRACT entity: "<entity_text>" -> val: <numeric_value>
        
    Example:
        '[E1] EXTRACT entity: "debt of 20 dollars" -> val: -20'
        
    Returns:
        dict: {"step_id": "E1", "type": "EXTRACT", "entity": "debt of 20 dollars", "value": "-20"}
    """
    if classify_trace_line(line) != TraceStepType.EXTRACT:
        raise ValueError("Line is not an EXTRACT line.")

    # 1. Step ID: Isolate text inside brackets [ ]
    open_bracket = line.find("[")
    close_bracket = line.find("]")
    step_id = line[open_bracket + 1:close_bracket].strip()

    # 2. Entity: Extract text inside quotes after 'entity: "'
    entity_marker = 'entity: "'
    entity_start = line.find(entity_marker) + len(entity_marker)
    entity_end = line.find('"', entity_start)
    entity = line[entity_start:entity_end]

    # 3. Value: Extract text after 'val: '
    val_marker = "val: "
    val_start = line.find(val_marker) + len(val_marker)
    val = line[val_start:].strip()

    return {
        "step_id": step_id,
        "type": TraceStepType.EXTRACT.value,
        "entity": entity,
        "value": val,
    }


def parse_map_line(line: str) -> dict:
    """
    Parse a MAP trace line.
    
    Format:
        [<id>] MAP trigger: "<trig>" -> gen_trigger: "<gen>" -> concept: "<concept>" -> op: <OP>
        
    Example:
        '[M1] MAP trigger: "deposit is made" -> gen_trigger: "deposit" -> concept: "incremental addition" -> op: ADD'
        
    Returns:
        dict with step_id, type, trigger, gen_trigger, concept, operator.
    """
    if "MAP" not in line:
        raise ValueError("Line does not contain MAP.")

    # 1. Step ID
    open_bracket = line.find("[")
    close_bracket = line.find("]")
    step_id = line[open_bracket + 1:close_bracket].strip()

    # 2. Split the rest of the line by the arrow delimiter " -> "
    parts = line.split(" -> ")
    
    # parts[0] contains step_id and trigger, e.g., '[M1] MAP trigger: "deposit is made"'
    trigger_marker = 'trigger: "'
    trig_start = parts[0].find(trigger_marker) + len(trigger_marker)
    trig_end = parts[0].rfind('"')
    trigger = parts[0][trig_start:trig_end]

    # parts[1] contains gen_trigger, e.g., 'gen_trigger: "deposit"'
    gen_marker = 'gen_trigger: "'
    gen_start = parts[1].find(gen_marker) + len(gen_marker)
    gen_end = parts[1].rfind('"')
    gen_trigger = parts[1][gen_start:gen_end]

    # parts[2] contains concept, e.g., 'concept: "incremental addition"'
    concept_marker = 'concept: "'
    concept_start = parts[2].find(concept_marker) + len(concept_marker)
    concept_end = parts[2].rfind('"')
    concept = parts[2][concept_start:concept_end]

    # parts[3] contains op, e.g., 'op: ADD'
    op_marker = "op: "
    op_start = parts[3].find(op_marker) + len(op_marker)
    operator = parts[3][op_start:].strip()

    return {
        "step_id": step_id,
        "type": TraceStepType.MAP.value,
        "trigger": trigger,
        "gen_trigger": gen_trigger,
        "concept": concept,
        "operator": operator,
    }


def parse_bind_line(line: str) -> dict:
    """
    Parse a BIND trace line.
    
    Format:
        [<id>] <dep1, dep2> BIND logic: "<logic>" -> role: LEFT = <val1>, RIGHT = <val2>
        
    Example:
        '[B1] <E1, E2, M1> BIND logic: "Deposit added to balance" -> role: LEFT = -20, RIGHT = 100'
        
    Returns:
        dict with step_id, type, dependencies, logic, roles (dict of role bindings).
    """
    if "BIND" not in line:
        raise ValueError("Line does not contain BIND.")

    # 1. Step ID
    open_bracket = line.find("[")
    close_bracket = line.find("]")
    step_id = line[open_bracket + 1:close_bracket].strip()

    # 2. Dependencies: text inside < >
    angle_open = line.find("<")
    angle_close = line.find(">")
    deps_raw = line[angle_open + 1:angle_close]
    # Split by comma and strip each dependency identifier
    dependencies = [dep.strip() for dep in deps_raw.split(",") if dep.strip()]

    # 3. Logic description: quoted string after logic: "
    logic_marker = 'logic: "'
    logic_start = line.find(logic_marker) + len(logic_marker)
    logic_end = line.find('"', logic_start)
    logic = line[logic_start:logic_end]

    # 4. Roles: after 'role: '
    role_marker = "role: "
    role_start = line.find(role_marker) + len(role_marker)
    roles_str = line[role_start:].strip()

    # Parse role pairs, e.g., "LEFT = -20, RIGHT = 100" or "ARG = X"
    roles = {}
    role_pairs = roles_str.split(",")
    for pair in role_pairs:
        if "=" in pair:
            key, value = pair.split("=", 1)
            roles[key.strip()] = value.strip()

    return {
        "step_id": step_id,
        "type": TraceStepType.BIND.value,
        "dependencies": dependencies,
        "logic": logic,
        "roles": roles,
    }


def parse_construct_line(line: str) -> dict:
    """
    Parse a CONSTRUCT trace line.
    
    Format:
        [CONSTRUCT] Tree: <ast_expression> -> target: "<target_unit>"
        
    Example:
        '[CONSTRUCT] Tree: ADD[balance](-20, 100) -> target: "dollars"'
        
    Returns:
        dict with step_id="CONSTRUCT", type="CONSTRUCT", ast_expression, target.
    """
    if "CONSTRUCT" not in line:
        raise ValueError("Line does not contain CONSTRUCT.")

    # 1. AST Expression: between 'Tree: ' and ' -> target:'
    tree_marker = "Tree: "
    tree_start = line.find(tree_marker) + len(tree_marker)
    target_split = line.find(" -> target:")
    ast_expression = line[tree_start:target_split].strip()

    # 2. Target unit: inside quotes after 'target: "'
    target_marker = 'target: "'
    target_start = line.find(target_marker, target_split) + len(target_marker)
    target_end = line.rfind('"')
    target = line[target_start:target_end]

    return {
        "step_id": "CONSTRUCT",
        "type": TraceStepType.CONSTRUCT.value,
        "ast_expression": ast_expression,
        "target": target,
    }


def parse_full_trace(trace_text: str) -> list[dict]:
    """
    Parse a multi-line reasoning trace into a list of step dictionaries.
    
    Args:
        trace_text: Raw multi-line trace output from model.
        
    Returns:
        list of parsed step dictionaries.
    
    Example:
        >>> trace = '''
        ... [E1] EXTRACT entity: "debt of 20 dollars" -> val: -20
        ... [CONSTRUCT] Tree: -20 -> target: "dollars"
        ... '''
        >>> parse_full_trace(trace)
        [
            {"step_id": "E1", "type": "EXTRACT", "entity": "debt of 20 dollars", "value": "-20"},
            {"step_id": "CONSTRUCT", "type": "CONSTRUCT", "ast_expression": "-20", "target": "dollars"}
        ]    
    """
    parsed_steps = []
    lines = trace_text.strip().split("\n")

    for line in lines:
        clean_line = line.strip()
        if not clean_line:
            continue  # Skip empty lines

        step_type = classify_trace_line(clean_line)

        if step_type == TraceStepType.EXTRACT:
            parsed_steps.append(parse_extract_line(clean_line))
        elif step_type == TraceStepType.MAP:
            parsed_steps.append(parse_map_line(clean_line))
        elif step_type == TraceStepType.BIND:
            parsed_steps.append(parse_bind_line(clean_line))
        elif step_type == TraceStepType.CONSTRUCT:
            parsed_steps.append(parse_construct_line(clean_line))

    return parsed_steps