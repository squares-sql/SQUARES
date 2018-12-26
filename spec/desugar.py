from .spec import TypeSpec, ProductionSpec, ProgramSpec, TyrellSpec
from .type import Type, EnumType, ValueType
import logger
from .parser import Visitor_Recursive
from ast import literal_eval
from typing import List

logger = logger.get('tyrell.desugar')


class ParseTreeProcessingError(RuntimeError):
    pass


class TypeCollector(Visitor_Recursive):
    _spec: TypeSpec

    def __init__(self):
        self._spec = TypeSpec()

    def enum_decl(self, tree):
        name = str(tree.children[0])
        domain = [literal_eval(str(x)) for x in tree.children[1].children]
        self._spec.define_type(EnumType(name, domain))

    def value_decl(self, tree):
        name = tree.children[0]
        self._spec.define_type(ValueType(name))

    def collect(self) -> TypeSpec:
        return self._spec


class ProgramCollector(Visitor_Recursive):
    _type_spec: TypeSpec
    _name: str
    _input_tys: List[Type]
    _output_ty: Type

    def __init__(self, type_spec):
        self._type_spec = type_spec

    def program_decl(self, tree):
        self._name = str(tree.children[0])
        input_names = [str(x) for x in tree.children[1].children]
        output_name = str(tree.children[2])
        self._input_tys = [
            self._type_spec.get_type_or_raise(x) for x in input_names]
        self._output_ty = self._type_spec.get_type_or_raise(output_name)

    def collect(self) -> ProgramSpec:
        return ProgramSpec(name=self._name,
                           in_types=self._input_tys,
                           out_type=self._output_ty)


class ProductionCollecotr(Visitor_Recursive):
    _type_spec: TypeSpec
    _prod_spec: ProductionSpec

    def __init__(self, type_spec):
        self._type_spec = type_spec
        self._prod_spec = ProductionSpec()

    @staticmethod
    def _process_opt_arg(opt_arg):
        return str(opt_arg.children[0])

    def func_decl(self, tree):
        name = str(tree.children[0])
        tree_body = tree.children[1]
        lhs_name = self._process_opt_arg(tree_body.children[0])
        rhs_names = [self._process_opt_arg(x)
                     for x in tree_body.children[1].children]
        lhs = self._type_spec.get_type_or_raise(lhs_name)
        rhs = [self._type_spec.get_type_or_raise(x) for x in rhs_names]
        self._prod_spec.add_func_production(name=name, lhs=lhs, rhs=rhs)

    def collect(self) -> ProductionSpec:
        return self._prod_spec


def desugar(parse_tree):
    logger.debug('Building Tyrell spec from parse tree...')
    try:
        logger.debug('Processing type definitions...')
        type_collector = TypeCollector()
        type_collector.visit(parse_tree)
        type_spec = type_collector.collect()

        logger.debug('Processing input/output definitions...')
        prog_collector = ProgramCollector(type_spec)
        prog_collector.visit(parse_tree)
        prog_spec = prog_collector.collect()

        # Process function definitions
        logger.debug('Processing function definitions...')
        prod_collector = ProductionCollecotr(type_spec)
        prod_collector.visit(parse_tree)
        prod_spec = prod_collector.collect()

        return TyrellSpec(type_spec, prog_spec, prod_spec)
    except (KeyError, ValueError) as e:
        raise ParseTreeProcessingError(str(e))
