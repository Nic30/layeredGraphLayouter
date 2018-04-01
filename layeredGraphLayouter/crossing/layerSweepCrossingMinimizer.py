from collections import deque
from math import inf
from random import Random
from typing import List, Optional

from layeredGraphLayouter.containers.constants import PortSide, PortConstraints,\
    NodeType, HierarchyHandling
from layeredGraphLayouter.containers.lGraph import LGraph
from layeredGraphLayouter.containers.lNode import LNode
from layeredGraphLayouter.crossing.allCrossingsCounter import AllCrossingsCounter
from layeredGraphLayouter.crossing.barycenterHeuristic import BarycenterHeuristic
from layeredGraphLayouter.crossing.dummyPortDistributor import DummyPortDistributor
from layeredGraphLayouter.crossing.forsterConstraintResolver import ForsterConstraintResolver
from layeredGraphLayouter.crossing.graphInfoHolder import GraphInfoHolder
from layeredGraphLayouter.crossing.nodeRelativePortDistributor import NodeRelativePortDistributor
from layeredGraphLayouter.crossing.sweepCopy import SweepCopy
from layeredGraphLayouter.iLayoutProcessor import ILayoutProcessor
from layeredGraphLayouter.layoutProcessorConfiguration import LayoutProcessorConfiguration
from layeredGraphLayouter.edgeManipulators.longEdgeSplitter import LongEdgeSplitter
from layeredGraphLayouter.nodeManipulators.inLayerConstraintProcessor import InLayerConstraintProcessor
from layeredGraphLayouter.edgeManipulators.longEdgeJoiner import LongEdgeJoiner


def firstFree(isForwardSweep, length):
    return 1 if isForwardSweep else length - 2


def firstIndex(isForwardSweep: bool, length: int):
    return 0 if isForwardSweep else length - 1


def endIndex(isForwardSweep: bool, length: int):
    return length - 1 if isForwardSweep else 0


def sideForStep(isForwardSweep: bool) -> PortSide:
    if isForwardSweep:
        return PortSide.EAST
    else:
        return PortSide.WEST


def sideOpposedSweepDirection(isForwardSweep):
    return PortSide.WEST if isForwardSweep else PortSide.EAST


def iterLayerIndexes(layers_cnt, isForwardSweep):
    i = firstFree(isForwardSweep, layers_cnt)
    if isForwardSweep:
        return range(layers_cnt)
    else:
        return range(layers_cnt - 1, -1, -1)


def isExternalPortDummy(firstNode: LNode) -> bool:
    return firstNode.type == NodeType.EXTERNAL_PORT


