from collections import deque
from math import inf
from random import Random
from typing import List

from layeredGraphLayouter.containers.constants import PortSide
from layeredGraphLayouter.containers.lGraph import LGraph
from layeredGraphLayouter.containers.lNode import LNode
from layeredGraphLayouter.crossing.allCrossingsCounter import AllCrossingsCounter
from layeredGraphLayouter.crossing.barycenterHeuristic import BarycenterHeuristic
from layeredGraphLayouter.crossing.dummyPortDistributor import DummyPortDistributor
from layeredGraphLayouter.crossing.forsterConstraintResolver import ForsterConstraintResolver
from layeredGraphLayouter.crossing.nodeRelativePortDistributor import NodeRelativePortDistributor
from layeredGraphLayouter.crossing.sweepCopy import SweepCopy


def firstFree(isForwardSweep, length):
    return 1 if isForwardSweep else length - 2


def firstIndex(isForwardSweep: bool, length: int):
    return 0 if isForwardSweep else length - 1


def endIndex(isForwardSweep: bool, length: int):
    return length - 1 if isForwardSweep else 0


def isOnEndOfSweepSide(port, isForwardSweep: bool) -> bool:
    if isForwardSweep:
        return port.side == PortSide.EAST
    else:
        return port.side == PortSide.WEST


def sideOpposedSweepDirection(isForwardSweep):
    return PortSide.WEST if isForwardSweep else PortSide.EAST


def isNotEnd(length, freeLayerIndex, isForwardSweep):
    return freeLayerIndex < length if isForwardSweep else freeLayerIndex >= 0


def next_step(isForwardSweep: bool):
    return 1 if isForwardSweep else -1


