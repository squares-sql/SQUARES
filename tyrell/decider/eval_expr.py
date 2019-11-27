from typing import ClassVar, Callable, List, Dict, Any
from ..spec.expr import *
from ..interpreter import Interpreter
from ..visitor import GenericVisitor


class ExprVisitor(GenericVisitor):
    _interp: Interpreter
    _in_values: List[Any]
    _out_value: Any

    _unary_dispatch_table: ClassVar[Dict[UnaryOperator, Callable[[Any], Any]]] = {
        UnaryOperator.NOT: lambda x: not x,
        UnaryOperator.NEG: lambda x: -x
    }
    _binary_dispatch_table: ClassVar[Dict[BinaryOperator, Callable[[Any, Any], Any]]] = {
        BinaryOperator.ADD: lambda x, y: x + y,
        BinaryOperator.SUB: lambda x, y: x - y,
        BinaryOperator.MUL: lambda x, y: x * y,
        # FIXME: Semantics of the following two operators may diverge in Python and Z3
        BinaryOperator.DIV: lambda x, y: x / y,
        BinaryOperator.MOD: lambda x, y: x % y,
        BinaryOperator.EQ: lambda x, y: x == y,
        BinaryOperator.NE: lambda x, y: x != y,
        BinaryOperator.LT: lambda x, y: x < y,
        BinaryOperator.LE: lambda x, y: x <= y,
        BinaryOperator.GT: lambda x, y: x > y,
        BinaryOperator.GE: lambda x, y: x >= y,
        BinaryOperator.AND: lambda x, y: x and y,
        BinaryOperator.OR: lambda x, y: x or y,
        BinaryOperator.IMPLY: lambda x, y: (not x) or y
    }

    def __init__(self, interp: Interpreter, in_values: List[Any], out_value: Any):
        self._interp = interp
        self._in_values = in_values
        self._out_value = out_value

    def visit_const_expr(self, const_expr: ConstExpr):
        return const_expr.value

    def visit_param_expr(self, param_expr: ParamExpr):
        if param_expr.index == 0:
            return self._out_value
        else:
            return self._in_values[param_expr.index - 1]

    def visit_unary_expr(self, unary_expr: UnaryExpr):
        arg = self.visit(unary_expr.operand)
        return self._unary_dispatch_table[unary_expr.operator](arg)

    def visit_binary_expr(self, binary_expr: BinaryExpr):
        larg = self.visit(binary_expr.lhs)
        rarg = self.visit(binary_expr.rhs)
        return self._binary_dispatch_table[binary_expr.operator](larg, rarg)

    def visit_cond_expr(self, cond_expr: CondExpr):
        cond_arg = self.visit(cond_expr.condition)
        if cond_arg:
            return self.visit(cond_expr.true_value)
        else:
            return self.visit(cond_expr.false_value)

    def visit_property_expr(self, prop_expr: PropertyExpr):
        arg = self.visit(prop_expr.operand)
        method_name = self._apply_method_name(prop_expr.name)
        method = getattr(self._interp, method_name, None)
        if method is None:
            raise ValueError(
                'Cannot find the required apply method: {}'.format(method_name))
        return method(arg)

    @staticmethod
    def _apply_method_name(name):
        return 'apply_' + name


def eval_expr(interpreter: Interpreter, in_values: List[Any], out_value: Any, expr: Expr):
    return ExprVisitor(interpreter, in_values, out_value).visit(expr)
