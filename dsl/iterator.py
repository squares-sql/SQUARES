from typing import Iterator
from collections import deque
from .node import Node


def dfs(node: Node) -> Iterator[Node]:
    stack = [node]
    while len(stack) > 0:
        node = stack.pop()
        yield node
        for child in reversed(node.children):
            stack.append(child)


def bfs(node: Node) -> Iterator[Node]:
    queue = deque([node])
    while len(queue) > 0:
        node = queue.popleft()
        yield node
        for child in node.children:
            queue.append(child)
