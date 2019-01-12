import unittest
from itertools import product
from .. import spec as S
from .. import dsl as D
from .post_order import PostOrderInterpreter
from .error import GeneralError


class BoolInterpreter(PostOrderInterpreter):
    def eval_BoolLit(self, data):
        if data == 'true':
            return True
        elif data == 'false':
            return False
        else:
            raise GeneralError(
                msg='Cannot evaluate bool literal: {}'.format(data))

    def eval_const(self, node, args):
        return args[0]

    def eval_not(self, node, args):
        return not args[0]

    def eval_and(self, node, args):
        return args[0] and args[1]

    def eval_or(self, node, args):
        return args[0] or args[1]

    def eval_assertTrue(self, node, args):
        if not args[0]:
            raise GeneralError(
                'Argument of assertTrue() does not evaluate to true: {}'.format(node))
        return True


spec_str = '''
    enum BoolLit {
      "false", "true"
    }
    value BoolExpr;

    program Bool(BoolExpr, BoolExpr) -> BoolExpr;
    func const: BoolExpr -> BoolLit;
    func and: BoolExpr -> BoolExpr, BoolExpr;
    func or: BoolExpr -> BoolExpr, BoolExpr;
    func not: BoolExpr -> BoolExpr;
    func assertTrue: BoolExpr -> BoolExpr;
'''
spec = S.parse(spec_str)


class TestSimpleInterpreter(unittest.TestCase):

    def setUp(self):
        self._builder = D.Builder(spec)
        self._interp = BoolInterpreter()
        self._domain = [False, True]

    def test_interpreter0(self):
        b = self._builder
        p0 = b.make_param(0)
        p1 = b.make_param(1)
        p = b.make_apply('and', [p0, p1])

        for x, y in product(self._domain, self._domain):
            out_value = self._interp.eval(p, [x, y])
            expect_value = x and y
            self.assertEqual(out_value, expect_value)

    def test_interpreter1(self):
        b = self._builder
        p = b.from_sexp_string(
            '(and (const (BoolLit "true")) (const (BoolLit "false")))')

        for x, y in product(self._domain, self._domain):
            out_value = self._interp.eval(p, [x, y])
            expect_value = False
            self.assertEqual(out_value, expect_value)

    def test_interpreter2(self):
        b = self._builder
        p0 = b.make_param(0)
        p1 = b.make_param(1)
        np0 = b.make_apply('not', [p0])
        p = b.make_apply('or', [np0, p1])

        for x, y in product(self._domain, self._domain):
            out_value = self._interp.eval(p, [x, y])
            expect_value = (not x) or y
            self.assertEqual(out_value, expect_value)

    def test_context(self):
        b = self._builder
        p0 = b.make_param(0)
        p1 = b.make_param(1)
        lit = b.make_enum('BoolLit', 'true')
        c = b.make_apply('const', [lit])
        ap0 = b.make_apply('assertTrue', [p0])
        acap0 = b.make_apply('and', [c, ap0])
        nacap0 = b.make_apply('not', [acap0])
        p = b.make_apply('or', [nacap0, p1])

        try:
            self._interp.eval(p, [False, True])
        except GeneralError as e:
            ctx = e.context
            self.assertIsNotNone(ctx)
            self.assertListEqual(ctx.stack, [p, nacap0, acap0])
            self.assertListEqual(
                ctx.observed, [p, nacap0, acap0, c, lit, ap0, p0])
            self.assertListEqual(ctx.evaluated, [lit, c, p0])


if __name__ == '__main__':
    unittest.main()
