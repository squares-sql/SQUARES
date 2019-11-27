import tyrell.spec as S
import tyrell.dsl as D
from tyrell.interpreter import PostOrderInterpreter
from tyrell.logger import get_logger

logger = get_logger('tyrell')

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


def toy_dsl_func(params):
    return (params[0] + params[1]) * (params[0] - params[1]) + 1


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


def main():
    logger.info('Parsing Spec...')
    spec = S.parse(toy_spec_str)
    logger.info('Parsing succeeded')

    logger.info('Building sample program...')
    prog = D.Builder(spec).from_sexp_string(toy_dsl_sexp)
    logger.info('Build program = {}'.format(prog))

    interpreter = ToyInterpreter()
    logger.info('Executing program on inputs {}...'.format(input0))
    out_value = execute(interpreter, prog, input0)
    logger.info('Execution finished with output = {}'.format(out_value))
    assert out_value == toy_dsl_func(input0)

    logger.info('Executing program on inputs {}...'.format(input1))
    out_value = execute(interpreter, prog, input1)
    logger.info('Execution finished with output = {}'.format(out_value))
    assert out_value == toy_dsl_func(input1)


if __name__ == '__main__':
    logger.setLevel('DEBUG')
    main()
