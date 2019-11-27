import unittest
from ..spec import parse
from ..dsl import Builder
from ..interpreter import PostOrderInterpreter, AssertionViolation
from .assert_violation_handler import AssertionViolationHandler
from .blame import Blame

spec_str = r'''
    enum SmallInt {
        "-3", "-2", "2", "3"
    }
    value IntExpr;

    program Foo() -> IntExpr;
    func const: IntExpr -> SmallInt;
    func sqrt: IntExpr -> SmallInt;
    func id: IntExpr -> IntExpr;
    func idiv: IntExpr -> IntExpr, SmallInt;
'''
spec = parse(spec_str)
builder = Builder(spec)


class FooInterpreter(PostOrderInterpreter):
    def eval_SmallInt(self, s):
        return int(s)

    def eval_const(self, node, args):
        return args[0]

    def eval_sqrt(self, node, args):
        self.assertArg(node, args, 0, lambda x: x >= 0)
        return int(args[0] ** 0.5)

    def eval_idiv(self, node, args):
        self.assertArg(node, args,
                       index=1,
                       cond=lambda x: args[0] % x == 0,
                       capture_indices=[0])
        return args[0] / args[1]

    def eval_id(self, node, args):
        return args[0]


class TestTypeErrorHandler(unittest.TestCase):

    def test_blame(self):
        enode0 = builder.make_enum('SmallInt', '-3')
        enode1 = builder.make_enum('SmallInt', '-2')
        snode = builder.make_apply('sqrt', [enode0])
        inode = builder.make_apply('id', [snode])

        interp = FooInterpreter()
        handler = AssertionViolationHandler(spec, interp)

        with self.assertRaises(AssertionViolation) as cm:
            interp.eval(inode, [])
        type_error = cm.exception
        blames = handler.handle_interpreter_error(type_error)
        self.assertIsNotNone(blames)
        self.assertEqual(len(blames), 2)
        for blame in blames:
            self.assertNotIn(Blame(inode, inode.production), blame)
            self.assertIn(Blame(snode, snode.production), blame)
            self.assertTrue(
                (Blame(enode0, enode0.production) in blame) or
                (Blame(enode0, enode1.production) in blame)
            )

    def test_blame_with_capture(self):
        enode0 = builder.make_enum('SmallInt', '-2')
        cnode = builder.make_apply('const', [enode0])
        enode1 = builder.make_enum('SmallInt', '-3')
        enode2 = builder.make_enum('SmallInt', '3')
        dnode = builder.make_apply('idiv', [cnode, enode1])

        interp = FooInterpreter()
        handler = AssertionViolationHandler(spec, interp)

        with self.assertRaises(AssertionViolation) as cm:
            interp.eval(dnode, [])
        type_error = cm.exception
        blames = handler.handle_interpreter_error(type_error)
        self.assertIsNotNone(blames)
        self.assertEqual(len(blames), 2)
        for blame in blames:
            self.assertIn(Blame(dnode, dnode.production), blame)
            self.assertTrue(
                (Blame(enode1, enode1.production) in blame) or
                (Blame(enode1, enode2.production) in blame)
            )
            # These nodes are captured in our assertion
            self.assertIn(Blame(cnode, cnode.production), blame)
            self.assertIn(Blame(enode0, enode0.production), blame)


if __name__ == '__main__':
    unittest.main()
