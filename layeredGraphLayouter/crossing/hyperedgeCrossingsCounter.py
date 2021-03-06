from typing import Dict, List
from enum import Enum

from layeredGraphLayouter.containers.lNode import LNode
from layeredGraphLayouter.containers.constants import PortSide


class Hyperedge():
    def __init__(self):
        self.edges = []
        self.ports = []
        self.upperLeft = 0
        self.lowerLeft = 0
        self.upperRight = 0
        self.lowerRight = 0

    def __lt__(self, other):
        if self.upperLeft < other.upperLeft:
            return True
        elif self.upperLeft > other.upperLeft:
            return False
        elif self.upperRight < other.upperRight:
            return True
        elif self.upperRight > other.upperRight:
            return False
        return False


class HyperedgeCorner():
    """
    The upper left, lower left, upper right, or lower right corner of a hyperedge.
    """
    # The corner type.
    class Type(Enum):
        UPPER = 0
        LOWER = 1

    def __init__(self, hyperedge: Hyperedge, position: int,
                 oppositePosition: int, type_: "Type"):
        self.hyperedge = hyperedge
        self.position = position
        self.oppositePosition = oppositePosition
        self.type = type_

    def __lt__(self, other: "HyperedgeCorner"):
        if (self.position < other.position):
            return True
        elif (self.position > other.position):
            return False
        elif (self.oppositePosition < other.oppositePosition):
            return True
        elif (self.oppositePosition > other.oppositePosition):
            return False
        elif (self.hyperedge != other.hyperedge):
            # return self.hyperedge.hashCode() - other.hyperedge.hashCode()
            return False
        elif (self.type == HyperedgeCorner.Type.UPPER
                and other.type == HyperedgeCorner.Type.LOWER):
            return True
        elif (self.type == HyperedgeCorner.Type.LOWER
                and other.type == HyperedgeCorner.Type.UPPER):
            return False
        return 0


