#!/usr/bin/env python

import tyrell.spec as S
from tyrell.interpreter import PostOrderInterpreter
from tyrell.enumerator import SmtEnumerator
from tyrell.decider import Example, ExampleConstraintDecider
from tyrell.synthesizer import Synthesizer
from tyrell.logger import get_logger

logger = get_logger('tyrell')

toy_spec_str = '''
enum SmallInt {
  "-1", "-2", "0", "1", "2"
}
value Int {
    is_positive: bool;
}
value Empty;

program Toy(Int, Int) -> Int;
func const: Int -> SmallInt;
func sqrt_const: Int -> SmallInt;
func plus: Int -> Int, Int;
func minus: Int -> Int, Int;
func mult: Int r -> Int a, Int b {
    is_positive(a) && is_positive(b) ==> is_positive(r);
    is_positive(a) && !is_positive(b) ==> !is_positive(r);
    !is_positive(a) && is_positive(b) ==> !is_positive(r);
}
func empty: Empty -> Empty;

# You can use any number larger than 0 as weight (does not need to be bounded at 100)
# predicate occurs(minus, 80);
predicate occurs(mult, 10);
predicate is_parent(minus, mult, 99);
predicate is_not_parent(mult, minus, 500);

# Since the program we want is mult(@param1, minus(@param0, @param1))
# The following 2 constraints would find that program very quickly
# predicate occurs(mult, 999);
# predicate is_parent(mult, minus, 999);

'''


class ToyInterpreter(PostOrderInterpreter):
    def eval_SmallInt(self, v):
        return int(v)

    def eval_const(self, node, args):
        return args[0]

    def eval_sqrt_const(self, node, args):
        self.assertArg(node, args,
                       index=0,
                       cond=lambda x: x >= 0,
                       capture_indices=[])
        return int(args[0] ** 0.5)

    def eval_plus(self, node, args):
        return args[0] + args[1]

    def eval_minus(self, node, args):
        return args[0] - args[1]

    def eval_mult(self, node, args):
        return args[0] * args[1]

    def apply_is_positive(self, val):
        return val > 0


def main():
    logger.info('Parsing Spec...')
    spec = S.parse(toy_spec_str)
    logger.info('Parsing succeeded')

    logger.info('Building synthesizer...')
    synthesizer = Synthesizer(
        enumerator=SmtEnumerator(spec, depth=3, loc=2),
        decider=ExampleConstraintDecider(
            spec=spec,
            interpreter=ToyInterpreter(),
            examples=[
                # we want to synthesize the program (x-y)*y (depth=3, loc=2)
                # which is also equivalent to x*y-y*y (depth=3, loc=3)
                Example(input=[4, 3], output=3),
                Example(input=[6, 3], output=9),
                Example(input=[1, 2], output=-2),
                Example(input=[1, 1], output=0),
            ]
        )
    )
    logger.info('Synthesizing programs...')

    prog = synthesizer.synthesize()
    if prog is not None:
        logger.info('Solution found: {}'.format(prog))
    else:
        logger.info('Solution not found!')


if __name__ == '__main__':
    logger.setLevel('DEBUG')
    main()
