"""
Abstract Syntax Tree (AST) Node Representations (Pure Python)

This module defines the tree node classes representing prefix operations in mathematical formulas:
- LiteralNode: Represents raw numeric constants (e.g. 100, -20)
- VariableNode: Represents named identifiers (e.g. x, balance)
- UnaryOpNode: Represents single-argument functions (e.g. NEG(X), SQRT(Y))
- BinaryOpNode: Represents two-argument functions (e.g. ADD(A, B), SUB(A, B))
"""


class ASTNode:
    """Base class for all Abstract Syntax Tree nodes."""

    def evaluate(self) -> float:
        """Evaluate the numerical value of the AST node recursively."""
        raise NotImplementedError("Subclasses must implement evaluate()")

    def to_dict(self) -> dict:
        """Convert the AST node into a dictionary representation."""
        raise NotImplementedError("Subclasses must implement to_dict()")


class LiteralNode(ASTNode):
    """Represents a numeric literal value (e.g., 5, -20, 3.14)."""

    def __init__(self, value: float | int):
        self.value = float(value)

    def evaluate(self) -> float:
        return self.value

    def to_dict(self) -> dict:
        return {
            "type": "LiteralNode",
            "value": self.value,
        }

    def __repr__(self) -> str:
        # If float is an integer value like -20.0, format nicely as integer
        if self.value.is_integer():
            return str(int(self.value))
        return str(self.value)


class VariableNode(ASTNode):
    """Represents a variable identifier (e.g., balance, x[length])."""

    def __init__(self, name: str, annotation: str | None = None, value: float | None = None):
        self.name = name
        self.annotation = annotation
        self.value = value

    def evaluate(self) -> float:
        if self.value is None:
            raise ValueError(f"Variable '{self.name}' has no assigned numeric value.")
        return self.value

    def to_dict(self) -> dict:
        return {
            "type": "VariableNode",
            "name": self.name,
            "annotation": self.annotation,
            "value": self.value,
        }

    def __repr__(self) -> str:
        if self.annotation:
            return f"{self.name}[{self.annotation}]"
        return self.name


class UnaryOpNode(ASTNode):
    """
    Represents a unary operation (1 operand).
    Operators: NEG, ABS, SQRT, LOG
    """

    def __init__(self, op: str, operand: ASTNode, metadata: str | None = None):
        self.op = op.upper()
        self.operand = operand
        self.metadata = metadata

    def evaluate(self) -> float:
        child_val = self.operand.evaluate()

        if self.op == "NEG":
            return -child_val
        elif self.op == "ABS":
            return abs(child_val)
        elif self.op == "SQRT":
            if child_val < 0:
                raise ValueError(f"Cannot compute SQRT of negative number: {child_val}")
            return child_val ** 0.5
        elif self.op == "LOG":
            import math
            if child_val <= 0:
                raise ValueError(f"Cannot compute LOG of non-positive number: {child_val}")
            return math.log(child_val)
        else:
            raise ValueError(f"Unsupported unary operator: {self.op}")

    def to_dict(self) -> dict:
        return {
            "type": "UnaryOpNode",
            "operator": self.op,
            "metadata": self.metadata,
            "operand": self.operand.to_dict(),
        }

    def __repr__(self) -> str:
        meta_str = f"[{self.metadata}]" if self.metadata else ""
        return f"{self.op}{meta_str}({self.operand})"


class BinaryOpNode(ASTNode):
    """
    Represents a binary operation (2 operands: left and right).
    Operators: ADD, SUB, MUL, DIV, POW, MOD, MIN, MAX
    """

    def __init__(self, op: str, left: ASTNode, right: ASTNode, metadata: str | None = None):
        self.op = op.upper()
        self.left = left
        self.right = right
        self.metadata = metadata

    def evaluate(self) -> float:
        left_val = self.left.evaluate()
        right_val = self.right.evaluate()

        if self.op == "ADD":
            return left_val + right_val
        elif self.op == "SUB":
            return left_val - right_val
        elif self.op == "MUL":
            return left_val * right_val
        elif self.op == "DIV":
            if right_val == 0:
                raise ZeroDivisionError("Division by zero in binary AST evaluation.")
            return left_val / right_val
        elif self.op == "POW":
            return left_val ** right_val
        elif self.op == "MOD":
            return left_val % right_val
        elif self.op == "MIN":
            return min(left_val, right_val)
        elif self.op == "MAX":
            return max(left_val, right_val)
        else:
            raise ValueError(f"Unsupported binary operator: {self.op}")

    def to_dict(self) -> dict:
        return {
            "type": "BinaryOpNode",
            "operator": self.op,
            "metadata": self.metadata,
            "left": self.left.to_dict(),
            "right": self.right.to_dict(),
        }

    def __repr__(self) -> str:
        meta_str = f"[{self.metadata}]" if self.metadata else ""
        return f"{self.op}{meta_str}({self.left}, {self.right})"
