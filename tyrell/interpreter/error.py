from abc import ABC, abstractmethod
from typing import Callable, Iterable, Optional, Any
from ..dsl import Node
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
    _index: int
    _reason: Callable[[Any], bool]
    _captures: Iterable[int]

    def __init__(self, node: Node, index: int, reason: Callable[[Any], bool], captures: Iterable[int]):
        super().__init__()
        self._node = node
        self._index = index
        self._reason = reason
        self._captures = captures

    @property
    def node(self) -> Node:
        return self._node

    @property
    def arg(self) -> Node:
        return self._node.children[self._index]

    @property
    def index(self) -> int:
        return self._index

    @property
    def reason(self) -> Callable[[Any], bool]:
        return self._reason

    @property
    def captures(self) -> Iterable[int]:
        return self._captures