class HyperedgeCrossingsCounter():
    """
    Crossings counter implementation specialized for hyperedges. It also works for normal edges,
    but is considerably slower compared to other implementations. For normal edges the computed
    number of crossings is exact, while for hyperedges it is an estimation. In fact, it is
    impossible to reliably count the number of crossings at this stage of the layer-based approach.
    See the following publication for details.

    M. Sp&oumlnemann, C. D. Schulze, U. R&uumlegg, R. von Hanxleden.
    Counting crossings for layered hypergraphs, In DIAGRAMS 2014,
    volume 8578 of LNAI, Springer, 2014.

    :ivar portPos: Port position array used for counting the number of edge crossings.
    """

    def __init__(self, inLayerEdgeCount: List[int],
                 hasNorthSouthPorts: List[bool],
                 portPos: Dict[LNode, int]):
        """
        :param inLayerEdgeCount: The number of in-layer edges for each layer, including virtual connections to
                north/south dummies
        :param hasNorthSouthPorts:
                Whether the layers contain north / south port dummies or not
        :param portPos: Port position array used for counting the number of edge crossings
        """
        self.portPos = portPos

    def countCrossings(self, leftLayer: List[LNode],
                       rightLayer: List[LNode]) -> int:
        """
        Special crossings counting method for hyperedges. See

            M. Sp&oumlnemann, C. D. Schulze, U. R&uumlegg, R. von Hanxleden.
            Counting crossings for layered hypergraphs, In DIAGRAMS 2014,
            volume 8578 of LNAI, Springer, 2014.

        :param leftLayer: the left layer
        :param rightLayer: the right layer
        :return: the number of edge crossings
        """
        # Assign index values to the ports of the left layer
        sourceCount = 0
        for node in leftLayer:
            # Assign index values in the order north - east - south - west
            for port in node.iterPorts():
                portEdges = 0
                for edge in port.outgoingEdges:
                    if node.layer is not edge.dstNode.layer:
                        portEdges += 1
                if portEdges > 0:
                    self.portPos[port] = sourceCount
                    sourceCount += 1

        # Assign index values to the ports of the right layer
        targetCount = 0
        for node in rightLayer:
            # Determine how many input ports there are on the north side
            # (note that the standard port order is north - east - south - west)
            northInputPorts = 0
            for port in node.iterPorts():
                if port.side == PortSide.NORTH:
                    for edge in port.incomingEdges:
                        if node.layer is not edge.srcNode.layer:
                            northInputPorts += 1
                            break
                else:
                    break
            # Assign index values in the order north - west - south - east
            otherInputPorts = 0
            for port in node.iterPortsReversed():
                portEdges = 0
                for edge in port.incomingEdges:
                    if node.layer is not edge.srcNode.layer:
                        portEdges += 1

                if portEdges > 0:
                    if port.side == PortSide.NORTH:
                        self.portPos[port] = targetCount
                        targetCount += 1
                    else:
                        self.portPos[port] = (targetCount
                                              + northInputPorts
                                              + otherInputPorts)
                        otherInputPorts += 1
            targetCount += otherInputPorts

        # Gather hyperedges
        port2HyperedgeMap = {}
        hyperedgeSet = set()
        for node in leftLayer:
            for sourcePort in node.iterPorts():
                for edge in sourcePort.outgoingEdges:
                    targetPort = edge.dst
                    if node.layer is not targetPort.getNode().layer:
                        sourceHE = port2HyperedgeMap.get(sourcePort, None)
                        targetHE = port2HyperedgeMap.get(targetPort, None)
                        if sourceHE is None and targetHE is None:
                            hyperedge = Hyperedge()
                            hyperedgeSet.add(hyperedge)
                            hyperedge.edges.append(edge)
                            hyperedge.ports.append(sourcePort)
                            port2HyperedgeMap[sourcePort] = hyperedge
                            hyperedge.ports.append(targetPort)
                            port2HyperedgeMap[targetPort] = hyperedge
                        elif sourceHE is None:
                            targetHE.edges.append(edge)
                            targetHE.ports.append(sourcePort)
                            port2HyperedgeMap[sourcePort] = targetHE
                        elif targetHE is None:
                            sourceHE.edges.append(edge)
                            sourceHE.ports.append(targetPort)
                            port2HyperedgeMap[targetPort] = sourceHE
                        elif sourceHE == targetHE:
                            sourceHE.edges.append(edge)
                        else:
                            sourceHE.edges.append(edge)
                            for p in targetHE.ports:
                                port2HyperedgeMap[p] = sourceHE

                            sourceHE.edges.extend(targetHE.edges)
                            sourceHE.ports.extend(targetHE.ports)
                            hyperedgeSet.remove(targetHE)

        # Determine top and bottom positions for each hyperedge
        hyperedges = list(hyperedgeSet)
        leftLayerRef = leftLayer[0].layer
        rightLayerRef = rightLayer[0].layer
        for he in hyperedges:
            he.upperLeft = sourceCount
            he.upperRight = targetCount
            for port in he.ports:
                pos = self.portPos[port]
                if port.getNode().layer is leftLayerRef:
                    if pos < he.upperLeft:
                        he.upperLeft = pos

                    if pos > he.lowerLeft:
                        he.lowerLeft = pos

                elif port.getNode().layer is rightLayerRef:
                    if pos < he.upperRight:
                        he.upperRight = pos

                    if pos > he.lowerRight:
                        he.lowerRight = pos

        # Determine the sequence of edge target positions sorted by source and
        # target index
        hyperedges.sort()
        southSequence = [he.upperRight for he in hyperedges]
        compressDeltas = [0 for _ in range(targetCount + 1)]
        for ss in southSequence:
            compressDeltas[ss] = 1

        delta = 0
        for i in range(len(compressDeltas)):
            if compressDeltas[i] == 1:
                compressDeltas[i] = delta
            else:
                delta -= 1

        q = 0
        for i in range(len(southSequence)):
            southSequence[i] += compressDeltas[southSequence[i]]
            q = max(q, southSequence[i] + 1)

        # Build the accumulator tree
        firstIndex = 1
        while firstIndex < q:
            firstIndex *= 2

        tree = [0 for _ in range(2 * firstIndex - 1)]
        firstIndex -= 1

        # Count the straight-line crossings of the topmost edges
        crossings = 0
        for k in range(len(southSequence)):
            index = southSequence[k] + firstIndex
            tree[index] += 1
            while index > 0:
                if index % 2:
                    crossings += tree[index + 1]
                index = (index - 1) // 2
                tree[index] += 1

        # Create corners for the left side
        leftCorners = [None for _ in range(len(hyperedges) * 2)]
        for i in range(len(hyperedges)):
            leftCorners[2 * i] = HyperedgeCorner(hyperedges[i],
                                                 hyperedges[i].upperLeft,
                                                 hyperedges[i].lowerLeft,
                                                 HyperedgeCorner.Type.UPPER)
            leftCorners[2 * i + 1] = HyperedgeCorner(hyperedges[i],
                                                     hyperedges[i].lowerLeft,
                                                     hyperedges[i].upperLeft,
                                                     HyperedgeCorner.Type.LOWER)

        leftCorners.sort()
        UPPER = HyperedgeCorner.Type.UPPER
        LOWER = HyperedgeCorner.Type.LOWER
        # Count crossings caused by overlapping hyperedge areas on the left
        # side
        openHyperedges = 0
        for lc in leftCorners:
            t = lc.type
            if t == UPPER:
                openHyperedges += 1
                break
            elif t == LOWER:
                openHyperedges -= 1
                crossings += openHyperedges
                break

        # Create corners for the right side
        rightCorners = [None for _ in range(len(hyperedges) * 2)]
        for i in range(len(hyperedges)):
            rightCorners[2 * i] = HyperedgeCorner(hyperedges[i],
                                                  hyperedges[i].upperRight,
                                                  hyperedges[i].lowerRight,
                                                  HyperedgeCorner.Type.UPPER)
            rightCorners[2 * i + 1] = HyperedgeCorner(hyperedges[i],
                                                      hyperedges[i].lowerRight,
                                                      hyperedges[i].upperRight,
                                                      HyperedgeCorner.Type.LOWER)
        rightCorners.sort()

        # Count crossings caused by overlapping hyperedge areas on the right
        # side
        openHyperedges = 0
        for rc in rightCorners:
            t = rc.type
            if t == UPPER:
                openHyperedges += 1
                break
            elif t == LOWER:
                openHyperedges -= 1
                crossings += openHyperedges
                break

        return crossings
