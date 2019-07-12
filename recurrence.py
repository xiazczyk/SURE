import logic as lo
import aodag as dag
import itertools
import pprint as pp

#
#
"""
satisfied if all consequents in rule are among nodes
"""
def satisfied(rule, nodes):
    nodesArgs = [node.arg for node in nodes]
    sat = True
    for n in rule.conse:
        if n not in nodesArgs:
            sat = False
    return sat

def backchain(rollingNodes, rule):
    usedNodes = []
    bP = []
    if satisfied(rule, rollingNodes):
        usedNodes += [node for node in rollingNodes if node.arg in rule.conse]
        bP += rule.ante
    return (bP, usedNodes)

def indexUpdate(index, rollingNodes):
    for o in rollingNodes:
        if lo.predPattern(o.arg) not in index.keys():
            index[lo.predPattern(o.arg)] = o
        else:
            index[lo.predPattern(o.arg)].append(o)
    return index


def parse(varList):
    args = [varList[i].split(' ') for i in range(len(varList))]
    args = [lo.Form(args[i][0], args[i][1:]) for i in range(len(args))]
    return args




################### MAIN
f = open("test1.txt", "r")
obsv = f.readline().strip()
obsvNodes = obsv.split(', ')
obsvNodes = [x.split(' ') for x in obsvNodes]
# convert obsv to Nodes
rollingNodes = []
for i in obsvNodes:
    rollingNodes.append(dag.Node(lo.Form(i[0], i[1:]), 'lit'))
# print(rollingNodes)
KB = []
G = dag.initGraph(rollingNodes)
# index stores lists of nodes that satisfy a certain predicate pattern
index = dict()
index = indexUpdate(index, rollingNodes)

for line in f:
    implication = line.strip().split('. ')
    antecedents = implication[0].split(', ')
    consequents = implication[1].split(', ')
    antecedentsArgs, consequentsArgs = parse(antecedents), parse(consequents)
    KB.append(lo.Rule(len(KB)+1, antecedentsArgs, consequentsArgs))

# Erase useless rules from KB
# KB filter  consequents in rolling nodes
# KB = [rule if any i in rule.conse in x.arg for x in rollingNodes for rule in KB]

"""
Assume KB filtered
"""
# Refd[o] = True <=> o is an observable; do I need this tho
Refd = dict()
uniPair = dict()
uniPredicate = dict()
for o in rollingNodes:
    Refd[o] = False

# # Convert KB to a KB of Axioms
d = 1
while(d>0):
    seriesNodes = []
    # Backchaining
    for axiom in KB:
        newAxiom = dag.Node(axiom.no, 'ax')
        # print(axiom)
        # Axiom is of the form HornClause(args, args)
        # rollingNodes is the list of Nodes already explored
        # bP is a list of backchained PREDICATES
        # Need to: create nodes for predicates, THEN connect bp-axiom-up
        (bP, usedNodes) = backchain(rollingNodes, axiom) #Parse root?
        if bP:
            #Something was bchained -> create axiom node
            dag.addChildren(G, newAxiom, [usedNodes])

            for backchained in bP:
                back = dag.Node(backchained, 'lit')
                pp = lo.predPattern(backchained)
                index[pp] = [back] if pp not in index.keys() else index[pp] + [back]
                dag.addChildren(G, back, [newAxiom])
                seriesNodes.append(back)
        """
        Putting Refs in the graph
        """
        for a in axiom.conse:
            if a not in Refd.keys():
                Refd[a] = dag.Node(a, 'ref')
            dag.addChildren(G, Refd[a], [newAxiom])
    rollingNodes += seriesNodes
    """
    Unification
    Don't have num nodes yet
    Unification duplicates. why
        Problem: if two nodes added in one go then it fucks up bc it goes through both


    Keep track of which variables have been unified - uniPair
    Keep track of whether there exists a U node for a given symbol - uniPredicate
    Looking for unifications among nodes... [match sth from seriesNodes to sth from rollingNodes]
    If two candidates found:
    1. Check if this pair has been unified before
        NO:
            add pair node.
            uniPair(sorted(pair)) = node (sorted pair)
        YES:
            if their child is already the same as symbol, quit loop
        check uniPredicate(current literal)
            EMPTY? create node(current literal), make child of current pair node
            A NODE? create a connection between pair and that node

    """
    for x in seriesNodes:
        # For each backchained literal, try to unify it with whatever you can
        xPttn = lo.predPattern(x.arg) # can only unify literals of same pattern
        if xPttn in index.keys(): # if not in index then there's nothing to unify
            for y in index[xPttn]: # try to unify against every literal in index
                sorted = lo.sort(x.arg,y.arg)
                if not sorted:
                    break # to avoid (x=y,y=x)
                if sorted not in uniPair.keys(): # if no x=y node in graph
                    uniPair[sorted] = dag.Node(sorted, 'eq') #create node
                if xPttn not in uniPredicate.keys():
                    uniPredicate[xPttn] = dag.Node(sorted, 'uni')
                    dag.addChildren(G, uniPredicate[xPttn], [x,y])
                if uniPair[sorted] not in G.keys() or G[uniPair[sorted]] != uniPredicate[xPttn]: # if the child of unif
                    dag.addChildren(G, uniPair[sorted], [uniPredicate[xPttn]])
    d -= 1
for x in G.keys():
    print(str(x) + " --> " + str(G[x]))
