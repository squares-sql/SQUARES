#!/usr/bin/env python

import spec as S
from interpreter import PostOrderInterpreter
from enumerator import SmtEnumerator
from synthesizer import ExampleConstraintSynthesizer, Example
import rpy2.robjects as robjects
import logger

logger = logger.get('tyrell')

robjects.r('''
    library(dplyr)
    library(tidyr)
   ''')

## Common utils.
def get_collist(sel):
    sel_str = ",".join(sel)
    return "c(" + sel_str + ")"

class MorpheusInterpreter(PostOrderInterpreter):
    ## Concrete interpreter
    def eval_ColInt(self, v):
        return int(v)

    def eval_ColList(self, v):
        return v

    def eval_const(self, node, args):
        return args[0]

    def eval_select(self, node, args):
        _script = "select(" + args[0] + ", " + get_collist(args[1]) + ")"
        ret_val = robjects.r(_script)
        return ret_val

    def eval_unite(self, node, args):
        # logger.info('    unite=======: {} '.format(node))
        _script = "unite(" + args[0] + ", TT, " + str(args[1]) + "," + str(args[2]) + ")"
        return robjects.r(_script)

    ## Abstract interpreter
    def apply_row(self, val):
        df = val
        if isinstance(val, str):
            df = robjects.r(val)
        ## df: rpy2.robjects.vectors.DataFrame

        return df.nrow

    def apply_col(self, val):
        df = val
        if isinstance(val, str):
            df = robjects.r(val)

        return df.ncol


def main():

    ##### Input-output constraint
    benchmark1_input = robjects.r('''
    dat <- read.table(text="
    round var1 var2 nam        val
    round1   22   33 foo 0.16912201
    round2   11   44 foo 0.18570826
    round1   22   33 bar 0.12410581
    round2   11   44 bar 0.03258235
    ", header=T)
    dat
   ''')

    benchmark1_output = robjects.r('''
    dat2 <- read.table(text="
    nam val_round1 val_round2 var1_round1 var1_round2 var2_round1 var2_round2
    bar  0.1241058 0.03258235          22          11          33          44
    foo  0.1691220 0.18570826          22          11          33          44
    ", header=T)
    dat2
   ''')

    logger.info('Parsing Spec...')
    spec = None
    with open('example/morpheus.tyrell', 'r') as f:
        m_spec_str = f.read()
        spec = S.parse(m_spec_str)
    logger.info('Parsing succeeded')

    logger.info('Building synthesizer...')
    synthesizer = ExampleConstraintSynthesizer(
        #loc: # of function productions
        enumerator=SmtEnumerator(spec, depth=2, loc=1),
        interpreter=MorpheusInterpreter(),
        examples=[
            Example(input=['dat'], output=benchmark1_output),
        ]
    )
    logger.info('Synthesizing programs...')

    prog = synthesizer.synthesize()
    if prog is not None:
        logger.info('Solution found: {}'.format(prog))
    else:
        logger.info('Solution not found!')


if __name__ == '__main__':
    logger.setLevel('DEBUG')
    main()
