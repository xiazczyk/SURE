import logic as lo
import aodag as dag
import itertools
import pprint as pp
import copy

"""
Satisfied if all consequents in rule are among nodes
"""
def satisfied(rule, nodes):
    nodesArgs = [node.arg for node in nodes]
    sat = True
    for n in rule.conse:
        if n not in nodesArgs:
            sat = False
    return sat

"""
Pattern matching
"""
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
            index[lo.predPattern(o.arg)] = [o]
        else:
            index[lo.predPattern(o.arg)].append(o)
    return index

def backchainAndUnify(KB, rollingNodes, G, Litd, index, obsvNodes, d=3):
    Refd = dict()
    Axd = dict()
    Numd = dict()
    uniPair = dict()
    uniPredicate = dict()
    while(d>0):
        seriesNodes = []
        # Backchaining
        for axiom in KB:
            if axiom.no not in Axd.keys():
                Axd[axiom.no] = dag.Node(axiom.no, 'ax')
                Numd[axiom.no] = dag.Node(axiom.no, 'num')
                dag.addChildren(G, Numd[axiom.no], [Axd[axiom.no]])
            # Axiom is of the form HornClause(args, args)
            # rollingNodes is the list of Nodes already explored
            # bP is a list of backchained PREDICATES
            # Need to: create nodes for predicates, THEN connect bp-axiom-up
            (bP, usedNodes) = backchain(rollingNodes, axiom) #Parse root?
            if bP:
                #Something was bchained -> create axiom node
                dag.addChildren(G, Axd[axiom.no], usedNodes)
                for b in bP:
                    if b not in Litd.keys():
                        Litd[b] = dag.Node(b, 'lit')
                    pp = lo.predPattern(b)
                    index[pp] = [Litd[b]] if pp not in index.keys() else index[pp] + [Litd[b]]
                    dag.addChildren(G, Litd[b], [Axd[axiom.no]])
                    seriesNodes.append(Litd[b])

            #Putting Refs in the graph
            for a in axiom.conse:
                if a not in Refd.keys():
                    Refd[a] = dag.Node(a, 'ref', False, True if Litd[a] in obsvNodes else False)
                dag.addChildren(G, Refd[a], [Axd[axiom.no]])
        rollingNodes += seriesNodes

        # Unification
        for x in seriesNodes:
            # For each backchained literal, try to unify it with whatever you can
            xPttn = lo.predPattern(x.arg) # can only unify literals of same pattern
            if xPttn in index.keys(): # if not in index then there's nothing to unify
                for y in index[xPttn]: # try to unify against every literal in index
                    # Now I'm at the pair. want to know if these are unifiable [also no if theta empty]
                    theta = lo.unifyTerms(x.arg,y.arg)
                    if not theta:
                        break # to avoid (x=y,y=x)
                    for pair in theta.items():
                        if pair not in uniPair.keys(): # if no x=y node in graph
                            uniPair[pair] = dag.Node(pair, 'eq') #create node
                        if xPttn not in uniPredicate.keys():
                            uniPredicate[xPttn] = dag.Node(xPttn, 'uni')
                            dag.addChildren(G, uniPredicate[xPttn], [x,y])
                            if not x.obsv:
                                dag.addChildren(G, uniPredicate[xPttn], [Numd[G[x][0].arg]])
                            if not y.obsv:
                                dag.addChildren(G, uniPredicate[xPttn], [Numd[G[y][0].arg]])
                        if uniPair[pair] not in G.keys() or G[uniPair[pair]] != uniPredicate[xPttn]: # if the child of unif
                            dag.addChildren(G, uniPair[pair], [uniPredicate[xPttn]])
        d -= 1
    return Refd, Axd, Numd, uniPair, uniPredicate

def parseInput(obsvNodes, f):
    KB = []
    index = dict()
    rollingNodes = []
    G = dict()
    Litd = dict()
    print(obsvNodes)
    obsvNodes = [x.split('(') for x in obsvNodes]
    # convert obsv to Nodes

    for i in obsvNodes:
        a = parseLit(i)
        aNode = dag.Node(a, 'lit', True)
        Litd[a] = aNode
        rollingNodes.append(aNode)

    obsvNodes = copy.deepcopy(rollingNodes)
    G = dag.initGraph(rollingNodes)
    # index stores lists of nodes that satisfy a certain predicate pattern
    index = indexUpdate(index, rollingNodes)

    for line in f:
        implication = line.strip().split(' -> ')
        antecedents = implication[0].split(' and ')
        consequents = implication[1].split(' and ')
        antecedentsArgs, consequentsArgs = parse(antecedents), parse(consequents)
        KB.append(lo.Rule(len(KB)+1, antecedentsArgs, consequentsArgs))
    return KB, Litd, rollingNodes, G, index, obsvNodes

