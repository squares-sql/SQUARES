#!/usr/bin/env python

from z3 import *
from collections import deque

class AST:
	def __init__(self):
		self.head = None

class ASTNode:
	def __init__(self, nb=None, depth=None, children=None):
		self.id = nb
		self.depth = depth
		self.children = children
		self.production = None

class Production:
  def __init__(self, i=None, t=None, name=None, high=None, leaf=None, inp=None, children=None):
    self.id = i
    self.type = t
    self.name = name
    self.high = high
    self.leaf = leaf
    self.input = inp
    self.children = children

class Variable:
  def __init__(self, node=None, name=None):
    self.name = 'x' + node + '_' + name
    self.node = node
    self.production = name

class Enumerator:
  # z3 solver
  z3_solver = Solver()

  # productions that are leaf
  leaf_productions = []

  # productions that are input
  input_productions = []

  # z3 variables for each production node
  variables = []

  # z3 variables for each higher order node
  variables_high = []

  # productions of a given type
  type_productions = {}

  # id -> production map
  id2production = {}

  def initProductionMap(self):
    for p in self.productions:
      self.id2production[p.id] = p.name

  def initTypeProductions(self):
    for t in self.types:
      self.type_productions[t] = []
      for p in self.productions:
        if p.type == t:
          self.type_productions[t].append(p)

  def initLeafProductions(self):
    for p in self.productions:
      if p.leaf:
        self.leaf_productions.append(p)

  def initInputProductions(self):
    for p in self.productions:
      if p.input:
        self.input_productions.append(p)

  def createVariables(self, solver):
    for x in range(0,len(nodes)):
      name = 'n' + str(x+1)
      v = Int(name)
      self.variables.append(v)
      # variable range constraints
      solver.add(And(v >= 1, v <= len(self.productions)))
      hname = 'h' + str(x+1)
      h = Int(hname)
      self.variables_high.append(h)
      # high variables range constraints
      solver.add(And(h >= 0, h <= 1))

  def createOutputConstraints(self, solver):
    '''The output production matches the output type'''
    ctr = None
    for p in self.productions:
      if p.type == output:
        if ctr == None:
          # variables[0] is the root of the tree
          ctr = self.variables[0] == p.id
        else:
          ctr = Or(ctr, self.variables[0] == p.id)
    solver.add(ctr)

  def createLocConstraints(self, solver):
    '''Exactly k higher order functions are used in the program'''
    ctr = self.variables_high[0]
    for x in range(1,len(self.variables_high)):
      ctr += self.variables_high[x]
    ctr_high = ctr == self.loc
    solver.add(ctr_high)

  def createInputConstraints(self, solver):
    '''Each input will appear at least once in the program'''
    for x in range(0,len(self.input_productions)):
      ctr = None
      for y in range(0, len(self.nodes)):
        if ctr == None:
          ctr = self.variables[y] == self.input_productions[x].id
        else:
          ctr = Or(self.variables[y] == self.input_productions[x].id, ctr)
      solver.add(ctr)

  def createHigherOrderConstraints(self, solver):
    '''If a higher order function occurs then set the higher order variable to 1 and 0 otherwise'''
    assert len(self.nodes) == len(self.variables_high)
    for x in range(0,len(self.nodes)):
      for p in self.productions:
        if p.high:
          ctr = Implies(self.variables[x] == p.id, self.variables_high[x] == 1)
          solver.add(ctr)
        else:
          ctr = Implies(self.variables[x] == p.id, self.variables_high[x] == 0)
          solver.add(ctr)

  def createLeafConstraints(self, solver):
    for x in range(0,len(self.nodes)):
      if n.children == None:
        ctr = self.variables[x] == self.leaf_productions[0]
        for y in range(1,len(self.leaf_productions)):
          ctr = Or(variables[x] == leaf_productions[y], ctr)
        solver.add(ctr)

  def createChildrenConstraints(self, solver):
    for x in range(0,len(self.nodes)):
      n = self.nodes[x]
      if n.children != None:
        for p in self.productions:
          assert len(n.children) > 0
          for y in range(0,len(n.children)):
            ctr = None
            child_type = 'empty'
            if y < len(p.children):
              child_type = p.children[y].type
            for t in self.type_productions[child_type]:
              if ctr == None:
                ctr = self.variables[n.children[y].id-1] == t.id
              else:
                ctr = Or(ctr, self.variables[n.children[y].id-1] == t.id)
              ctr = Implies(self.variables[x] == p.id, ctr)
            solver.add(ctr)

  def __init__(self, output=None, types=None, ast=None, nodes=None, productions=None, loc=None):
    self.output = output
    self.ast = ast
    self.productions = productions
    self.nodes = nodes
    self.loc = loc
    self.types = types
    self.initProductionMap()
    self.initTypeProductions()
    self.initLeafProductions()
    self.initInputProductions()
    self.createVariables(self.z3_solver)
    self.createOutputConstraints(self.z3_solver)
    self.createLocConstraints(self.z3_solver)
    self.createInputConstraints(self.z3_solver)
    self.createHigherOrderConstraints(self.z3_solver)
    self.createChildrenConstraints(self.z3_solver)

  def blockModel(self):
    m = self.z3_solver.model()
    block = []
    for d in m:
      c = d()
      block.append(c != m[d])
    self.z3_solver.add(Or(block))

  def printModel(self):
    m = self.z3_solver.model()
    print("=====================")
    result = [0] * len(m)
    for x in m:
      c = x()
      a=str(x)
      if a[:1] == 'n':
        result[int(a[1:])-1] = int(str(m[c]))

    code = []
    index=1
    for n in nodes:
      prod=self.id2production[result[n.id-1]]
      print(prod)
      index += 1
    print("=====================")

  def solve(self):
    return self.z3_solver.check()


