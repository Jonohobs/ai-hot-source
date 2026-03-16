"""Safe formula evaluation using AST parsing (no eval/exec)."""

from __future__ import annotations

import ast
import math
import operator
from typing import Any

from .models import FormulaDefinition

# Allowed operations — no attribute access, no imports
_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}

_FUNCTIONS = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sqrt": math.sqrt,
    "log": math.log,
    "log10": math.log10,
    "pow": pow,
}


class _SafeEval(ast.NodeVisitor):
    """AST-walking evaluator. No builtins, no imports, no attribute access."""

    def __init__(self, names: dict[str, float]):
        self.names = names

    def visit_Expression(self, node: ast.Expression) -> float:
        return self.visit(node.body)

    def visit_Constant(self, node: ast.Constant) -> float:
        if isinstance(node.value, (int, float)):
            return float(node.value)
        raise ValueError(f"Unsupported constant: {node.value!r}")

    def visit_Name(self, node: ast.Name) -> float:
        if node.id in self.names:
            return self.names[node.id]
        raise ValueError(f"Unknown variable: {node.id}")

    def visit_BinOp(self, node: ast.BinOp) -> float:
        op = _OPERATORS.get(type(node.op))
        if op is None:
            raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
        left = self.visit(node.left)
        right = self.visit(node.right)
        return float(op(left, right))

    def visit_UnaryOp(self, node: ast.UnaryOp) -> float:
        op = _OPERATORS.get(type(node.op))
        if op is None:
            raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
        return float(op(self.visit(node.operand)))

    def visit_Call(self, node: ast.Call) -> float:
        if not isinstance(node.func, ast.Name):
            raise ValueError("Only named function calls allowed")
        func = _FUNCTIONS.get(node.func.id)
        if func is None:
            raise ValueError(f"Unknown function: {node.func.id}")
        args = [self.visit(a) for a in node.args]
        return float(func(*args))

    def generic_visit(self, node: ast.AST) -> Any:
        raise ValueError(f"Unsupported expression: {type(node).__name__}")


def evaluate_formula(formula: FormulaDefinition, values: dict[str, float]) -> float:
    """Safely evaluate a formula expression with provided variable values."""
    missing = set(formula.variables) - set(values)
    if missing:
        raise ValueError(f"Missing variable values: {missing}")

    try:
        tree = ast.parse(formula.expression, mode="eval")
    except SyntaxError as e:
        raise ValueError(f"Invalid formula syntax: {e}") from e

    evaluator = _SafeEval(values)
    try:
        return evaluator.visit(tree)
    except ZeroDivisionError:
        raise ValueError("Formula resulted in division by zero")
