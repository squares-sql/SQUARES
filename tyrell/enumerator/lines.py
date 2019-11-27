from z3 import *
from collections import deque
from .enumerator import Enumerator
from .gen_lattices import SymmetryFinder
from .. import dsl as D
from ..logger import get_logger
from copy import deepcopy
import time

logger = get_logger('tyrell.enumerator.smt')

class Node(object):
    def __init__(self, nb=None):
        self.nb = nb
        self.var = None
        self.parent = None
        self.children = None
        self.production = None
        self.h = None
        self.id = None

    def __repr__(self) -> str:
        return 'Node({})'.format(self.nb)

class Root(Node):
    def __init__(self, id=None, nb=None, depth=None, children=None, type=None):
        super().__init__(nb)
        self.id = id
        self.depth = depth #num of children
        self.children = children
        self.type = type

    def __repr__(self) -> str:
        return 'Root({}, children={})'.format(self.id, len(self.children))

class Leaf(Node):
    def __init__(self, nb=None, parent=None, lines=None):
        super().__init__(nb)
        self.parent = parent #parent id
        self.lines = lines

    def __repr__(self) -> str:
        return 'Leaf({}, parent={})'.format(self.nb, self.parent)

class LineProduction(object):
    def __init__(self, id=None, type=None):
        self.id = id
        self.lhs = type

def writeLattice(node, pos):
    try:
        string = str(pos[node.nb])
    except:
        string = str(node.id)
    for c in node.children:
        string += writeLattice(c, pos)
    return string

