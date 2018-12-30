#!/usr/bin/env python

import spec as S
from interpreter import PostOrderInterpreter
from enumerator import SmtEnumerator
import logger

logger = logger.get('tyrell')

toy_spec_str = '''
enum SmallInt {
  "0", "1", "2", "3"
}
value Int;
value Empty;

program Toy(Int, Int) -> Int;
func const: Int -> SmallInt;
func plus: Int -> Int, Int;
func minus: Int -> Int, Int;
func mult: Int -> Int, Int;
func empty: Empty -> Empty;
'''


class ToyInterpreter(PostOrderInterpreter):
    def eval_SmallInt(self, v):
        return int(v)

    def eval_const(self, node, args):
        return args[0]

    def eval_plus(self, node, args):
        return args[0] + args[1]

    def eval_minus(self, node, args):
        return args[0] - args[1]

    def eval_mult(self, node, args):
        return args[0] * args[1]


def execute(interpreter, prog, args):
    return interpreter.eval(prog, args)


def test_all(interpreter, prog, inputs, outputs):
    return all(
        execute(interpreter, prog, inputs[x]) == outputs[x]
        for x in range(0, len(inputs))
    )


def main():
    logger.info('Parsing Spec...')
    spec = S.parse(toy_spec_str)
    logger.info('Parsing succeeded')

    logger.info('Building Sketcher...')
    sketcher = SmtEnumerator(spec, depth=3, loc=2)
    logger.info('Enumerating programs...')

    interpreter = ToyInterpreter()

    # we want to synthesize the program (x-y)*y (depth=3, loc=2)
    # which is also equivalent to x*y-y*y (depth=3, loc=3)
    inputs = [[4, 3], [6, 3], [1, 2], [1, 1]]
    outputs = [3, 9, -2, 0]

    programs = 0
    found = False
    prog = sketcher.next()
    while prog is not None:
        logger.info('Build program = {}'.format(prog))
        programs += 1

        # testing the program
        found = test_all(interpreter, prog, inputs, outputs)
        if found:
            break
        sketcher.update()
        prog = sketcher.next()

    if found:
        logger.info('Solution found!')
    else:
        logger.info('Solution not found!')
    logger.info('Programs explored = {}'.format(programs))


if __name__ == '__main__':
    logger.setLevel('DEBUG')
    main()
