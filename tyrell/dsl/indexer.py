from typing import List, Dict, Optional
from collections import deque
from .node import Node
from .iterator import bfs


class NodeIndexer:
    '''
    A utility class providing bidirectional mapping between AST Node and integer ID.
    '''

    _node_map: Dict[Node, int]
    _index_map: List[Node]

    def _add_node(self, node: Node):
        next_id = len(self._index_map)
        self._node_map[node] = next_id
        self._index_map.append(node)

    def __init__(self, prog: Node):
        self._node_map = dict()
        self._index_map = list()
        # Assign ID to nodes in BFS order
        for node in bfs(prog):
            self._add_node(node)

    def get_id(self, node: Node) -> Optional[int]:
        '''Get the ID of the node, or None if the node is not indexed.'''
        return self._node_map.get(node, None)

    def get_id_or_raise(self, node: Node) -> int:
        '''Get the ID of the node, or raise `KeyError` if the node is not indexed.'''
        return self._node_map[node]

    def get_node(self, nid: int) -> Optional[Node]:
        '''Get the Node which corresponds to the given ID, or None if the ID is not assigned.'''
        if nid >= 0 and nid < len(self._index_map):
            return self._index_map[nid]
        else:
            return None

    def get_node_or_raise(self, nid: int) -> Node:
        '''Get the Node which corresponds to the given ID, or raise `KeyError` if the ID is not assigned.'''
        res = self.get_node(nid)
        if res is None:
            raise KeyError('Node ID is not assigned: {}'.format(nid))
        return res

    @property
    def nodes(self) -> List[Node]:
        return self._index_map

    @property
    def num_nodes(self):
        return len(self._index_map)

    @property
    def indices(self) -> List[int]:
        return [x for x in range(len(self._index_map))]
