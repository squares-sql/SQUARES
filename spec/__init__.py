from .parser import Lark_StandAlone
from .parser import LarkError as ParseError


def parse(input_str):
    parser = Lark_StandAlone()
    return parser.parse(input_str)