class LayerSweepCrossingMinimizer():
    """
    This class minimizes crossings by sweeping through a graph,
    holding the order of nodes in one layer fixed and switching the nodes
    in the other layer. After each re-sorting step, the ports in the two
    current layers are sorted.

    By using a LayerSweepTypeDecider as called by the GraphInfoHolder
    initializing class, each graph can either be dealt with bottom-up
    or hierarchically.

    bottom-up: the nodes of a child graph are sorted, then the order
        of ports of hierarchy border traversing edges are fixed.
        Then the parent  graph is laid out, viewing the child graph
        as an atomic node.

    hierarchical: When reaching a node with a child graph marked
        as hierarchical: First the ports are sorted on the outside
        of the graph. Then the nodes on the inside are sorted
        by the order of the ports. Then the child graph is swept through.
        Then the ports of the parent node are sorted by the order of the nodes
        on the last layer of the child graph. Finally the sweep through
        the parent graph is continued.

    Therefore this is a hierarchical processor which must have access
    to the root graph.

    Reference for the original layer sweep:
    Kozo Sugiyama, Shojiro Tagawa, and Mitsuhiko Toda. Methods for visual
    understanding of hierarchical system structures. IEEE Transactions
    on Systems, Man and Cybernetics, 11(2):109–125, February 1981.

    Precondition:
    The graph has a proper layering, i.e. all long edges have been splitted
    all nodes have at least fixed port sides.

    Postcondition:
    The order of nodes in each layer and the order of ports in each node
    are optimized to yield as few edge crossings as possible

    :note: port from ELK
    """

    def process(self, graph: LGraph):
        """
        Short-circuit cases in which no crossings can be minimized.
        Note that in-layer edges may be subject to crossing minimization
        if |layers| = 1 and that hierarchical crossing minimization may dive
        into a graph with a single node. There can be graphs that consist
        only of empty layers, for example due to inside self-loops
        with unconnected ports
        """

        layers = graph.layers
        self.randomSeed = 0
        self.random = Random(self.randomSeed)

        self.graphsWhoseNodeOrderChanged = set()

        emptyGraph = not layers or sum(len(l) for l in layers) == 0
        singleNode = len(layers) == 1 and len(layers[0]) == 1

        # [TODO]
        hierarchicalLayout = False

        if emptyGraph or (singleNode and not hierarchicalLayout):
            return

        graphsToSweepOn = [graph, ]

        constraintResolver = ForsterConstraintResolver(graph.layers)

        for g in graphsToSweepOn:
            for name in ["crossMinimizer", "currentNodeOrder", "portDistributor",
                         "crossCounter", "currentlyBestNodeAndPortOrder"]:
                assert not hasattr(g, name)
            g.currentlyBestNodeAndPortOrder = None
            #g.portDistributor = NodeRelativePortDistributor(g)
            g.portDistributor = DummyPortDistributor(g.layers)
            g.crossMinimizer = BarycenterHeuristic(
                constraintResolver, self.random, g.portDistributor,
                g.layers)
            g.currentNodeOrder = SweepCopy(g.layers)
            g.inLayerSuccessorConstraint = []
            g.crossCounter = AllCrossingsCounter(g)

        minimizingMethod = self.chooseMinimizingMethod(graphsToSweepOn)
        self.minimizeCrossings(graphsToSweepOn, minimizingMethod)
        self.transferNodeAndPortOrdersToGraph(graphsToSweepOn)

        for g in graphsToSweepOn:
            del g.crossMinimizer
            del g.currentNodeOrder
            del g.portDistributor
            del g.currentlyBestNodeAndPortOrder

    def chooseMinimizingMethod(self, graphsToSweepOn):
        parent = graphsToSweepOn[0]
        if not parent.crossMinimizer.isDeterministic:
            return self.compareDifferentRandomizedLayouts
        elif parent.crossMinAlwaysImproves:
            return self.minimizeCrossingsNoCounter
        else:
            return self.minimizeCrossingsWithCounter

    def compareDifferentRandomizedLayouts(self, gData: LGraph):
        # Reset the seed, otherwise copies of hierarchical
        # graphs in different parent nodes are layouted differently.
        self.random = Random(self.randomSeed)

        # In order to only copy graphs whose node order has changed,
        # save them in a set.
        self.graphsWhoseNodeOrderChanged.clear()

        bestCrossings = inf
        thouroughness = gData.thoroughness
        for _ in range(thouroughness):
            crossings = self.minimizeCrossingsWithCounter(gData)
            if crossings < bestCrossings:
                bestCrossings = crossings
                self.saveAllNodeOrdersOfChangedGraphs()
                if not bestCrossings:
                    break

    def saveAllNodeOrdersOfChangedGraphs(self):
        for graph in self.graphsWhoseNodeOrderChanged:
            sc = SweepCopy(graph.currentlyBestNodeAndPortOrder)
            graph.bestNodeAndPortOrder = sc

    def countCurrentNumberOfCrossings(self, currentGraph):
        """
        We only need to count crossings below the current graph and also only
        if they are marked as to be processed hierarchically.
        """
        totalCrossings = 0
        countCrossingsIn = deque()
        countCrossingsIn.append(currentGraph)
        while countCrossingsIn:
            gD = countCrossingsIn.pop()
            totalCrossings += gD.crossCounter.countAllCrossings(
                gD.currentNodeOrder)
            for child in gD.childGraphs:
                if child.dontSweepInto():
                    totalCrossings += self.countCurrentNumberOfCrossings(child)
        return totalCrossings

    def minimizeCrossingsWithCounter(self, gData):
        isForwardSweep = bool(self.random.getrandbits(1))

        gData.crossMinimizer.setFirstLayerOrder(
            gData.currentNodeOrder, isForwardSweep)
        self.sweepReducingCrossings(gData, isForwardSweep, True)
        crossingsInGraph = self.countCurrentNumberOfCrossings(gData)

        oldNumberOfCrossings = 0
        while True:
            self.setCurrentlyBestNodeOrders()

            if crossingsInGraph == 0:
                return 0

            isForwardSweep = not isForwardSweep
            oldNumberOfCrossings = crossingsInGraph
            self.sweepReducingCrossings(gData, isForwardSweep, False)
            crossingsInGraph = self.countCurrentNumberOfCrossings(gData)
            if not (oldNumberOfCrossings > crossingsInGraph):
                break

        return oldNumberOfCrossings

    def minimizeCrossings(self, graphsToSweepOn: List[LGraph], minimizingMethod):
        for gData in graphsToSweepOn:
            if gData.currentNodeOrder:
                minimizingMethod(gData)
                if gData.parent is not None:
                    self.setPortOrderOnParentGraph(gData)

    def setPortOrderOnParentGraph(self, gData):
        if (gData.hasExternalPorts()):
            bestSweep = gData.getBestSweep()
            # Sort ports on left and right side of the parent node
            self.sortPortsByDummyPositionsInLastLayer(
                bestSweep.nodes, gData.parent, True)
            self.sortPortsByDummyPositionsInLastLayer(
                bestSweep.nodes, gData.parent, False)
            #gData.parent().setProperty(LayeredOptions.PORT_CONSTRAINTS, PortConstraints.FIXED_ORDER)

    def sortPortsByDummyPositionsInLastLayer(self,
                                             nodeOrder: List[List[LNode]],
                                             parent, onRightMostLayer: bool):
        _endIndex = endIndex(onRightMostLayer, nodeOrder.length)
        lastLayer = nodeOrder[_endIndex]
        if not lastLayer[0].isExternalPortDummy:
            return

        j = firstIndex(onRightMostLayer, lastLayer.length)
        ports = parent.getPorts()
        for i in range(i, len(ports)):
            port = ports[i]
            if (isOnEndOfSweepSide(port, onRightMostLayer)
                    and port.isHierarchical):
                ports[i] = lastLayer[j].origin
                j += next(onRightMostLayer)

    @staticmethod
    def getBestSweep(graph):
        if graph.crossMinimizer.isDeterministic:
            return graph.currentlyBestNodeAndPortOrder
        else:
            return graph.currentNodeOrder

    def transferNodeAndPortOrdersToGraph(self, graphsToSweepOn):
        for gD in graphsToSweepOn:
            bestSweep = self.getBestSweep(gD)
            if bestSweep is not None:
                bestSweep.transferNodeAndPortOrdersToGraph(gD)

    # For use with any two-layer crossing minimizer which always improves
    # crossings (e.g. two-sided greedy switch).
    def minimizeCrossingsNoCounter(self, gData):
        isForwardSweep = True
        improved = True
        while improved:
            improved = False
            improved = gData.crossMinimizer.setFirstLayerOrder(
                gData.currentNodeOrder, isForwardSweep)
            improved |= self.sweepReducingCrossings(
                gData, isForwardSweep, False)
            isForwardSweep = not isForwardSweep

        self.setCurrentlyBestNodeOrders()

    def setCurrentlyBestNodeOrders(self):
        for graph in self.graphsWhoseNodeOrderChanged:
            graph.currentlyBestNodeAndPortOrder = SweepCopy(
                graph.currentNodeOrder)

    def sweepReducingCrossings(self, graph, forward: bool, firstSweep: bool):
        nodes = graph.currentNodeOrder
        length = len(nodes)

        improved = graph.portDistributor.distributePortsWhileSweeping(
            nodes,
            firstIndex(forward, length),
            forward)
        firstLayer = nodes[firstIndex(forward, length)]
        improved |= self.sweepInHierarchicalNodes(
            firstLayer, forward, firstSweep)
        i = firstFree(forward, length)

        minimizeCrossings = graph.crossMinimizer.minimizeCrossings
        distributePortsWhileSweeping = graph.portDistributor.distributePortsWhileSweeping
        sweepInHierarchicalNodes = self.sweepInHierarchicalNodes
        step = next_step(forward)
        while isNotEnd(length, i, forward):
            improved |= minimizeCrossings(
                nodes, i, forward, firstSweep)
            improved |= distributePortsWhileSweeping(nodes, i, forward)
            improved |= sweepInHierarchicalNodes(
                nodes[i], forward, firstSweep)
            i += step

        self.graphsWhoseNodeOrderChanged.add(graph)
        return improved

    def sweepInHierarchicalNodes(self, layer, isForwardSweep, isFirstSweep):
        improved = False
        for node in layer:
            if (node.nestedGraph is not None
                    and not self.graphInfoHolders[node.nestedGraph].dontSweepInto()):
                improved |= self.sweepInHierarchicalNode(
                    isForwardSweep,
                    node, isFirstSweep)

        return improved

    def sweepInHierarchicalNode(self, isForwardSweep, node, isFirstSweep):
        nestedLGraph = node.nestedGraph
        nestedGraph = self.graphInfoHolders[nestedLGraph]
        nestedGraphNodeOrder = nestedGraph.currentNodeOrder
        startIndex = firstIndex(
            isForwardSweep, nestedGraphNodeOrder.length)
        firstNode = nestedGraphNodeOrder[startIndex][0]

        if firstNode.isExternalPortDummy:
            nestedGraphNodeOrder[startIndex] = self.sortPortDummiesByPortPositions(
                node,
                nestedGraphNodeOrder[startIndex],
                sideOpposedSweepDirection(isForwardSweep))
        else:
            nestedGraph.crossMinimizer.setFirstLayerOrder(
                nestedGraphNodeOrder, isForwardSweep)

        improved = self.sweepReducingCrossings(
            nestedGraph, isForwardSweep, isFirstSweep)
        self.sortPortsByDummyPositionsInLastLayer(
            nestedGraph.currentNodeOrder,
            nestedGraph.parent,
            isForwardSweep)

        return improved