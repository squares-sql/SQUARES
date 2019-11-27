from .enumerator import Enumerator
from typing import Optional, List, Iterator
from ..dsl import Node


class FromIteratorEnumerator(Enumerator):
    '''
    A enumerator that is constructed from a python iterator.
    '''
    _iter: Iterator[Node]

    def __init__(self, iter: Iterator[Node]):
        super().__init__()
        self._iter = iter

    def next(self) -> Optional[Node]:
        try:
            return next(self._iter)
        except StopIteration:
            return None


def make_empty_enumerator() -> Enumerator:
    '''Return an enumerator that enumerates nothing.'''
    return FromIteratorEnumerator(iter(()))


def make_singleton_enumerator(prog: Node) -> Enumerator:
    '''Return an enumerator that only enumerates the given program.'''
    return FromIteratorEnumerator(iter([prog]))


def make_list_enumerator(progs: List[Node]) -> Enumerator:
    '''Return an enumerator that only enumerates programs in the given list.'''
    return FromIteratorEnumerator(iter(progs))
