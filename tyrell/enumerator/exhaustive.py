from typing import Iterator
from itertools import product
from ..spec import TyrellSpec, Type
from ..dsl import Node, Builder
from .enumerator import Enumerator
from .from_iterator import FromIteratorEnumerator


class ExhaustiveIterator:
    _builder: Builder
    _max_depth: int

    def __init__(self, spec: TyrellSpec, max_depth: int):
        self._builder = Builder(spec)
        if max_depth <= 0:
            raise ValueError(
                'Max depth cannot be non-positive: {}'.format(max_depth))
        self._max_depth = max_depth

    def _do_iter(self, ty: Type, curr_depth: int) -> Iterator[Node]:
        prods = self._builder.get_productions_with_lhs(ty)
        enum_prods, param_prods, func_prods = [], [], []
        force_leaf = curr_depth >= self._max_depth - 1
        for prod in prods:
            if prod.is_enum():
                enum_prods.append(prod)
            elif prod.is_param():
                param_prods.append(prod)
            elif not force_leaf and prod.is_function():
                func_prods.append(prod)

        for prod in enum_prods:
            yield self._builder.make_node(prod)
        for prod in param_prods:
            yield self._builder.make_node(prod)
        for prod in func_prods:
            child_iters = [self._do_iter(x, curr_depth + 1) for x in prod.rhs]
            for children in product(*child_iters):
                yield self._builder.make_node(prod, children)

    def iter(self) -> Iterator[Node]:
        if self._builder.num_productions() == 0:
            return iter(())
        else:
            return self._do_iter(self._builder.output, 0)


class ExhaustiveEnumerator(FromIteratorEnumerator):

    def __init__(self, spec: TyrellSpec, max_depth: int):
        super().__init__(ExhaustiveIterator(spec, max_depth).iter())
