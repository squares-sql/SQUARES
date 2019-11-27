import unittest
from ..spec import parse
from ..dsl import Builder
from ..interpreter import PostOrderInterpreter
from .example_base import Example, ExampleDecider

spec_str = r'''
    value IntExpr {
        pos: bool;
        neg: bool;
    }

    program Foo(IntExpr, IntExpr) -> IntExpr;
    func plus: IntExpr -> IntExpr, IntExpr;
    func mult: IntExpr -> IntExpr, IntExpr;
'''
spec = parse(spec_str)
builder = Builder(spec)


class FooInterpreter(PostOrderInterpreter):
    def eval_mult(self, node, args):
        return args[0] * args[1]

    def eval_plus(self, node, args):
        return args[0] + args[1]


class TestExample(unittest.TestCase):

    def test_analyze(self):
        decider = ExampleDecider(
            interpreter=FooInterpreter(),
            examples=[
                Example(input=[2, 2], output=4),
                Example(input=[2, 3], output=5)
            ]
        )
        plus_prog = builder.from_sexp_string('(plus (@param 0) (@param 1))')
        mult_prog = builder.from_sexp_string('(mult (@param 0) (@param 1))')

        res_plus = decider.analyze(plus_prog)
        self.assertTrue(res_plus.is_ok())
        self.assertFalse(res_plus.is_bad())
        self.assertFalse(decider.has_failed_examples(plus_prog))
        self.assertListEqual(decider.get_failed_examples(plus_prog), [])

        res_mult = decider.analyze(mult_prog)
        self.assertFalse(res_mult.is_ok())
        self.assertTrue(res_mult.is_bad())
        self.assertTrue(decider.has_failed_examples(mult_prog))
        self.assertListEqual(decider.get_failed_examples(
            mult_prog), [Example(input=[2, 3], output=5)])

    def test_custom_equal(self):
        def my_equal(x, y):
            return abs(x - y) <= 1
        decider = ExampleDecider(
            interpreter=FooInterpreter(),
            examples=[
                Example(input=[2, 3], output=5)
            ],
            equal_output=my_equal
        )
        prog = builder.from_sexp_string('(mult (@param 0) (@param 1))')
        self.assertEqual(decider.has_failed_examples(prog), False)
        failed_examples = decider.get_failed_examples(prog)
        self.assertEqual(len(failed_examples), 0)
        res = decider.analyze(prog)
        self.assertTrue(res.is_ok())


if __name__ == '__main__':
    unittest.main()
