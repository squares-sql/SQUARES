from typing import Tuple, List, Iterator, Any
from .interpreter import Interpreter
from dsl import Node, AtomNode, ParamNode, ApplyNode
from visitor import GenericVisitor


class PostOrderInterpreter(Interpreter):

    def eval_step(self, prog: Node, inputs: List[Any]) -> Iterator[Tuple[Node, List[Any], Any]]:
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
                atom_value = method(atom_node.data)
                yield (atom_node, [], atom_value)

            def visit_param_node(self, param_node: ParamNode):
                param_index = param_node.index
                if param_index >= len(inputs):
                    msg = 'Input parameter access({}) out of bound({})'.format(
                        param_index, len(inputs))
                    raise InterpreterError(msg)
                yield (param_node, [], inputs[param_index])

            def visit_apply_node(self, apply_node: ApplyNode):
                in_values = []
                for child in apply_node.args:
                    for step in self.visit(child):
                        yield step
                    in_values.append(step[2])

                method_name = self._eval_method_name(apply_node.name)
                method = getattr(self._interp, method_name,
                                 self._method_not_found)
                out_value = method(apply_node, in_values)
                yield (apply_node, in_values, out_value)

            def _method_not_found(self, apply_node: ApplyNode, arg_values: List[Any]):
                msg = 'Cannot find required eval method: "{}"'.format(
                    self._eval_method_name(apply_node.name))
                raise NotImplementedError(msg)

            @staticmethod
            def _eval_method_name(name):
                return 'eval_' + name

        return NodeVisitor(self).visit(prog)
