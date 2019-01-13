from .synthesizer import Synthesizer
from ..interpreter import Interpreter
from ..enumerator import Enumerator
from ..spec import TyrellSpec


class InterpreterBasedSynthesizer(Synthesizer):
    '''
    A synthesizer that needs an additional interpreter
    '''
    _interpreter: Interpreter

    def __init__(self, spec: TyrellSpec, enumerator: Enumerator, interpreter: Interpreter):
        self._interpreter = interpreter
        super().__init__(spec, enumerator)

    @property
    def interpreter(self):
        return self._interpreter
