#!/usr/bin/env python
# File:	squares-enumerator.py
# Description: An SQL Synthesizer Using Query Reverse Engineering
# Author:	Pedro M Orvalho
# Created on:	22-02-2019 15:13:15
# Usage:	python3 squaresEnumerator.py [flags|(-h for help)] specFile.in
# Python version:	3.6.4

from sys import argv
from string import *
import tyrell.spec as S
from tyrell.interpreter import PostOrderInterpreter, GeneralError
from tyrell.enumerator import *
from tyrell.decider import Example, ExampleConstraintDecider, ExampleConstraintPruningDecider
from tyrell.synthesizer import Synthesizer
from tyrell.logger import get_logger
import rpy2.robjects as robjects
from itertools import permutations
import warnings
from rpy2.rinterface import RRuntimeWarning
import sqlparse as sp
import re
import sys
import os
warnings.filterwarnings("ignore", category=RRuntimeWarning)

logger = get_logger('tyrell')
counter_ = 0
distinct = False
getProgram = False
final_program = ''
_tables = dict()
output_attrs = ""
attributes = []
robjects.r('''
	library(dplyr)
	library(dbplyr)
	library(tidyr)
	library(stringr)
	options(warn=-1)
   ''')

## Common utils.
def get_collist(sel):
	return sel

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

# get the string format to be used in filter
def getConst(cons):
	global attributes
	try:
		if int(cons):
			return str(cons)
	except:
		if str(cons)=="max(n)" or cons in attributes:
			return str(cons)
		else:
			return "\""+str(cons)+"\""

def getColsPermutations(cols, num):
	if num == 0:
		return []
	return [", ".join(a) for a in permutations(cols, num)] + getColsPermutations(cols,num-1)

def eq_r(actual, expect):
	global distinct
	_rscript = 'all.equal(lapply({lhs}, as.character),lapply({rhs}, as.character))'.format(lhs=actual, rhs=expect)
	# _rscript = 'all.equal(lapply({lhs}, FUN=function(x){{ data.frame(as.matrix(x))}}),lapply({rhs}, FUN=function(x){{ data.frame(as.matrix(x)) }} ))'.format(lhs=actual, rhs=expect)
	try:
		ret_val = robjects.r(_rscript)
	except:
		return False
	return True == ret_val[0]

# find if there is one integer constant in the list of constants
def findConst(consts):
	if consts == []:
		return False
	try:
		if int(consts[0][1:-1]):
			return True
	except:
		return findConst(consts[1:])


