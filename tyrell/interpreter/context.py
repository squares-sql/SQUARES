from typing import List, Optional
from ..dsl import Node


class Context:
    _observed: List[Node]
    _evaluated: List[Node]
    _stack: List[Node]

    def __init__(self):
        self._observed = list()
        self._evaluated = list()
        self._stack = list()

    def observe(self, node: Node) -> None:
        self._observed.append(node)
        if not node.is_leaf():
            self._stack.append(node)

    def finish(self, node: Node) -> None:
        self._evaluated.append(node)

    def pop(self) -> Optional[Node]:
        if len(self._stack) == 0:
            return None
        return self._stack.pop()

    def pop_or_raise(self) -> Node:
        return self._stack.pop()

    @property
    def observed(self):
        return self._observed

    @property
    def evaluated(self):
        return self._evaluated

    @property
    def stack(self):
        return self._stack
