from abc import ABC, abstractmethod
from typing import Any
from ..dsl import Node
from ..interpreter import InterpreterError
from .result import Result


class Decider(ABC):

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def analyze(self, ast: Node) -> Result:
        '''
        The main API of this class.
        It is expected to analyze the given AST and check if it is valid. If not, optionally returns why, which is used to update the enumerator.
        '''
        raise NotImplementedError

    def analyze_interpreter_error(self, error: InterpreterError) -> Any:
        '''
        Take an interpreter error and return a data structure that can be used to update the enumerator.
        '''
        return None
