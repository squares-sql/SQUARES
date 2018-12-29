from dsl import Node, AtomNode, ParamNode, ApplyNode
from visitor import GenericVisitor
from abc import ABC, abstractmethod
from typing import Tuple, List, Iterator, Any


class InterpreterError(RuntimeError):
    pass


class Interpreter(ABC):

    @abstractmethod
    def eval(self, prog: Node, inputs: List[Any]) -> Any:
        '''
        This is the main API for the interpreter module.

        This method is expected to evaluate a DSL `prog` on input `inputs`, and return the output.
        It is also expected that this method would raise `InterpreterError` when error occurs during the interpretation.
        '''
        raise NotImplementedError


class PostOrderInterpreter(Interpreter):

    def eval(self, prog: Node, inputs: List[Any]) -> Any:
        '''
        Interpret the Given AST in post-order. Assumes the existence of `eval_XXX` method where `XXX` is the name of a function defined in the DSL.
        '''
        class NodeVisitor(GenericVisitor):
            _interp: PostOrderInterpreter

            def __init__(self, interp):
                self._interp = interp

            def visit_atom_node(self, atom_node: AtomNode):

                method_name = self._eval_method_name(atom_node.type.name)
                method = getattr(self._interp, method_name, lambda x: x.data)
                return method(atom_node.data)

            def visit_param_node(self, param_node: ParamNode):
                param_index = param_node.index
                if param_index >= len(inputs):
                    msg = 'Input parameter access({}) out of bound({})'.format(
                        param_index, len(inputs))
                    raise InterpreterError(msg)
                return inputs[param_index]

            def visit_apply_node(self, apply_node: ApplyNode):
                in_values = [self.visit(x) for x in apply_node.args]
                method_name = self._eval_method_name(apply_node.name)
                method = getattr(self._interp, method_name,
                                 self._method_not_found)
                return method(apply_node, in_values)

            def _method_not_found(self, apply_node: ApplyNode, arg_values: List[Any]):
                msg = 'Cannot find required eval method: "{}"'.format(
                    self._eval_method_name(apply_node.name))
                raise InterpreterError(msg)

            @staticmethod
            def _eval_method_name(name):
                return 'eval_' + name

        return NodeVisitor(self).visit(prog)