class SquaresInterpreter(PostOrderInterpreter):
	## Concrete interpreter
	def eval_ColInt(self, v):
		return v

	def eval_ColList(self, v):
		return v

	def eval_const(self, node, args):
		return args[0]

	def eval_unused(self, node, args):
		return get_fresh_name()

	def eval_select(self, node, args):
		global final_program, getProgram
		ret_df_name = get_fresh_name()
		_tables[ret_df_name] = counter_
		_script = '{ret_df} <- {table} %>% ungroup() %>% select({cols})'.format(ret_df=ret_df_name, table=args[0], cols=get_collist(args[1]))
		if args[2] == "distinct":
			_script += ' %>% distinct()'
		# print(_script)
		if getProgram:
			final_program += _script + "\n"
		try:
			ret_val = robjects.r(_script)
			return ret_df_name
		except:
			#LOGGER 			logger.error('Error in interpreting select...')
			raise GeneralError()

	def eval_filter(self, node, args):
		global final_program, getProgram
		ret_df_name = get_fresh_name()
		_tables[ret_df_name] = counter_
		if "str_detect" not in args[1]:
			col, op, const = args[1].split(" ")
			_script = '{ret_df} <- {table} %>% ungroup() %>% filter({col} {op} {const})'.format(ret_df=ret_df_name, table=args[0], op=op, col=col, const=getConst(const)) if const != "max(n)" else '{ret_df} <- filter({table}, {col} {op} {const})'.format(ret_df=ret_df_name, table=args[0], op=op, col=col, const="max(n)")
		else:
			col, string = args[1].split("|")
			_script = '{ret_df} <- {table} %>% ungroup() %>% filter({col}, {const}))'.format(ret_df=ret_df_name, table=args[0], col=col, const="\""+string[:-1]+"\"")
		# print(_script)
		if getProgram:
			final_program += _script + "\n"
		try:
			ret_val = robjects.r(_script)
			return ret_df_name
		except:
			#LOGGER 			logger.error('Error in interpreting filter...')
			raise GeneralError()

	def eval_filters(self, node, args):
		global final_program, getProgram
		ret_df_name = get_fresh_name()
		_tables[ret_df_name] = counter_
		if "str_detect" not in args[1]:
			col, op, const = args[1].split(" ")
			const = getConst(const) if const != "max(n)" else "max(n)"
			arg1 = col + " " + op + " " + const
		else:
			col, string = args[1].split("|")
			arg1 = col+", "+"\""+string[:-1]+"\")"
		if "str_detect" not in args[2]:
			col, op, const = args[2].split(" ")
			const = getConst(const) if const != "max(n)" else "max(n)"
			arg2 = col + " " + op + " " + const
		else:
			col, string = args[2].split("|")
			arg2 = col+", "+"\""+string[:-1]+"\")"

		_script = '{ret_df} <- {table} %>% ungroup() %>% filter({arg1} {Operator} {arg2})'.format(ret_df=ret_df_name, table=args[0], arg1=arg1, arg2=arg2, Operator=args[3])
		# print(_script)
		if getProgram:
			final_program += _script + "\n"
		try:
			ret_val = robjects.r(_script)
			return ret_df_name
		except:
			#LOGGER 			logger.error('Error in interpreting filters...')
			raise GeneralError()

	def eval_summariseGrouped(self, node, args):
		global final_program, getProgram
		ret_df_name = get_fresh_name()
		_tables[ret_df_name] = counter_
		if "paste" in args[1]:
			args[1] = '{at} = paste({at}, collapse=:)'.format(at=args[1].split("|")[1])

		_script = '{ret_df} <- {table} %>% group_by({cols}) %>% summarise({cond})'.format(ret_df=ret_df_name, table=args[0], cols=get_collist(args[2]), cond=args[1].replace(":", "\":\""))
		# print(_script)
		if getProgram:
			final_program += _script + "\n"
		try:
			ret_val = robjects.r(_script)
			return ret_df_name
		except:
			#LOGGER 			logger.error('Error in interpreting summarise...')
			raise GeneralError()

	def eval_summarise(self, node, args):
		global final_program, getProgram
		ret_df_name = get_fresh_name()
		_tables[ret_df_name] = counter_
		if "paste" in args[1]:
			args[1] = '{at} = paste({at}, collapse=\":\")'.format(at=args[1].split("|")[1])
		_script = '{ret_df} <- {table} %>% summarise({cond})'.format(ret_df=ret_df_name, table=args[0], cond=args[1])

		# print(_script)
		if getProgram:
			final_program += _script + "\n"
		try:
			ret_val = robjects.r(_script)
			return ret_df_name
		except:
			#LOGGER 			logger.error('Error in interpreting summarise...')
			raise GeneralError()

	def eval_inner_join(self, node, args):
		global final_program, getProgram
		ret_df_name = get_fresh_name()
		_tables[ret_df_name] = counter_

		_script = '{ret_df} <- inner_join({t1}, {t2})'.format(
				  ret_df=ret_df_name, t1=args[0], t2=args[1])
		# print(_script)
		if getProgram:
			final_program += _script + "\n"
		try:
			ret_val = robjects.r(_script)
			return ret_df_name
		except:
			#LOGGER 			logger.error('Error in interpreting innerjoin...')
			raise GeneralError()

	def eval_inner_join3(self, node, args):
		global final_program, getProgram
		ret_df_name = get_fresh_name()
		_tables[ret_df_name] = counter_

		_script = '{ret_df} <- inner_join(inner_join({t1}, {t2}), {t3})'.format(
				  ret_df=ret_df_name, t1=args[0], t2=args[1], t3=args[2])

		if getProgram:
			final_program += _script + "\n"
		try:
			ret_val = robjects.r(_script)
			return ret_df_name
		except:
			#LOGGER 			logger.error('Error in interpreting innerjoin3...')
			raise GeneralError()

	def eval_inner_join4(self, node, args):
		global final_program, getProgram
		ret_df_name = get_fresh_name()
		_tables[ret_df_name] = counter_

		_script = '{ret_df} <- inner_join(inner_join(inner_join({t1}, {t2}), {t3}), {t4})'.format(
				  ret_df=ret_df_name, t1=args[0], t2=args[1], t3=args[2], t4=args[3])
		# print(_script)
		if getProgram:
			final_program += _script + "\n"
		try:
			ret_val = robjects.r(_script)
			return ret_df_name
		except:
			#LOGGER 			logger.error('Error in interpreting innerjoin4...')
			raise GeneralError()

	def eval_anti_join(self, node, args):
		global final_program, getProgram
		ret_df_name = get_fresh_name()
		_tables[ret_df_name] = counter_

		_script = '{ret_df} <- anti_join(select({t1},{col}), select({t2}, {col}))'.format(
				  ret_df=ret_df_name, t1=args[0], t2=args[1], col=get_collist(args[2]))
		# print(_script)
		if getProgram:
			final_program += _script + "\n"
		try:
			ret_val = robjects.r(_script)
			return ret_df_name
		except:
			#LOGGER 			logger.error('Error in interpreting innerjoin...')
			raise GeneralError()

	def eval_left_join(self, node, args):
		global final_program, getProgram
		ret_df_name = get_fresh_name()
		_tables[ret_df_name] = counter_

		_script = '{ret_df} <- left_join({t1}, {t2})'.format(
				  ret_df=ret_df_name, t1=args[0], t2=args[1])
		# print(_script)
		if getProgram:
			final_program += _script + "\n"
		try:
			ret_val = robjects.r(_script)
			return ret_df_name
		except:
			#LOGGER 			logger.error('Error in interpreting innerjoin...')
			raise GeneralError()

	def eval_bind_rows(self, node, args):
		global final_program, getProgram
		ret_df_name = get_fresh_name()
		_tables[ret_df_name] = counter_

		_script = '{ret_df} <- bind_rows({t1}, {t2})'.format(
				  ret_df=ret_df_name, t1=args[0], t2=args[1])
		# print(_script)
		if getProgram:
			final_program += _script + "\n"
		try:
			ret_val = robjects.r(_script)
			return ret_df_name
		except:
			#LOGGER 			logger.error('Error in interpreting innerjoin...')
			raise GeneralError()

	def eval_intersect(self, node, args):
		global final_program, getProgram
		ret_df_name = get_fresh_name()
		_tables[ret_df_name] = counter_

		_script = '{ret_df} <- intersect(select({t1},{col}), select({t2}, {col}))'.format(
				  ret_df=ret_df_name, t1=args[0], t2=args[1], col=get_collist(args[2]))
		# print(_script)
		if getProgram:
			final_program += _script + "\n"
		try:
			ret_val = robjects.r(_script)
			return ret_df_name
		except:
			#LOGGER 			logger.error('Error in interpreting innerjoin...')
			raise GeneralError()

	def eval_unite(self, node, args):
		global final_program, getProgram
		ret_df_name = get_fresh_name()
		_tables[ret_df_name] = counter_

		_script = '{ret_df} <- unite({t1}, {col1}, which(colnames({t1})=="{col1}"), {col2}, which(colnames({t1})=="{col2}"), sep=":")'.format(
				  ret_df=ret_df_name, t1=args[0], col1=get_collist(args[1]), col2=get_collist(args[2]))
		# print(_script)
		if getProgram:
			final_program += _script + "\n"
		try:
			ret_val = robjects.r(_script)
			return ret_df_name
		except:
			#LOGGER 			logger.error('Error in interpreting innerjoin...')
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

	def apply_name(self, val):
		return _tables[val]

