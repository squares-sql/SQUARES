#!/usr/bin/env python

from z3 import *
from collections import deque
import dsl as D

class AST:
	def __init__(self):
		self.head = None

class ASTNode:
	def __init__(self, nb=None, depth=None, children=None):
		self.id = nb
		self.depth = depth
		self.children = children
		self.production = None

class Enumerator:
  # z3 solver
  z3_solver = Solver()

  # productions that are leaf
  leaf_productions = []

  # productions that are input
  input_productions = []

  # z3 variables for each production node
  variables = []

  # z3 variables to denote if a node is a function or not
  variables_fun = []

  # productions of a given type
  type_productions = {}

  # maps the id to the corresponding production
  id2production = {}

  def initProduction(self):
    for p in self.spec.productions():
      self.id2production[p.id] = p

  def initTypeProductions(self):
    for t in self.spec.types():
      self.type_productions[str(t)] = []
      for p in self.spec.productions():
        if p.lhs == t:
          self.type_productions[str(t)].append(p)

  def initLeafProductions(self):
    for p in self.spec.productions():
      #FIXME: improve empty integration
      if not p.is_function() or str(p).find('Empty')!=-1:
        self.leaf_productions.append(p)

  def initInputProductions(self):
    for p in self.spec.productions():
      #FIXME: improve the check to see if a production is an input
      if len(p.rhs)==1 and str(p).find('param')!=-1:
      #if isinstance(p, ParamProduction):
        self.input_productions.append(p)

  def createVariables(self, solver):
    for x in range(0,len(self.nodes)):
      name = 'n' + str(x+1)
      v = Int(name)
      self.variables.append(v)
      # variable range constraints
      solver.add(And(v >= 0, v < self.spec.num_productions()))
      hname = 'h' + str(x+1)
      h = Int(hname)
      self.variables_fun.append(h)
      # high variables range constraints
      solver.add(And(h >= 0, h <= 1))

  def createOutputConstraints(self, solver):
    '''The output production matches the output type'''
    ctr = None
    for p in self.spec.productions():
      if p.lhs == self.output:
        if ctr == None:
          # variables[0] is the root of the tree
          ctr = self.variables[0] == p.id
        else:
          ctr = Or(ctr, self.variables[0] == p.id)
    solver.add(ctr)

  def createLocConstraints(self, solver):
    '''Exactly k functions are used in the program'''
    ctr = self.variables_fun[0]
    for x in range(1,len(self.variables_fun)):
      ctr += self.variables_fun[x]
    ctr_fun = ctr == self.loc
    solver.add(ctr_fun)

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

  def createFunctionConstraints(self, solver):
    '''If a function occurs then set the function variable to 1 and 0 otherwise'''
    assert len(self.nodes) == len(self.variables_fun)
    for x in range(0,len(self.nodes)):
      for p in self.spec.productions():
        # FIXME: improve empty integration
        if p.is_function() and str(p).find('Empty')==-1:
          ctr = Implies(self.variables[x] == p.id, self.variables_fun[x] == 1)
          solver.add(ctr)
        else:
          ctr = Implies(self.variables[x] == p.id, self.variables_fun[x] == 0)
          solver.add(ctr)

  def createLeafConstraints(self, solver):
    for x in range(0,len(self.nodes)):
      n = self.nodes[x]
      if n.children == None:
        ctr = self.variables[x] == self.leaf_productions[0].id
        for y in range(1,len(self.leaf_productions)):
          ctr = Or(self.variables[x] == self.leaf_productions[y].id, ctr)
        solver.add(ctr)

  def createChildrenConstraints(self, solver):
    for x in range(0,len(self.nodes)):
      n = self.nodes[x]
      if n.children != None:
        for p in self.spec.productions():
          assert len(n.children) > 0
          for y in range(0,len(n.children)):
            ctr = None
            child_type = 'Empty'
            if p.is_function() and y < len(p.rhs):
              child_type = str(p.rhs[y])
            for t in self.type_productions[child_type]:
              if ctr == None:
                ctr = self.variables[n.children[y].id-1] == t.id
              else:
                ctr = Or(ctr, self.variables[n.children[y].id-1] == t.id)
              ctr = Implies(self.variables[x] == p.id, ctr)
            solver.add(ctr)

  def maxChildren(self) -> int:
    '''Finds the maximum number of children in the productions'''
    max = 0
    for p in self.spec.productions():
      if len(p.rhs) > max:
        max = len(p.rhs)
    return max

  def buildKTree(self,children, depth):
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

  def __init__(self, spec=None, depth=None, loc=None):
    self.spec = spec
    self.depth = depth
    self.loc = loc
    self.output = spec.output
    self.max_children = self.maxChildren()
    self.tree,self.nodes = self.buildKTree(self.max_children, self.depth)
    self.initProduction()
    self.initTypeProductions()
    self.initLeafProductions()
    self.initInputProductions()
    self.createVariables(self.z3_solver)
    self.createOutputConstraints(self.z3_solver)
    self.createLocConstraints(self.z3_solver)
    self.createInputConstraints(self.z3_solver)
    self.createFunctionConstraints(self.z3_solver)
    self.createLeafConstraints(self.z3_solver)
    self.createChildrenConstraints(self.z3_solver)

  def blockModel(self):
    m = self.z3_solver.model()
    block = []
    for d in m:
      c = d()
      block.append(c != m[d])
    self.z3_solver.add(Or(block))

  def buildProgram(self):
    m = self.z3_solver.model()
    result = [0] * len(m)
    for x in m:
      c = x()
      a=str(x)
      if a[:1] == 'n':
        result[int(a[1:])-1] = int(str(m[c]))

    code = []
    for n in self.nodes:
      prod=self.id2production[result[n.id-1]]
      code.append(prod)

    builder = D.Builder(self.spec)
    builder_nodes = [None] * len(self.nodes)
    for x in range(0,len(self.nodes)):
      y=len(self.nodes)-x-1
      if str(code[self.nodes[y].id-1]).find('Empty') == -1:
        children = []
        if self.nodes[y].children != None:
          for c in self.nodes[y].children:
            if str(code[c.id-1]).find('Empty') == -1:
              assert builder_nodes[c.id-1] != None
              children.append(builder_nodes[c.id-1])
        builder_nodes[y] = builder.make_node(code[self.nodes[y].id-1].id, children)
      
    assert(builder_nodes[0] != None)
    return builder_nodes[0]

  def solve(self):
    return self.z3_solver.check()
