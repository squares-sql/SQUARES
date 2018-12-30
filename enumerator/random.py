from typing import Set, Optional
from random import Random
from .enumerator import Enumerator
import dsl as D
import spec as S
import logger

logger = logger.get('tyrell.enumerator.random')


class RandomEnumerator(Enumerator):
    _rand: Random
    _max_depth: int
    _max_trial: int
    _builder: D.Builder
    _enumerated: Set[D.Node]

    def __init__(self, spec: S.TyrellSpec, max_depth: int, max_trial: int, seed: Optional[int]=None):
        self._rand = Random(seed)
        self._builder = D.Builder(spec)
        if max_depth <= 0:
            raise ValueError(
                'Max depth cannot be non-positive: {}'.format(max_depth))
        if max_trial <= 0:
            raise ValueError(
                'Max trial cannot be non-positive: {}'.format(max_trial))
        self._max_depth = max_depth
        self._max_trial = max_trial
        self._enumerated = set()

    def _do_generate(self, curr_type: S.Type, curr_depth: int, force_leaf: bool):
        # First, get all the relevant production rules for current type
        productions = self._builder.get_productions_with_lhs(curr_type)
        if force_leaf:
            productions = list(
                filter(lambda x: not x.is_function(), productions))
        if len(productions) == 0:
            raise RuntimeError('RandomASTGenerator ran out of productions to try for type {} at depth {}'.format(
                curr_type, curr_depth))

        # Pick a production rule uniformly at random
        prod = self._rand.choice(productions)
        if not prod.is_function():
            # make_node() will produce a leaf node
            return self._builder.make_node(prod)
        else:
            # Recursively expand the right-hand-side (generating children first)
            children = [self._generate(x, curr_depth + 1) for x in prod.rhs]
            # make_node() will produce an internal node
            return self._builder.make_node(prod, children)

    def _generate(self, curr_type: S.Type, curr_depth: int):
        return self._do_generate(curr_type, curr_depth,
                                 force_leaf=(curr_depth >= self._max_depth - 1))

    def next(self):
        num_trials = 0
        while num_trials < self._max_trial:
            num_trials += 1
            ast = self._generate(self._builder.output, 0)
            if ast not in self._enumerated:
                self._enumerated.add(ast)
                logger.debug(
                    'RandomEnumerator.next() completed with {} trials'.format(num_trials))
                return ast
        logger.debug(
            'RandomEnumerator.next() failed with {} trials'.format(num_trials))
        return None