def divide_int_str_constants(const):
	str_const, int_const = [], []
	for c in const:
		try:
			if c == '0' or int(c):
				int_const.append(c)
		except:
			str_const.append(c)

	return str_const, int_const

def divide_int_str_attributes(files, attrs):
	str_attr, int_attr = [], []
	for a in attrs:
		if a == "n":
			if a not in int_attr:
				int_attr.append(a)
		for i in files:
			with open(i, 'r') as f:
				columns = f.readline()[:-1].split(",")
				if a in columns:
					ind = columns.index(a)
					try:
						if f.readline()[:-1].split(",")[ind]=='0' or int(f.readline()[:-1].split(",")[ind]):
							if a not in int_attr:
								int_attr.append(a)
					except:
						if a not in str_attr:
							str_attr.append(a)
	return str_attr, int_attr

def find_filter_conditions(str_const, int_const, str_attr, int_attr, new_int_attr, aggrs, files, necessary_conditions, summarise_conditions):
	conditions = []
	int_ops = ["==", ">", "<", ">=", "<="]
	str_ops = ["==", "!="]
	happens_before = []

	for sc in str_const + int_const:
		necessary_conditions.append([])
		for sa in str_attr:
			att = False
			for i in files:
				if att:
					break
				with open(i, 'r') as f:
					columns = f.readline()[:-1].split(",")
					if sa in columns:
						ind = columns.index(sa)
						for l in f:
							if l[:-1].split(",")[ind] == sc:
								att = True
								break
					else:
						continue
			if 'like' in aggrs:
				conditions.append('str_detect({sa}|{sc})'.format(sa=sa, sc=sc))
				necessary_conditions[-1].append(conditions[-1])

			if not att:
				continue
			for so in str_ops:
				conditions.append('{sa} {so} {sc}'.format(sa=sa, so=so, sc=sc))
				necessary_conditions[-1].append(conditions[-1])

	for ic in int_const:
		necessary_conditions.append([])
		for ia in int_attr + new_int_attr:
			if ic == ia:
				continue
			for io in int_ops:
				conditions.append('{ia} {io} {ic}'.format(ia=ia, io=io, ic=ic))
				necessary_conditions[-1].append(conditions[-1])
				if ia == "n":
					happens_before.append((conditions[-1],"n = n()"))

	for ic in new_int_attr:
		for ia in int_attr + new_int_attr:
			if ic == ia:
				continue
			for io in int_ops:
				conditions.append('{ia} {io} {ic}'.format(ia=ia, io=io, ic=ic))
				for sc in summarise_conditions:
					if ic in sc:
						happens_before.append((conditions[-1], sc))

	necessary_conditions = list(filter(lambda a: a != [], necessary_conditions))
	# if "max" in aggrs and "n" in aggrs or "max(n)" in aggrs:
	if "max(n)" in aggrs:
		conditions.append("n == max(n)")
		happens_before.append((conditions[-1],"n = n()"))
		necessary_conditions.append([conditions[-1]])

	# print("filter conditions "+str(conditions))
	return conditions, necessary_conditions, happens_before

