#!/usr/bin/env python

import tyrell.spec as S
from tyrell.interpreter import PostOrderInterpreter
from tyrell.enumerator import SmtEnumerator
from tyrell.enumerator import LinesEnumerator
from tyrell.decider import Example, ExampleConstraintDecider
from tyrell.synthesizer import Synthesizer
from tyrell.logger import get_logger
from sys import *

logger = get_logger('tyrell')

toy_spec_str = '''
# First, specify the types that will be used
enum SmallInt {
  #"0", "1", "2", "3"
  "1"
}

value Int;
value Empty;


#program Toy(Int) -> Int;
program Toy(Int, Int) -> Int;
#program Toy(Int, Int, Int) -> Int;

# Finally, specify the production rules
func const: Int -> SmallInt;
func minus: Int -> Int, Int;
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


def main():
    logger.info('Parsing Spec...')
    spec = S.parse(toy_spec_str)
    logger.info('Parsing succeeded')

    logger.info('Building synthesizer...')
    # loc = 6
    loc = 3
    enumerator = SmtEnumerator(spec, depth=loc+1, loc=loc) if argv[1]=="smt" else LinesEnumerator(spec, depth=loc+1, loc=loc)
    synthesizer = Synthesizer(
        # enumerator=LinesEnumerator(spec, depth=loc+1, loc=loc),
        enumerator=enumerator,
        # enumerator=LinesEnumerator(spec, depth=4, loc=3),
        # enumerator=SmtEnumerator(spec, depth=4, loc=3),
        decider=ExampleConstraintDecider(
            spec=spec,
            interpreter=ToyInterpreter(),
            examples=[
                # we want to synthesize the program (x-y)*y (depth=3, loc=2)
                # which is also equivalent to x*y-y*y (depth=3, loc=3)
                # Example(input=[3, 2], output=5), # loc 4
                # Example(input=[3, 2], output=6), # loc 3 res: 118
                # Example(input=[3], output=5), # loc 4 res: 190
                # Example(input=[3, 2, 1], output=6), # loc 4 
                Example(input=[4, 2], output=1), # loc 3
                # Example(input=[6, 3], output=9),
                # Example(input=[1, 2], output=-2),
                # Example(input=[1, 1], output=0),
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
