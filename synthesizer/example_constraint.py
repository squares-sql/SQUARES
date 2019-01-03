from typing import cast, NamedTuple, List, Set, FrozenSet, Dict, Any, ClassVar, Callable
from collections import deque
import z3
from interpreter import Interpreter
from enumerator import Enumerator
from dsl import Node, AtomNode, ParamNode, ApplyNode
from spec import Production, ValueType
from spec.expr import *
import logger
from visitor import GenericVisitor
from .example_base import Example, ExampleSynthesizer
from .eval_expr import eval_expr
from .result import ok, bad

logger = logger.get('tyrell.synthesizer.constraint')
Blame = NamedTuple('Blame', [('node', Node), ('production', Production)])


class NodeIndexer:
    _index_map: Dict[Node, int]

    def __init__(self, prog: Node):
        self._index_map = dict()
        # Assign ID to nodes in BFS order
        queue = deque([prog])
        counter = 0
        while len(queue) > 0:
            node = queue.popleft()
            self._index_map[node] = counter
            counter += 1
            for child in node.children:
                queue.append(child)

    def get(self, node: Node) -> int:
        return self._index_map[node]


class ConstraintVisitor(GenericVisitor):
    _encoder: 'Z3Encoder'
    _nodes: List[Node]

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

    def __init__(self, encoder: 'Z3Encoder', nodes: List[Node]):
        self._encoder = encoder
        self._nodes = nodes

    def visit_const_expr(self, const_expr: ConstExpr):
        return const_expr.value

    def visit_param_expr(self, param_expr: ParamExpr):
        return self._nodes[param_expr.index]

    def visit_property_expr(self, prop_expr: PropertyExpr):
        node = self.visit(prop_expr.operand)
        pname = prop_expr.name
        pty = prop_expr.type
        return self._encoder.get_z3_var(node, pname, pty)

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


class Z3Encoder(GenericVisitor):
    _interp: Interpreter
    _indexer: NodeIndexer
    _example: Example
    _unsat_map: Dict[str, Node]
    _solver: z3.Solver

    def __init__(self, interp: Interpreter, indexer: NodeIndexer, example: Example):
        self._interp = interp
        self._indexer = indexer
        self._example = example
        self._unsat_map = dict()
        self._solver = z3.Solver()

    def get_z3_var(self, node: Node, pname: str, ptype: ExprType):
        node_id = self._indexer.get(node)
        var_name = '{}_n{}'.format(pname, node_id)
        if ptype is ExprType.INT:
            return z3.Int(var_name)
        elif ptype is ExprType.BOOL:
            return z3.Bool(var_name)
        else:
            raise RuntimeError('Unrecognized ExprType: {}'.format(ptype))

    def _get_constraint_var(self, node: Node, index: int):
        node_id = self._indexer.get(node)
        var_name = '@n{}_c{}'.format(node_id, index)
        return var_name

    def encode_param_alignment(self, node: Node, ty: ValueType, index: int):
        if not isinstance(ty, ValueType):
            raise RuntimeError(
                'Unexpected program output type: {}'.format(ty))
        for pname, pty in ty.properties:
            actual = self.get_z3_var(node, pname, pty)
            expected_expr = PropertyExpr(pname, pty, ParamExpr(index))
            expected = eval_expr(
                self._interp, self._example.input, self._example.output, expected_expr)
            self._solver.add(actual == expected)

    def encode_output_alignment(self, prog: Node):
        self.encode_param_alignment(prog, prog.type, 0)

    def visit_param_node(self, param_node: ParamNode):
        self.encode_param_alignment(
            param_node, param_node.type, param_node.index + 1)

    def visit_atom_node(self, atom_node: AtomNode):
        pass

    def visit_apply_node(self, apply_node: ApplyNode):
        nodes = [apply_node] + apply_node.args
        constraint_visitor = ConstraintVisitor(self, nodes)
        for index, constraint in enumerate(apply_node.production.constraints):
            cname = self._get_constraint_var(apply_node, index)
            z3_clause = constraint_visitor.visit(constraint)
            self._unsat_map[cname] = apply_node
            self._solver.assert_and_track(z3_clause, cname)
        for arg in apply_node.args:
            self.visit(arg)

    def get_blame_nodes(self):
        if self._solver.check() != z3.unsat:
            # Abstract semantics is satisfiable or unknown. Cannot learn anything.
            return None
        unsat_core = self._solver.unsat_core()
        if len(unsat_core) == 0:
            return None
        unsat_nodes = set(self._unsat_map[str(x)] for x in unsat_core)
        return list(unsat_nodes)


class BlameFinder:
    _interp: Interpreter
    _prog: Node
    _indexer: NodeIndexer
    _blames_collection: Set[FrozenSet[Blame]]

    def __init__(self, interp: Interpreter, prog: Node):
        self._interp = interp
        self._prog = prog
        self._indexer = NodeIndexer(prog)
        self._blames_collection = set()

    def get_blames(self) -> Set[Blame]:
        num_blames = len(self._blames_collection)
        if num_blames == 0:
            return None
        # TODO: Add more blames by analyzing equivalence class
        return [list(x) for x in self._blames_collection]

    def process_examples(self, examples: List[Example]):
        for example in examples:
            self.process_example(example)

    def process_example(self, example: Example):
        z3_encoder = Z3Encoder(self._interp, self._indexer, example)
        z3_encoder.encode_output_alignment(self._prog)
        z3_encoder.visit(self._prog)
        blame_nodes = z3_encoder.get_blame_nodes()
        if blame_nodes is not None:
            blames = tuple(Blame(node=n, production=n.production)
                           for n in blame_nodes)
            self._blames_collection.add(blames)


class ExampleConstraintSynthesizer(ExampleSynthesizer):

    def __init__(self,
                 enumerator: Enumerator,
                 interpreter: Interpreter,
                 examples: List[Example]):
        super().__init__(enumerator, interpreter, examples)

    def analyze(self, prog):
        '''
        This version of analyze() tries to analyze the reason why a synthesized program fails, if it does not pass all the tests.
        '''
        failed_examples = self.get_failed_examples(prog)
        if len(failed_examples) == 0:
            return ok()
        else:
            blame_finder = BlameFinder(self.interpreter, prog)
            blame_finder.process_examples(failed_examples)
            return bad(why=blame_finder.get_blames())
