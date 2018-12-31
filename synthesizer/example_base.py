from typing import NamedTuple, List, Any
from .synthesizer import Synthesizer
from interpreter import Interpreter
from enumerator import Enumerator
from .result import ok, bad

Example = NamedTuple('Example', [
    ('input', List[Any]),
    ('output', Any)])


class ExampleSynthesizer(Synthesizer):
    _examples: List[Example]

    def __init__(self,
                 enumerator: Enumerator,
                 interpreter: Interpreter,
                 examples: List[Example]):
        super().__init__(enumerator, interpreter)
        if len(examples) == 0:
            raise ValueError(
                'ExampleSynthesizer cannot take an empty list of examples')
        self._examples = examples

    def _test_all_examples(self, prog):
        return all(
            self.interpreter.eval(prog, example_in) == example_out
            for example_in, example_out in self._examples)

    def analyze(self, prog):
        '''
        This basic version of analyze() merely interpret the AST and see if it conforms to our examples
        '''
        if self._test_all_examples(prog):
            return ok()
        else:
            # TODO: return a more useful reason
            return bad(why=None)
