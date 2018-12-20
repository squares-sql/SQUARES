from typing import List, Any
import production

class Node(object):

    id: int = None

    symbol: str = None

    component: int = None

    children: List[Node] = None

    decision: Production = None