class LinesEnumerator(Enumerator):
    # z3 solver
    z3_solver = Solver()

    # productions that are leaf
    leaf_productions = []

    line_productions = []

    # for learning
    program2tree = {}

    # z3 variables for each production node
    variables = []

    def initLeafProductions(self):
        for p in self.spec.productions():
            # FIXME: improve empty integration
            if not p.is_function() or str(p).find('Empty') != -1:
                self.leaf_productions.append(p)

    def initLineProductions(self):
        for l in range(1,self.loc):
            line_productions = []
            for t in self.types:
                self.num_prods += 1
                line_productions.append(LineProduction(self.num_prods, self.spec.get_type(t)))
                #ENCODING print("NEW PROD "+str(self.num_prods))

            self.line_productions.append(line_productions)

    def findTypes(self):
        types = []
        for t in self.spec.types():
            types.append(t.name[:])
            flag = False
            for p in self.spec.productions():
                if not p.is_function() or p.lhs.name[:] == 'Empty':
                    continue
                if p.lhs.name[:] == types[-1]:
                    flag = True
                    break
            if not flag:
                types.pop()
        # print(types)
        self.types = types
        self.num_types = len(self.types)

    def buildTrees(self):
        '''Builds a loc trees, each tree will be a line of the program'''
        nodes = []
        nb = 1
        leafs = []
        for i in range(1,self.loc+1):
            n = Root(i, nb, self.max_children)
            n.var = self.createRootVariables(nb)
            children = []
            for x in range(self.max_children):
                nb += 1
                child = Leaf(nb, n)
                child.lines = self.createLinesVariables(nb, n.id)
                # print(child.lines)
                child.var = self.createLeafVariables(nb, n.id)
                children.append(child)
                leafs.append(child)
            self.propagateEmpty(children)
            n.children = children
            n.type = self.createTypeVariables(n.id)
            nodes.append(n)
            nb += 1
        return nodes, leafs

    def createLinesVariables(self, nb, parent):
        lines = []
        for x in range(1,parent):
            name = 'l' +str(nb)+"_"+ str(x)
            v = Int(name)
            # print(v)
            self.linesVars.append(v)
            # self.variables.append(v)
            lines.append(v)
            # variable range constraints
            self.z3_solver.add(Or(v == 0, v == 1))
            self.num_constraints += 1
            #ENCODING print(Or(v == 0, v == 1))
        return lines

    def createTypeVariables(self, nb):
        name = 't'+str(nb)
        v = Int(name)
        # self.variables.append(v)
        # variable range constraints
        self.typeVars.append(v)
        self.z3_solver.add(And(v >= 0, v < self.num_types))
        self.num_constraints += 1
        #ENCODING print(And(v >= 0, v < self.num_types))
        return v

    def createRootVariables(self, nb):
        name = 'n' + str(nb)
        v = Int(name)
        self.variables.append(v)
        ctr = []

        for p in self.spec.productions():
            if p not in self.leaf_productions:
                ctr.append(v == p.id)

        #ENCODING print(Or(ctr))
        self.z3_solver.add(Or(ctr))
        self.num_constraints += 1
        return v

    def createLeafVariables(self, nb, parent):
        name = 'n' + str(nb)
        v = Int(name)
        self.variables.append(v)
        ctr = []

        values = self.leaf_productions + [i for a in range(0,parent-1) for i in self.line_productions[a]]
        for p in values:
            ctr.append(v == p.id)

        #ENCODING print(Or(ctr))
        self.z3_solver.add(Or(ctr))
        self.num_constraints += 1
        self.parentId[nb] = parent
        return v

    def propagateEmpty(self, children):
        for c in range(len(children)-1):
            self.z3_solver.add(Implies(children[c].var==0, children[c+1].var==0))
            self.num_constraints += 1
            #ENCODING print(Implies(children[c].var==0, children[c+1].var==0))

    def createOutputConstraints(self):
        '''The output production matches the output type'''
        ctr = []
        var = self.roots[-1].var # last line corresponds to the output line
        for p in self.spec.get_productions_with_lhs(self.spec.output):
            ctr.append(var == p.id)
            for r in range(len(self.roots)-1):
                self.z3_solver.add(self.roots[r].var != p.id)
        self.z3_solver.add(Or(ctr))
        self.num_constraints += 1
        # ENCODING print(Or(ctr))

    def createLinesConstraints(self):
        '''Each line is used exactly once in the program'''
        for r in range(1,len(self.roots)):
            ctr = None
            for l in range(len(self.leafs)):
                for v in self.leafs[l].lines:
                    if int(str(v).split("_")[-1]) == r:
                        if ctr is None:
                            ctr = v
                        else:
                            ctr += v
            ctr_fun = ctr == 1
            self.z3_solver.add(ctr_fun)
            self.num_constraints += 1
            #ENCODING print(ctr_fun)

    def createInputConstraints(self):
        '''Each input will appear at least once in the program'''
        input_productions = self.spec.get_param_productions()
        for x in range(0, len(input_productions)):
            ctr = []
            for y in self.leafs:
                ctr.append(y.var == input_productions[x].id)
            self.z3_solver.add(Or(ctr))
            self.num_constraints += 1
            #ENCODING print(Or(ctr))

    def createTypeConstraints(self):
        '''If a production is used in a node, then the nodes' type is equal to the production's type'''
        for r in self.roots:
            for t in range(len(self.types)):
                ctr = []
                if self.types[t] == 'Empty':
                    continue
                for p in self.spec.productions():
                    if p.is_function() and p.lhs.name[:] == self.types[t]:
                        self.z3_solver.add(Implies(r.var==p.id,r.type==t))
                        self.num_constraints += 1
                        #ENCODING print(Implies(r.var==p.id,r.type==t))

    def createChildrenConstraints(self):
        for r in self.roots:
            for p in self.spec.productions():
                if not p.is_function() or p.lhs.name[:] == 'Empty':
                    continue
                aux = r.var == p.id
                for c in range(len(r.children)):
                    ctr = []
                    if len(p.rhs) == c:
                        ctr.append(r.children[c].var==self.leaf_productions[0].id)
                        self.num_constraints += 1
                        if len(ctr) > 1:
                            self.z3_solver.add(Implies(aux, Or(ctr)))
                            #ENCODING print(Implies(aux, Or(ctr)))
                        else:
                            self.z3_solver.add(Implies(aux, ctr[0]))
                            #ENCODING print(Implies(aux, ctr[0]))
                        break

                    for t in self.leaf_productions:
                        if t.lhs.name[:] == p.rhs[c].name[:]:
                            ctr.append(r.children[c].var==t.id)

                    for l in range(r.id-1):
                        for t in self.line_productions[l]:
                            if t.lhs.name[:] == p.rhs[c].name[:]:
                                ctr.append(r.children[c].var==t.id)
                                # if a previous line is used, then its flag must be true
                                line_var = r.children[c].lines[l]
                                self.z3_solver.add(Implies(line_var==1, r.children[c].var==t.id))
                                self.z3_solver.add(Implies(r.children[c].var==t.id, line_var==1))
                                self.num_constraints += 2
                                #ENCODING print(Implies(line_var==1, r.children[c].var==t.id))
                                #ENCODING print(Implies(r.children[c].var==t.id, line_var==1))

                    self.num_constraints += 1
                    if len(ctr) > 1:
                        self.z3_solver.add(Implies(aux, Or(ctr)))
                        #ENCODING print(Implies(aux, Or(ctr)))
                    else:
                        self.z3_solver.add(Implies(aux, ctr[0]))
                        #ENCODING print(Implies(aux, ctr[0]))

    def maxChildren(self) -> int:
        '''Finds the maximum number of children in the productions'''
        max = 0
        for p in self.spec.productions():
            if len(p.rhs) > max:
                max = len(p.rhs)
        return max

    @staticmethod
    def _check_arg_types(pred, python_tys):
        if pred.num_args() < len(python_tys):
            msg = 'Predicate "{}" must have at least {} arugments. Only {} is found.'.format(
                pred.name, len(python_tys), pred.num_args())
            raise ValueError(msg)
        for index, (arg, python_ty) in enumerate(zip(pred.args, python_tys)):
            if not isinstance(arg, python_ty):
                msg = 'Argument {} of predicate {} has unexpected type.'.format(
                    index, pred.name)
                raise ValueError(msg)

    def _resolve_is_not_parent_predicate(self, pred):
        # return
        self._check_arg_types(pred, [str, str, (int, float)])
        prod0 = self.spec.get_function_production_or_raise(pred.args[0])
        prod1 = self.spec.get_function_production_or_raise(pred.args[1])

        for r in self.roots:
            for s in range(len(r.children[0].lines)):
                children = []
                for c in r.children:
                    children.append(c.lines[s]==1)
                self.z3_solver.add(Implies(And(Or(children), self.roots[s].var==prod1.id), r.var!=prod0.id))

    def _resolve_distinct_inputs_predicate(self, pred):
        self._check_arg_types(pred, [str])
        prod0 = self.spec.get_function_production_or_raise(pred.args[0])
        for r in self.roots:
            for c_1 in range(len(r.children)):
                child_1 = r.children[c_1]
                for c_2 in range(c_1+1,len(r.children)):
                    child_2 = r.children[c_2]
                    # this works because even a inner_join between two filters, the children will have different values for the variables because of the lines produtions
                    self.z3_solver.add(Implies(r.var==prod0.id, Or(child_1.var != child_2.var, And(child_1.var == 0, child_2.var == 0))))
                    # print(Implies(r.var==prod0.id, Or(child_1.var != child_2.var, And(child_1.var == 0, child_2.var == 0))))

    def _resolve_distinct_filters_predicate(self, pred):
        self._check_arg_types(pred, [str])
        prod0 = self.spec.get_function_production_or_raise(pred.args[0])
        for r in self.roots:
            self.z3_solver.add(Implies(r.var==prod0.id, r.children[int(pred.args[1])].var != r.children[int(pred.args[2])].var))
            # print(Implies(r.var==prod0.id, r.children[int(pred.args[1])].var != r.children[int(pred.args[2])].var))


    def _resolve_constant_occurs_predicate(self, pred):
        conditions = pred.args[0].split(",")
        lst = []
        for c in conditions:
            for p in self.spec.productions():
                if p.is_enum() and p.rhs[0] == c:
                    for l in self.leafs:
                        lst.append(l.var==p.id)

        self.z3_solver.add(Or(lst))


    def _resolve_happens_before_predicate(self, pred):
        pos = pre = 0
        for p in self.spec.productions():
            if p.is_enum() and p.rhs[0] == pred.args[0]:
                pos = p.id
            if p.is_enum() and p.rhs[0] == pred.args[1]:
                pre = p.id

        for r_i in range(len(self.roots)):
            previous_roots = []
            for r_ia in range(r_i):
                for c in self.roots[r_ia].children:
                    previous_roots.append(c.var==pre)

            self.z3_solver.add(Implies(Or([c.var==pos for c in self.roots[r_i].children]), Or(previous_roots)))


    def resolve_predicates(self):
        try:
            for pred in self.spec.predicates():
                if pred.name == 'is_not_parent':
                    self._resolve_is_not_parent_predicate(pred)
                elif pred.name == 'distinct_inputs':
                    self._resolve_distinct_inputs_predicate(pred)
                elif pred.name == 'constant_occurs':
                    self._resolve_constant_occurs_predicate(pred)
                elif pred.name == 'happens_before':
                    self._resolve_happens_before_predicate(pred)
                elif pred.name == 'distinct_filters':
                    self._resolve_distinct_filters_predicate(pred)
                else:
                    logger.warning('Predicate not handled: {}'.format(pred))
        except (KeyError, ValueError) as e:
            msg = 'Failed to resolve predicates. {}'.format(e)
            raise RuntimeError(msg) from None

    def __init__(self, spec, depth=None, loc=None, sym_breaker=True, break_sym_online=False):
        self.z3_solver = Solver()

        # productions that are leaves
        self.leaf_productions = []

        self.line_productions = []

        # for learning
        self.program2tree = {}

        # z3 variables for each production node
        self.variables = []
        self.spec = spec
        self.num_constraints = 0
        self.num_variables = 0
        self.sym_breaker = sym_breaker
        self.break_sym_online = break_sym_online
        if depth <= 0:
            raise ValueError(
                'Depth cannot be non-positive: {}'.format(depth))
        self.depth = depth
        if loc <= 0:
            raise ValueError(
                'LOC cannot be non-positive: {}'.format(loc))
        self.start_time = time.time()
        self.loc = loc

        self.parentId = dict()
        if self.sym_breaker:
            if self.loc > 2:
                root = Node(1)
                root.h = 1
                id, tree = self.createCleanTree(1, root)
                tree.insert(0, root)
                self.cleanedTree = tree
                self.symFinder = SymmetryFinder(self.loc)

            self.lattices = dict()
            if self.loc > 2 and not self.break_sym_online:
                self.findLattices()

        self.cleanedModel = dict()
        self.num_prods = self.spec.num_productions()
        self.max_children = self.maxChildren()
        self.diff_models = []
        self.findTypes()
        self.initLeafProductions()
        self.initLineProductions()
        self.linesVars = []
        self.typeVars = []
        self.roots, self.leafs = self.buildTrees()
        self.model = None
        # Times
        self.symTime = 0
        self.totalSymTime = 0
        self.blockingTime = 0
        self.blockModelsTime = 0
        self.solverTime = 0
        self.time1 = 0
        self.time2 = 0
        self.time3 = 0
        self.time4 = 0
        self.blockedModels = 0
        self.totalBlockedModels = 0
        self.blockCicle = 0
        self.addModel = 0

        self.modelConstraint = 0
        self.createInputConstraints()
        self.createOutputConstraints()
        self.createLinesConstraints()
        self.createTypeConstraints()
        self.createChildrenConstraints()
        self.resolve_predicates()
        logger.error('Number of Nodes: {} '.format(len(self.roots+self.leafs)))
        logger.error('Number of Variables: {}'.format(len(self.variables+self.typeVars+self.linesVars)))
        logger.error('Number of Constraints: {}'.format(self.num_constraints))
        logger.error('Time spent encoding: {}'.format(time.time() - self.start_time))
        res = self.z3_solver.check()
        if res != sat:
            # UNSAT
            logger.error("UNSAT : There is no solution for current depth (loc="+str(self.loc-1)+"), try to increase it (e.g. loc="+str(self.loc)+").")
            return
        self.model = self.z3_solver.model()
        self.getModelConstraint()

    def getParentId(self, nb_child):
        return self.parentId[nb_child]

    def getFirstChild(self, node, pos):
        for c_ind in range(len(node.children)):
            try:
                i = pos[node.children[c_ind].nb]
                continue
            except:
                return c_ind
        return len(node.children)-1

    def findLattices(self):
        # lattices = dict()
        # try:
        lats = open("tyrell/enumerator/lattices/loc-"+str(self.loc), "r+")
        lats = lats.readlines()
        for l in lats:
            # print(l)
            lat, mods = l.split(":",1)
            models = []
            if mods[:-1] != '':
                mods = mods[:-1].replace(" ","").split("|", self.loc*2)
                for m in mods:
                    if m == "":
                        continue
                    model = dict()
                    m = m[1:-1].split(",")
                    if m == ['']:
                        break
                    for c in m:
                        c = c.split("=") if "=" in c else c.split(":")
                        # print(c)
                        model[Int(c[0])] = Int(c[1])
                    # print(model)
                    models.append(model)
            if lat not in self.lattices:
                self.lattices[lat] = models
        # print(lattices)
        # return lattices
        # except:
        #     print(lattices)
        #     return lattices

    def closeLattices(self):
        logger.error('Total Solver Time: {}'.format(self.solverTime))
        logger.error('Total Time Symmetries: {}'.format(self.totalSymTime))
        logger.error('Total Blocked Models: {}'.format(self.totalBlockedModels))
        if self.loc < 6 or self.break_sym_online or not self.sym_breaker:
            return

        lats = open("tyrell/enumerator/lattices/loc-"+str(self.loc), "w+")

        for l, mdls in self.lattices.items():
            st = l + ":"
            if mdls != []:
                for m in mdls:
                    st += str(m) + "|"

                lats.write(st[:-1]+"\n")
            else:
                lats.write(st+"[]\n")

        lats.close()

    def createCleanTree(self, id, node):
        j = id
        node.children = []
        childs = []
        for i in range(j+1,j+self.loc):
            l = Node(i)
            l.h = node.h + 1
            l.id = 0
            l.children = []
            id += 1
            node.children.append(l)
            childs.append(l)

        for l in node.children:
            if l.h == self.loc:
                break
            id, childs_aux = self.createCleanTree(id, l)
            childs += childs_aux

        return id, childs

    def printTree(self, root):
        for c in root.children:
            print('Id father: {} h {} -> Id son {} h {}'.format(root.nb, root.h, c.nb, c.h))
            self.printTree(c)

    def createCompleteLattice(self, node):
        node.children = []
        for c in self.roots[node.nb-1].children:
            for l in c.lines:
                if self.model[l]==1:
                    child = Node(int(str(l).split("_")[1]))
                    child.h = node.h + 1
                    self.createCompleteLattice(child)
                    node.children.append(child)

    def createLattice(self, node, nb_root, dic):
        for c_ind in range(len(self.roots[nb_root-1].children)):
            c = self.roots[nb_root-1].children[c_ind]
            for l_ind in range(len(c.lines)):
                l = c.lines[l_ind]
                if self.model[l]==1:
                    node_child = node.children[self.getFirstChild(node, dic)]
                    # i = int(str(l).split("_")[1])
                    dic[node_child.nb] = l_ind+1
                    self.createLattice(node_child, l_ind+1, dic)
                    break

    def findSymmetries(self):
        pos = dict()
        pos[1] = self.loc
        root = self.cleanedTree[0]
        self.createLattice(root, self.loc, pos)
        if not self.break_sym_online and self.loc < 6:
            # print("offline")
            try:
                return self.lattices[writeLattice(root, pos)]
            except:
                return []
        else:
            # print("online")
            lat = writeLattice(root, pos)
            try:
                # print(self.lattices[lat])
                return self.lattices[lat]
            except:
                last_line = Node(self.loc)
                last_line.h = 0
                self.createCompleteLattice(last_line)
                models = self.symFinder.findSymmetries(last_line)
                self.lattices[lat] = models
                # print(lat,":",models)
                if self.loc > 5 and not self.break_sym_online:
                    self.findLattices()
                    self.closeLattices()
                # print("updated")
                # exit()
                return models

    def changeNode(self, node_pos, new_node_pos, new_model, model):
        root, new_root = self.roots[node_pos-1], self.roots[int(str(new_node_pos))-1]

        for c in range(len(root.children)):
            val = int(str(model[root.children[c].var]))
            if val != 0:
                new_model[new_root.children[c].var] = model[root.children[c].var]
            else:
                new_model[new_root.children[c].var] = self.model[root.children[c].var]
            #DEBUG print("leaf:", root.children[c].var, "--->",new_root.children[c].var)
            #DEBUG print("prods:", model[root.children[c].var], "--->",new_model[new_root.children[c].var])

        # change the type of the line
        new_model[new_root.type] = model[root.type]

    def fromSymmetries2Programs(self, model, m_aux):
        time_3 = time.time()
        for t in range(len(self.typeVars)-1):
            k = self.typeVars[t]
            m_aux[k] = self.model[k] # NEW
            root_num = t+1
            type = int(str(self.model[k]))
            new_node = int(str(model[Int('x_'+str(root_num))]))
            old_prod = self.line_productions[root_num-1][type].id
            new_prod = self.line_productions[new_node-1][type].id
            start = root_num*self.max_children
            for i in range(start, len(self.leafs)):
                n = self.leafs[i]
                if self.model[n.var] == old_prod:
                    #DEBUG print("type var:", n, old_prod, "--->", new_prod)
                    m_aux[n.var] = IntVal(new_prod)
                    break
        m_aux[self.typeVars[-1]] = self.model[self.typeVars[-1]]
        #TIME self.time3 += time.time() - time_3

        #TIME time_4 = time.time()
        n_model = dict(m_aux)
        for v in model:
            var, new_node_pos = v, int(str(model[v]))
            node_pos = int(str(var).split("_")[1])
            #DEBUG print("num root:",node_pos, "--->", new_node_pos)
            n_model[self.roots[new_node_pos-1].var] = self.model[self.roots[node_pos-1].var]
            #DEBUG print("root:", Int('n'+str(node_nb)), "--->", Int('n'+str(new_node_nb)))
            self.changeNode(node_pos, new_node_pos, n_model, m_aux)

            #DEBUG print("new model:",n_model)

        n_model[self.roots[-1].var] = self.model[self.roots[-1].var]
        #DEBUG print("root:", Int('n'+str(node_nb)), "--->", Int('n'+str(new_node_nb)))
        self.changeNode(0, 0, n_model, m_aux)

        #TIME self.time4 += time.time() - time_4

        #DEBUG print(),print(),print()
        return n_model

    def getModelConstraint(self):
        block = []
        for x in self.variables:
            block.append(x != Int('val_'+str(x)))
        self.modelConstraint = Or(block)

        for m in self.model:
            self.cleanedModel[m()] = IntVal(0)

    def blockModelAux(self, model):
        # block the model using only the variables that correspond to productions (nodes = leafs + roots)
        #TIME cicle_time = time.time()
        const = substitute(self.modelConstraint, [(Int('val_'+str(x)), model[x]) for x in self.variables])
        #TIME  self.blockCicle += time.time() - cicle_time

        #TIME  add_time = time.time()
        self.z3_solver.add(const)
        #TIME  self.addModel += time.time() - add_time

    def blockModel(self):
        assert(self.model is not None)
        models_sols = []
        # in order to find symmetric programs
        self.blockModelAux(self.model)

        if self.sym_breaker and self.loc > 2:
            #TIME time_1 = time.time()
            time_1 = time.time()
            models_sols = self.findSymmetries()
            #TIME self.symTime += time.time() - time_1

            if len(models_sols) > 0:
                for mdl in models_sols:
                    #TIME time_1 = time.time()
                    m_2 = dict(self.cleanedModel)
                    #TIME self.time1 += time.time() - time_1
                    #TIME time_2 = time.time()
                    m = self.fromSymmetries2Programs(mdl, m_2)
                    #TIME self.blockModelsTime += time.time() - time_2
                    #TIME time_3 = time.time()
                    self.blockModelAux(m)
                    self.blockedModels += 1
                    #TIME self.blockingTime += time.time() - time_3
            self.symTime = time.time() - time_1 # EQUAL NOT PLUS EQUAL
            self.totalSymTime += self.symTime


    def update(self, info=None, id=None):
        if info is not None and not isinstance(info, str):
            for core in info:
                ctr = []
                for constraint in core:
                    ctr.append(self.program2tree[constraint[0]] != constraint[1].id)
                self.z3_solver.add(Or(ctr))
        else:
            self.blockedModels = 0
            self.blockModel()
            self.totalBlockedModels += self.blockedModels
            if self.blockedModels != 0:
                logger.error('Total Blocked Models: {}'.format(self.totalBlockedModels))
                logger.error('Total Time Symmetries: {}'.format(self.totalSymTime))


    def makeNode(self, c, builder_nodes, builder):
        if str(c.production).find('Empty') == -1:
            if c.children is None:
                builder_nodes[c.nb-1] = builder.make_node(c.production.id, [])
                self.program2tree[builder_nodes[c.nb-1]] = c.var
            else:
                children = []
                for r_c in c.children:
                    if builder_nodes[r_c.nb-1] is None:
                        self.makeNode(r_c, builder_nodes, builder)

                    children.append(builder_nodes[r_c.nb-1])
                    self.program2tree[builder_nodes[r_c.nb-1]] = r_c.var

                builder_nodes[c.nb-1] = builder.make_node(c.production.id, [c for c in children if c is not None])
                self.program2tree[builder_nodes[c.nb-1]] = c.var

    def constructProgram(self):
        model = self.model
        roots = deepcopy(self.roots)
        self.program2tree.clear()

        for r in roots:
            r.production = self.spec.get_production(int(str(model[r.var])))
            root = k = None
            for c in r.children:
                c.production = self.spec.get_production(int(str(model[c.var])))
                if c.production is None:
                    for l in c.lines:
                        if model[l] == 1:
                            s = "line_"+str(l).split("_")[1]
                            c.production = s
                            break
            #DEBUG print(line[:-1]+")")
            # logger.info(line[:-1]+")")

        builder = D.Builder(self.spec)
        num_nodes = self.roots+self.leafs
        builder_nodes = [None] * len(num_nodes)

        for r in roots:
            for c in range(len(r.children)):
                if "line_" in str(r.children[c].production):
                    root = int(r.children[c].production.split("_")[1]) - 1
                    r.children[c] = roots[root]
            self.makeNode(r, builder_nodes, builder)

        # print(builder_nodes[roots[-1].nb-1])
        return builder_nodes[roots[-1].nb-1]


    # use to count number of models enumerated
    # def next(self):
    #     count = 0
    #     res = self.z3_solver.check()
    #     start_time = time.time()
    #     if res != sat:
    #         print("UNSAT")
    #     self.model = self.z3_solver.model()
    #     self.getModelConstraint()
    #     while True:
    #         if self.model is not None:
    #             count +=1
    #             # print(self.model)
    #             # print(count)
    #             # DEBUG
    #             # self.constructProgram()
    #             self.blockModel()
    #             res = self.z3_solver.check()
    #             if res != sat:
    #                 logger.error(count)
    #                 logger.error('Total Time: {}'.format(time.time()-start_time))
    #                 #TIME logger.error('Time to find Symmetries: {}'.format(self.symTime))
    #                 #TIME logger.error('Time to get symmetric models: {}'.format(self.blockModelsTime))
    #                 #TIME logger.error('Time to block the new models: {}'.format(self.blockingTime))
    #                 #TIME logger.error('Time to check all vars: {}'.format(self.blockCicle))
    #                 #TIME logger.error('Time to add constraint: {}'.format(self.addModel))
    #                 #TIME logger.error('Number of blocked models: {}'.format(self.blockedModels))
    #                 #TIME logger.error('Time block 1: {}'.format(self.time1))
    #                 #TIME logger.error('Time block 2: {}'.format(self.time2))
    #                 #TIME logger.error('Time block 3: {}'.format(self.time3))
    #                 #TIME logger.error('Time block 4: {}'.format(self.time4))
    #                 exit()

    #             if count % 100 == 0 :
    #                 logger.error(count)
    #             self.model = self.z3_solver.model()
    #             # print(self.model)
    #         else:
    #             logger.error(count)
    #             exit()

    def next(self):
        while True:
            start_time = time.time()
            res = self.z3_solver.check()
            # logger.error('Solver Check Time: {}'.format(time.time()-start_time))
            self.solverTime += time.time()-start_time
            if res != sat:
                return None
            model_time = time.time()
            self.model = self.z3_solver.model()
            # logger.error('Solver Model Time: {}'.format(time.time()-model_time))

            if self.model is not None:
                return self.constructProgram()
            else:
                return None
