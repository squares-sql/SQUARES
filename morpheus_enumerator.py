#!/usr/bin/env python

import spec as S
from interpreter import PostOrderInterpreter, GeneralError
from enumerator import SmtEnumerator
from synthesizer import AssertionViolationHandler, ExampleConstraintSynthesizer, Example
import rpy2.robjects as robjects
from logger import get_logger

logger = get_logger('tyrell')

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
        n_cols = robjects.r('ncol(' + args[0] + ')')[0]
        max_idx = max(list(map(lambda x: int(x), args[1])))
        self.assertArg(node, args,
                index=1,
                cond=lambda x: max_idx <= n_cols,
                capture_indices=[0])

        _script = '{ret_df} <- select({table}, {cols})'.format(
                   ret_df='RET_DF', table=args[0], cols=get_collist(args[1]))
        try:
            ret_val = robjects.r(_script)
            return 'RET_DF'
        except:
            raise GeneralError()

    def eval_unite(self, node, args):
        n_cols = robjects.r('ncol(' + args[0] + ')')[0]
        self.assertArg(node, args,
                index=1,
                cond=lambda x: x <= n_cols,
                capture_indices=[0])
        self.assertArg(node, args,
                index=2,
                cond=lambda x: x <= n_cols,
                capture_indices=[0])

        _script = '{ret_df} <- unite({table}, TMP, {col1}, {col2})'.format(
                  ret_df='RET_DF', table=args[0], col1=str(args[1]), col2=str(args[2]))
        try:
            ret_val = robjects.r(_script)
            return 'RET_DF'
        except:
            raise GeneralError()

    def eval_filter(self, node, args):
        n_cols = robjects.r('ncol(' + args[0] + ')')[0]
        self.assertArg(node, args,
                index=2,
                cond=lambda x: x <= n_cols,
                capture_indices=[0])

        _script = '{ret_df} <- {table} %>% filter(.[[{col}]] {op} {const})'.format(
                  ret_df='RET_DF', table=args[0], op=args[1], col=str(args[2]), const=str(args[3]))
        try:
            ret_val = robjects.r(_script)
            return 'RET_DF'
        except:
            raise GeneralError()

    def eval_separate(self, node, args):
        n_cols = robjects.r('ncol(' + args[0] + ')')[0]
        self.assertArg(node, args,
                index=1,
                cond=lambda x: x <= n_cols,
                capture_indices=[0])


        _script = '{ret_df} <- separate({table}, {col1}, c("TMP1", "TMP2"))'.format(
                  ret_df='RET_DF', table=args[0], col1=str(args[1])) 
        try:
            ret_val = robjects.r(_script)
            return 'RET_DF'
        except:
            raise GeneralError()

    def eval_spread(self, node, args):
        n_cols = robjects.r('ncol(' + args[0] + ')')[0]
        self.assertArg(node, args,
                index=1,
                cond=lambda x: x <= n_cols,
                capture_indices=[0])
        self.assertArg(node, args,
                index=2,
                cond=lambda x: x <= n_cols,
                capture_indices=[0])


        _script = '{ret_df} <- spread({table}, {col1}, {col2})'.format(
                  ret_df='RET_DF', table=args[0], col1=str(args[1]), col2=str(args[2]))
        try:
            ret_val = robjects.r(_script)
            return 'RET_DF'
        except:
            raise GeneralError()

    def eval_gather(self, node, args):
        n_cols = robjects.r('ncol(' + args[0] + ')')[0]
        max_idx = max(list(map(lambda x: int(x), args[1])))
        self.assertArg(node, args,
                index=1,
                cond=lambda x: max_idx <= n_cols,
                capture_indices=[0])

        _script = '{ret_df} <- gather({table}, KEY, VALUE, {cols})'.format(
                   ret_df='RET_DF', table=args[0], cols=get_collist(args[1]))
        try:
            ret_val = robjects.r(_script)
            return 'RET_DF'
        except:
            raise GeneralError()

    def eval_group_by(self, node, args):
        n_cols = robjects.r('ncol(' + args[0] + ')')[0]
        max_idx = max(list(map(lambda x: int(x), args[1])))
        self.assertArg(node, args,
                index=1,
                cond=lambda x: max_idx <= n_cols,
                capture_indices=[0])

        _script = '{ret_df} <- group_by({table}, {cols})'.format(
                   ret_df='RET_DF', table=args[0], cols=get_collist(args[1]))
        try:
            ret_val = robjects.r(_script)
            return 'RET_DF'
        except:
            raise GeneralError()

    def eval_summarise(self, node, args):
        n_cols = robjects.r('ncol(' + args[0] + ')')[0]
        self.assertArg(node, args,
                index=2,
                cond=lambda x: x <= n_cols,
                capture_indices=[0])

        _script = '{ret_df} <- {table} %>% summarise(TMP = {aggr} (.[[{col}]]))'.format(
                  ret_df='RET_DF', table=args[0], aggr=str(args[1]), col=str(args[2]))
        try:
            ret_val = robjects.r(_script)
            return 'RET_DF'
        except:
            raise GeneralError()

    def eval_mutate(self, node, args):
        n_cols = robjects.r('ncol(' + args[0] + ')')[0]
        self.assertArg(node, args,
                index=2,
                cond=lambda x: x <= n_cols,
                capture_indices=[0])
        self.assertArg(node, args,
                index=3,
                cond=lambda x: x <= n_cols,
                capture_indices=[0])

        _script = '{ret_df} <- {table} %>% mutate(TMP=.[[{col1}]] {op} .[[{col2}]])'.format(
                  ret_df='RET_DF', table=args[0], op=args[1], col1=str(args[2]), col2=str(args[3]))
        try:
            ret_val = robjects.r(_script)
            return 'RET_DF'
        except:
            raise GeneralError()

    def eval_inner_join(self, node, args):
        _script = '{ret_df} <- inner_join({t1}, {t2})'.format(
                  ret_df='RET_DF', t1=args[0], t2=args[1])
        try:
            ret_val = robjects.r(_script)
            return 'RET_DF'
        except:
            raise GeneralError()

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


class MorpheusSynthesizer(AssertionViolationHandler, ExampleConstraintSynthesizer):
    pass

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
    synthesizer = MorpheusSynthesizer(
        spec=spec,
        #loc: # of function productions
        # enumerator=SmtEnumerator(spec, depth=2, loc=1),
        enumerator=SmtEnumerator(spec, depth=3, loc=2),
        interpreter=MorpheusInterpreter(),
        examples=[
            # Example(input=[DataFrame2(benchmark1_input)], output=benchmark1_output),
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
