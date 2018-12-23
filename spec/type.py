from abc import ABC, abstractmethod
from typing import List


class Type(ABC):
    '''A generic class for types in DSL'''
    _name: str

    @abstractmethod
    def __init__(self, name: str):
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def __str__(self) -> str:
        return self._name

    def __eq__(self, other):
        """Overrides the default implementation"""
        if isinstance(other, Type):
            return self._name == other._name
        return NotImplemented

    def __hash__(self):
        """Overrides the default implementation"""
        return hash(self._name)


class EnumType(Type):
    '''A special kind of type whose domain is finite and specified up-front'''

    _domain: List[str]

    def __init__(self, name: str, domain: List[str] = []):
        super().__init__(name)
        self._domain = domain

    @property
    def domain(self) -> List[str]:
        return self._domain

    def __repr__(self) -> str:
        return 'EnumType({}, domain={})'.format(self._name, self._domain)


class ValueType(Type):

    def __init__(self, name: str):
        super().__init__(name)

    def __repr__(self) -> str:
        return 'ValueType({})'.format(self._name)
