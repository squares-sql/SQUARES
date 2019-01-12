from .parser import Lark_StandAlone
from .desugar import desugar

# This has to be global since Lark_StandAlone() is not re-entrant.
# See https://github.com/lark-parser/lark/issues/299
parser = Lark_StandAlone()

def parse(input_str):
    parse_tree = parser.parse(input_str)
    return desugar(parse_tree)
