from abc import ABC, abstractmethod


class GenericVisitor(ABC):

    @abstractmethod
    def visit(self, node):
        method_name = self._visit_method_name(node)
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        raise Exception(
            '{}: No {} method'.format(
                type(self).__name__,
                self._visit_method_name(node)))

    def _visit_method_name(node):
        return 'visit_' + type(node).__name__.lower()
