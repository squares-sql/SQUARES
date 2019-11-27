#!/usr/bin/env python
# File:	gen_lattices.py
# Description:	lattices generator
# Author:	Pedro M Orvalho
# Created on:	05-04-2019 14:09:37
# Usage:	python gen_lattices.py loc
# Python version:	3.6.4

from .lines import *
from sys import argv, stderr

def blockModelAux(variables, model, solver):
	block = []
	# block the model using only the variables that correspond to productions

	for x in variables:
		block.append(x != model[x])

	ctr = Or(block)
	solver.add(ctr)
	# return models

def getModels(solver, vars):
	models = []
	while 1:
			res = solver.check()
			if res != sat:
				break
			model = solver.model()
			if model is not None:
				models.append(model)
				blockModelAux(vars, model, solver)
		
	return models

def getModel(solver, vars):
	res = solver.check()
	if res != sat:
		return
	model = solver.model()
	if model is not None:
		blockModelAux(vars, model, solver)
		return model
		
def printModels(models):
	string = ''
	for m in models:
		string += str(m) + "|"
	return string[:-1]

def writeLattice(node):
    string = str(node.nb)
    for c in node.children:
        string += writeLattice(c)    
    return string
    
class SymmetryFinder(object):

	def __init__(self, loc):
		self.loc = loc
		
	def getChildrenNonZero(self, children):
		cnt = 0
		for c in children:
			if c.nb != 0:
				cnt += 1 
		return cnt

	def getSymmetryConstraints(self, node, pid):
		if node.nb == 0:
			return [], [], []
		name = 'x_' +str(node.nb)
		node.var = Int(name)
		if node.children != []:
			res, vars, cur_val = [And(self.getChildrenNonZero(node.children) < node.var, node.var < pid)], [node.var], [node.var!=node.nb]

			for c in node.children:
				vars_aux, res_aux, cur_val_aux = self.getSymmetryConstraints(c, node.var)
				res += res_aux
				vars += vars_aux
				cur_val += cur_val_aux
			return vars, res, cur_val
		else:
			return [node.var], [And(1 <= node.var,node.var < pid)], [node.var!=node.nb]

	def allDiff(self, vars, solver):
		for v in range(len(vars)):
			for v_1 in range(v+1,len(vars)):
				if vars[v] is not vars[v_1]:
					solver.add(vars[v]!=vars[v_1])

	def findSymmetries(self, last_line):
		# print("Finding findSymmetries")
		models = []
		#DEBUG self.printTree(last_line)
		constraints = []
		all_vars = []
		current_values = []
		
		for c in last_line.children:
			if c.nb == 0:
				continue
			vars_aux, constraints_aux, cur_val = self.getSymmetryConstraints(c, last_line.nb)
			all_vars += vars_aux
			constraints += constraints_aux
			current_values += cur_val
		# print(constraints)
		# print(current_values)
		
		sym_solver = Solver()
		sym_solver.add(Or(current_values))
		sym_solver.add(constraints)
		# for const in constraints:
			# print(const)
			# sym_solver.add(const)

		# create all diff constraint for all variables
		self.allDiff(all_vars, sym_solver)
		# print(And(self.allDiff(all_vars)))
		return getModels(sym_solver, all_vars)

class LatticeBuilder(object):
	"""docstring for LatticeBuilder"""
	def __init__(self, loc):
		self.loc = loc
		self.sym_finder = SymmetryFinder(self.loc)

	def createTree(self, id, node):
	    j = id
	    node.children = []
	    for i in range(j+1,j+self.loc):
	        l = Node(i)
	        l.h = node.h + 1
	        name = 'x_' +str(l.nb)
	        l.var = Int(name)
	        l.children = []
	        id += 1
	        node.children.append(l)

	    for l in node.children:
	        if l.h == self.loc:
	            break
	        id = self.createTree(id, l)

	    return id

	def printTree(self, root):

		for c in root.children:
			print('Id father: {} h {} var {} -> Id son {} h {} var {}'.format(root.nb, root.h, root.var, c.nb, c.h, c.var))
			self.printTree(c)

	def Constraints(self, node):
		res = [Or(And(1 <= node.var, node.var < self.loc), node.var == 0)]
		vars = [node.var]
		
		prev_child = None
		for c in node.children:
			res += [Implies(node.var == 0, c.var == 0)]
			if prev_child is not None:
				res += [Implies(prev_child.var == 0, c.var == 0)]
				
			res += [Or(node.var > c.var, node.var == 0)]
			res_aux, vars_aux = self.Constraints(c)
			res += res_aux
			vars += vars_aux
			prev_child = c

		return res, vars

	def createLattice(self, lat_node, node, model):
		lat_node.children = []
		for c in node.children:
			val = int(str(model[c.var]))
			child = Node(val)
			if val !=0:
				name = 'x_' +str(val)
				child.var = Int(name)
			child.h = lat_node.h + 1
			self.createLattice(child, c, model)
			lat_node.children.append(child)

	def printLattice(self, root):
		for c in root.children:
			print('Id father: {} h {} -> Id son {} h {}'.format(root.nb, root.h, c.nb, c.h))
			self.printTree(c)

	def genLattices(self):
		lat_solver = Solver()
		root = Node(1)
		root.h = 1
		name = 'x_' +str(root.nb)
		root.var = Int(name)
		self.createTree(1, root)
		# self.printTree(root)
		lat_solver.add(root.var==self.loc)
		constraints, vars = [], []
		prev_child = None
		for c in root.children:
			consts_aux, vars_aux = self.Constraints(c)
			constraints += consts_aux
			if prev_child is not None:
				constraints += [Implies(prev_child.var == 0, c.var == 0)]
			prev_child = c
			vars += vars_aux

		lat_solver.add(constraints)
		# print(constraints)

		for v in range(len(vars)):
			for v_1 in range(v+1,len(vars)):
				if vars[v] is not vars[v_1]:
					lat_solver.add(Or(vars[v]!=vars[v_1],And(vars[v]==0,vars[v_1]==0)))
					# print(Or(vars[v]!=vars[v_1],And(vars[v]==0,vars[v_1]==0)))

		for i in range(1,self.loc):
			lst = []
			for v in vars:
				lst.append(v==i)
			lat_solver.append(Or(lst))
			# print(Or(lst))
		# print("Gerring models for lattices")
		while 1:
			model = getModel(lat_solver, vars)
			if model is None:
				break
			last_line = Node(self.loc)
			last_line.h = 0
			self.createLattice(last_line, root, model)
			models = self.sym_finder.findSymmetries(last_line)
			print(writeLattice(last_line), file=sys.stderr)
			print(writeLattice(last_line)+":"+printModels(models))


if __name__ == '__main__':
	if len(argv)!= 2:
		exit("Usage: python3 gen_lattices.py loc")
	lat_builder = LatticeBuilder(int(argv[-1]))
	lat_builder.genLattices()
	