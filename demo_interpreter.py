import spec as S
import dsl as D
from interpreter import PostOrderInterpreter
import logger

logger = logger.get('tyrell')

toy_spec_str = '''
enum SmallInt {
  "0", "1", "2", "3"
}
value Int;

program Toy(Int, Int) -> Int;
func const: Int -> SmallInt;
func plus: Int -> Int, Int;
func minus: Int -> Int, Int;
func mult: Int -> Int, Int;
'''

toy_dsl_sexp = '''
(plus
    (mult
        (plus (@param 0) (@param 1))
        (minus (@param 0) (@param 1))
    )
    (const (SmallInt "1"))
)
'''
input0 = [4, 3]
input1 = [6, 5]


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


def main():
    logger.info('Parsing Spec...')
    spec = S.parse(toy_spec_str)
    logger.info('Parsing succeeded')

    logger.info('Building sample program...')
    prog = D.Builder(spec).from_sexp_string(toy_dsl_sexp)
    logger.info('Build program = {}'.format(prog))

    interpreter = ToyInterpreter()
    logger.info('Executing program on inputs {} step-by-step...'.format(input0))
    out_value = execute_step(interpreter, prog, input0)
    logger.info('Execution finished with output = {}'.format(out_value))

    logger.info('Executing program on inputs {} all at once...'.format(input1))
    out_value = execute_all(interpreter, prog, input1)
    logger.info('Execution finished with output = {}'.format(out_value))


if __name__ == '__main__':
    logger.setLevel('DEBUG')
    main()
