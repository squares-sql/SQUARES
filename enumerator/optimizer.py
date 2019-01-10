from z3 import *
import dsl as D

class Optimizer:

  # additional variables to track if a production occurs or not in a program
  var_occurs = []

  # relaxation variables
  relax_vars = []

  # keeps track of the current assumptions
  assumptions = []

  # keeps track of the cost of each relaxation variable
  cost_relax_vars = {}

  def __init__(self, solver, spec, variables, nodes):
    self.bound = None
    self.solver = solver
    self.spec = spec
    self.variables = variables
    self.id = 0
    self.objective = []
    self.nodes = nodes

  def createVariablesOccurrence(self):
    for x in range(0, self.spec.num_productions()):
      name = 'occ' + str(x)
      v = Int(name)
      self.var_occurs.append(v)
      self.solver.add(And(v >= 0, v <= 1))

    for x in range(0, len(self.var_occurs)):
      ctr = self.var_occurs[x] == 1
      rhs = self.variables[0] == x 
      for y in range(1, len(self.variables)):
        rhs = Or(rhs, self.variables[y] == x)
        self.solver.add(Implies(self.variables[y] == x, self.var_occurs[x] == 1))
      self.solver.add(Implies(ctr, rhs))

    for x in range(0, len(self.variables)):
      for y in range(0, len(self.variables)):
        self.solver.add(Implies(self.var_occurs[x] == 0, self.variables[y] != x))

  def mk_is_not_parent(self, parent, child, weight=None):
    child_pos = []
    # find positions that type-check between parent and child
    for x in range(0,len(parent.rhs)):
       if child.lhs == parent.rhs[x]:
        child_pos.append(x)

    for n in self.nodes:
      # not a leaf node
      if n.children != None:
        if weight != None:
          # FIXME: reduce duplication of code
          name = 'relax' + str(self.id)
          v = Int(name)
          self.cost_relax_vars[v] = weight
          self.relax_vars.append(v)
          self.objective.append(Product(weight,v))
          # domain of the relaxation variable
          self.solver.add(Or(v == 0, v == 1))
          # constraint for the is_parent constraint
          ctr_children = []
          for p in range(0,len(child_pos)):
            ctr_children.append(self.variables[n.children[p].id-1] == child.id)

          self.solver.add(Or(Implies(Or(ctr_children),self.variables[n.id - 1] != parent.id), v == 1))
          # relation between relaxation variables and constraint
          self.solver.add(Implies(v == 1, Or(self.variables[n.id - 1] == parent.id, Not(Or(ctr_children)))))
          self.solver.add(Implies(And(self.variables[n.id - 1] != parent.id, Or(ctr_children)), v == 0))
          self.id = self.id + 1
        else:
          ctr_children = []
          for p in range(0,len(child_pos)):
            ctr_children.append(self.variables[n.children[p].id-1] == child.id)

          self.solver.add(Implies(Or(ctr_children),self.variables[n.id - 1] != parent.id))

  # FIXME: dissociate the creation of variables with the creation of constraints?
  def mk_is_parent(self, parent, child, weight=None):
    '''children production will have the parent production with probability weight'''
    
    child_pos = []
    # find positions that type-check between parent and child
    for x in range(0,len(parent.rhs)):
       if child.lhs == parent.rhs[x]:
        child_pos.append(x)

    for n in self.nodes:
      # not a leaf node
      if n.children != None:
        if weight != None:
          # FIXME: reduce duplication of code
          name = 'relax' + str(self.id)
          v = Int(name)
          self.cost_relax_vars[v] = weight
          self.relax_vars.append(v)
          self.objective.append(Product(weight,v))
          # domain of the relaxation variable
          self.solver.add(Or(v == 0, v == 1))
          # constraint for the is_parent constraint
          ctr_children = []
          for p in range(0,len(child_pos)):
            ctr_children.append(self.variables[n.children[p].id-1] == child.id)

          self.solver.add(Or(Implies(self.variables[n.id - 1] == parent.id, Or(ctr_children)), v == 1))
          # relation between relaxation variables and constraint
          self.solver.add(Implies(v == 1, Or(self.variables[n.id - 1] != parent.id, Not(Or(ctr_children)))))
          self.solver.add(Implies(And(self.variables[n.id - 1] == parent.id, Or(ctr_children)), v == 0))
          self.id = self.id + 1
        else:
          ctr_children = []
          for p in range(0,len(child_pos)):
            ctr_children.append(self.variables[n.children[p].id-1] == child.id)

          self.solver.add(Implies(self.variables[n.id - 1] == parent.id, Or(ctr_children)))  

  def mk_not_occurs(self, production, weight=None):
    '''a production will not occur with a given probability'''
    if len(self.var_occurs) == 0:
      self.createVariablesOccurrence()

    if weight != None:
      name = 'relax' + str(self.id)
      v = Int(name)
      self.cost_relax_vars[v] = weight
      self.relax_vars.append(v)
      self.objective.append(Product(weight,v))
      # domain of the relaxation variable
      self.solver.add(Or(v == 0, v == 1))
      # constraint for at least once
      self.solver.add(Or(self.var_occurs[production.id] == 0, v == 1))
      # relation between relaxation variables and constraint
      self.solver.add(Implies(v == 1, self.var_occurs[production.id] != 0))
      self.solver.add(Implies(self.var_occurs[production.id] == 0, v == 0))
      self.id = self.id + 1
    else:
      self.solver.add(self.var_occurs[production.id] == 0)

  # FIXME: dissociate the creation of variables with the creation of constraints?
  def mk_occurs(self, production, weight=None):
    '''a production will occur with a given probability'''
    if len(self.var_occurs) == 0:
      self.createVariablesOccurrence()

    if weight != None:
      name = 'relax' + str(self.id)
      v = Int(name)
      self.cost_relax_vars[v] = weight
      self.relax_vars.append(v)
      self.objective.append(Product(weight,v))
      # domain of the relaxation variable
      self.solver.add(Or(v == 0, v == 1))
      # constraint for at least once
      self.solver.add(Or(self.var_occurs[production.id] == 1, v == 1))
      # relation between relaxation variables and constraint
      self.solver.add(Implies(v == 1, self.var_occurs[production.id] != 1))
      self.solver.add(Implies(self.var_occurs[production.id] == 1, v == 0))
      self.id = self.id + 1
    else:
      self.solver.add(self.var_occurs[production.id] == 1)

  def optimize(self, solver):
    model = None
    cost = None
    res = sat
    nb_sat = 0
    # no optimization is defined
    if len(self.objective) == 0:
      res = solver.check()
      if res == sat:
        model = solver.model()

    # optimization using the LSU algorithm
    else:
      while res == sat:
        res = solver.check()
        if res == sat:
          nb_sat += 1
          model = solver.model()
          cost = self.computeCost(model)
          if nb_sat != 1:
            solver.pop()
          if cost == 0:
            break;
          solver.push()
          ctr = Sum(self.objective) <= (cost-1)
          solver.add(ctr)
        else:
          if nb_sat != 0:
            solver.pop()
            # FIXME: use the previous bound to speedup the optimization
            bound = cost
    
    return model

  def computeCost(self, model):
    cost = 0
    for v in self.relax_vars:
      if model[v] == 1:
        cost = cost + self.cost_relax_vars[v]

    return cost
