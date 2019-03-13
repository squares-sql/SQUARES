from typing import Any, Callable, ClassVar, Dict
import z3

from ..spec.expr import *
from ..visitor import GenericVisitor


class ConstraintEncoder(GenericVisitor):
    _encode_property: Callable[[PropertyExpr], z3.ExprRef]

    _unary_dispatch_table: ClassVar[Dict[UnaryOperator, Callable[[Any], Any]]] = {
        UnaryOperator.NOT: lambda x: z3.Not(x),
        UnaryOperator.NEG: lambda x: -x
    }
    _binary_dispatch_table: ClassVar[Dict[BinaryOperator, Callable[[Any, Any], Any]]] = {
        BinaryOperator.ADD: lambda x, y: x + y,
        BinaryOperator.SUB: lambda x, y: x - y,
        BinaryOperator.MUL: lambda x, y: x * y,
        BinaryOperator.DIV: lambda x, y: x / y,
        BinaryOperator.MOD: lambda x, y: x % y,
        BinaryOperator.EQ: lambda x, y: x == y,
        BinaryOperator.NE: lambda x, y: x != y,
        BinaryOperator.LT: lambda x, y: x < y,
        BinaryOperator.LE: lambda x, y: x <= y,
        BinaryOperator.GT: lambda x, y: x > y,
        BinaryOperator.GE: lambda x, y: x >= y,
        BinaryOperator.AND: lambda x, y: z3.And(x, y),
        BinaryOperator.OR: lambda x, y: z3.Or(x, y),
        BinaryOperator.IMPLY: lambda x, y: z3.Implies(x, y)
    }

    def __init__(self, encode_property: Callable[[PropertyExpr], z3.ExprRef]):
        self._encode_property = encode_property

    def visit_const_expr(self, const_expr: ConstExpr):
        return const_expr.value

    def visit_property_expr(self, prop_expr: PropertyExpr):
        return self._encode_property(prop_expr)

    def visit_unary_expr(self, unary_expr: UnaryExpr):
        arg = self.visit(unary_expr.operand)
        return self._unary_dispatch_table[unary_expr.operator](arg)

    def visit_binary_expr(self, binary_expr: BinaryExpr):
        larg = self.visit(binary_expr.lhs)
        rarg = self.visit(binary_expr.rhs)
        return self._binary_dispatch_table[binary_expr.operator](larg, rarg)

    def visit_cond_expr(self, cond_expr: CondExpr):
        cond_arg = self.visit(cond_expr.condition)
        true_arg = self.visit(cond_expr.true_value)
        false_arg = self.visit(cond_expr.false_value)
        return z3.If(cond_arg, true_arg, false_arg)
