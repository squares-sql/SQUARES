from dsl import Node
from abc import ABC, abstractmethod
from typing import List, Any


class Interpreter(ABC):

    @abstractmethod
    def eval(self, prog: Node, inputs: List[Any]) -> Any:
        '''
        Evaluate a DSL `prog` on input `inputs`. The output is returned.
        This is a covenient wrapper over `eval_step` that repeatedly invoke the generator until we get the final result.
        '''
        raise NotImplementedError
