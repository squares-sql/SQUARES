from abc import ABC, abstractmethod
from typing import Callable, Optional, Any
from dsl import Node
from .context import Context


class InterpreterError(RuntimeError):
    context: Optional[Context]

    @abstractmethod
    def __init__(self, *args):
        super().__init__(args)
        self.context = None


class GeneralError(InterpreterError):
    def __init__(self, msg: str=""):
        super().__init__(msg)


class AssertionViolation(InterpreterError):
    _node: Node
    _reason: Callable[[Any], bool]

    def __init__(self, node: Node, reason: Callable[[Any], bool]):
        super().__init__()
        self._node = node
        self._reason = reason

    @property
    def node(self) -> Node:
        return self._node

    @property
    def reason(self) -> Callable[[Any], bool]:
        return self._reason
