from enum import Enum, unique
from abc import ABC, abstractmethod
from typing import List, Dict, Union


@unique
class ExprType(Enum):
    VALUE = "value"  # We don't track the exact user-defined type here
    BOOL = "bool"
    INT = "int"


@unique
class UnaryOperator(Enum):
    NEG = "-"
    NOT = "!"


_unary_sig: Dict[UnaryOperator, ExprType] = {
    UnaryOperator.NEG: ExprType.INT,
    UnaryOperator.NOT: ExprType.BOOL
}


def unary_param_type(op: UnaryOperator):
    return _unary_sig[op]


def unary_return_type(op: UnaryOperator):
    return _unary_sig[op]


@unique
class BinaryOperator(Enum):
    ADD = "+"
    SUB = "-"
    MUL = "*"
    DIV = "/"
    MOD = "%"

    EQ = "=="
    NE = "!="
    LT = "<"
    LE = "<="
    GT = ">"
    GE = ">="

    AND = "&&"
    OR = "||"
    IMPLY = "==>"


_binary_param_sig: Dict[BinaryOperator, ExprType] = {
    BinaryOperator.ADD: ExprType.INT,
    BinaryOperator.SUB: ExprType.INT,
    BinaryOperator.MUL: ExprType.INT,
    BinaryOperator.DIV: ExprType.INT,
    BinaryOperator.MOD: ExprType.INT,
    BinaryOperator.LT: ExprType.INT,
    BinaryOperator.LE: ExprType.INT,
    BinaryOperator.GT: ExprType.INT,
    BinaryOperator.GE: ExprType.INT,
    BinaryOperator.AND: ExprType.BOOL,
    BinaryOperator.OR: ExprType.BOOL,
    BinaryOperator.IMPLY: ExprType.BOOL,
}


def binary_param_type(op: BinaryOperator):
    return _binary_param_sig[op]


binary_return_sig: Dict[BinaryOperator, ExprType] = {
    BinaryOperator.ADD: ExprType.INT,
    BinaryOperator.SUB: ExprType.INT,
    BinaryOperator.MUL: ExprType.INT,
    BinaryOperator.DIV: ExprType.INT,
    BinaryOperator.MOD: ExprType.INT,
    BinaryOperator.EQ: ExprType.BOOL,
    BinaryOperator.NE: ExprType.BOOL,
    BinaryOperator.LT: ExprType.BOOL,
    BinaryOperator.LE: ExprType.BOOL,
    BinaryOperator.GT: ExprType.BOOL,
    BinaryOperator.GE: ExprType.BOOL,
    BinaryOperator.AND: ExprType.BOOL,
    BinaryOperator.OR: ExprType.BOOL,
    BinaryOperator.IMPLY: ExprType.BOOL,
}


def binary_return_type(op: BinaryOperator):
    return binary_return_sig[op]


class Expr(ABC):

    @abstractmethod
    def __init__(self):
        pass

    @property
    @abstractmethod
    def operands(self) -> List['Expr']:
        raise NotImplementedError

    @property
    @abstractmethod
    def type(self) -> ExprType:
        raise NotImplementedError


class ConstExpr(Expr):
    _value: Union[bool, int]

    def __init__(self, value: Union[bool, int]):
        super().__init__()
        if not isinstance(value, bool) and not isinstance(value, int):
            raise ValueError(
                'ConstExpr does not accept non-boolean/int constants: {}'.format(value))
        self._value = value

    @property
    def value(self):
        return self._value

    @property
    def type(self):
        if isinstance(self._value, bool):
            return ExprType.BOOL
        elif isinstance(self._value, int):
            return ExprType.INT
        else:
            raise ValueError(
                'ConstExpr found unknown value type: {}'.format(self._value))

    @property
    def operands(self) -> List[Expr]:
        return []

    def __str__(self) -> str:
        if isinstance(self._value, bool):
            return 'true' if self._value else 'false'
        else:
            return str(self._value)

    def __repr__(self) -> str:
        return 'ConstExpr({})'.format(self._value)


class ParamExpr(Expr):
    _index: int

    def __init__(self, index: int):
        super().__init__()
        self._index = index

    @property
    def index(self) -> int:
        return self._index

    @property
    def type(self) -> ExprType:
        return ExprType.VALUE

    @property
    def operands(self) -> List[Expr]:
        return []

    def __str__(self) -> str:
        if self._index == 0:
            return '@ret'
        else:
            return '@arg{}'.format(self._index - 1)

    def __repr__(self) -> str:
        return 'ParamExpr({})'.format(self._index)


