"""
Reasoning Trace Evaluator & Visualizer (Pure Python)

Provides end-to-end evaluation of reasoning traces:
1. Parses trace text into structured steps
2. Checks dependency integrity
3. Constructs AST from prefix notation
4. Recursively computes final mathematical result
5. Generates clean ASCII visual representation of the reasoning tree
"""

from ainstein_math.reasoning_grammar.parser import parse_full_trace
from ainstein_math.verification.trace_checker import verify_trace_dependencies
from ainstein_math.parse_tree_ir.tree_builder import parse_ast_expression
from ainstein_math.parse_tree_ir.nodes import (
    ASTNode,
    BinaryOpNode,
    UnaryOpNode,
    LiteralNode,
    VariableNode,
)


def format_ascii_tree(node: ASTNode, prefix: str = "", is_last: bool = True) -> str:
    """
    Generate an ASCII tree string for visual representation of AST.
    
    Example:
    └── ADD[balance]
        ├── -20
        └── 100
    """
    lines = []

    connector = "└── " if is_last else "├── "
    node_repr = repr(node)

    if isinstance(node, BinaryOpNode):
        label = f"{node.op}"
        if node.metadata:
            label += f"[{node.metadata}]"
        lines.append(f"{prefix}{connector}{label}")
        new_prefix = prefix + ("    " if is_last else "│   ")
        lines.append(format_ascii_tree(node.left, new_prefix, is_last=False))
        lines.append(format_ascii_tree(node.right, new_prefix, is_last=True))

    elif isinstance(node, UnaryOpNode):
        label = f"{node.op}"
        if node.metadata:
            label += f"[{node.metadata}]"
        lines.append(f"{prefix}{connector}{label}")
        new_prefix = prefix + ("    " if is_last else "│   ")
        lines.append(format_ascii_tree(node.operand, new_prefix, is_last=True))

    else:
        lines.append(f"{prefix}{connector}{node_repr}")

    return "\n".join(lines)


def evaluate_reasoning_trace(trace_text: str) -> dict:
    """
    Full end-to-end evaluation pipeline for a reasoning trace.
    
    Args:
        trace_text: Raw reasoning trace string.
        
    Returns:
        dict containing:
        - steps: list of parsed steps
        - verification: trace verification results
        - ast_expression: the prefix AST string
        - ast_root: the ASTNode root object
        - result: final numerical answer (float/int)
        - ascii_tree: ASCII visualization of the tree
        - target_unit: target measurement unit (e.g., dollars)
    """
    # 1. Parse steps
    steps = parse_full_trace(trace_text)

    # 2. Check dependencies
    verification = verify_trace_dependencies(steps)
    if not verification["valid"]:
        raise ValueError(f"Trace verification failed with errors: {verification['errors']}")

    # 3. Find CONSTRUCT step
    construct_step = None
    for step in steps:
        if step["type"] == "CONSTRUCT":
            construct_step = step
            break

    if not construct_step:
        raise ValueError("Trace contains no CONSTRUCT step to evaluate.")

    ast_expr = construct_step["ast_expression"]
    target_unit = construct_step.get("target", "")

    # 4. Build AST
    ast_root = parse_ast_expression(ast_expr)

    # 5. Evaluate result recursively
    result_val = ast_root.evaluate()

    # If result is an integer float like 80.0, format as 80
    if result_val.is_integer():
        result_val = int(result_val)

    # 6. Format ASCII tree
    ascii_tree = format_ascii_tree(ast_root)

    return {
        "steps": steps,
        "verification": verification,
        "ast_expression": ast_expr,
        "ast_root": ast_root,
        "result": result_val,
        "target_unit": target_unit,
        "ascii_tree": ascii_tree,
    }
