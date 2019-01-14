from abc import ABC, abstractmethod
from typing import Any
from ..interpreter import InterpreterError
from ..enumerator import Enumerator
from ..decider import Decider
from ..dsl import Node
from ..logger import get_logger

logger = get_logger('tyrell.synthesizer')


class Synthesizer(ABC):

    _enumerator: Enumerator
    _decider: Decider

    def __init__(self, enumerator: Enumerator, decider: Decider):
        self._enumerator = enumerator
        self._decider = decider

    @property
    def enumerator(self):
        return self._enumerator

    @property
    def decider(self):
        return self._decider

    def synthesize(self):
        '''
        A convenient method to enumerate ASTs until the result passes the analysis.
        Returns the synthesized program, or `None` if the synthesis failed.
        '''
        num_attempts = 0
        prog = self._enumerator.next()
        while prog is not None:
            num_attempts += 1
            logger.debug('Enumerator generated: {}'.format(prog))
            try:
                res = self._decider.analyze(prog)
                if res.is_ok():
                    logger.debug(
                        'Program accepted after {} attempts'.format(num_attempts))
                    return prog
                else:
                    info = res.why()
                    logger.debug('Program rejected. Reason: {}'.format(info))
                    self._enumerator.update(info)
                    prog = self._enumerator.next()
            except InterpreterError as e:
                info = self._decider.analyze_interpreter_error(e)
                logger.debug('Interpreter failed. Reason: {}'.format(info))
                self._enumerator.update(info)
                prog = self._enumerator.next()
        logger.debug(
            'Enumerator is exhausted after {} attempts'.format(num_attempts))
        return None
