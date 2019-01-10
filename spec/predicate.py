from typing import Any, List


class Predicate:
    _name: str
    _args: List[Any]

    def __init__(self, name: str, args: List[Any] = []):
        self._name = name
        self._args = args

    @property
    def name(self):
        return self._name

    @property
    def args(self):
        return self._args

    def __repr__(self) -> str:
        return 'Predicate(name={}, args={})'.format(self._name, self._args)

    def __str__(self) -> str:
        return '{}({})'.format(self._name, ', '.join([str(x) for x in self._args]))
