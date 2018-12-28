#!/usr/bin/env python

from z3 import *
import spec as S
import dsl as D
from interpreter import PostOrderInterpreter
import logger
import enumerator as E

logger = logger.get('demo')

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
  nb_solved=0
  for x in range(0,len(inputs)):
    inp = inputs[x]
    out_value = execute_all(interpreter, prog, inp)
    if out_value == outputs[x]:
      nb_solved += 1
  if nb_solved == len(outputs):
    return True
  else:
    return False

def main():
  logger.info('Parsing Spec...')
  spec = S.parse(toy_spec_str)
  logger.info('Parsing succeeded')

  logger.info('Building Sketcher...')
  sketcher = E.Enumerator(spec, 3, 2)
  logger.info('Enumerating programs...')

  interpreter = ToyInterpreter()

  # we want to synthesize the program (x-y)*y (depth=3, loc=2)
  # which is also equivalent to x*y-y*y (depth=3, loc=3)
  inputs = [[4,3], [6,3], [1,2], [1,1]]
  outputs = [3, 9, -2, 0]

  res = sat 
  programs = 0
  found = False
  while res == sat:
    res = sketcher.solve()
    if res == sat:
      prog = sketcher.buildProgram()
      logger.info('Build program = {}'.format(prog))
      programs += 1

      # testing the program
      found = test_all(interpreter, prog, inputs, outputs)
      if found:
        break
      sketcher.blockModel()
    else:
      break
  if found:
    logger.info('Solution found!')
  else:
    logger.info('Solution not found!')
  logger.info('Programs explored = {}'.format(programs))


if __name__ == '__main__':
    logger.setLevel('DEBUG')
    main()