def find_summarise_conditions(int_attr, str_attr, aggrs, necessary_conditions):
	conditions = []
	new_int_attr = []
	for a in aggrs:
		if a == "like":
			continue
		necessary_conditions.append([])
		if "n" == a:
			conditions.append('{a} = {a}()'.format(a=a))
			necessary_conditions[-1].append(conditions[-1])
			continue
		if 'concat' in a:
			for at in int_attr + str_attr:
				conditions.append('paste|{at}'.format(at=at))
				necessary_conditions[-1].append(conditions[-1])
			continue
		if "max(n)" == a:
			continue
		for ia in int_attr:
			conditions.append('{a}{ia} = {a}({ia})'.format(ia=ia, a=a))
			necessary_conditions[-1].append(conditions[-1])
			new_int_attr.append('{a}{ia}'.format(ia=ia, a=a))
	return list(filter(lambda a: a != [], necessary_conditions)), new_int_attr, conditions

def find_conditions(files, const, attrs, aggrs, bools):
	global attributes
	necessary_conditions = []
	str_const, int_const  =divide_int_str_constants(const)
	str_attr, int_attr = divide_int_str_attributes(files, attrs)
	# print("str_consts "+str(str_const))
	# print("int consts "+str(int_const))
	# print("str attrs "+str(str_attr))
	# print("int attrs "+str(int_attr))
	necessary_conditions, new_int_attr, sum_cond = find_summarise_conditions(int_attr, str_attr, aggrs, necessary_conditions)
	# print("new_int_attr " + str(new_int_attr))
	# print("summarise cond "+ str(sum_cond))
	filt_cond, necessary_conditions, happens_before = find_filter_conditions(str_const, int_const, str_attr, int_attr, new_int_attr, aggrs, files, necessary_conditions, sum_cond)
	# exit()
	attributes = int_attr + new_int_attr
	return filt_cond, sum_cond, necessary_conditions, happens_before

