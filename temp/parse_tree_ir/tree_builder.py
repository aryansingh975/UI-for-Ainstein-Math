"""
AST Tree Builder (Pure Python Recursive Parser)

Converts prefix AST string expressions into in-memory ASTNode trees.
Example AST strings:
- "ADD[balance](-20, 100)"
- "MUL(SUB(10, 2), 5)"
- "NEG(-20)"
- "100"

Key pure-Python parsing technique:
To split binary arguments like "ADD(SUB(1, 2), 3)" without breaking nested parentheses,
we use a manual character loop with a depth counter:
- depth increases when opening '('
- depth decreases when closing ')'
- comma ',' splits arguments only when depth == 0
"""

from ainstein_math.parse_tree_ir.nodes import (
    ASTNode,
    LiteralNode,
    VariableNode,
    UnaryOpNode,
    BinaryOpNode,
)

# Known operators supported by the paper's grammar
BINARY_OPERATORS = {"ADD", "SUB", "MUL", "DIV", "POW", "MOD", "MIN", "MAX"}
UNARY_OPERATORS = {"NEG", "ABS", "SQRT", "LOG"}


def split_top_level_arguments(arguments_str: str) -> list[str]:
    """
    Splits comma-separated arguments at top bracket level (depth == 0).
    
    Example:
        Input:  "SUB(10, 2), 5"
        Output: ["SUB(10, 2)", "5"]
    """
    args = []
    current_arg = []
    depth = 0

    for char in arguments_str:
        if char == "(" or char == "[" or char == "{":
            depth += 1
            current_arg.append(char)
        elif char == ")" or char == "]" or char == "}":
            depth -= 1
            current_arg.append(char)
        elif char == "," and depth == 0:
            # We hit a comma at the top level! End current argument.
            args.append("".join(current_arg).strip())
            current_arg = []
        else:
            current_arg.append(char)

    if current_arg:
        args.append("".join(current_arg).strip())

    return args


def parse_ast_expression(expr_str: str) -> ASTNode:
    """
    Recursively parse an AST string expression into ASTNode tree objects.
    
    Args:
        expr_str: The AST string, e.g. "ADD[balance](-20, 100)"
        
    Returns:
        ASTNode (BinaryOpNode, UnaryOpNode, LiteralNode, or VariableNode)
    """
    expr = expr_str.strip()

    if not expr:
        raise ValueError("Cannot parse empty AST expression.")

    # 1. Check if the expression contains parentheses indicating a function call
    open_paren = expr.find("(")
    if open_paren != -1 and expr.endswith(")"):
        # Everything before open_paren is operator + optional metadata: e.g. "ADD[balance]" or "ADD"
        op_part = expr[:open_paren].strip()
        args_part = expr[open_paren + 1:-1].strip()

        # Check for optional metadata inside [...] e.g., "ADD[balance]"
        metadata = None
        bracket_start = op_part.find("[")
        if bracket_start != -1 and op_part.endswith("]"):
            op_name = op_part[:bracket_start].strip()
            metadata = op_part[bracket_start + 1:-1].strip()
        else:
            op_name = op_part

        op_name = op_name.upper()

        # Split top-level arguments inside parentheses
        arg_strings = split_top_level_arguments(args_part)

        if op_name in BINARY_OPERATORS:
            if len(arg_strings) != 2:
                raise ValueError(
                    f"Binary operator {op_name} requires exactly 2 arguments, got {len(arg_strings)}: '{args_part}'"
                )
            left_node = parse_ast_expression(arg_strings[0])
            right_node = parse_ast_expression(arg_strings[1])
            return BinaryOpNode(op=op_name, left=left_node, right=right_node, metadata=metadata)

        elif op_name in UNARY_OPERATORS:
            if len(arg_strings) != 1:
                raise ValueError(
                    f"Unary operator {op_name} requires exactly 1 argument, got {len(arg_strings)}: '{args_part}'"
                )
            operand_node = parse_ast_expression(arg_strings[0])
            return UnaryOpNode(op=op_name, operand=operand_node, metadata=metadata)

        else:
            raise ValueError(f"Unknown operator in AST expression: '{op_name}'")

    # 2. If no function call, check if it's a numeric literal (e.g. -20, 100, 3.14)
    try:
        val = float(expr)
        return LiteralNode(value=val)
    except ValueError:
        pass

    # 3. Otherwise, it's a Variable node (e.g., balance, x)
    # Check if variable has annotation bracket e.g. "x[length]"
    bracket_start = expr.find("[")
    if bracket_start != -1 and expr.endswith("]"):
        var_name = expr[:bracket_start].strip()
        annotation = expr[bracket_start + 1:-1].strip()
        return VariableNode(name=var_name, annotation=annotation)

    return VariableNode(name=expr)
