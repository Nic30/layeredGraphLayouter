from itertools import chain
from math import inf

from layeredGraphLayouter.containers.constants import PortSide, NodeType
from layeredGraphLayouter.containers.lEdge import LEdge
from layeredGraphLayouter.containers.lNode import LNode
from layeredGraphLayouter.containers.lPort import LPort


class NodeInfo():
    """
    For a single node, collects number of paths to nodes with random
    or hierarchical nodes.
    """

    def __init__(self):
        self.connectedEdges = 0
        self.hierarchicalInfluence = 0
        self.randomInfluence = 0

    def transfer(self, nodeInfo: "NodeInfo"):
        self.hierarchicalInfluence += nodeInfo.hierarchicalInfluence
        self.randomInfluence += nodeInfo.randomInfluence
        self.connectedEdges += nodeInfo.connectedEdges

    def __repr__(self):
        return ("<NodeInfo [connectedEdges=" + self.connectedEdges
                + ", hierarchicalInfluence=" + self.hierarchicalInfluence
                + ", randomInfluence=" + self.randomInfluence + "]>")


def bottomUpForced(boundary: float):
    return boundary < -1


def hasNoEasternPorts(node: LNode):
    return not bool(node.east)


def hasNoWesternPorts(node: LNode):
    return not bool(node.west)


def isExternalPortDummy(node: LNode):
    return node.type == NodeType.EXTERNAL_PORT


def isNorthSouthDummy(node: LNode):
    return node.type == NodeType.NORTH_SOUTH_PORT


def originPort(node: LNode) -> LPort:
    return node.origin


def isEasternDummy(node: LNode):
    return originPort(node).side == PortSide.EAST


class LayerSweepTypeDecider():
    """
    In order to decide whether to sweep into the graph or not, we compare
    the number of paths to nodes whose position is decided on by random decisions
    to the number of paths to nodes whose position depends on cross-hierarchy edges.
    By calculating (pathsToRandom - pathsToHierarchical) / allPaths, this value
    will always be between -1 (many cross hierarchical paths) and +1 (many random paths).
    By setting the boundary CROSSING_MINIMIZATION_HIERARCHICAL_SWEEPINESS,
    we can choose how likely it is to be hierarchical or more bottom up.
    """

    def __init__(self, graphData: "GraphInfoHolder"):
        """
        Creates LayerSweepTypeDecider for deciding whether to sweep into graphs or not.

        :param graphData: the graph holder object for auxiliary graph
            information needed in crossing minimization
        """
        self.graphData = graphData
        self.nodeInfo = {n: NodeInfo() for n in graphData.lGraph.nodes}

    def useBottomUp(self) -> bool:
        """
        Decide whether to use bottom up or cross-hierarchical sweep method.

        @return decision
        """
        boundary = self.graphData.lGraph.crossingMinimizationHierarchicalSweepiness
        if (bottomUpForced(boundary)
                or self.rootNode()
                or self.fixedPortOrder()
                or self.fewerThanTwoInOutEdges()):
            return True

        if self.graphData.crossMinDeterministic():
            return False

        pathsToRandom = 0
        pathsToHierarchical = 0

        nsPortDummies = []
        for layer in self.graphData.currentNodeOrder:
            for node in layer:
                # We must visit all sources of edges first, so we collect north
                # south dummies for later.
                if isNorthSouthDummy(node):
                    nsPortDummies.add(node)
                    continue

                currentNode = self.nodeInfo[node]
                # Check for hierarchical port dummies or random influence.
                if isExternalPortDummy(node):
                    currentNode.hierarchicalInfluence = 1
                    if isEasternDummy(node):
                        pathsToHierarchical += currentNode.connectedEdges
                elif hasNoWesternPorts(node):
                    currentNode.randomInfluence = 1
                elif hasNoEasternPorts(node):
                    pathsToRandom += currentNode.connectedEdges

                # Increase counts of paths by the number outgoing edges times the influence
                # and transfer information to targets.
                for edge in node.getOutgoingEdges():
                    pathsToRandom += currentNode.randomInfluence
                    pathsToHierarchical += currentNode.hierarchicalInfluence
                    self.transferInfoToTarget(currentNode, edge)

                # Do the same for north/south dummies: Increase counts of paths
                # by the number outgoing edges times the
                # influence and transfer information to dummies.
                northSouthPorts = list(chain(node.getPortSideView(PortSide.NORTH),
                                             node.getPortSideView(PortSide.SOUTH)))
                for port in northSouthPorts:
                    nsDummy = port.portDummy
                    if nsDummy is not None:
                        pathsToRandom += currentNode.randomInfluence
                        pathsToHierarchical += currentNode.hierarchicalInfluence
                        self.transferInfoTo(currentNode, nsDummy)

            # Now process nsPortDummies
            for node in nsPortDummies:
                currentNode = self.nodeInfo[node]
                for edge in node.getOutgoingEdges():
                    pathsToRandom += currentNode.randomInfluence
                    pathsToHierarchical += currentNode.hierarchicalInfluence
                    self.transferInfoToTarget(currentNode, edge)

            nsPortDummies.clear()

        allPaths = pathsToRandom + pathsToHierarchical
        if allPaths == 0:
            normalized = inf
        else:
            normalized = (pathsToRandom - pathsToHierarchical) / allPaths

        return normalized >= boundary

    def fixedPortOrder(self) -> bool:
        return self.graphData.parent.portConstraints.isOrderFixed()

    def transferInfoToTarget(self, currentNode: NodeInfo, edge: LEdge) -> None:
        self.transferInfoTo(currentNode, edge.dstNode)

    def transferInfoTo(self, currentNode: NodeInfo, target: LNode):
        targetNodeInfo = self.nodeInfo[target]
        targetNodeInfo.transfer(currentNode)
        targetNodeInfo.connectedEdges += 1

    def fewerThanTwoInOutEdges(self):
        p = self.graphData.parent
        return (len(p.getPortSideView(PortSide.EAST)) < 2
                and len(p.getPortSideView(PortSide.WEST)) < 2)

    def rootNode(self):
        return not self.graphData.hasParent