def find_necessary_conditions(conds):
	predicates = ""
	for c in conds:
		if c == []:
			break
		predicate = "\npredicate constant_occurs(\""
		for i in c:
			predicate += i + ","
		predicates += predicate[:-1]+"\");"
	return predicates

def happensBefore(conds):
	predicates = ""
	for c in conds:
		if c == ():
			break
		predicates += "\npredicate happens_before(\""+c[0]+"\",\""+c[1]+"\");"
	return predicates

def DSL():
	global counter_
	global _tables
	global output_attrs
	prog_out = ""
	Operators = ""
	concat = ""
	input_tables, ags, cns, ats, bls, db_columns = [], [], [], [], [], []

	filtersOne = "\nfunc filter: Table r -> Table a, FilterCondition f {\n row(r) <= row(a);\n col(r) == col(a);\n}"
	filters = filtersOne
	filterAndOr = "\nfunc filters: Table r -> Table a, FilterCondition f, FilterCondition g, Op o {\n row(r) <= row(a);\n col(r) == col(a);\n}"
	filterPredicateOne = "\npredicate is_not_parent(inner_join3, filter, 100);\npredicate is_not_parent(inner_join4, filter, 100);\npredicate is_not_parent(filter, filter, 100);\npredicate distinct_inputs(filter);\n"
	filterPredicate = filterPredicateOne
	filterPredicateTwo = "predicate distinct_filters(filters, 1, 2);\npredicate is_not_parent(filters, filters, 100);\npredicate is_not_parent(inner_join, filters, 100);\npredicate is_not_parent(inner_join3, filters, 100);\npredicate is_not_parent(inner_join4, filters, 100);\npredicate distinct_inputs(filters);"
	summarise = "\nfunc summariseGrouped: Table r -> Table a, SummariseCondition s, Cols b {\n row(r) <= row(a);\n col(r) <= 3;\n}\n\npredicate is_not_parent(inner_join4, summariseGrouped, 100);\npredicate is_not_parent(summariseGrouped, summariseGrouped, 100);"
	# \nfunc summarise: Table r -> Table a, SummariseCondition s {\n row(r) == 1;\n col(r) == 1;\n}\n\npredicate is_not_parent(summariseGrouped, summarise, 100);\npredicate is_not_parent(inner_join3, summarise, 100);\npredicate is_not_parent(inner_join4, summarise, 100);\npredicate is_not_parent(summarise, summariseGrouped, 100);\npredicate is_not_parent(summarise, summarise, 100);
	# summarise = "\nfunc summariseGrouped: Table r -> Table a, SummariseCondition s, Cols b;\n\nfunc summarise: Table r -> Table a, SummariseCondition s;\n\npredicate is_not_parent(summariseGrouped, summarise, 100);\npredicate is_not_parent(inner_join3, summarise, 100);\npredicate is_not_parent(inner_join4, summarise, 100);\npredicate is_not_parent(inner_join4, summariseGrouped, 100);\npredicate is_not_parent(summarise, summariseGrouped, 100);\npredicate is_not_parent(summarise, summarise, 100);\npredicate is_not_parent(summariseGrouped, summariseGrouped, 100);"
	# read the input and output files
	f_in = open(argv[-1], 'r')
	inputs = f_in.readline()[:-1].split(":")[1].replace(" ","").split(",")
	prog_out += "con <- DBI::dbConnect(RSQLite::SQLite(), \":memory:\")\n"
	for i in inputs:
		_script = 'input{cnt} <- read.table("{file}", sep =",", header=T)\ninput{cnt}\n'.format(file=i, cnt=counter_)
		prog_out += _script
		prog_out += 'input{cnt} <- copy_to(con,input{cnt})\n'.format(cnt=counter_)
		benchmark1_input = robjects.r(_script)
		input_tables.append('input{cnt}'.format(cnt=counter_))
		_tables[input_tables[-1]] = counter_
		counter_+=1
		with open(i, 'r') as f:
			db_columns = list(set(db_columns + f.readline()[:-1].split(",")))

	output = f_in.readline()[:-1].split(":")[1].replace(" ","")
	_script = 'expected_output <- read.table("{file}", sep =",", header=T)\nexpected_output\n'.format(file=output)
	prog_out += _script
	# print(_script)
	_tables['expected_output'] = counter_
	counter_+=1
	benchmark1_output = robjects.r(_script)
	# read the list of constants from the input
	consts = f_in.readline()[:-1].replace(" ","").split(":",1)
	intConst = findConst(consts[1].replace(" ","").split(","))
	filterFlag = 0
	if(consts[1]!=''):
		filterFlag = 1
		consts_temp = ""
		if len(consts[1].split(","))>1:
			filterFlag = 2
			filters = filterAndOr
			filterPredicate = filterPredicateTwo
			Operators = "enum Op{\n \"|\", \"&\"\n}"

		cns = consts[1].replace(" ","").replace("\"","").split(",")
	else:
		filterPredicate, filters, consts = "", "", ""

	# read the list of aggregation functions from the input file
	aggrs = f_in.readline()[:-1].replace(" ","").split(":")
	if aggrs[1]!='':
		ags = aggrs[1].replace(" ","").replace("\"","").split(",")
		for a in ags:
			if a == "concat":
				ags.remove(a)
				concat = "\nfunc unite: Table r -> Table a, Col c, Col d {\n row(r) <= row(a);\n col(r) < col(a);\n}"
		if (len(ags) == 1 and "like" in ags) or len(ags)==0:
			summarise = ""

	else:
		aggrs = ""
		summarise = ""

	if "\"max(n)\"" in aggrs:
		cns.append("max(n)")
		aggrs = aggrs.replace(",\"max(n)\"", "")

	file_path = 'example/squares.tyrell'

	# read the list of attributes from the input file
	attrs = f_in.readline()[:-1].replace(" ","").split(":")
	if(attrs[1]!=''):
		ats = list(attrs[1].replace(" ","").replace("\"","").split(","))
		ats = ats + ["n"] if "n" in ags and intConst else ats
	elif "\"n\"" in aggrs:
		ats.append("n")
	else:
		attrs = ""

	hasBools = False
	bools = f_in.readline()[:-1].replace(" ","").split(":")
	if "bools" in bools:
		hasBools = True
	if not hasBools:
		loc = int(bools[1])
	else:
		loc = int(f_in.readline()[:-1].replace(" ","").split(":")[1])

	# print("constants "+str(cns))
	# print("attributes "+str(ats))
	# print("aggrs "+str(ags))
	# print("bools "+str(bls))
	filterConditions, summariseConditions, necessary_conditions, happens_before = find_conditions(inputs, cns, ats, ags, bls)

	if filters == "" and filterConditions != []:
		filters = filtersOne
		filterPredicate = "\npredicate is_not_parent(filter, filter, 100);"
		# \npredicate is_not_parent(inner_join3, filter, 100);\npredicate is_not_parent(inner_join4, filter, 100);
	if len(necessary_conditions) > 1:
		filters = filtersOne + filterAndOr
		filterPredicate = "predicate distinct_filters(filters, 1, 2);\n\npredicate is_not_parent(filters, filter, 100);\npredicate is_not_parent(filter, filters, 100);\npredicate is_not_parent(filter, filter, 100);\npredicate is_not_parent(filters, filters, 100);"
		# \npredicate is_not_parent(inner_join3, filter, 100);\npredicate is_not_parent(inner_join, filters, 100);\npredicate is_not_parent(inner_join3, filters, 100);\npredicate is_not_parent(inner_join4, filters, 100);\npredicate is_not_parent(anti_join, filters, 100);\npredicate is_not_parent(inner_join4, filter, 100);
		Operators = "enum Op{\n \"|\", \"&\"\n}"

	necessary_conditions = find_necessary_conditions(necessary_conditions)
	necessary_conditions += happensBefore(happens_before)
	# find which attributes are in the output table, and format the DSL
	with open(output, 'r') as f:
		cols = f.readline()

	output_attrs = cols[:-1]

	cols = str(getColsPermutations(str(db_columns)[1:-1].replace("'","").replace(" ","").split(","), 2))[1:-1].replace("'", "\"")
	oneColumn = str(getColsPermutations(str(db_columns)[1:-1].replace("'","").replace(" ","").split(","), 1))[1:-1].replace("'", "\"")
	# try:
	with open(dir+file_path, 'r') as f:
		spec_str = f.read()
	# except:
	# 	with open('../example/squares.tyrell', 'r') as f:
	# 		spec_str = f.read()

	fil_conditions = "enum FilterCondition{\n"+ str(filterConditions)[1:-1].replace("'","\"") +"\n}\n" if filterConditions!=[] else ""
	sum_conditions = "enum SummariseCondition{\n"+ str(summariseConditions)[1:-1].replace("'","\"") +"\n}\n" if summariseConditions != [] else ""
	# print("final filter conditions "+ str(fil_conditions))
	# print("final summarise conditions "+ str(sum_conditions))

	return spec_str.format(cols=cols, Tables=str("Table, "*len(inputs))[:-2], summarise=summarise, filters=filters, filterPred=filterPredicate, FilterConditions=fil_conditions, SummariseConditions=sum_conditions, Op=Operators, necessaryConditions=necessary_conditions, SelectCols=str("\""+output_attrs+"\""), col=oneColumn, concat=concat), input_tables, prog_out, loc


