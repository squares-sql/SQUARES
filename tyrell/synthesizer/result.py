from abc import ABC, abstractmethod
from typing import Any


class Result(ABC):

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def is_ok(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def why(self) -> Any:
        raise NotImplementedError

    def is_bad(self) -> bool:
        return not self.is_ok()


class OkResult(Result):
    def __init__(self):
        super().__init__()

    def is_ok(self) -> bool:
        return True

    def why(self):
        return None


class BadResult(Result):
    _why: Any

    def __init__(self, why):
        super().__init__()
        self._why = why

    def is_ok(self) -> bool:
        return False

    def why(self):
        return self._why


def ok() -> OkResult:
    return OkResult()


def bad(why=None) -> BadResult:
    return BadResult(why)
