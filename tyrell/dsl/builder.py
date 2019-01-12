from typing import Union
import sexpdata
from .node import *
from ..spec import TyrellSpec, Production, EnumType
from ..visitor import GenericVisitor


class ProductionVisitor(GenericVisitor):
    _children: List[Node]

    def __init__(self, children: List[Node]):
        self._children = children

    def visit_enum_production(self, prod) -> Node:
        return AtomNode(prod)

    def visit_param_production(self, prod) -> Node:
        return ParamNode(prod)

    def visit_function_production(self, prod) -> Node:
        return ApplyNode(prod, self._children)


class Builder:
    '''A factory class to build AST node'''

    _spec: TyrellSpec

    def __init__(self, spec: TyrellSpec):
        self._spec = spec

    def _make_node(self, prod: Production, children: List[Node] = []) -> Node:
        return ProductionVisitor(children).visit(prod)

    def make_node(self, src: Union[int, Production], children: List[Node] = []) -> Node:
        '''
        Create a node with the given production index and children.
        Raise `KeyError` or `ValueError` if an error occurs
        '''
        if isinstance(src, int):
            return self._make_node(self._spec.get_production_or_raise(src), children)
        elif isinstance(src, Production):
            # Sanity check first
            prod = self._spec.get_production_or_raise(src.id)
            if src != prod:
                raise ValueError(
                    'DSL Builder found inconsistent production instance')
            return self._make_node(prod, children)
        else:
            raise ValueError(
                'make_node() only accepts int or production, but found {}'.format(src))

    def make_enum(self, name: str, value: str) -> Node:
        '''
        Convenient method to create an enum node.
        Raise `KeyError` or `ValueError` if an error occurs
        '''
        ty = self.get_type_or_raise(name)
        prod = self.get_enum_production_or_raise(ty, value)
        return self.make_node(prod.id)

    def make_param(self, index: int) -> Node:
        '''
        Convenient method to create a param node.
        Raise `KeyError` or `ValueError` if an error occurs
        '''
        prod = self.get_param_production_or_raise(index)
        return self.make_node(prod.id)

    def make_apply(self, name: str, args: List[Node]) -> Node:
        '''
        Convenient method to create an apply node.
        Raise `KeyError` or `ValueError` if an error occurs
        '''
        prod = self.get_function_production_or_raise(name)
        return self.make_node(prod.id, args)

    def _from_sexp(self, sexp) -> Node:
        if not isinstance(sexp, list) or len(sexp) < 2 or not isinstance(sexp[0].value(), str):
            # None of our nodes serializes to atom
            msg = 'Cannot parse sexp into dsl.Node: {}'.format(sexp)
            raise ValueError(msg)
        sym = sexp[0].value()

        # First check for param node
        if sym == '@param':
            index = int(sexp[1])
            return self.make_param(index)

        # Next, check for atom node
        ty = self.get_type(sym)
        if ty is not None and ty.is_enum():
            if isinstance(sexp[1], list):
                # Could be a enum list
                value = [str(x) for x in sexp[1]]
                return self.make_enum(ty.name, value)
            else:
                value = str(sexp[1])
                return self.make_enum(ty.name, value)

        # Finally, check for apply node
        args = [self._from_sexp(x) for x in sexp[1:]]
        return self.make_apply(sym, args)

    def from_sexp_string(self, sexp_str: str) -> Node:
        '''
        Convenient method to create an AST from an sexp string.
        Raise `KeyError` or `ValueError` if an error occurs
        '''
        try:
            sexp = sexpdata.loads(sexp_str)
        # This library is liberal on its exception raising...
        except Exception as e:
            raise ValueError('Sexp parsing error: {}'.format(e))
        return self._from_sexp(sexp)

    # For convenience, expose all methods in TyrellSpec so that the client do not need to keep a reference of it
    def __getattr__(self, attr):
        return getattr(self._spec, attr)
