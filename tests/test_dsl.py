import unittest
import spec as S
import dsl as D


class TestDSL(unittest.TestCase):

    def setUp(self):
        type_spec = S.TypeSpec()
        self._vty0 = type_spec.define_type(S.ValueType('VType0'))
        self._vty1 = type_spec.define_type(S.ValueType('VType1'))
        self._ety0 = type_spec.define_type(
            S.EnumType('EType0', ['e0', 'e1']))

        prod_spec = S.ProductionSpec()
        self._prod0 = prod_spec.add_enum_production(self._ety0, choice=0)
        self._prod1 = prod_spec.add_param_production(self._vty0, index=0)
        self._prod2 = prod_spec.add_func_production(
            name='f', lhs=self._vty1, rhs=[self._ety0, self._vty0])

        prog_spec = S.ProgramSpec(
            name='test', in_types=[self._vty0], out_type=self._vty1)

        self._spec = S.TyrellSpec(type_spec, prog_spec, prod_spec)

    def test_node(self):
        node0 = D.AtomNode(self._prod0)
        self.assertEqual(node0.data, 'e0')
        self.assertEqual(node0.type, self._ety0)
        node1 = D.ParamNode(self._prod1)
        self.assertEqual(node1.index, 0)
        self.assertEqual(node1.type, self._vty0)
        node2 = D.ApplyNode(self._prod2, [node0, node1])
        self.assertEqual(node2.name, 'f')
        self.assertEqual(node2.type, self._vty1)

    def test_builder(self):
        builder = D.Builder(self._spec)

        node0 = builder.make_node(self._prod0.id)
        self.assertEqual(node0.data, 'e0')
        self.assertEqual(node0.type, self._ety0)

        node1 = builder.make_node(self._prod1)
        self.assertEqual(node1.index, 0)
        self.assertEqual(node1.type, self._vty0)

        node2 = builder.make_node(self._prod2, children=[node0, node1])
        self.assertEqual(node2.name, 'f')
        self.assertEqual(node2.type, self._vty1)


if __name__ == '__main__':
    unittest.main()
