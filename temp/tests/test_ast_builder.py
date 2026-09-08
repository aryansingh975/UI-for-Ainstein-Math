from ainstein_math.parse_tree_ir.nodes import (
    LiteralNode,
    VariableNode,
    BinaryOpNode,
    UnaryOpNode,
)
from ainstein_math.parse_tree_ir.tree_builder import (
    split_top_level_arguments,
    parse_ast_expression,
)


def test_split_top_level_arguments():
    # Test simple comma split
    args = split_top_level_arguments("-20, 100")
    assert args == ["-20", "100"]

    # Test nested paren split
    args = split_top_level_arguments("ADD(-20, 10), SUB(50, 5)")
    assert args == ["ADD(-20, 10)", "SUB(50, 5)"]


def test_parse_literal():
    node = parse_ast_expression("100")
    assert isinstance(node, LiteralNode)
    assert node.evaluate() == 100.0

    node_neg = parse_ast_expression("-20")
    assert isinstance(node_neg, LiteralNode)
    assert node_neg.evaluate() == -20.0


def test_parse_variable():
    node = parse_ast_expression("balance")
    assert isinstance(node, VariableNode)
    assert node.name == "balance"

    node_annotated = parse_ast_expression("x[length]")
    assert isinstance(node_annotated, VariableNode)
    assert node_annotated.name == "x"
    assert node_annotated.annotation == "length"


def test_parse_binary_op():
    expr = "ADD[balance](-20, 100)"
    node = parse_ast_expression(expr)

    assert isinstance(node, BinaryOpNode)
    assert node.op == "ADD"
    assert node.metadata == "balance"
    assert isinstance(node.left, LiteralNode)
    assert node.left.evaluate() == -20.0
    assert isinstance(node.right, LiteralNode)
    assert node.right.evaluate() == 100.0
    assert node.evaluate() == 80.0


def test_parse_nested_ast():
    expr = "MUL(ADD(10, 5), SUB(20, 4))"
    node = parse_ast_expression(expr)

    assert isinstance(node, BinaryOpNode)
    assert node.op == "MUL"
    assert node.evaluate() == (10 + 5) * (20 - 4)  # 15 * 16 = 240.0


def test_parse_unary_op():
    expr = "NEG(-20)"
    node = parse_ast_expression(expr)

    assert isinstance(node, UnaryOpNode)
    assert node.op == "NEG"
    assert node.evaluate() == 20.0