index_table_aux = 0
def beautifier(sql):
	# parsed = sp.parse(sql)
	# new_sql = beautifier_aux(parsed[0])
	sql = re.sub("\`TBL_LEFT\`\.\`[^,\`]*\` AS |\`LHS\`\.\`[^,\`]*\` AS ", "", sql)
	sql = re.sub("\`TBL_RIGHT\`\.\`[^,\`]*\` AS |\`RHS\`\.\`[^,\`]*\` AS ", "", sql)
	return sp.format(sql, reindent=True, keyword_case='upper')
	# print(sp.format(new_sql, reindent=True, keyword_case='upper'))

def main(seed=None):
	global getProgram, final_program
	if not debug:
		sys.stderr = open(dir+'output.err', 'w+')

	# os.close(sys.stderr.fileno())
	warnings.filterwarnings("ignore", category=RRuntimeWarning)
	warnings.filterwarnings('ignore')
	logger.info('Parsing Spec...')
	dsl, input_tables, prog_out, loc = DSL()
	# print(dsl)
	spec =  S.parse(dsl)
	logger.info('Parsing succeeded')
	# loc += 1 #select
	# logger.info("Lines of Code: "+str(loc))

	logger.info('Building synthesizer...')
	loc = 1
	while (True):
		logger.info("Lines of Code: "+str(loc))
		if argv[1]=="tree":
			enumerator = SmtEnumerator(spec, depth=loc+1, loc=loc)
		else:
			if "-off" in argv:
				enumerator = LinesEnumerator(spec, depth=loc+1, loc=loc)
			elif "-on" in argv:
				enumerator = LinesEnumerator(spec, depth=loc+1, loc=loc, break_sym_online=True)
			else:
				enumerator = LinesEnumerator(spec, depth=loc+1, loc=loc, sym_breaker=False)


		synthesizer = Synthesizer(
			#loc: # of function productions
			enumerator=enumerator,
			# decider=ExampleConstraintDecider(
			decider=ExampleConstraintPruningDecider(
				spec=spec,
				interpreter=SquaresInterpreter(),
				examples=[
					Example(input=input_tables, output='expected_output'),
				],
				equal_output=eq_r
			)
		)
		logger.info('Synthesizing programs...')

		prog = synthesizer.synthesize()
		if prog is not None:
			logger.info('Solution found: {}'.format(prog))
			# print(prog_out+"select("+str(prog).replace("@param", "table")+","+output_attrs+")")
			# print(prog_out+str(prog).replace("@param", "table"))
			getProgram = True
			interpreter=SquaresInterpreter()
			evaluation = interpreter.eval(prog, input_tables)
			if dir == "./":
				print()
				if "-nr" not in argv:
					print("------------------------------------- R Solution ---------------------------------------\n")
					print(prog_out)
					print(final_program)
					print();print()
				print("+++++++++++++++++++++++++++++++++++++ SQL Solution +++++++++++++++++++++++++++++++++++++\n")
			robjects.r('{rscript}'.format(rscript=prog_out+final_program))
			sql_query = robjects.r('sql_render({result_table})'.format(result_table=evaluation))
			if dir == "./":
				print(beautifier(str(sql_query)[6:]))
				print()
			return final_program,beautifier(str(sql_query)[6:])

		else:
			logger.info('No more queries to be tested. Solution not found!')
			logger.info('Increasing the number of lines of code.')
			loc = loc + 1


