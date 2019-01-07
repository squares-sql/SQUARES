from typing import Tuple, List, Iterator, Any
from dsl import Node, AtomNode, ParamNode, ApplyNode
from visitor import GenericVisitor
from .interpreter import Interpreter


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
                    raise GeneralError(msg)
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
                raise NotImplementedError(msg)

            @staticmethod
            def _eval_method_name(name):
                return 'eval_' + name

        return NodeVisitor(self).visit(prog)
