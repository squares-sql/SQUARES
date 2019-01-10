from typing import Any, List, Iterable


class Predicate:
    _name: str
    _args: List[Any]

    def __init__(self, name: str, args: List[Any] = []):
        self._name = name
        self._args = args

    @property
    def name(self) -> str:
        return self._name

    @property
    def args(self) -> Iterable[Any]:
        return self._args

    def num_args(self) -> int:
        return len(self._args)

    def __repr__(self) -> str:
        return 'Predicate(name={}, args={})'.format(self._name, self._args)

    def __str__(self) -> str:
        return '{}({})'.format(self._name, ', '.join([str(x) for x in self._args]))
