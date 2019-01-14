import unittest
from .. import spec as S
from .node import AtomNode, ParamNode, ApplyNode
from .builder import Builder
from .iterator import bfs, dfs
from .indexer import NodeIndexer
from .parent_finder import ParentFinder


class TestDSL(unittest.TestCase):

    def setUp(self):
        type_spec = S.TypeSpec()
        self._vty0 = type_spec.define_type(S.ValueType('VType0'))
        self._vty1 = type_spec.define_type(S.ValueType('VType1'))
        self._ety0 = type_spec.define_type(
            S.EnumType('EType0', ['e0', 'e1']))

        prod_spec = S.ProductionSpec()
        self._prod0 = prod_spec.add_enum_production(self._ety0, choice=0)
        self._prod2 = prod_spec.add_func_production(
            name='f', lhs=self._vty1, rhs=[self._ety0, self._vty0])
        self._prod3 = prod_spec.add_func_production(
            name='g', lhs=self._vty1, rhs=[self._vty1, self._ety0]
        )

        prog_spec = S.ProgramSpec(
            name='test', in_types=[self._vty0], out_type=self._vty1)

        self._spec = S.TyrellSpec(type_spec, prog_spec, prod_spec)
        self._prod1 = self._spec.get_param_production_or_raise(0)

    def test_node(self):
        node0 = AtomNode(self._prod0)
        self.assertEqual(node0.data, 'e0')
        self.assertEqual(node0.type, self._ety0)
        node1 = ParamNode(self._prod1)
        self.assertEqual(node1.index, 0)
        self.assertEqual(node1.type, self._vty0)
        node2 = ApplyNode(self._prod2, [node0, node1])
        self.assertEqual(node2.name, 'f')
        self.assertEqual(node2.type, self._vty1)

        node0_dup = AtomNode(self._prod0)
        self.assertNotEqual(node0, node0_dup)
        self.assertTrue(node0.deep_eq(node0_dup))
        self.assertTrue(node0_dup.deep_eq(node0))
        self.assertEqual(node0.deep_hash(), node0_dup.deep_hash())
        node1_dup = ParamNode(self._prod1)
        self.assertNotEqual(node1, node1_dup)
        self.assertTrue(node1.deep_eq(node1_dup))
        self.assertTrue(node1_dup.deep_eq(node1))
        self.assertEqual(node1.deep_hash(), node1_dup.deep_hash())
        node2_dup = ApplyNode(self._prod2, [node0_dup, node1_dup])
        self.assertNotEqual(node2, node2_dup)
        self.assertTrue(node2.deep_eq(node2_dup))
        self.assertTrue(node2_dup.deep_eq(node2))
        self.assertEqual(node2.deep_hash(), node2_dup.deep_hash())

    def test_builder_low_level_apis(self):
        builder = Builder(self._spec)

        node0 = builder.make_node(self._prod0.id)
        self.assertEqual(node0.data, 'e0')
        self.assertEqual(node0.type, self._ety0)

        node1 = builder.make_node(self._prod1)
        self.assertEqual(node1.index, 0)
        self.assertEqual(node1.type, self._vty0)

        node2 = builder.make_node(self._prod2, children=[node0, node1])
        self.assertEqual(node2.name, 'f')
        self.assertEqual(node2.type, self._vty1)

    def test_builder_high_level_apis(self):
        builder = Builder(self._spec)

        node0 = builder.make_enum('EType0', 'e0')
        self.assertEqual(node0.type, self._ety0)
        self.assertEqual(node0.data, 'e0')
        with self.assertRaises(KeyError):
            builder.make_enum('NotAType', 'e0')
        with self.assertRaises(KeyError):
            builder.make_enum('VType0', 'e0')
        with self.assertRaises(KeyError):
            builder.make_enum("EType0", "NotAValue")

        node1 = builder.make_param(0)
        self.assertEqual(node1.type, self._vty0)
        self.assertEqual(node1.index, 0)
        with self.assertRaises(KeyError):
            builder.make_param(1)

        node2 = builder.make_apply('f', [node0, node1])
        self.assertEqual(node2.name, 'f')
        self.assertListEqual(node2.args, [node0, node1])
        with self.assertRaises(KeyError):
            builder.make_apply('h', [])
        with self.assertRaises(ValueError):
            builder.make_apply('f', [])

    def test_iterator(self):
        builder = Builder(self._spec)
        node0 = builder.make_enum('EType0', 'e0')
        node1 = builder.make_param(0)
        node2 = builder.make_apply('f', [node0, node1])
        node3 = builder.make_enum('EType0', 'e1')
        node4 = builder.make_apply('g', [node2, node3])

        bfs_res = [x for x in bfs(node4)]
        self.assertListEqual(bfs_res, [node4, node2, node3, node0, node1])

        dfs_res = [x for x in dfs(node4)]
        self.assertListEqual(dfs_res, [node4, node2, node0, node1, node3])

    def test_node_indexer(self):
        builder = Builder(self._spec)
        node0 = builder.make_enum('EType0', 'e0')
        node1 = builder.make_param(0)
        node2 = builder.make_apply('f', [node0, node1])

        indexer = NodeIndexer(node2)
        self.assertEqual(indexer.num_nodes, 3)
        self.assertSetEqual(set(indexer.nodes), set([node0, node1, node2]))
        self.assertSetEqual(set(indexer.indices), set([x for x in range(3)]))

        id0 = indexer.get_id(node0)
        self.assertIsNotNone(id0)
        id1 = indexer.get_id(node1)
        self.assertIsNotNone(id1)
        id2 = indexer.get_id(node2)
        self.assertIsNotNone(id2)
        extra_node = builder.make_enum('EType0', 'e1')
        self.assertIsNone(indexer.get_id(extra_node))
        with self.assertRaises(KeyError):
            indexer.get_id_or_raise(extra_node)

        self.assertIs(indexer.get_node(id0), node0)
        self.assertIs(indexer.get_node(id1), node1)
        self.assertIs(indexer.get_node(id2), node2)
        invalid_id = 1 + id0 + id1 + id2
        self.assertIsNone(indexer.get_node(invalid_id))
        with self.assertRaises(KeyError):
            indexer.get_node_or_raise(invalid_id)

    def test_parent_finder(self):
        builder = Builder(self._spec)
        node0 = builder.make_enum('EType0', 'e0')
        node1 = builder.make_param(0)
        node2 = builder.make_apply('f', [node0, node1])

        pfinder = ParentFinder(node2)
        self.assertIsNone(pfinder.get_parent(node2))
        with self.assertRaises(KeyError):
            pfinder.get_parent_or_raise(node2)
        self.assertIs(pfinder.get_parent(node1), node2)
        self.assertIs(pfinder.get_parent(node0), node2)

        extra_node = builder.make_enum('EType0', 'e1')
        self.assertIsNone(pfinder.get_parent(extra_node))
        with self.assertRaises(KeyError):
            pfinder.get_parent_or_raise(extra_node)


if __name__ == '__main__':
    unittest.main()
