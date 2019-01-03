#!/usr/bin/env python

from sys import argv
import spec as S
from interpreter import PostOrderInterpreter
from enumerator import RandomEnumerator
from synthesizer import ExampleSynthesizer, Example
from logger import get_logger

logger = get_logger('tyrell')

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


def execute_step(interpreter, prog, args):
    step = 0
    for node, in_values, out_value in interpreter.eval_step(prog, args):
        if node.is_leaf():
            logger.debug('[Step {}] leaf node {} = {}'.format(
                step, node, out_value))
        else:
            logger.debug('[Step {}] {}({}) = {}'.format(
                step, node.name, ', '.join([str(x) for x in in_values]), out_value))
        step += 1
    return out_value


def execute_all(interpreter, prog, args):
    return interpreter.eval(prog, args)


def test_all(interpreter, prog, inputs, outputs):
    nb_solved = 0
    for x in range(0, len(inputs)):
        inp = inputs[x]
        out_value = execute_all(interpreter, prog, inp)
        if out_value == outputs[x]:
            nb_solved += 1
    if nb_solved == len(outputs):
        return True
    else:
        return False


def main(seed=None):
    logger.info('Parsing Spec...')
    spec = S.parse(toy_spec_str)
    logger.info('Parsing succeeded')

    logger.info('Building synthesizer...')
    synthesizer = ExampleSynthesizer(
        enumerator=RandomEnumerator(
            spec, max_depth=4, max_trial=1000, seed=seed),
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
    logger.info('Synthesizing programs...')

    prog = synthesizer.synthesize()
    if prog is not None:
        logger.info('Solution found: {}'.format(prog))
    else:
        logger.info('Solution not found!')


if __name__ == '__main__':
    logger.setLevel('DEBUG')
    seed = None
    if len(argv) > 1:
        try:
            seed = int(argv[1])
        except ValueError:
            pass
    main(seed)
