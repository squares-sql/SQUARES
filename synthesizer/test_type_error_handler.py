import unittest
from spec import parse
from dsl import Builder
from enumerator import make_empty_enumerator
from interpreter import PostOrderInterpreter, AssertionViolation
from .assert_violation_handler import AssertionViolationHandler
from .example_constraint import Blame
from .result import ok

spec_str = r'''
    enum SmallInt {
        "-2", "-1", "0", "1", "2"
    }
    value IntExpr;

    program Foo() -> IntExpr;
    func sqrt: IntExpr -> SmallInt;
    func id: IntExpr -> IntExpr;
'''
spec = parse(spec_str)
builder = Builder(spec)


class FooInterpreter(PostOrderInterpreter):
    def eval_SmallInt(self, s):
        return int(s)

    def eval_sqrt(self, node, args):
        self.assertArg(node, args, 0, lambda x: x >= 0)
        return int(args[0] ** 0.5)

    def eval_id(self, node, args):
        return args[0]


class FooSynthesizer(AssertionViolationHandler):

    # A dummy implementation
    def analyze(self, ast):
        return ok()


class TestTypeErrorHandler(unittest.TestCase):

    def test_blame(self):
        enode0 = builder.make_enum('SmallInt', '-1')
        enode1 = builder.make_enum('SmallInt', '-2')
        snode = builder.make_apply('sqrt', [enode0])
        inode = builder.make_apply('id', [snode])

        interp = FooInterpreter()
        handler = FooSynthesizer(
            spec=spec,
            enumerator=make_empty_enumerator(),
            interpreter=interp
        )

        with self.assertRaises(AssertionViolation) as cm:
            interp.eval(inode, [])
        type_error = cm.exception
        blames = handler.analyze_interpreter_error(type_error)
        self.assertIsNotNone(blames)
        self.assertEqual(len(blames), 2)
        for blame in blames:
            self.assertNotIn(Blame(inode, inode.production), blame)
            self.assertIn(Blame(snode, snode.production), blame)
            self.assertTrue(
                (Blame(enode0, enode0.production) in blame) or
                (Blame(enode0, enode1.production) in blame)
            )


if __name__ == '__main__':
    unittest.main()
