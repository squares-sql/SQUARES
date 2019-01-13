from typing import cast, List
from ..spec import Production
from ..dsl import AtomNode, dfs
from ..interpreter import InterpreterError, AssertionViolation
from .synthesizer import Synthesizer
from .example_constraint import Blame


class AssertionViolationHandler(Synthesizer):
    '''
    A mixin class for Synthesizer that provide pruning capabilities for dynamic type errors.
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _compute_blame_base(self, error: AssertionViolation) -> List[Blame]:
        node = error.node
        capture_set = set(error.captures)
        # Exclude the failed child itself
        capture_set.discard(error.index)
        capture_nodes = [node.children[x] for x in capture_set]

        blame_nodes = [node]
        for capture_node in capture_nodes:
            for child in dfs(capture_node):
                blame_nodes.append(child)
        return [Blame(n, n.production) for n in blame_nodes]

    def _analyze_enum(self, prod: Production, error: AssertionViolation) -> List[List[Blame]]:
        blames = list()
        arg_node = error.arg
        blame_base = self._compute_blame_base(error)
        for alt_prod in self.spec.get_productions_with_lhs(prod.lhs):
            alt_node = AtomNode(alt_prod)
            # Inputs doesn't matter here as we don't have any ParamNode
            value = self.interpreter.eval(alt_node, [])
            if not error.reason(value):
                blames.append(blame_base + [Blame(arg_node, alt_prod)])
        return blames

    def analyze_assertion_violation(self, error: AssertionViolation):
        prod = error.arg.production
        if prod.is_enum():
            return self._analyze_enum(prod, error)
        else:
            # TODO: Handle other types of production
            return None

    def analyze_interpreter_error(self, error: InterpreterError):
        if not isinstance(error, AssertionViolation):
            return None
        dyn_type_error = cast(AssertionViolation, error)
        return self.analyze_assertion_violation(dyn_type_error)