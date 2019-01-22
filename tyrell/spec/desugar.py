from ast import literal_eval
from typing import List, cast
from .spec import TypeSpec, ProductionSpec, ProgramSpec, PredicateSpec, TyrellSpec
from .type import Type, EnumType, ValueType
from .expr import *
from .parser import Visitor_Recursive
from .util import enum_set_domain
from ..logger import get_logger

logger = get_logger('tyrell.desugar')


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

    def enum_set_decl(self, tree):
        name = str(tree.children[0])
        max_len = int(tree.children[1])
        domain = [literal_eval(str(x)) for x in tree.children[2].children]
        self._spec.define_type(
            EnumType(name, enum_set_domain(domain, max_len)))

    def _process_properties(self, items):
        ret = []
        for item in items:
            pname = str(item.children[0])
            ptype_name = str(item.children[1].data)
            if ptype_name == 'expr_bool':
                ptype = ExprType.BOOL
            elif ptype_name == 'expr_int':
                ptype = ExprType.INT
            else:
                msg = 'Unknown property type: {}'.format(ptype_name)
                raise ParseTreeProcessingError(msg)
            ret.append((pname, ptype))
        return ret

    def value_decl(self, tree):
        name = tree.children[0]
        properties = self._process_properties(tree.children[1].children)
        try:
            self._spec.define_type(ValueType(name, properties))
        except ValueError as e:
            # Handle duplicated property name
            raise ParseTreeProcessingError('{}'.format(e))

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


class ProductionCollector(Visitor_Recursive):
    _type_spec: TypeSpec
    _prod_spec: ProductionSpec

    def __init__(self, type_spec):
        self._type_spec = type_spec
        self._prod_spec = ProductionSpec()

    @staticmethod
    def _process_opt_arg(opt_arg):
        return str(opt_arg.children[0])

    @staticmethod
    def _create_index_map(opt_args):
        ret = dict()
        for index, opt_arg in enumerate(opt_args):
            if len(opt_arg.children) > 1:
                var_name = str(opt_arg.children[1])
                ret[var_name] = index
        return ret

    @staticmethod
    def _create_type_map(types):
        ret = dict()
        for index, ty in enumerate(types):
            ret[index] = ty
        return ret

    def _process_expr(self, index_map, type_map, tree):
        expr_kind = str(tree.data)
        if expr_kind == 'expr_false':
            return ConstExpr(False)
        elif expr_kind == 'expr_true':
            return ConstExpr(True)
        elif expr_kind == 'expr_intlit':
            value = int(tree.children[0])
            return ConstExpr(value)
        elif expr_kind == 'expr_var':
            name = str(tree.children[0])
            index = index_map.get(name, None)
            if index is None:
                raise ValueError(
                    'Cannot find parameter binding for variable "{}"'.format(name))
            return ParamExpr(index)
        elif expr_kind == 'property_expr':
            name = str(tree.children[0])
            arg = cast(ParamExpr, self._process_expr(
                index_map, type_map, tree.children[1]))
            param_ty = cast(ValueType, type_map[arg.index])
            param_ety = param_ty.get_property(name)
            if param_ety is None:
                raise ValueError(
                    'Cannot find property {} for type {}'.format(name, param_ty))
            return PropertyExpr(name, param_ety, arg)
        elif expr_kind == 'unary_expr':
            operand = self._process_expr(index_map, type_map, tree.children[1])
            operator = str(tree.children[0].data)
            if operator == 'expr_neg':
                operator = UnaryOperator.NEG
            elif operator == 'expr_not':
                operator = UnaryOperator.NOT
            else:
                raise ValueError(
                    'Unrecognized unary operator: {}'.format(operator))
            return UnaryExpr(operator, operand)
        elif expr_kind == 'factor_expr':
            lhs = self._process_expr(index_map, type_map, tree.children[0])
            operator = str(tree.children[1].data)
            rhs = self._process_expr(index_map, type_map, tree.children[2])
            if operator == 'expr_mul':
                operator = BinaryOperator.MUL
            elif operator == 'expr_div':
                operator = BinaryOperator.DIV
            elif operator == 'expr_mod':
                operator = BinaryOperator.MOD
            else:
                raise ValueError(
                    'Unrecognized binary operator: {}'.format(operator))
            return BinaryExpr(operator, lhs, rhs)
        elif expr_kind == 'term_expr':
            lhs = self._process_expr(index_map, type_map, tree.children[0])
            operator = str(tree.children[1].data)
            rhs = self._process_expr(index_map, type_map, tree.children[2])
            if operator == 'expr_add':
                operator = BinaryOperator.ADD
            elif operator == 'expr_sub':
                operator = BinaryOperator.SUB
            else:
                raise ValueError(
                    'Unrecognized binary operator: {}'.format(operator))
            return BinaryExpr(operator, lhs, rhs)
        elif expr_kind == 'cmp_expr':
            lhs = self._process_expr(index_map, type_map, tree.children[0])
            operator = str(tree.children[1].data)
            rhs = self._process_expr(index_map, type_map, tree.children[2])
            if operator == 'expr_eq':
                operator = BinaryOperator.EQ
            elif operator == 'expr_ne':
                operator = BinaryOperator.NE
            elif operator == 'expr_lt':
                operator = BinaryOperator.LT
            elif operator == 'expr_le':
                operator = BinaryOperator.LE
            elif operator == 'expr_gt':
                operator = BinaryOperator.GT
            elif operator == 'expr_ge':
                operator = BinaryOperator.GE
            else:
                raise ValueError(
                    'Unrecognized binary operator: {}'.format(operator))
            return BinaryExpr(operator, lhs, rhs)
        elif expr_kind == 'and_expr':
            lhs = self._process_expr(index_map, type_map, tree.children[0])
            rhs = self._process_expr(index_map, type_map, tree.children[1])
            return BinaryExpr(BinaryOperator.AND, lhs, rhs)
        elif expr_kind == 'or_expr':
            lhs = self._process_expr(index_map, type_map, tree.children[0])
            rhs = self._process_expr(index_map, type_map, tree.children[1])
            return BinaryExpr(BinaryOperator.OR, lhs, rhs)
        elif expr_kind == 'imply_expr':
            lhs = self._process_expr(index_map, type_map, tree.children[0])
            rhs = self._process_expr(index_map, type_map, tree.children[1])
            return BinaryExpr(BinaryOperator.IMPLY, lhs, rhs)
        elif expr_kind == 'cond_expr':
            cond = self._process_expr(index_map, type_map, tree.children[0])
            true_val = self._process_expr(
                index_map, type_map, tree.children[1])
            false_val = self._process_expr(
                index_map, type_map, tree.children[2])
            return CondExpr(cond, true_val, false_val)
        else:
            msg = 'Unrecognized expr kind: {}'.format(expr_kind)
            raise NotImplementedError(msg)

    def func_decl(self, tree):
        name = str(tree.children[0])
        tree_body = tree.children[1]
        lhs_name = self._process_opt_arg(tree_body.children[0])
        rhs_names = [self._process_opt_arg(x)
                     for x in tree_body.children[1].children]
        index_map = self._create_index_map(
            [tree_body.children[0]] + tree_body.children[1].children)
        lhs = self._type_spec.get_type_or_raise(lhs_name)
        rhs = [self._type_spec.get_type_or_raise(x) for x in rhs_names]
        type_map = self._create_type_map([lhs] + rhs)
        constraints = [self._process_expr(index_map, type_map,
                                          x) for x in tree.children[2].children]
        self._prod_spec.add_func_production(
            name=name, lhs=lhs, rhs=rhs, constraints=constraints)

    def collect(self) -> ProductionSpec:
        return self._prod_spec