debug=False
dir ="./"
if __name__ == '__main__':
	# sys.stderr = open('output.err', 'w')
	# sys.stderr.close()
	# sys.stderr = sys.__stderr__
	if "-d" in argv:
		debug = True
		print("Hey")
		logger.setLevel('DEBUG')
	else:
		logger.setLevel('CRITICAL')
	seed = None
	if "-h" in argv:
		exit("Usage: python3 squaresEnumerator.py [tree|lines] [flags -h, ...] input.in\nflags:\n-on : computing symmetries online\n-off : computing symmetries offline\n-d : debug info\n\n-nr : only SQL solution\n\nDefault: lines enumerator and without symmetry breaking")
	if len(argv) > 1:
		try:
			seed = int(argv[1])
		except ValueError:
			pass
	prog = main(seed)


class Squares(object):
	"""docstring for Squares."""

	def __init__(self):
		super(Squares, self).__init__()
		self.template = "inputs: {inputs}\noutput: {output}\nconst: {const}\naggrs: {aggrs}\nattrs: {attrs}\nbools:\nloc: {loc}\n"

	def synthesize(self, inputs, output_ex, const="", aggrs="", attrs="", loc=0):
		"""docstring for Squares."""
		global argv, dir
		dir = "../"
		ins = list([])
		temp = self.template

		try:
			path, dirs, files = next(os.walk("../users/files"))
		except:
			path, dirs, files = next(os.walk("users/files"))
			dir="./"
		file_count = str(len(files) +1)

		i_c = 0
		for i in inputs:
			input = open(dir+"users/tables/"+"i"+str(file_count)+str(i_c),"w+")
			input.write(i)
			input.close()
			ins.append(dir+"users/tables/"+"i"+str(file_count)+str(i_c))
			i_c += 1
		output = open(dir+"users/tables/"+"o"+str(file_count),"w+")
		output.write(output_ex)
		output.close()
		output = dir+"users/tables/o"+str(file_count)

		input_file_name = dir+"users/files/"+"f"+str(file_count)
		input_file = open(input_file_name, "w+")
		inputs=str(ins).replace("\'","").replace("]","").replace("[","")
		input_file.write(temp.format(inputs=inputs,output=output, const="\""+const.replace(",","\",\"").replace(" ","")+"\"", aggrs="\""+aggrs.replace(",","\",\"").replace(" ","")+"\"", attrs="\""+attrs.replace(",","\",\"").replace(" ","")+"\"", loc=str(loc)).replace("\"\"",""))
		input_file.close()

		argv = []
		argv.append("lines")
		argv.append(input_file_name)
		return main()




