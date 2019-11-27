import unittest
from .type import EnumType, ValueType
from .spec import TypeSpec, ProductionSpec, PredicateSpec


class TestTyrellSpec(unittest.TestCase):

    def test_type(self):
        ty0 = EnumType('Type0')
        ty1 = ValueType('Type1')
        spec = TypeSpec()
        spec.define_type(ty0)
        spec.define_type(ty1)
        self.assertEqual(spec.get_type('Type0'), ty0)
        self.assertEqual(spec.get_type('Type1'), ty1)
        self.assertEqual(spec.get_type_or_raise('Type0'), ty0)
        self.assertEqual(spec.get_type_or_raise('Type1'), ty1)
        self.assertIsNone(spec.get_type('Type2'))
        with self.assertRaises(KeyError):
            spec.get_type_or_raise('Type2')
        with self.assertRaises(ValueError):
            spec.define_type(ty0)

    def test_production(self):
        ty0 = EnumType('Type0')
        ty1 = ValueType('Type1')
        spec = ProductionSpec()
        prod0 = spec.add_func_production(name='base', lhs=ty1, rhs=[ty0])
        prod1 = spec.add_func_production(name='rec', lhs=ty1, rhs=[ty0, ty1])
        self.assertEqual(spec.get_production(prod0.id), prod0)
        self.assertEqual(spec.get_production(prod1.id), prod1)
        self.assertEqual(spec.get_production_or_raise(prod0.id), prod0)
        self.assertEqual(spec.get_production_or_raise(prod1.id), prod1)

        fake_id = prod0.id + prod1.id + 1
        self.assertIsNone(spec.get_production(fake_id))
        with self.assertRaises(KeyError):
            spec.get_production_or_raise(fake_id)

        prods = spec.get_productions_with_lhs(ty1)
        self.assertListEqual(prods, [prod0, prod1])
        self.assertListEqual(spec.get_productions_with_lhs('NotAType'), [])

        # TyrellSpec will *NOT* try to uniquify productions
        self.assertEqual(len(list(spec.productions())), 2)
        spec.add_func_production(name='base2', lhs=ty1, rhs=[ty0])
        self.assertEqual(len(list(spec.productions())), 3)

    def test_predicate(self):
        spec = PredicateSpec()
        pred0 = spec.add_predicate('f', ['abc', 3, False])
        pred1 = spec.add_predicate('g', [2.5])
        pred2 = spec.add_predicate('f', ['def', 4, True])

        preds = spec.predicates()
        self.assertEqual(len(preds), 3)
        self.assertIn(pred0, preds)
        self.assertIn(pred1, preds)
        self.assertIn(pred2, preds)

        f_preds = spec.get_predicates_with_name('f')
        self.assertEqual(len(f_preds), 2)
        self.assertIn(pred0, f_preds)
        self.assertIn(pred2, f_preds)

        g_preds = spec.get_predicates_with_name('g')
        self.assertEqual(len(g_preds), 1)
        self.assertIn(pred1, g_preds)

        h_preds = spec.get_predicates_with_name('h')
        self.assertEqual(len(h_preds), 0)


if __name__ == '__main__':
    unittest.main()