class PredicateCollector(Visitor_Recursive):
    _pred_spec: PredicateSpec

    def __init__(self):
        self._pred_spec = PredicateSpec()

    def _process_arg(self, tree):
        arg_kind = str(tree.data)
        if arg_kind == 'pred_var':
            return str(tree.children[0])
        elif arg_kind == 'pred_str':
            return literal_eval(str(tree.children[0]))
        elif arg_kind == 'pred_false':
            return False
        elif arg_kind == 'pred_true':
            return True
        elif arg_kind == 'pred_num':
            num_str = str(tree.children[0])
            try:
                # Try integer first
                return int(num_str)
            except ValueError:
                # If that doesn't work, try float instead
                return float(num_str)
        else:
            msg = 'Unrecognized predicate arg kind: {}'.format(arg_kind)
            raise NotImplementedError(msg)

    def pred_body(self, tree):
        name = tree.children[0]
        args = [self._process_arg(x) for x in tree.children[1].children]
        self._pred_spec.add_predicate(name, args)

    def collect(self) -> PredicateSpec:
        return self._pred_spec


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
        prod_collector = ProductionCollector(type_spec)
        prod_collector.visit(parse_tree)
        prod_spec = prod_collector.collect()

        # Process global predicates
        logger.debug('Processing global predicates...')
        pred_collector = PredicateCollector()
        pred_collector.visit(parse_tree)
        pred_spec = pred_collector.collect()

        return TyrellSpec(type_spec, prog_spec, prod_spec, pred_spec)
    except (KeyError, ValueError) as e:
        raise ParseTreeProcessingError('{}'.format(e))
