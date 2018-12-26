#!/usr/bin/env python

from z3 import *
from collections import deque

class Variable:
  def __init__(self, node=None, name=None):
    self.name = 'x' + node + '_' + name
    self.node = node
    self.production = name

class TreeNode:
  def __init__(self, nb=None, depth=None, children=None):
    self.id = nb
    self.depth = depth
    self.nextval = children

class Node:
  def __init__(self, t=None, v=None, high=None, children=None):
    self.type = t
    self.val = v
    self.high = high
    self.nextval = children

class SLinkedList:
  def __init__(self):
    self.headval = None

class Enumerator:
  s = Solver()
  value2production = {}
  production2value = {}
  production2high = {}

  def createConstraints(self):
    i = 1
    for p in productions:
      self.value2production[p.val] = i
      self.production2value[i] = p.val
      if p.high:
        self.production2high[p.val] = True
      else:
        self.production2high[p.val] = False
      i += 1

    type2production = {}
    for t in types:
      type2production[t] = []

    i = 1
    for p in productions:
      type2production[p.type].append(i)
      i += 1

    leaf_productions = []
    i = 1
    for p in productions:
      if len(p.nextval) == 0:
        leaf_productions.append(i)
      i += 1

    input_productions = []
    i = 1 
    for p in productions:
      if p.val[:5] == 'input':
        input_productions.append(i)
      i += 1

    print("nodes=",len(nodes))
    print("productions=",len(productions))

    variables = []
    high_variables = []
    for x in range(0,len(nodes)):
      name = 'node' + str(x+1)
      v = Int(name)
      variables.append(v)
      # variable range constraints
      self.s.add(And(v >= 1, v <= len(productions)))
      hname = 'hnode' + str(x+1)
      h = Int(hname)
      high_variables.append(h)
      # high variables range constraints
      self.s.add(And(h >= 0, h <= 1))

    variable_root = variables[0]

    # output constraints
    ctr_output = None
    index = 1
    for n in productions:
      if n.type == output:
        if ctr_output == None:
          ctr_output = variable_root == index
        else:
          ctr_output = Or(ctr_output, variable_root == index)
      index += 1
    self.s.add(ctr_output)   

    # fix the number of higher order functions
    ctr = high_variables[0]
    for x in range(1,len(high_variables)):
      ctr += high_variables[x]
    ctr_high = ctr == self.loc
    self.s.add(ctr_high)

    # each input will appear somewhere
    for x in range(0,len(input_productions)):
      node_pos = 1
      ctr = None
      for n in nodes:
        if ctr == None:
          ctr = variables[node_pos-1] == input_productions[x]
        else:
          ctr = Or(variables[node_pos-1] == input_productions[x], ctr)
        node_pos += 1
      self.s.add(ctr)

    node_pos = 1
    for n in nodes:
      prod_pos = 1
      for p in productions:
          #print("production=",p.val)
        if p.high:
          ctr = Implies(variables[node_pos-1] == prod_pos, high_variables[node_pos-1] == 1)
          #print(ctr)
          self.s.add(ctr)
        else:
          ctr = Implies(variables[node_pos-1] == prod_pos, high_variables[node_pos-1] == 0)
          #print(ctr)
          self.s.add(ctr)
        prod_pos += 1
      node_pos += 1

    # children constraints
    node_pos = 1
    for n in nodes:
      prod_pos = 1
      #print("node=",node_pos)
      if n.nextval == None:
        # leaf node
        ctr = variables[node_pos-1] == leaf_productions[0]
        for x in range(1,len(leaf_productions)):
          ctr = Or(variables[node_pos-1] == leaf_productions[x], ctr)
        self.s.add(ctr)
      else:
        for p in productions:
          #print("production=",p.val)
          if n.nextval != None:
            assert len(n.nextval) > 0
            child_pos = 0
            #print("production children=",len(p.nextval))
            for c in n.nextval:
              ctr = None
              child_type = 'empty'
              if child_pos < len(p.nextval):
                child_type = p.nextval[child_pos].type
              #print("child type=",child_type)
              for t in type2production[child_type]:
                if ctr == None:
                  ctr = variables[c.id-1] == t
                else:
                  ctr = Or(ctr, variables[c.id-1] == t)
              ctr = Implies(variables[node_pos-1] == prod_pos, ctr)
              self.s.add(ctr)
              child_pos += 1
          prod_pos += 1
      node_pos += 1

  def __init__(self, ast=None, nodes=None, productions=None, loc=None):
    self.ast = ast
    self.productions = productions
    self.nodes = nodes
    self.loc = loc
    self.createConstraints()
  
  def blockModel(self):
    m = self.s.model()
    block = []
    for d in m:
      c = d()
      block.append(c != m[d])
    self.s.add(Or(block))

  def printModel(self):
    m = self.s.model()
    print("=====================")
    result = [0] * len(m)
    for x in m:
      c = x()
      a=str(x)
      if a[:4] == 'node':
        result[int(a[4:])-1] = int(str(m[c]))

    code = []
    index=1
    for n in nodes:
      prod=self.production2value[result[n.id-1]]
      print(prod)
      index += 1
    print("=====================")

  def solve(self):
    return self.s.check()

def buildKTree(children, depth) -> (Node,SLinkedList):
  nodes = []
  tree = SLinkedList()
  root = TreeNode(1,1)
  nb = 1
  tree.headval = root
  d = deque()  
  d.append(root)
  nodes.append(root)
  while len(d) != 0:
    current = d.popleft()
    current.nextval = []
    for x in range(0, children):
      nb += 1
      c = TreeNode(nb,current.depth+1)
      nodes.append(c)
      current.nextval.append(c)
      if c.depth < depth:
        d.append(c)
  return tree,nodes

def maxChildren(prod) -> int:
    max = 0
    for p in productions:
      if len(p.nextval) > max:
        max = len(p.nextval)
    return max

types = ['empty','int','list']
output = 'int'
productions = []
productions.append(Node('empty','empty',False,[]))
productions.append(Node('int','0',False,[]))
productions.append(Node('int','1',False,[]))
productions.append(Node('int','2',False,[]))
productions.append(Node('int','last',True,[Node('list')]))
productions.append(Node('int','head',True,[Node('list')]))
productions.append(Node('int','sum',True,[Node('list')]))
productions.append(Node('list','take',True,[Node('list'),Node('int')]))
productions.append(Node('list','sort',True,[Node('list')]))
productions.append(Node('list','reverse',True,[Node('list')]))
productions.append(Node('list','input1',False,[]))

max_children = maxChildren(productions)
tree, nodes = buildKTree(max_children, 4)
enum = Enumerator(tree, nodes, productions, 3)

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
