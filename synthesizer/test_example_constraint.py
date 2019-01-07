import unittest
from spec import parse
from dsl import Builder
from enumerator import make_empty_enumerator
from interpreter import PostOrderInterpreter
from .example_base import Example, ExampleSynthesizer
from .example_constraint import ExampleConstraintSynthesizer


spec_str = r'''
    value IntExpr {
        pos: bool;
        neg: bool;
    }

    program Foo(IntExpr, IntExpr) -> IntExpr;
    func mult: IntExpr r -> IntExpr a, IntExpr b {
        pos(a) && neg(b) ==> neg(r);
    }
    func div: IntExpr r -> IntExpr a, IntExpr b {
        pos(a) && neg(b) ==> neg(r);
        pos(b) && neg(a) ==> neg(r);
    }
'''
spec = parse(spec_str)
builder = Builder(spec)


class FooInterpreter(PostOrderInterpreter):
    def eval_mult(self, node, args):
        return args[0] * args[1]

    def apply_pos(self, arg):
        return arg > 0

    def apply_neg(self, arg):
        return arg < 0


class TestExample(unittest.TestCase):

    def test_custom_equal(self):
        def my_equal(x, y):
            return abs(x - y) <= 1
        synthesizer = ExampleSynthesizer(
            enumerator=make_empty_enumerator(),
            interpreter=FooInterpreter(),
            examples=[
                Example(input=[2, 3], output=5)
            ],
            equal_output=my_equal
        )
        prog = builder.from_sexp_string('(mult (@param 0) (@param 1))')
        failed_examples = synthesizer.get_failed_examples(prog)
        self.assertEqual(len(failed_examples), 0)


class TestExampleConstraint(unittest.TestCase):

    @staticmethod
    def do_analyze(prog, examples):
        synthesizer = ExampleConstraintSynthesizer(
            enumerator=make_empty_enumerator(),
            interpreter=FooInterpreter(),
            spec=spec,
            examples=examples
        )
        return synthesizer.analyze(prog)

    def test_satisfied_concrete(self):
        prog = builder.from_sexp_string('(mult (@param 0) (@param 1))')
        res = self.do_analyze(
            prog,
            [Example(input=[1, -1], output=-1)]
        )
        self.assertTrue(res.is_ok())

    def test_satisfied_abstract(self):
        prog = builder.from_sexp_string('(mult (@param 0) (@param 1))')
        res = self.do_analyze(
            prog,
            [Example(input=[1, -1], output=-2)]
        )
        self.assertTrue(res.is_bad())
        reason = res.why()
        self.assertIsNone(reason)

    def test_violated_abstract(self):
        prog = builder.from_sexp_string('(mult (@param 0) (@param 1))')
        res = self.do_analyze(
            prog,
            [Example(input=[1, -1], output=2)]
        )
        self.assertTrue(res.is_bad())
        reason = res.why()
        self.assertIsNotNone(reason)
        self.assertIn([(prog, prog.production)], reason)

        # Failure of mult would imply that div also does not work
        div_prod = builder.get_function_production_or_raise('div')
        self.assertIn([(prog, div_prod)], reason)

    def test_violated_abstract2(self):
        prog = builder.from_sexp_string('(div (@param 0) (@param 1))')
        res = self.do_analyze(
            prog,
            [Example(input=[2, -1], output=2)]
        )
        self.assertTrue(res.is_bad())
        reason = res.why()
        self.assertIsNotNone(reason)
        self.assertIn([(prog, prog.production)], reason)

        # Failure of div would not imply that mult also does not work
        mult_prod = builder.get_function_production_or_raise('mult')
        self.assertNotIn([(prog, mult_prod)], reason)


if __name__ == '__main__':
    unittest.main()
