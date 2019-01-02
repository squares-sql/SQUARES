from typing import ClassVar, Callable, List, Dict, Any
from .example_base import Example, ExampleSynthesizer
from .result import ok, bad
from interpreter import Interpreter
from enumerator import Enumerator
from dsl import Node
from spec.expr import *
from visitor import GenericVisitor
import logger

logger = logger.get('tyrell.synthesizer.constraint')


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


class ExampleConstraintSynthesizer(ExampleSynthesizer):

    def __init__(self,
                 enumerator: Enumerator,
                 interpreter: Interpreter,
                 examples: List[Example]):
        super().__init__(enumerator, interpreter, examples)

    @staticmethod
    def _eval_constraint(interp: Interpreter, constraint: Expr, in_values: List[Any], out_value: Any):
        pass

    def _do_compute_unsat_node(self, prog: Node, failed_example: Example):
        unsat_node = None
        for node, in_values, out_value in self.interpreter.eval_step(prog, failed_example.input):
            # We don't care about leaf nodes
            if node.is_leaf():
                continue
            for constraint in node.production.constraints:
                if not eval_expr(self.interpreter, in_values, out_value, constraint):
                    unsat_node = node
                    break
        return unsat_node

    def _compute_unsat_nodes(self, prog: Node, failed_examples: List[Example]):
        unsat_nodes = []
        for example in failed_examples:
            unsat_node = self._do_compute_unsat_node(prog, example)
            if unsat_node is not None:
                unsat_nodes.append(unsat_node)
        return unsat_nodes

    @staticmethod
    def _compute_depth_map(prog: Node):
        depth_map = dict()

        def traverse(node: Node, curr_depth: int):
            depth_map[node] = curr_depth
            for child in node.children:
                traverse(child, curr_depth + 1)
        traverse(prog, 0)
        return depth_map

    @staticmethod
    def _get_min_node(depth_map: Dict[Node, int], nodes: List[Node]):
        assert len(nodes) > 0
        min_depth = max(depth_map.values())
        min_node = None
        for node in nodes:
            depth = depth_map[node]
            if depth_map[node] < min_depth:
                min_depth = depth
                min_node = node
        return min_node

    def _get_unsat_node(self, prog: Node, failed_examples: List[Example]):
        unsat_nodes = self._compute_unsat_nodes(prog, failed_examples)
        if len(unsat_nodes) > 0:
            depth_map = self._compute_depth_map(prog)
            return self._get_min_node(depth_map, unsat_nodes)
        else:
            return None

    def analyze(self, prog):
        '''
        This version of analyze() tries to analyze the reason why a synthesized program fails, if it does not pass all the tests.
        '''
        failed_examples = self.get_failed_examples(prog)
        if len(failed_examples) == 0:
            return ok()
        else:
            unsat_node = self._get_unsat_node(prog, failed_examples)
            return bad(why=unsat_node)
