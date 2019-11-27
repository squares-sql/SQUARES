#!/usr/bin/env python
# File:	squares_enumerator.py
# Description:	Squares based on sql
# Author:	Pedro M Orvalho
# Created on:	20-02-2019 16:17:30
# Usage:	python squares_enumerator.py
# Python version:	3.6.4

from sys import argv
import tyrell.spec as S
import sqlite3
from tyrell.interpreter import PostOrderInterpreter, GeneralError
from tyrell.enumerator import *
from tyrell.decider import Example, ExampleConstraintDecider
from tyrell.synthesizer import Synthesizer
from tyrell.logger import get_logger
from sqlite3 import Error

logger = get_logger('tyrell')

counter_ = 1
conn = None

def create_connection(db_file=None):
	global conn
	""" create a database connection to a SQLite database """
	try:
		if not db_file:
			conn = sqlite3.connect(':memory:')
		else:
			conn = sqlite3.connect(db_file)
		# print(sqlite3.version)
		return conn
	except Error as e:
		print(e)

## Common utils.
def get_collist(sel):
	sel_str = ",".join(sel)
	return sel_str
	return "c(" + sel_str + ")"

def getNaturalJoins(sel):
	return " natural join ".join(sel)

def get_fresh_name():
	global counter_ 
	counter_ = counter_ + 1

	fresh_str = 'RET_DF' + str(counter_)
	return fresh_str

def get_fresh_col():
	global counter_ 
	counter_ = counter_ + 1

	fresh_str = 'COL' + str(counter_)
	return fresh_str

def get_type(df, index):
	_rscript = 'sapply({df_name}, class)[{pos}]'.format(df_name=df, pos=index)
	ret_val = robjects.r(_rscript)
	return ret_val[0]

def eq_r(actual, expect):
	# _rscript = 'all.equal({lhs}, {rhs}, tolerance=0.000001)'.format(lhs=actual, rhs=expect)
	# ret_val = robjects.r(_rscript)
	# return True == ret_val[0]
	print(actual)
	# print(expect)
	return actual == expect

class SquaresInterpreter(PostOrderInterpreter):
	## Concrete interpreter
	def eval_ColInt(self, v):
		return int(v)

	def eval_ColList(self, v):
		return v

	def eval_const(self, node, args):
		return args[0]

	def eval_select(self, node, args):
		global conn
		# n_cols = robjects.r('ncol(' + args[0] + ')')[0]
		# self.assertArg(node, args, index=1, cond=lambda x: max(list(map(lambda y: int(y), x))) <= n_cols, capture_indices=[0])

		ret_df_name = get_fresh_name()
		_script = '{type} {cols} from {table};'.format(
				   ret_df=ret_df_name, type=str(args[0][0]), table=getNaturalJoins(args[1]), cols=get_collist(args[2]))
		logger.error(_script)
		output = ""
		try:
			c = conn.cursor()
			c.execute(_script)
			rows = c.fetchall()
			for r in rows:
				output += str(r)
			return output
		except sqlite3.Error as er:
			return output
			logger.error('er:', er.message)
			raise GeneralError()

	# def eval_inner_join(self, node, args):
	# 	ret_df_name = get_fresh_name()
	# 	_script = '{ret_df} <- inner_join({t1}, {t2})'.format(
	# 			  ret_df=ret_df_name, t1=args[0], t2=args[1])
	# 	try:
	# 		ret_val = robjects.r(_script)
	# 		return ret_df_name
	# 	except:
	# 		logger.error('Error in interpreting innerjoin...')
	# 		raise GeneralError()

	## Abstract interpreter
	def apply_row(self, val):
		return int(val)
		df = val
		if isinstance(val, str):
			df = robjects.r(val)
		## df: rpy2.robjects.vectors.DataFrame

		return df.nrow

	def apply_col(self, val):
		return 1
		return int(val)
		df = val
		if isinstance(val, str):
			df = robjects.r(val)

		return df.ncol


def main(seed):
	global conn
	conn = create_connection("squares.db")
	# c = conn.cursor()
	# benchmark1_input = ""
	# c.execute("select * from faculty;")
	# rows = c.fetchall()
	# for r in rows:
	# 	# print(str(r))
	# 	benchmark1_input += str(r)
	# print(benchmark1_input)
	benchmark1_output = ""
	c = conn.cursor()
	c.execute("SELECT fid, fname FROM faculty natural join class;")
	rows = c.fetchall()
	for r in rows:
		benchmark1_output += str(r)
		# print(r)
	# print(benchmark1_output)

	logger.info('Parsing Spec...')
	spec = S.parse_file('example/squares.tyrell')
	logger.info('Parsing succeeded')

	logger.info('Building synthesizer...')
	synthesizer = Synthesizer(
		#loc: # of function productions
		# enumerator=SmtEnumerator(spec, depth=2, loc=1),
		# enumerator=SmtEnumerator(spec, depth=3, loc=2),
		enumerator=SmtEnumerator(spec, depth=4, loc=3),
		# enumerator=RandomEnumerator(
		# 	spec, max_depth=4, seed=seed),
		decider=ExampleConstraintDecider(
			spec=spec,
			interpreter=SquaresInterpreter(),
			examples=[
				Example(input=None, output=benchmark1_output),
			],
			equal_output=eq_r
		)
	)
	logger.info('Synthesizing programs...')

	prog = synthesizer.synthesize()
	if prog is not None:
		logger.info('Solution found: {}'.format(prog))
	else:
		logger.info('Solution not found!')
	conn.close()

if __name__ == '__main__':
	logger.setLevel('DEBUG')
	seed = None
	if len(argv) > 1:
		try:
			seed = int(argv[1])
		except ValueError:
			pass
	main(seed)
	
