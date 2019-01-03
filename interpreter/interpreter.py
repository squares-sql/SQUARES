from dsl import Node
from abc import ABC, abstractmethod
from typing import Tuple, List, Iterator, Any


class InterpreterError(RuntimeError):
    _why: Any

    def __init__(self, why: Any = None):
        self._why = why

    def why(self) -> Any:
        return self._why


class Interpreter(ABC):

    @abstractmethod
    def eval_step(self, prog: Node, inputs: List[Any]) -> Iterator[Tuple[Node, List[Any], Any]]:
        '''
        This is the main API for the interpreter module.
        This method is expected to evaluate a DSL `prog` on input `inputs` for one step.
        It is expected that subclasses implement this function as a generator,  where after each step the evaluated AST node, the inputs, and the output are yielded.
        It is also expected that this method would raise `InterpreterError` when error occurs during the interpretation.
        '''
        raise NotImplementedError

    def eval(self, prog: Node, inputs: List[Any]) -> Any:
        '''
        Evaluate a DSL `prog` on input `inputs`. The output is returned.
        This is a covenient wrapper over `eval_step` that repeatedly invoke the generator until we get the final result.
        '''
        for _, _, out in self.eval_step(prog, inputs):
            pass
        # We only care about the final output
        return out
