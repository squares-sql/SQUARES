from typing import Callable, NamedTuple, List, Any
from .decider import Decider
from ..interpreter import Interpreter
from .result import ok, bad

Example = NamedTuple('Example', [
    ('input', List[Any]),
    ('output', Any)])


class ExampleDecider(Decider):
    _interpreter: Interpreter
    _examples: List[Example]
    _equal_output: Callable[[Any, Any], bool]

    def __init__(self,
                 interpreter: Interpreter,
                 examples: List[Example],
                 equal_output: Callable[[Any, Any], bool] = lambda x, y: x == y):
        self._interpreter = interpreter
        if len(examples) == 0:
            raise ValueError(
                'ExampleDecider cannot take an empty list of examples')
        self._examples = examples
        self._equal_output = equal_output

    @property
    def interpreter(self):
        return self._interpreter

    @property
    def examples(self):
        return self._examples

    @property
    def equal_output(self):
        return self._equal_output

    def get_failed_examples(self, prog):
        '''
        Test the program on all examples provided.
        Return a list of failed examples.
        '''
        return list(filter(
            lambda x: not self._equal_output(
                self.interpreter.eval(prog, x.input), x.output),
            self._examples
        ))

    def has_failed_examples(self, prog):
        '''
        Test whether the given program would fail on any of the examples provided.
        '''
        return any(
            not self._equal_output(
                self.interpreter.eval(prog, x.input), x.output)
            for x in self._examples
        )

    def analyze(self, prog):
        '''
        This basic version of analyze() merely interpret the AST and see if it conforms to our examples
        '''
        if self.has_failed_examples(prog):
            return bad()
        else:
            return ok()
