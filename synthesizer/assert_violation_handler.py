from typing import cast, List, Callable, Any
from spec import Production
from dsl import Node, AtomNode
from interpreter import InterpreterError, AssertionViolation, Context
from .synthesizer import Synthesizer
from .example_constraint import Blame


class AssertionViolationHandler(Synthesizer):
    '''
    A mixin class for Synthesizer that provide pruning capabilities for dynamic type errors.
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _analyze_enum(self, ctx: Context, node: Node, prod: Production, is_ok: Callable[[Any], bool]) -> List[List[Blame]]:
        blames = list()
        blame_nodes = filter(lambda x: x is not node, ctx.observed)
        blame_base = [Blame(n, n.production) for n in blame_nodes]
        for alt_prod in self.spec.get_productions_with_lhs(prod.lhs):
            alt_node = AtomNode(alt_prod)
            # Inputs doesn't matter here as we don't have any ParamNode
            value = self.interpreter.eval(alt_node, [])
            if not is_ok(value):
                blames.append(blame_base + [Blame(node, alt_prod)])
        return blames

    def analyze_assertion_violation(self, error: AssertionViolation):
        node = error.node
        prod = node.production
        if prod.is_enum():
            return self._analyze_enum(error.context, node, prod, error.reason)
        else:
            # TODO: Handle other types of production
            return None

    def analyze_interpreter_error(self, error: InterpreterError):
        if not isinstance(error, AssertionViolation):
            return None
        dyn_type_error = cast(AssertionViolation, error)
        return self.analyze_assertion_violation(dyn_type_error)
