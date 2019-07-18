import logic as lo
import copy
import pprint as pp
"""
ADD CODE COMMENTING THE CLASS
"""
class Node:
    def __init__(self, arg, family, obsv=False, refObsv=False):
        self.family = family
        self.arg = arg
        self.andor = 'AND' if self.family in ['uni','ax'] else 'OR'
        self.num = 0 if self.family == 'num' else None
        self.symbol = arg.symbol if self.family == 'uni' else None
        self.obsv = obsv
        self.refObsv = refObsv
    def __repr__(self):
        return "<" + self.family + "> " + repr(self.arg)
    def __eq__(self, other):
        if isinstance(other, Node):
            return self.arg == other.arg and self.family == other.family
    def __hash__(self):
        return hash((self.arg,self.family))

######### METHODS #########
def initGraph(nodes):
    G = dict()
    for node in nodes:
        #Observational nodes are children of axiom 0
        G[node] = []
    return G

def addChildren(graph, node, children):
    if node not in graph.keys():
        graph[node] = []
    for c in children:
        if c not in graph[node]:
            graph[node].append(c)

def dfsDegree(graph, node, degreeTable, vis):
    if node.family == 'ref':
        print(node)
        print(node.refObsv)
    for i in graph[node]:
        degreeTable[i] += 1
        if not vis[i]:
            vis[i] = True
            dfsDegree(graph, i, degreeTable, vis)
    return degreeTable

def dfsTop(graph, node, order, degreeTable, vis):
    order.append(node)
    for i in graph[node]:
        degreeTable[i] -= 1
        if degreeTable[i] == 0 and not vis[i]:
            vis[i] = True
            dfsTop(graph, i, order, degreeTable, vis)

# Decide if a node will be T or F in the combo
def analyseNode(node, combo, par, orderIndex):
    trueParents = [p for p in par[orderIndex[node]] if combo[p] == True]
    falseParents = [p for p in par[orderIndex[node]] if combo[p] == False]
    if len(trueParents) == 0 and len(falseParents) == 0:
        return (True, True)
    # Only True if all parents True
    if node.andor == 'AND':
        if falseParents:
            return (False, True)
        else:
            return (True, False)
    # True if any parent True; True or False if all parents False
    elif node.andor == 'OR':
        if trueParents:
            return (True, False)
        else:
            return (True, True)
    else:
        print("Error: undefined node")
        return (False, False)

#
def traversal(graph, node, combo, par, orderIndex):
    appendedCombos = []
    for c in combo:
        (truth, falsity) = analyseNode(node, c, par, orderIndex)
        # print(node, truth, falsity)
        if truth:
            if falsity:
            #Split on c
                cCopy = copy.deepcopy(c)
                cCopy.append(False)
                appendedCombos.append(cCopy)
            c.append(True)
        elif falsity:
            c.append(False)
        else:
            print("False and False")
    if truth and falsity:
        combo += appendedCombos
    return combo

def checkObsv(combo, obsvNodes):
    goodCombos = []
    for c in combo:
        falseCombo = False
        for o in obsvNodes:
            if c[o] == False:
                falseCombo = True
        if falseCombo == False:
            goodCombos.append(c)
    return goodCombos

def usefulCombo(combo):
    for c in combo:
        for c1 in c:
            if c1 == True:
                if 
