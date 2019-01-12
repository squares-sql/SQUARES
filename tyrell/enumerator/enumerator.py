from abc import ABC, abstractmethod
from typing import Optional, Any
from ..dsl import Node


class Enumerator(ABC):

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def next(self) -> Optional[Node]:
        '''
        The main API for this class. Subclasses are required to override this method.
        Enumerate the next AST, or return `None` if all ASTs has been enumerated.
        '''
        raise NotImplementedError

    def update(self, info: Any=None) -> None:
        '''
        Update the internal state of the enumerator. This can be useful when trying to prune the search space.
        By default, it does nothing.
        '''
        pass
