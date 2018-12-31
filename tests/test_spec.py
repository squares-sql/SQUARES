import unittest
import spec as S


class TestTyrellSpec(unittest.TestCase):

    def test_type(self):
        ty0 = S.EnumType('Type0')
        ty1 = S.ValueType('Type1')
        spec = S.TypeSpec()
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
        ty0 = S.EnumType('Type0')
        ty1 = S.ValueType('Type1')
        spec = S.ProductionSpec()
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


if __name__ == '__main__':
    unittest.main()
