import unittest
import itertools
import spec as S
import dsl as D
from interpreter import PostOrderInterpreter, InterpreterError


class BoolInterpreter(PostOrderInterpreter):
    def eval_BoolLit(self, data):
        if data == 'true':
            return True
        elif data == 'false':
            return False
        else:
            raise InterpreterError(
                'Cannot evaluate bool literal: {}'.format(data))

    def eval_const(self, node, args):
        return args[0]

    def eval_not(self, node, args):
        return not args[0]

    def eval_and(self, node, args):
        return args[0] and args[1]

    def eval_or(self, node, args):
        return args[0] or args[1]


# It seems that the generated Lark parser is not reentrant...
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

        for x, y in itertools.product(self._domain, self._domain):
            out_value = self._interp.eval(p, [x, y])
            expect_value = x and y
            self.assertEqual(out_value, expect_value)

    def test_interpreter1(self):
        b = self._builder
        p = b.from_sexp_string(
            '(and (const (BoolLit "true")) (const (BoolLit "false")))')

        for x, y in itertools.product(self._domain, self._domain):
            out_value = self._interp.eval(p, [x, y])
            expect_value = False
            self.assertEqual(out_value, expect_value)

    def test_interpreter2(self):
        b = self._builder
        p0 = b.make_param(0)
        p1 = b.make_param(1)
        np0 = b.make_apply('not', [p0])
        p = b.make_apply('or', [np0, p1])

        for x, y in itertools.product(self._domain, self._domain):
            out_value = self._interp.eval(p, [x, y])
            expect_value = (not x) or y
            self.assertEqual(out_value, expect_value)


if __name__ == '__main__':
    unittest.main()
