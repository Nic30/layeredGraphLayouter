from typing import List

from layeredGraphLayouter.containers.lGraph import LGraph
from layeredGraphLayouter.crossing.allCrossingsCounter import AllCrossingsCounter
from layeredGraphLayouter.crossing.forsterConstraintResolver import ForsterConstraintResolver
from layeredGraphLayouter.crossing.layerSweepTypeDecider import LayerSweepTypeDecider


class GraphInfoHolder():
    """
    Collects data needed for cross minimization and port distribution.

    :note: Ported from ELK.
    :ivar lGraph: Raw graph data.
    """

    def __init__(self, graph: LGraph,
                 crossMinCls,
                 portDistributorCls,
                 graphs: List["GraphInfoHolder"]):
        """
        Create object collecting information about a graph.

        @param graph
                   The graph
        @param crossMinType
                   The CrossMinimizer
        @param graphs
                   the complete list of all graphs in the hierarchy
        """
        self.lGraph = graph
        self.currentNodeOrder = graph.layers
        self.bestNodeAndPortOrder = None
        self.currentlyBestNodeAndPortOrder = None

        # Hierarchy information.
        self.parent = graph.parentLnode
        self.hasParent = self.parent is not None
        self.parentGraphData = graphs[self.parent.graph] if self.hasParent else None
        self.hasExternalPorts = graph.p_externalPorts
        self.childGraphs = []
        for layer in graph.layers:
            for node in layer:
                if node.nestedLgraph is not None:
                    self.childGraphs.append(node.nestedLgraph)

        # Init all objects needing initialization by graph traversal.
        self.crossingsCounter = AllCrossingsCounter(self.lGraph)
        self.random = graph.random
        self.portDistributor = portDistributorCls(
            graph.random, self.lGraph)
        layerSweepTypeDecider = LayerSweepTypeDecider(self)

        self.constraintResolver = ForsterConstraintResolver(
            self.currentNodeOrder)
        self.crossMinimizer = crossMinCls(self.constraintResolver,
                                          self.random,
                                          self.portDistributor,
                                          self.currentNodeOrder)

        # calculate whether we need to use bottom up or sweep into this graph.
        self.useBottomUp = layerSweepTypeDecider.useBottomUp()

    def dontSweepInto(self):
        """
        :return: the processRecursively
        """
        return self.useBottomUp

    def getBestSweep(self):
        """
        :return Copy of node order for currently best sweep.
        """
        if self.crossMinimizer.isDeterministic:
            return self.currentlyBestNodeAndPortOrder
        else:
            return self.bestNodeAndPortOrder

    def crossMinDeterministic(self):
        return self.crossMinimizer.isDeterministic

    def crossMinAlwaysImproves(self):
        """
        :return: whether this CrossingMinimizer always improves
        """
        return self.crossMinimizer.alwaysImproves
