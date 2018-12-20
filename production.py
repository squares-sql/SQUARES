from typing import List
from typing import Any

class Production(object):

    id: int = -1

    higher: bool = False

    function: str = None

    source: Any = None

    inputs: List[Any] = None

    def __init__(self, src: Any, function: str, inputs: List[Any]):
        self.source = src;
        self.function = function;
        self.inputs = inputs;
        self.higher = false;
