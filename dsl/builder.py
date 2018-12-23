from .node import *
from spec import TyrellSpec, Production
from typing import Union
from visitor import GenericVisitor


class ProductionVisitor(GenericVisitor):
    _children: List[Node]

    def __init__(self, children: List[Node]):
        self._children = children

    def visit_enum_production(self, prod):
        return AtomNode(prod)

    def visit_param_production(self, prod):
        return ParamNode(prod)

    def visit_function_production(self, prod):
        return ApplyNode(prod, self._children)


class Builder:
    '''A factory class to build AST node'''

    _spec: TyrellSpec

    def __init__(self, spec: TyrellSpec):
        self._spec = spec

    def _make_node(self, prod: Production, children: List[Node] = []):
        return ProductionVisitor(children).visit(prod)

    def make_node(self, src: Union[int, Production], children: List[Node] = []):
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

    # For convenience, expose all methods in TyrellSpec so that the client do not need to keep a reference of it
    def __getattr__(self, attr):
        return getattr(self._spec, attr)