def parseLit(i):
    symbol = i[0]
    print(i)
    args = i[1][:-1].split(',')
    lit = lo.Form(symbol, args)
    return lit

def parse(varList):
    varList = [varList[i].split('(') for i in range(len(varList))]
    varList = [parseLit(i) for i in varList]
    return varList

def topSort(G):
    # Degree is a list of topologically sorted nodes
    order = []
    vis = dict()
    degree = dict()
    for i in G.keys():
        vis[i] = False if i.family not in ['num', 'ref'] else True
        degree[i] = 0
    for i in G:
        if not vis[i]:
            vis[i] = True
            degree = dag.dfsDegree(G, i, degree, vis)
    #Topsort
    for i in G.keys():
        vis[i] = False if i.family not in ['num', 'ref'] else True
    for i in degree.keys():
        if degree[i] == 0 and not vis[i]:
            vis[i] = True
            dag.dfsTop(G, i, order, degree, vis)
    return order

def computePar(order, G):
    par = [x[:] for x in [[]]*(len(order))]
    children = [x[:] for x in [[]]*(len(order))]
    orderIndex = dict()
    for i in range(len(order)):
        orderIndex[order[i]] = i

    # Compute par
    for node in order:
        for child in G[node]:
            if child.family not in ['ref', 'num']:
                par[orderIndex[child]].append(orderIndex[node])
                children[orderIndex[node]].append(orderIndex[child])
    return par, children, orderIndex

def computeCombo(order, par, children, orderIndex, G):
    combo = [[]]
    for i in order:
        combo = dag.traversal(G, i, combo, par, orderIndex)
    # Delete useless combinations (those which have false observables)
    obsvNodes = [orderIndex[i] for i in order if i.obsv == True]
    combo = dag.checkObsv(combo, obsvNodes)
    combo = dag.usefulCombo(combo, children)
    return combo

def computeHyp(combo, order, par):
    hyp = [x[:] for x in [[]]*(len(combo))]
    for j in range(len(combo)):
        for i in range(len(combo[j])):
            if combo[j][i] == True:
                noTrueParents = False
                for p in par[i]:
                    if combo[j][p] == True and order[p].family != 'uni':
                        noTrueParents = True
                        break
                if noTrueParents == False:
                    hyp[j].append(order[i])
    return hyp

def printHyp(hyp):
    strg = ""
    for i in range(1, len(hyp)+1):
        strg = strg + "Hypothesis #" + str(i) + ":\n"
        for node in hyp[i-1]:
            strg = strg + str(node.arg)
            strg += "\n"
        strg += "\n"
    return strg

def printGraph(G):
    strg = "\nGraph:\n"
    for x in G.keys():
        strg = strg + str(x) + " --> " + str(G[x])
        strg += "\n"
    return strg

def printKB(KB):
    strg = "Knowledge Base:\n"
    for i in range(1, len(KB)+1):
        strg = strg + str(KB[i-1]) + "\n"
    return strg

################### MAIN
def abduce(input=None, d=3):
    d = 5
    f = open("test1a", "r")
    KB, Litd, rollingNodes, G, index, obsvNodes = parseInput(f)
    """
    Assumption: KB is filtered so that each rule is going to be useful for backchaining.
    Not necessary, though speeds up inference. Will do if time allows, it can be done with just input.
    """
    # This goes in the work in progress field
    printKB(KB)

    Refd, Axd, Numd, uniPair, uniPredicate = backchainAndUnify(KB, rollingNodes, G, Litd, index, obsvNodes, d)

    # Work in progress field
    printGraph(G)
    # Calculate topological order for nodes
    order = topSort(G)

    """
    Now on to creating hypotheses
    each node is given a number depending on its order from topsort
    order is the topological order of nodes
    orderIndex is a dictionary node : number
    par is a reverse order graph computed on those numbers
    combo is a list of all possible combinations of truth/false assignments to nodes in graph
    """
    # Compute par, children and orderIndex
    par, children, orderIndex = computePar(order, G)
    # Compute combo
    combo = computeCombo(order, par, children, orderIndex, G)
    # Create a list of hypotheses
    hyp = computeHyp(combo, order, par)
    # Print out all hypotheses
    printHyp(hyp)

    ###TODO

    #update ref and num
    # Update NumbU
    # From now on work on G.. or incorporate num and ref into the previous representation
    return

if __name__ == '__main__':
    abduce()
