from z3 import *
from .. import dsl as D


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
        self.bound = 0
        self.ub = 0
        self.solver = solver
        self.spec = spec
        self.variables = variables
        self.id = 0
        self.objective = []
        self.nodes = nodes
        self.weights = []

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
                self.solver.add(
                    Implies(self.variables[y] == x, self.var_occurs[x] == 1))
            self.solver.add(Implies(ctr, rhs))

        for x in range(0, len(self.var_occurs)):
            for y in range(0, len(self.variables)):
                self.solver.add(
                    Implies(self.var_occurs[x] == 0, self.variables[y] != x))

    def mk_is_not_parent(self, parent, child, weight=100):
        child_pos = []
        # find positions that type-check between parent and child
        for x in range(0, len(parent.rhs)):
            if child.lhs == parent.rhs[x]:
                child_pos.append(x)

        for n in self.nodes:
            # not a leaf node
            if n.children != None:
                if weight != 100:
                    # FIXME: reduce duplication of code
                    name = 'relax' + str(self.id)
                    v = Int(name)
                    self.cost_relax_vars[v] = weight
                    self.relax_vars.append(v)
                    self.objective.append(Product(weight, v))
                    self.weights.append(weight)
                    self.ub += weight
                    # domain of the relaxation variable
                    self.solver.add(Or(v == 0, v == 1))
                    # constraint for the is_parent constraint
                    ctr_children = []
                    for p in range(0, len(child_pos)):
                        ctr_children.append(
                            self.variables[n.children[p].id - 1] == child.id)

                    self.solver.add(
                        Or(Implies(Or(ctr_children), self.variables[n.id - 1] != parent.id), v == 1))
                    # relation between relaxation variables and constraint
                    self.solver.add(Implies(v == 1, Or(
                        self.variables[n.id - 1] == parent.id, Not(Or(ctr_children)))))
                    self.solver.add(
                        Implies(And(self.variables[n.id - 1] != parent.id, Or(ctr_children)), v == 0))
                    self.id = self.id + 1
                else:
                    ctr_children = []
                    for p in range(0, len(child_pos)):
                        ctr_children.append(
                            self.variables[n.children[p].id - 1] == child.id)

                    self.solver.add(
                        Implies(Or(ctr_children), self.variables[n.id - 1] != parent.id))

    # FIXME: dissociate the creation of variables with the creation of constraints?
    def mk_is_parent(self, parent, child, weight=100):
        '''children production will have the parent production with probability weight'''

        child_pos = []
        # find positions that type-check between parent and child
        for x in range(0, len(parent.rhs)):
            if child.lhs == parent.rhs[x]:
                child_pos.append(x)

        for n in self.nodes:
            # not a leaf node
            if n.children != None:
                if weight != 100:
                    # FIXME: reduce duplication of code
                    name = 'relax' + str(self.id)
                    v = Int(name)
                    self.cost_relax_vars[v] = weight
                    self.relax_vars.append(v)
                    self.objective.append(Product(weight, v))
                    self.weights.append(weight)
                    self.ub += weight
                    # domain of the relaxation variable
                    self.solver.add(Or(v == 0, v == 1))
                    # constraint for the is_parent constraint
                    ctr_children = []
                    for p in range(0, len(child_pos)):
                        ctr_children.append(
                            self.variables[n.children[p].id - 1] == child.id)

                    self.solver.add(
                        Or(Implies(self.variables[n.id - 1] == parent.id, Or(ctr_children)), v == 1))
                    # relation between relaxation variables and constraint
                    self.solver.add(Implies(v == 1, Or(
                        self.variables[n.id - 1] != parent.id, Not(Or(ctr_children)))))
                    self.solver.add(
                        Implies(And(self.variables[n.id - 1] == parent.id, Or(ctr_children)), v == 0))
                    self.id = self.id + 1
                else:
                    ctr_children = []
                    for p in range(0, len(child_pos)):
                        ctr_children.append(
                            self.variables[n.children[p].id - 1] == child.id)

                    self.solver.add(
                        Implies(self.variables[n.id - 1] == parent.id, Or(ctr_children)))

    def mk_not_occurs(self, production, weight=100):
        '''a production will not occur with a given probability'''
        if len(self.var_occurs) == 0:
            self.createVariablesOccurrence()

        if weight != 100:
            name = 'relax' + str(self.id)
            v = Int(name)
            self.cost_relax_vars[v] = weight
            self.relax_vars.append(v)
            self.objective.append(Product(weight, v))
            self.weights.append(weight)
            self.ub += weight
            # domain of the relaxation variable
            self.solver.add(Or(v == 0, v == 1))
            # constraint for at least once
            self.solver.add(Or(self.var_occurs[production.id] == 0, v == 1))
            # relation between relaxation variables and constraint
            self.solver.add(
                Implies(v == 1, self.var_occurs[production.id] != 0))
            self.solver.add(
                Implies(self.var_occurs[production.id] == 0, v == 0))
            self.id = self.id + 1
        else:
            self.solver.add(self.var_occurs[production.id] == 0)

    # FIXME: dissociate the creation of variables with the creation of constraints?
    def mk_occurs(self, production, weight=100):
        '''a production will occur with a given probability'''
        if len(self.var_occurs) == 0:
            self.createVariablesOccurrence()

        if weight != 100:
            name = 'relax' + str(self.id)
            v = Int(name)
            self.cost_relax_vars[v] = weight
            self.relax_vars.append(v)
            self.objective.append(Product(weight, v))
            self.weights.append(weight)
            self.ub += weight
            # domain of the relaxation variable
            self.solver.add(Or(v == 0, v == 1))
            # constraint for at least once
            self.solver.add(Or(self.var_occurs[production.id] == 1, v == 1))
            # relation between relaxation variables and constraint
            self.solver.add(
                Implies(v == 1, self.var_occurs[production.id] != 1))
            self.solver.add(
                Implies(self.var_occurs[production.id] == 1, v == 0))
            self.id = self.id + 1
        else:
            self.solver.add(self.var_occurs[production.id] == 1)

    def isSubsetSum(self, set, n, sum):
        subset = ([[False for i in range(sum + 1)]
                   for i in range(n + 1)])

        # If sum is 0, then answer is true
        for i in range(n + 1):
            subset[i][0] = True

            # If sum is not 0 and set is empty,
            # then answer is false
            for i in range(1, sum + 1):
                subset[0][i] = False

            # Fill the subset table in botton up manner
            for i in range(1, n + 1):
                for j in range(1, sum + 1):
                    if j < set[i - 1]:
                        subset[i][j] = subset[i - 1][j]
                    if j >= set[i - 1]:
                        subset[i][j] = (subset[i - 1][j]
                                        or subset[i - 1][j - set[i - 1]])

        return subset[n][sum]

    def optimize(self, solver):
        model = None
        cost = 0
        res = sat
        nb_sat = 0
        nb_unsat = 0
        # no optimization is defined
        if len(self.objective) == 0:
            res = solver.check()
            if res == sat:
                model = solver.model()

        # optimization using the LSU algorithm
        else:
            solver.set(unsat_core=True)
            solver.push()
            ctr = Sum(self.objective) <= self.bound
            solver.assert_and_track(ctr, 'obj')

            while model == None and res == sat:
                res = solver.check()
                if res == sat:
                    nb_sat += 1
                    model = solver.model()
                    cost = self.computeCost(model)
                    assert (cost == self.bound)
                    solver.pop()
                else:
                    nb_unsat += 1
                    solver.pop()
                    core = solver.unsat_core()
                    if len(core) != 0:
                        self.bound += 1
                        while(not self.isSubsetSum(self.weights, len(self.weights), self.bound) and self.bound <= self.ub):
                            self.bound += 1
                        solver.push()
                        ctr = Sum(self.objective) <= self.bound
                        solver.assert_and_track(ctr, 'obj')
                        res = sat

        assert(solver.num_scopes() == 0)
        self.bound = cost
        return model

    def computeCost(self, model):
        cost = 0
        for v in self.relax_vars:
            if model[v] == 1:
                cost = cost + self.cost_relax_vars[v]

        return cost
