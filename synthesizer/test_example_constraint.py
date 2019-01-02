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

    def test_example_violated(self):
        examples = [Example(input=[1, -1], output=2)]
        synthesizer = ExampleConstraintSynthesizer(
            enumerator=make_empty_enumerator(),
            interpreter=FooInterpreter(),
            examples=examples
        )
        prog = builder.from_sexp_string('(mult (@param 0) (@param 1))')

        # The given program should fail the example test
        self.assertListEqual(
            synthesizer.get_failed_examples(prog), examples)

        res = synthesizer.analyze(prog)
        self.assertTrue(res.is_bad())
        reason = res.why()
        # TODO: check that the reason matches our expectation


if __name__ == '__main__':
    unittest.main()
