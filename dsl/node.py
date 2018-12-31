from typing import List
from abc import ABC, abstractmethod
from sexpdata import Symbol
from spec import Type, Production


class Node(ABC):
    '''Generic and abstract AST Node'''

    _prod: Production

    @abstractmethod
    def __init__(self, prod: Production):
        self._prod = prod

    @property
    def production(self):
        return self._production

    @property
    def type(self) -> Type:
        return self._prod.lhs

    @abstractmethod
    def is_leaf(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def to_sexp(self):
        raise NotImplementedError


class LeafNode(Node):
    '''Generic and abstract class for AST nodes that have no children'''
    @abstractmethod
    def __init__(self, prod: Production):
        super().__init__(prod)
        if prod.is_function():
            raise ValueError(
                'Cannot construct an AST leaf node from a FunctionProduction')

    def is_leaf(self) -> bool:
        return True


class AtomNode(LeafNode):
    '''Leaf AST node that holds string data'''

    def __init__(self, prod: Production):
        if not prod.is_enum():
            raise ValueError(
                'Cannot construct an AST atom node from a non-enum production')
        super().__init__(prod)

    @property
    def data(self) -> str:
        return self._prod.rhs[0]

    def to_sexp(self):
        return [Symbol(self.type.name), self.data]

    def __repr__(self) -> str:
        return 'AtomNode({})'.format(self.data)

    def __str__(self) -> str:
        return self.data

    def __eq__(self, other):
        if isinstance(other, AtomNode):
            return self.type == other.type and self.data == other.data
        return NotImplemented

    def __hash__(self):
        return hash((self.type, self.data))


class ParamNode(LeafNode):
    '''Leaf AST node that holds a param'''

    def __init__(self, prod: Production):
        if not prod.is_param():
            raise ValueError(
                'Cannot construct an AST param node from a non-param production')
        super().__init__(prod)

    @property
    def index(self) -> int:
        return self._prod.rhs[0]

    def to_sexp(self):
        return [Symbol('@param'), self.index]

    def __repr__(self) -> str:
        return 'ParamNode({})'.format(self.index)

    def __str__(self) -> str:
        return '@param{}'.format(self.index)

    def __eq__(self, other):
        if isinstance(other, ParamNode):
            return self.index == other.index
        return NotImplemented

    def __hash__(self):
        return hash(self.index)


class ApplyNode(Node):
    '''Internal AST node that represent function application'''
    _args: List[Node]

    def __init__(self, prod: Production, args: List[Node]):
        super().__init__(prod)
        if not prod.is_function():
            raise ValueError(
                'Cannot construct an AST internal node from a non-function production')
        if len(prod.rhs) != len(args):
            msg = 'Argument count mismatch: expected {} but found {}'.format(
                len(prod.rhs), len(args))
            raise ValueError(msg)
        for index, (decl_ty, node) in enumerate(zip(prod.rhs, args)):
            actual_ty = node.type
            if decl_ty != actual_ty:
                msg = 'Argument {} type mismatch: expected {} but found {}'.format(
                    index, decl_ty, actual_ty)
                raise ValueError(msg)
        self._args = args

    @property
    def name(self) -> str:
        return self._prod.name

    @property
    def args(self) -> List[Node]:
        return self._args

    def is_leaf(self) -> bool:
        return False

    def to_sexp(self):
        return [Symbol(self.name)] + [x.to_sexp() for x in self.args]

    def __repr__(self) -> str:
        return 'ApplyNode({}, {})'.format(self.name, self._args)

    def __str__(self) -> str:
        return '{}({})'.format(self.name, ', '.join([str(x) for x in self._args]))

    def __eq__(self, other):
        if isinstance(other, ApplyNode):
            return self.name == other.name and self.args == other.args
        return NotImplemented

    def __hash__(self):
        return hash((self.name, tuple(self.args)))