# # not used
# def beautifier_aux(tokens):
# 	# print(tokens)
# 	global index_table_aux
# 	sub_query = ""
# 	left_index = right_index = None
# 	for t in tokens:
# 		if "(SELECT" in str(t):
# 			if "AS `TBL_RIGHT`" == str(t)[-13:]:
# 				right_index = index_table_aux
# 				index_table_aux += 1
# 			elif "AS `TBL_LEFT`" == str(t)[-13:]:
# 				left_index = index_table_aux
# 				index_table_aux += 1
# 		if "`TBL_LEFT`" in str(t):
# 			left_index = index_table_aux
# 			index_table_aux += 1
# 		if "`TBL_RIGHT`" in str(t):
# 			right_index = index_table_aux
# 			index_table_aux += 1
# 	for t in tokens:
# 		if "(SELECT" in str(t):
# 			# print(t)
# 			if "AS `TBL_RIGHT`" == str(t)[-13:]:
# 				aux_str = str(t).split("AS `TBL_RIGHT`")
# 				new_input = sp.parse(aux_str[0])[0]
# 				# print("RIGHT", t, "-->", new_input)
# 				sub_query += beautifier_aux(new_input) + " AS " + "table_"+str(right_index)
# 			elif "AS `TBL_LEFT`" == str(t)[-13:]:
# 				aux_str = str(t).split("AS `TBL_LEFT`")
# 				new_input = sp.parse(aux_str[0])[0]
# 				# print("LEFT", t, "-->", new_input)
# 				sub_query += beautifier_aux(new_input) + " AS " + "table_"+str(left_index)
# 			else:
# 				sub_query += beautifier_aux(t)
# 		else:
# 			sub_query += str(t).replace("`TBL_LEFT`", "table_"+str(left_index)).replace("`TBL_RIGHT`", "table_"+str(right_index))
# 	return sub_query