def buildKTree(children, depth):
  '''Builds a K-tree that will contain the program'''
  nodes = []
  tree = AST()
  root = ASTNode(1,1)
  nb = 1
  tree.head = root
  d = deque()  
  d.append(root)
  nodes.append(root)
  while len(d) != 0:
    current = d.popleft()
    current.children = []
    for x in range(0, children):
      nb += 1
      c = ASTNode(nb,current.depth+1)
      nodes.append(c)
      current.children.append(c)
      if c.depth < depth:
        d.append(c)
  return tree,nodes

def maxChildren(prod) -> int:
    max = 0
    for p in productions:
      if len(p.children) > max:
        max = len(p.children)
    return max


# this information should come from the dsl, spec
# Note: input/empty *MUST* be part of the productions
types = ['empty','int','list']
output = 'int'
productions = []
productions.append(Production(1,'empty','empty',False,True,False,[]))
productions.append(Production(2,'int','0',False,True,False,[]))
productions.append(Production(3,'int','1',False,True,False,[]))
productions.append(Production(4,'int','2',False,True,False,[]))
productions.append(Production(5,'int','last',True,False,False,[Production(0,'list')]))
productions.append(Production(6,'int','head',True,False,False,[Production(0,'list')]))
productions.append(Production(7,'int','sum',True,False,False,[Production(0,'list')]))
productions.append(Production(8,'list','take',True,False,False,[Production(0,'list'),Production(0,'int')]))
productions.append(Production(9,'list','sort',True,False,False,[Production(0,'list')]))
productions.append(Production(10,'list','reverse',True,False,False,[Production(0,'list')]))
productions.append(Production(11,'list','input1',False,True,True,[]))

max_children = maxChildren(productions)
tree, nodes = buildKTree(max_children, 4)
enum = Enumerator(output, types, tree, nodes, productions, 3)

res = sat
program = 0
while res == sat:
  res = enum.solve()
  if res == sat:
    enum.printModel()
    enum.blockModel()
    program += 1
  else:
    break
print("#programs=",program)
