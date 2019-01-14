import unittest
from ..spec import parse
from ..interpreter import PostOrderInterpreter
from .eval_expr import eval_expr

spec_str = r'''
    value IntExpr {
        bprop: bool;
        iprop: int;
    }

    program Foo(IntExpr, IntExpr) -> IntExpr;
    func foo: IntExpr r -> IntExpr a, IntExpr b {
        true;
        false;
        true && false;
        true || false;
        !true;
        bprop(a);
        bprop(a) && bprop(b);
        bprop(a) || bprop(b);
        bprop(a) ==> bprop(r);
        !bprop(a);
        1 == 1;
        false != true;
        iprop(a) < iprop(b);
        iprop(a) <= iprop(b);
        iprop(a) > iprop(b);
        iprop(a) >= iprop(b);
        iprop(a) + iprop(b) == 1;
        iprop(a) - iprop(b) == 1;
        iprop(a) * iprop(b) == 1;
        iprop(a) / iprop(b) == 1;
        iprop(a) % iprop(b) == 1;
        # Parens are necessary to avoid ambiguities
        1 == (if bprop(r) then iprop(a) else iprop(b));
    }
'''
spec = parse(spec_str)


class FooInterpreter(PostOrderInterpreter):
    def eval_foo(self, node, args):
        return args[0] + args[1]

    def apply_bprop(self, arg):
        return arg % 2 == 0

    def apply_iprop(self, arg):
        return arg


class TestEvalExpr(unittest.TestCase):
    def test_eval_expr(self):
        prod = spec.get_function_production_or_raise('foo')
        constraints = prod.constraints

        in_values = [2, 1]
        out_value = 3
        expect_outs = [
            True,  # true;
            False,  # false;
            False,  # true && false;
            True,  # true || false;
            False,  # !true;
            True,  # bprop(a);
            False,  # bprop(a) && bprop(b);
            True,  # bprop(a) || bprop(b);
            False,  # bprop(a) ==> bprop(r);
            False,  # !bprop(a);
            True,  # 1 == 1;
            True,  # false != true;
            False,  # iprop(a) < iprop(b);
            False,  # iprop(a) <= iprop(b);
            True,  # iprop(a) > iprop(b);
            True,  # iprop(a) >= iprop(b);
            False,  # iprop(a) + iprop(b) == 1;
            True,  # iprop(a) - iprop(b) == 1;
            False,  # iprop(a) * iprop(b) == 1;
            False,  # iprop(a) / iprop(b) == 1;
            False,  # iprop(a) % iprop(b) == 1;
            True  # 1 == if bprop(r) then iprop(a) else iprop(b);
        ]
        self.assertEqual(len(constraints), len(expect_outs))

        interp = FooInterpreter()
        for constraint, expect in zip(constraints, expect_outs):
            actual = eval_expr(interp, in_values, out_value, constraint)
            self.assertEqual(actual, expect)


if __name__ == '__main__':
    unittest.main()