class UnaryExpr(Expr):
    _operator: UnaryOperator
    _operand: Expr

    def __init__(self, operator: UnaryOperator, operand: Expr):
        super().__init__()
        expect_ty = unary_param_type(operator)
        if operand.type is not expect_ty:
            raise ValueError(
                'Expression is expected to have type {}: {}'.format(expect_ty, operand))
        self._operator = operator
        self._operand = operand

    @property
    def operator(self):
        return self._operator

    @property
    def operand(self):
        return self._operand

    @property
    def operands(self) -> List[Expr]:
        return [self._operand]

    @property
    def type(self):
        return unary_return_type(self._operator)

    def __str__(self) -> str:
        return '({} {})'.format(self._operator.value, self._operand)

    def __repr__(self) -> str:
        return 'UnaryExpr({}, {!r})'.format(self._operator.name, self._operand)


class BinaryExpr(Expr):
    _operator: BinaryOperator
    _lhs: Expr
    _rhs: Expr

    def __init__(self, operator: BinaryOperator, lhs: Expr, rhs: Expr):
        super().__init__()
        if operator is BinaryOperator.EQ or operator is BinaryOperator.NE:
            # These two operators are polymorphic
            if lhs.type is not rhs.type:
                raise ValueError(
                    'Expression must have the same type: {} and {}'.format(lhs, rhs))
        else:
            expect_ty = binary_param_type(operator)
            if lhs.type is not expect_ty:
                raise ValueError(
                    'Expression is expected to have type {}: {}'.format(expect_ty, lhs))
            if rhs.type is not expect_ty:
                raise ValueError(
                    'Expression is expected to have type {}: {}'.format(expect_ty, rhs))
        self._operator = operator
        self._lhs = lhs
        self._rhs = rhs

    @property
    def operator(self):
        return self._operator

    @property
    def lhs(self):
        return self._lhs

    @property
    def rhs(self):
        return self._rhs

    @property
    def operands(self) -> List[Expr]:
        return [self._lhs, self._rhs]

    @property
    def type(self):
        return binary_return_type(self._operator)

    def __str__(self) -> str:
        return '({} {} {})'.format(self._lhs, self._operator.value, self._rhs)

    def __repr__(self) -> str:
        return 'BinaryExpr({}, {!r}, {!r})'.format(self._operator.name, self._lhs, self._rhs)


class CondExpr(Expr):
    _cond: Expr
    _true_val: Expr
    _false_val: Expr

    def __init__(self, cond: Expr, true_val: Expr, false_val: Expr):
        if cond.type is not ExprType.BOOL:
            raise ValueError(
                'Condition is not a boolean expr: {}'.format(cond))
        if true_val.type is not false_val.type:
            raise ValueError(
                'Expression must have the same type: {} and {}'.format(true_val, false_val))
        self._cond = cond
        self._true_val = true_val
        self._false_val = false_val

    @property
    def condition(self) -> Expr:
        return self._cond

    @property
    def true_value(self) -> Expr:
        return self._true_val

    @property
    def false_value(self) -> Expr:
        return self._false_val

    @property
    def operands(self) -> List[Expr]:
        return [self._cond, self._true_val, self._false_val]

    @property
    def type(self) -> ExprType:
        return self._true_val.type

    def __str__(self) -> str:
        return '(if {} then {} else {})'.format(self._cond, self._true_val, self._false_val)

    def __repr__(self) -> str:
        return 'CondExpr({!r}, {!r}, {!r})'.format(self._cond, self._true_val, self._false_val)


class PropertyExpr(Expr):
    _name: str
    _type: ExprType
    _operand: Expr

    def __init__(self, name: str, type: ExprType, operand: Expr):
        super().__init__()
        if operand.type is not ExprType.VALUE:
            raise ValueError(
                'PropertyExpr cannot be applied to non-value operand: {}'.format(operand))
        self._name = name
        self._type = type
        self._operand = operand

    @property
    def name(self) -> str:
        return self._name

    @property
    def type(self) -> ExprType:
        return self._type

    @property
    def operand(self) -> Expr:
        return self._operand

    @property
    def operands(self) -> List[Expr]:
        return [self._operand]

    def __str__(self) -> str:
        return '{}({})'.format(self._name, self._operand)

    def __repr__(self) -> str:
        return 'PropertyExpr({}, {}, {!r})'.format(self._name, self._type, self._operand)
