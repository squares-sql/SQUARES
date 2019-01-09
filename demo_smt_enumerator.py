#!/usr/bin/env python

import spec as S
from interpreter import PostOrderInterpreter
from enumerator import SmtEnumerator
from synthesizer import AssertionViolationHandler, ExampleConstraintSynthesizer, Example
from logger import get_logger

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


class DemoSynthesizer(AssertionViolationHandler, ExampleConstraintSynthesizer):
    pass


def main():
    logger.info('Parsing Spec...')
    spec = S.parse(toy_spec_str)
    logger.info('Parsing succeeded')

    logger.info('Building synthesizer...')
    synthesizer = DemoSynthesizer(
        enumerator=SmtEnumerator(spec, depth=3, loc=2),
        interpreter=ToyInterpreter(),
        spec=spec,
        examples=[
            # we want to synthesize the program (x-y)*y (depth=3, loc=2)
            # which is also equivalent to x*y-y*y (depth=3, loc=3)
            Example(input=[4, 3], output=3),
            Example(input=[6, 3], output=9),
            Example(input=[1, 2], output=-2),
            Example(input=[1, 1], output=0),
        ]
    )
    logger.info('Synthesizing programs...')

    for p in spec.productions():
        if p.id == 3:
            minus_prod = p
        if p.id == 4:
            mult_prod = p

    # You can use any number larger than 0 as weight (does not need to be bounded at 100)
    synthesizer.mk_occurs(minus_prod, 80)
    synthesizer.mk_occurs(mult_prod, 10)
    synthesizer.mk_is_parent(minus_prod, mult_prod, 99)

    # Since the program we want is mult(@param1, minus(@param0, @param1))
    # The following constraints would find that program very quickly
    # synthesizer.mk_occurs(mult_prod,999)
    # synthesizer.mk_is_parent(mult_prod, minus_prod, 999)

    prog = synthesizer.synthesize()
    if prog is not None:
        logger.info('Solution found: {}'.format(prog))
    else:
        logger.info('Solution not found!')


if __name__ == '__main__':
    logger.setLevel('DEBUG')
    main()
