from abc import ABC, abstractmethod
import re

first_cap_re = re.compile('(.)([A-Z][a-z]+)')
all_cap_re = re.compile('([a-z0-9])([A-Z])')


def camel_to_snake_case(name: str) -> str:
    s1 = first_cap_re.sub(r'\1_\2', name)
    return all_cap_re.sub(r'\1_\2', s1).lower()


class GenericVisitor(ABC):

    @abstractmethod
    def __init__(self):
        pass

    def visit(self, node):
        method_name = self._visit_method_name(node)
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        raise Exception(
            '{}: No {} method'.format(
                type(self).__name__,
                self._visit_method_name(node)))

    @staticmethod
    def _visit_method_name(node) -> str:
        return 'visit_' + camel_to_snake_case(type(node).__name__)
