from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Optional, Any
from .expr import ExprType


class Type(ABC):
    '''A generic class for types in DSL'''
    _name: str

    @abstractmethod
    def __init__(self, name: str):
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @abstractmethod
    def is_enum(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def is_value(self) -> bool:
        raise NotImplementedError

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

    _domain: List[Any]

    def __init__(self, name: str, domain: List[Any] = []):
        super().__init__(name)
        self._domain = domain

    @property
    def domain(self) -> List[Any]:
        return self._domain

    def is_enum(self) -> bool:
        return True

    def is_value(self) -> bool:
        return False

    def __repr__(self) -> str:
        return 'EnumType({}, domain={})'.format(self._name, self._domain)


class ValueType(Type):
    _properties: Dict[str, ExprType]

    def __init__(self, name: str, properties: List[Tuple[str, ExprType]] = []):
        super().__init__(name)
        self._properties = dict()
        for name, ty in properties:
            if name in self._properties:
                raise ValueError('Duplicate property name: {}'.format(name))
            self._properties[name] = ty

    def is_enum(self) -> bool:
        return False

    def is_value(self) -> bool:
        return True

    def get_property(self, name: str) -> Optional[ExprType]:
        return self._properties.get(name, None)

    def get_property_or_raise(self, name: str) -> ExprType:
        return self._properties[name]

    @property
    def properties(self):
        return list(self._properties.items())

    def __repr__(self) -> str:
        return 'ValueType({}, properties={})'.format(self._name, self._properties)