class LayerSweepCrossingMinimizer(ILayoutProcessor):
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

    def __init__(self):
        self.randomSeed = 0
        self.random = Random(self.randomSeed)

    @staticmethod
    def getLayoutProcessorConfiguration(graph: LGraph)->Optional[LayoutProcessorConfiguration]:
        return LayoutProcessorConfiguration(
            p3_node_ordering_before=[LongEdgeSplitter(),
                                     # PortListSorter()
                                     ],
            p4_node_placement_before=[InLayerConstraintProcessor()],
            p5_edge_routing_after=[LongEdgeJoiner()],
        )

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

        emptyGraph = not layers or sum(len(l) for l in layers) == 0
        singleNode = len(layers) == 1 and len(layers[0]) == 1

        hierarchicalLayout = graph.hierarchyHandling == HierarchyHandling.INCLUDE_CHILDREN

        if emptyGraph or (singleNode and not hierarchicalLayout):
            return

        graphsToSweepOn = self.initialize(graph)
        root = self.graphInfoHolders[graph]
        minimizingMethod = self.chooseMinimizingMethod(root)
        self.minimizeCrossings(graphsToSweepOn, minimizingMethod)
        self.transferNodeAndPortOrdersToGraph(graphsToSweepOn)

    def initialize(self, rootGraph: LGraph) ->List[GraphInfoHolder]:
        """
        Traverses inclusion breadth-first and initializes each Graph.
        """
        self.graphsWhoseNodeOrderChanged = set()
        self.graphInfoHolders = {}

        self.random = rootGraph.random
        self.randomSeed = self.random.random()

        _graphsToSweepOn = deque([rootGraph, ])
        graphsToSweepOn = []
        while _graphsToSweepOn:
            g = _graphsToSweepOn.pop()
            g.random = self.random
            gih = GraphInfoHolder(g,
                                  BarycenterHeuristic,
                                  NodeRelativePortDistributor,
                                  self.graphInfoHolders)
            assert g not in self.graphInfoHolders
            self.graphInfoHolders[g] = gih
            graphsToSweepOn.append(gih)
            _graphsToSweepOn.extend(g.childGraphs)
            for n in g.nodes:
                if n.nestedLgraph is not None:
                    _graphsToSweepOn.append(n.nestedLgraph)

        return graphsToSweepOn

    def chooseMinimizingMethod(self, root: GraphInfoHolder):
        if not root.crossMinimizer.isDeterministic:
            return self.compareDifferentRandomizedLayouts
        elif root.crossMinAlwaysImproves:
            return self.minimizeCrossingsNoCounter
        else:
            return self.minimizeCrossingsWithCounter

    def compareDifferentRandomizedLayouts(self, gData: GraphInfoHolder):
        # Reset the seed, otherwise copies of hierarchical
        # graphs in different parent nodes are layouted differently.
        self.random.seed(self.randomSeed)

        # In order to only copy graphs whose node order has changed,
        # save them in a set.
        self.graphsWhoseNodeOrderChanged.clear()

        bestCrossings = inf
        thouroughness = gData.lGraph.thoroughness
        for _ in range(thouroughness):
            crossings = self.minimizeCrossingsWithCounter(gData)
            if crossings < bestCrossings:
                bestCrossings = crossings
                self.saveAllNodeOrdersOfChangedGraphs()
                if bestCrossings == 0:
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
        graphInfoHolders = self.graphInfoHolders

        while countCrossingsIn:
            gD = countCrossingsIn.pop()
            totalCrossings += gD.crossingsCounter.countAllCrossings(
                gD.currentNodeOrder)

            for child in gD.childGraphs:
                child = graphInfoHolders[child]
                if child.dontSweepInto():
                    totalCrossings += self.countCurrentNumberOfCrossings(child)

        return totalCrossings

    def minimizeCrossingsWithCounter(self, gData):
        sweepReducingCrossings = self.sweepReducingCrossings

        isForwardSweep = bool(self.random.getrandbits(1))

        gData.crossMinimizer.setFirstLayerOrder(
            gData.currentNodeOrder, isForwardSweep)
        sweepReducingCrossings(gData, isForwardSweep, True)

        crossingsInGraph = self.countCurrentNumberOfCrossings(gData)
        countCurrentNumberOfCrossings = self.countCurrentNumberOfCrossings
        oldNumberOfCrossings = 0
        while True:
            self.setCurrentlyBestNodeOrders()

            if crossingsInGraph == 0:
                return 0

            isForwardSweep = not isForwardSweep
            oldNumberOfCrossings = crossingsInGraph
            sweepReducingCrossings(gData, isForwardSweep, False)
            crossingsInGraph = countCurrentNumberOfCrossings(gData)
            if not (oldNumberOfCrossings > crossingsInGraph):
                break

        return oldNumberOfCrossings

    def minimizeCrossings(self, graphsToSweepOn: List[GraphInfoHolder], minimizingMethod):
        for gData in graphsToSweepOn:
            if gData.currentNodeOrder:
                minimizingMethod(gData)
                if gData.parent is not None:
                    self.setPortOrderOnParentGraph(gData)

    def setPortOrderOnParentGraph(self, gData):
        if (gData.hasExternalPorts):
            bestSweep = gData.getBestSweep()
            # Sort ports on left and right side of the parent node
            self.sortPortsByDummyPositionsInLastLayer(
                bestSweep.nodeOrder, gData.parent, True)
            self.sortPortsByDummyPositionsInLastLayer(
                bestSweep.nodeOrder, gData.parent, False)
            gData.parent.portConstraints = PortConstraints.FIXED_ORDER

    def sortPortsByDummyPositionsInLastLayer(self,
                                             nodeOrder: List[List[LNode]],
                                             parent,
                                             onRightMostLayer: bool):
        _endIndex = endIndex(onRightMostLayer, len(nodeOrder))
        lastLayer = nodeOrder[_endIndex]
        if not isExternalPortDummy(lastLayer[0]):
            return

        j = firstIndex(onRightMostLayer, len(lastLayer))
        ports = parent.getPortSideView(sideForStep(onRightMostLayer))
        step = 1 if onRightMostLayer else -1
        for i in range(len(ports)):
            port = ports[i]
            if port.insideConnections:
                ports[i] = lastLayer[j].origin
                j += step

    def transferNodeAndPortOrdersToGraph(self, graphsToSweepOn):
        for gD in graphsToSweepOn:
            bestSweep = gD.getBestSweep()
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
        layers = graph.currentNodeOrder
        minimizeCrossings = graph.crossMinimizer.minimizeCrossings
        distributePortsWhileSweeping = graph.portDistributor.distributePortsWhileSweeping
        sweepInHierarchicalNodes = self.sweepInHierarchicalNodes

        length = len(layers)
        index0 = firstIndex(forward, length)
        improved = graph.portDistributor.distributePortsWhileSweeping(
            layers, index0, forward)
        firstLayer = layers[index0]
        improved |= sweepInHierarchicalNodes(firstLayer, forward, firstSweep)

        for i in iterLayerIndexes(length, forward):
            improved |= minimizeCrossings(layers, i, forward, firstSweep)
            improved |= distributePortsWhileSweeping(layers, i, forward)
            improved |= sweepInHierarchicalNodes(
                layers[i], forward, firstSweep)

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
            isForwardSweep, len(nestedGraphNodeOrder))
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
