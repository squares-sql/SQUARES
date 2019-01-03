import unittest
from spec import parse
from dsl import Builder
from enumerator import make_empty_enumerator
from interpreter import PostOrderInterpreter
from .example_base import Example
from .example_constraint import ExampleConstraintSynthesizer


spec_str = r'''
    value IntExpr {
        pos: bool;
        neg: bool;
    }

    program Foo(IntExpr, IntExpr) -> IntExpr;
    func mult: IntExpr r -> IntExpr a, IntExpr b {
        pos(a) && neg(b) ==> neg(r);
        pos(b) && neg(a) ==> neg(r);
    }
'''
builder = Builder(parse(spec_str))


class FooInterpreter(PostOrderInterpreter):
    def eval_mult(self, node, args):
        return args[0] * args[1]

    def apply_pos(self, arg):
        return arg > 0

    def apply_neg(self, arg):
        return arg < 0


class TestExampleConstraint(unittest.TestCase):

    @staticmethod
    def do_analyze(prog, examples):
        synthesizer = ExampleConstraintSynthesizer(
            enumerator=make_empty_enumerator(),
            interpreter=FooInterpreter(),
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


if __name__ == '__main__':
    unittest.main()
