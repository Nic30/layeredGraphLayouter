from typing import List

from layeredGraphLayouter.containers.constants import PortSide, NodeType
from layeredGraphLayouter.containers.lGraph import LGraph, LNodeLayer
from layeredGraphLayouter.crossing.crossingCounter import CrossingsCounter
from layeredGraphLayouter.crossing.hyperedgeCrossingsCounter import HyperedgeCrossingsCounter


class AllCrossingsCounter():
    """
    :note: Ported from ELK.

    Counts all crossings in a graph.
    """

    def __init__(self, graph: LGraph):
        inLayerEdgeCounts = [0 for _ in graph.layers]
        hasNorthSouthPorts = [False for _ in graph.layers]
        hasHyperEdgesEastOfIndex = hasNorthSouthPorts[:]

        self.inLayerEdgeCounts = inLayerEdgeCounts
        self.hasNorthSouthPorts = hasNorthSouthPorts
        self.hasHyperEdgesEastOfIndex = hasHyperEdgesEastOfIndex 
        self.nPorts = 0

        for l, layer in enumerate(graph.layers):
            for node in layer:
                hasNorthSouthPorts[l] |= node.type == NodeType.NORTH_SOUTH_PORT
                for port in node.iterPorts():
                    if len(port.incomingEdges) + len(port.outgoingEdges) > 1:
                        if port.side == PortSide.EAST:
                            hasHyperEdgesEastOfIndex[l] = True
                        elif (port.side == PortSide.WEST and l > 0):
                            hasHyperEdgesEastOfIndex[l - 1] = True

        for edge in graph.edges:
            if edge.srcNode.layer is edge.dstNode.layer:
                inLayerEdgeCounts[l] += 1

        portPos = {}
        self.hyperedgeCrossingsCounter = HyperedgeCrossingsCounter(
            inLayerEdgeCounts,
            hasNorthSouthPorts,
            portPos)
        self.crossingCounter = CrossingsCounter(portPos)

    def countAllCrossings(self, currentOrder: List[LNodeLayer]):
        """
        Count all crossings.

        :param currentOrder: the current node order
        :return: the number of crossings in the graph
        """
        if not currentOrder:
            return 0

        # count crossings on sides
        crossings = self.crossingCounter.countInLayerCrossingsOnSide(
            currentOrder[0], PortSide.WEST)
        crossings += self.crossingCounter.countInLayerCrossingsOnSide(
            currentOrder[len(currentOrder) - 1], PortSide.EAST)

        # cond crossing between layers
        countCrossingsAt = self.countCrossingsAt
        for layerIndex in range(len(currentOrder)):
            crossings += countCrossingsAt(layerIndex, currentOrder)

        return crossings

    def countCrossingsAt(self, layerIndex: int, currentOrder: List[LNodeLayer]):
        totalCrossings = 0
        leftLayer = currentOrder[layerIndex]
        isNotLast = layerIndex < len(currentOrder) - 1
        if isNotLast:
            rightLayer = currentOrder[layerIndex + 1]
            if self.hasHyperEdgesEastOfIndex[layerIndex]:
                totalCrossings = self.hyperedgeCrossingsCounter.countCrossings(
                    leftLayer, rightLayer)
                totalCrossings += self.crossingCounter.countInLayerCrossingsOnSide(
                    leftLayer, PortSide.EAST)
                totalCrossings += self.crossingCounter.countInLayerCrossingsOnSide(
                    rightLayer, PortSide.WEST)
            else:
                totalCrossings = self.crossingCounter.countCrossingsBetweenLayers(
                    leftLayer, rightLayer)

        if self.hasNorthSouthPorts[layerIndex]:
            totalCrossings += self.crossingCounter.countNorthSouthPortCrossingsInLayer(
                leftLayer)

        return totalCrossings
