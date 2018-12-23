from .parser import Lark_StandAlone
from .parser import LarkError as ParseError
from .type import Type, EnumType, ValueType
from .production import Production
from .spec import TypeSpec, ProductionSpec, ProgramSpec, TyrellSpec
from .desugar import desugar
from .desugar import ParseTreeProcessingError


def parse(input_str):
    parser = Lark_StandAlone()
    parse_tree = parser.parse(input_str)
    return desugar(parse_tree)
