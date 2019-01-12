from typing import Tuple, List, Iterator, Any
from ..dsl import Node, AtomNode, ParamNode, ApplyNode
from ..visitor import GenericVisitor
from .interpreter import Interpreter
from .context import Context
from .error import InterpreterError, GeneralError


class PostOrderInterpreter(Interpreter):

    def eval(self, prog: Node, inputs: List[Any]) -> Any:
        '''
        Interpret the Given AST in post-order. Assumes the existence of `eval_XXX` method where `XXX` is the name of a function defined in the DSL.
        '''
        class NodeVisitor(GenericVisitor):
            _interp: PostOrderInterpreter
            _context: Context

            def __init__(self, interp):
                self._interp = interp
                self._context = Context()

            def visit_with_context(self, node: Node):
                self._context.observe(node)
                res = self.visit(node)
                self._context.finish(node)
                return res

            def visit_atom_node(self, atom_node: AtomNode):
                method_name = self._eval_method_name(atom_node.type.name)
                method = getattr(self._interp, method_name, lambda x: x)
                return method(atom_node.data)

            def visit_param_node(self, param_node: ParamNode):
                param_index = param_node.index
                if param_index >= len(inputs):
                    msg = 'Input parameter access({}) out of bound({})'.format(
                        param_index, len(inputs))
                    raise GeneralError(msg)
                return inputs[param_index]

            def visit_apply_node(self, apply_node: ApplyNode):
                in_values = [self.visit_with_context(
                    x) for x in apply_node.args]
                self._context.pop()
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

        node_visitor = NodeVisitor(self)
        try:
            return node_visitor.visit_with_context(prog)
        except InterpreterError as e:
            e.context = node_visitor._context
            raise e from None
