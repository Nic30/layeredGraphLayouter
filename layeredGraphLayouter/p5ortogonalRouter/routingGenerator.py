from enum import Enum
from typing import Dict, List
from layeredGraphLayouter.containers.geometry import Point
from layeredGraphLayouter.containers.lPort import LPort
from collections import deque
from math import isnan, inf
from layeredGraphLayouter.containers.lNode import LNode
from layeredGraphLayouter.containers.constants import PortType, PortSide
from layeredGraphLayouter.containers.lEdge import LEdge
from random import Random
from layeredGraphLayouter.containers.lGraph import LGraph


class RoutingDirection(Enum):
    """
    Enumeration of available routing directions.
    """
    """ west to east routing direction."""
    WEST_TO_EAST = 0
    """ north to south routing direction."""
    NORTH_TO_SOUTH = 1
    """ south to north routing direction."""
    SOUTH_TO_NORTH = 2


class HyperNode():
    """
     * A hypernode used for routing a hyperedge.
    """

    def __init__(self):
        """
        :ivar ports: List[LPort] ports represented by this hypernode.
        :ivar mark: mark value used for cycle breaking.
        :ivar rank: the rank determines the horizontal distance to the preceding layer.
        :ivar start: vertical starting position of this hypernode.
        :ivar end: vertical ending position of this hypernode.
        :ivar sourcePosis: Dequeu[float], positions of line segments going to the preceding layer.
        :ivar targetPosis: Dequeu[float], positions of line segments going to the next layer.
        :ivar outgoing: List[Dependency] list of outgoing dependencies.
        :ivar outweight: sum of the weights of outgoing dependencies.
        :ivar incoming: List[Dependency], list of incoming dependencies.
        :ivar inweight: sum of the weights of incoming depencencies.
        """
        self.ports = []
        self.mark = 0
        self.rank = 0
        self.start = float('nan')
        self.end = float('nan')
        self.sourcePosis = deque()
        self.targetPosis = deque()
        self.outgoing = []
        self.outweight = 0
        self.incoming = []
        self.inweight = 0

    def addPortPositions(self, port: LPort, hyperNodeMap: Dict[LPort, "HyperNode"]):
        """
        Adds the positions of the given port and all connected ports.

        :param port a port
        :param hyperNodeMap map of ports to existing hypernodes
        """
        hyperNodeMap[port] = self
        self.ports.append(port)
        pos = routingStrategy.getPortPositionOnHyperNode(port)

        # set new start position
        if isnan(self.start):
            self.start = pos
        else:
            self.start = min(self.start, pos)

        # set new end position
        if isnan(self.end):
            self.end = pos
        else:
            self.end = max(self.end, pos)

        # add the new port position to the respective list
        if port.side == routingStrategy.getSourcePortSide():
            self.insertSorted(self.sourcePosis, pos)
        else:
            self.insertSorted(self.targetPosis, pos)

        # add connected ports
        for otherPort in port.iterConnectedPorts():
            if otherPort not in hyperNodeMap:
                self.addPortPositions(otherPort, hyperNodeMap)

    def __repr__(self):
        buff = []
        for port in self.ports:
            name = port.getNode().name
            if (name is None):
                name = "n" + port.getNode().getIndex()

            buff.append(name)

        buff.append('')
        return "{%s}" % (",".join(buff))

    def __lt__(self, other):
        return self.mark < other.mark

    def __eq__(self, other):
        if isinstance(other, HyperNode):
            return self.mark == other.mark

        return False

    def hashCode(self) -> int:
        return self.mark

    def getOutgoing(self) -> List["Dependency"]:
        """
         * Return the outgoing dependencies.
         *
         * :return: the outgoing dependencies
        """
        return self.outgoing


class Dependency():
    """
    A dependency between two hypernodes.

    :ivar source: the source hypernode of this dependency.
    :ivar target: the target hypernode of this dependency.
    :ivar weight: the weight of this dependency.
    """

    def __init__(self, thesource: HyperNode, thetarget: HyperNode,
                 theweight: int):
        """
        Creates a dependency from the given source to the given target.

        :param thesource the dependency source
        :param thetarget the dependency target
        :param theweight weight of the dependency
        """
        self.target = thetarget
        self.source = thesource
        self.weight = theweight
        self.source.outgoing.append(self)
        self.target.incoming.append(self)

    def __repr__(self):
        return "%r->%r" % (self.source, self.target)

    def getSource(self)-> HyperNode:
        """
         * Return the source node.
         *
         * :return: the source
        """
        return self.source

    def getTarget(self) -> HyperNode:
        """
         * Return the target node.
         *
         * :return: the target
        """
        return self.target

    def getWeight(self) -> int:
        """
         * Returns the weight of the hypernode dependency.
         *
         * :return: the weight
        """
        return self.weight


class OrthogonalRoutingGenerator():
    """
    Edge routing implementation that creates orthogonal bend points. Inspired by:
    <ul>
      <li>Georg Sander. Layout of directed hypergraphs with orthogonal hyperedges. In
        <i>Proceedings of the 11th International Symposium on Graph Drawing (GD '03)</i>,
        volume 2912 of LNCS, pp. 381-386. Springer, 2004.</li>
      <li>Giuseppe di Battista, Peter Eades, Roberto Tamassia, Ioannis G. Tollis,
        <i>Graph Drawing: Algorithms for the Visualization of Graphs</i>,
        Prentice Hall, New Jersey, 1999 (Section 9.4, for cycle breaking in the
        hyperedge segment graph)
    </ul>

    <p>This is a generic implementation that can be applied to all four routing directions.
    Usually, edges will be routed from west to east. However, with northern and southern
    external ports, this changes: edges are routed from south to north and north to south,
    respectively. To support these different requirements, the routing direction-related
    code is factored out into {@link IRoutingDirectionStrategy routing strategies.</p>

    <p>When instantiating a new routing generator, the concrete directional strategy must be
    specified. Once that is done, {@link #routeEdges(LGraph, List, int, List, double)
    is called repeatedly to route edges between given lists of nodes.</p>
    """
    # Constants and Variables

    """ differences below this tolerance value are treated as zero."""
    TOLERANCE = 1e-3

    """ factor for edge spacing used to determine the conflict threshold."""
    CONFL_THRESH_FACTOR = 0.2
    """ weight penalty for conflicts of horizontal line segments."""
    CONFLICT_PENALTY = 16

    """
    :ivar routingStrategy: routing direction strategy.
    :ivar edgeSpacing: spacing between edges.
    :ivar conflictThreshold: threshold at which conflicts of horizontal line segments are detected.
    :ivar createdJunctionPoints: set of already created junction points, to adef multiple points at the same position.
    :ivar debugPrefix: prefix of debug output files."""

    # /
    # Constructor

    def __init__(self, direction: RoutingDirection, edgeSpacing: float,
                 debugPrefix: str):
        """
         * Constructs a new instance.
         *
         * :param direction the direction edges should point at.
         * :param edgeSpacing the space between edges.
         * :param debugPrefix prefix of debug output files, or {@code null if no debug output should
         *                    be generated.
        """

        if direction == RoutingDirection.WEST_TO_EAST:
            self.routingStrategy = WestToEastRoutingStrategy()
        elif direction == RoutingDirection.NORTH_TO_SOUTH:
            self.routingStrategy = NorthToSouthRoutingStrategy()
        elif direction == RoutingDirection.SOUTH_TO_NORTH:
            self.routingStrategy = SouthToNorthRoutingStrategy()
        else:
            raise ValueError(direction)

        self.edgeSpacing = edgeSpacing
        self.conflictThreshold = self.CONFL_THRESH_FACTOR * edgeSpacing
        self.debugPrefix = debugPrefix
        self.createdJunctionPoints = set()

    # /
    # Edge Routing

    """
     * Route edges between the given layers.
     *
     * :param layeredGraph the layered graph.
     * :param sourceLayerNodes the left layer. May be {@code null.
     * :param sourceLayerIndex the source layer's index. Ignored if there is no source layer.
     * :param targetLayerNodes the right layer. May be {@code null.
     * :param startPos horizontal position of the first routing slot
     * :return: the number of routing slots for this layer
    """

    def routeEdges(self, layeredGraph: LGraph, sourceLayerNodes: List[LNode],
                   sourceLayerIndex: int, targetLayerNodes: List[LNode], startPos: float) -> int:

        portToHyperNodeMap = {}
        hyperNodes = []
        routingStrategy = self.routingStrategy
        conflictThreshold = self.conflictThreshold

        # create hypernodes for eastern output ports of the left layer and for western
        # output ports of the right layer
        self.createHyperNodes(sourceLayerNodes, routingStrategy.getSourcePortSide(),
                              hyperNodes, portToHyperNodeMap)
        self.createHyperNodes(targetLayerNodes, routingStrategy.getTargetPortSide(),
                              hyperNodes, portToHyperNodeMap)

        createDependency = self.createDependency
        # create dependencies for the hypernode ordering graph
        iter1 = hyperNodes.listIterator()
        while (iter1.hasNext()):
            hyperNode1 = iter1.next()
            iter2 = hyperNodes.listIterator(iter1.nextIndex())
            while (iter2.hasNext()):
                hyperNode2 = iter2.next()
                createDependency(hyperNode1, hyperNode2, conflictThreshold)

        # write the full dependency graph to an output file
        # elkjs-exclude-start
        if self.debugPrefix is not None:
            DebugUtil.writeDebugGraph(layeredGraph,
                                      0 if sourceLayerNodes is None else sourceLayerIndex + 1,
                                      hyperNodes, self.debugPrefix, "full")

        # elkjs-exclude-end

        # break cycles
        self.breakCycles(hyperNodes, layeredGraph.random)

        # write the acyclic dependency graph to an output file
        # elkjs-exclude-start
        if self.debugPrefix is not None:
            DebugUtil.writeDebugGraph(layeredGraph,
                                      0 if sourceLayerNodes is None else sourceLayerIndex + 1,
                                      hyperNodes, self.debugPrefix, "acyclic")

        # elkjs-exclude-end

        # assign ranks to the hypernodes
        self.topologicalNumbering(hyperNodes)

        TOLERANCE = self.TOLERANCE
        # set bend points with appropriate coordinates
        rankCount = -1
        for node in hyperNodes:
            # Hypernodes that are just straight lines don't take up a slot and
            # don't need bend points
            if abs(node.start - node.end) < TOLERANCE:
                continue

            rankCount = max(rankCount, node.rank)

            routingStrategy.calculateBendPoints(node, startPos)

        # release the created resources
        self.createdJunctionPoints.clear()
        return rankCount + 1

    # /
    # Hyper Node Graph Creation
    def createHyperNodes(self, nodes: List[LNode], portSide: PortSide,
                         hyperNodes: List[HyperNode], portToHyperNodeMap: Dict[LPort, HyperNode]):
        """
        Creates hypernodes for the given layer.

        :param nodes the layer. May be {@code null, in which case nothing happens.
        :param portSide side of the output ports for whose outgoing edges hypernodes should
                        be created.
        :param hyperNodes list the created hypernodes should be added to.
        :param portToHyperNodeMap map from ports to hypernodes that should be filled.
        """
        if nodes is not None:
            for node in nodes:
                for port in node.getPorts(PortType.OUTPUT, portSide):
                    hyperNode = portToHyperNodeMap[port]
                    if hyperNode is None:
                        hyperNode = HyperNode()
                        hyperNodes.append(hyperNode)
                        hyperNode.addPortPositions(port, portToHyperNodeMap)

    @classmethod
    def createDependency(cls, hn1: HyperNode, hn2: HyperNode,
                         minDiff: float):
        """
        Create a dependency between the two given hypernodes, if one is needed.

        :param hn1 first hypernode
        :param hn2 second hypernode
        :param minDiff the minimal difference between horizontal line segments to adef a conflict
        """
        # check if at least one of the two nodes is just a straight line those don't
        # create dependencies since they don't take up a slot
        if abs(hn1.start - hn1.end) < cls.TOLERANCE or abs(hn2.start - hn2.end) < cls.TOLERANCE:
            return
        countConflicts = cls.countConflicts
        countCrossings = cls.countCrossings
        # compare number of conflicts for both variants
        conflicts1 = countConflicts(hn1.targetPosis, hn2.sourcePosis, minDiff)
        conflicts2 = countConflicts(hn2.targetPosis, hn1.sourcePosis, minDiff)

        # compare number of crossings for both variants
        crossings1 = countCrossings(hn1.targetPosis, hn2.start, hn2.end)\
            + countCrossings(hn2.sourcePosis, hn1.start, hn1.end)
        crossings2 = countCrossings(hn2.targetPosis, hn1.start, hn1.end)\
            + countCrossings(hn1.sourcePosis, hn2.start, hn2.end)

        depValue1 = cls.CONFLICT_PENALTY * conflicts1 + crossings1
        depValue2 = cls.CONFLICT_PENALTY * conflicts2 + crossings2

        if depValue1 < depValue2:
            # create dependency from first hypernode to second one
            Dependency(hn1, hn2, depValue2 - depValue1)
        elif depValue1 > depValue2:
            # create dependency from second hypernode to first one
            Dependency(hn2, hn1, depValue1 - depValue2)
        elif depValue1 > 0 and depValue2 > 0:
            # create two dependencies with zero weight
            Dependency(hn1, hn2, 0)
            Dependency(hn2, hn1, 0)

    @staticmethod
    def countConflicts(posis1: List[float], posis2: List[float],
                       minDiff: float):
        """
        Counts the number of conflicts for the given lists of positions.

        :param posis1 sorted list of positions
        :param posis2 sorted list of positions
        :param minDiff minimal difference between two positions
        :return: number of positions that overlap
        """

        conflicts = 0

        if posis1 and posis2:
            iter1 = posis1.iterator()
            iter2 = posis2.iterator()
            pos1 = iter1.next()
            pos2 = iter2.next()

            while True:
                if (pos1 > pos2 - minDiff and pos1 < pos2 + minDiff):
                    conflicts += 1

                if pos1 <= pos2 and iter1.hasNext():
                    pos1 = iter1.next()
                elif pos2 <= pos1 and iter2.hasNext():
                    pos2 = iter2.next()
                else:
                    break

        return conflicts

    @staticmethod
    def countCrossings(posis: List[float], start: float, end: float):
        """
        Counts the number of crossings for a given list of positions.

        :param posis sorted list of positions
        :param start start of the critical area
        :param end end of the critical area
        :return: number of positions in the critical area
        """
        crossings = 0
        for pos in posis:
            if pos > end:
                break
            elif pos >= start:
                crossings += 1

        return crossings

    # /
    # Cycle Breaking

    @classmethod
    def breakCycles(cls, nodes: List[HyperNode], random: Random):
        """
        Breaks all cycles in the given hypernode structure by reversing or removing
        some dependencies. This implementation assumes that the dependencies of zero
        weight are exactly the two-cycles of the hypernode structure.

        :param nodes list of hypernodes
        :param random random number generator
        """
        sources = deque()
        sinks = deque()

        # initialize values for the algorithm
        nextMark = -1
        for node in nodes:
            node.mark = nextMark
            nextMark -= 1
            inweight = 0
            outweight = 0

            for dependency in node.outgoing:
                outweight += dependency.weight

            for dependency in node.incoming:
                inweight += dependency.weight

            node.inweight = inweight
            node.outweight = outweight

            if outweight == 0:
                sinks.append(node)
            elif inweight == 0:
                sources.append(node)

        # assign marks to all nodes, ignore dependencies of weight zero
        unprocessed = set(nodes)
        markBase = len(nodes)
        nextRight = markBase - 1
        nextLeft = markBase + 1
        maxNodes = []

        updateNeighbors = cls.updateNeighbors
        while unprocessed:
            while sinks:
                sink = sinks.removeFirst()
                unprocessed.remove(sink)
                sink.mark = nextRight
                nextRight -= 1
                updateNeighbors(sink, sources, sinks)

            while sources:
                source = sources.removeFirst()
                unprocessed.remove(source)
                source.mark = nextLeft
                nextLeft += 1
                updateNeighbors(source, sources, sinks)

            maxOutflow = -inf
            for node in unprocessed:
                outflow = node.outweight - node.inweight
                if (outflow >= maxOutflow):
                    if (outflow > maxOutflow):
                        maxNodes.clear()
                        maxOutflow = outflow

                    maxNodes.append(node)

            if maxNodes:
                # if there are multiple hypernodes with maximal outflow, select
                # one randomly
                maxNode = maxNodes[random.nextInt(len(maxNodes))]
                unprocessed.remove(maxNode)
                maxNode.mark = nextLeft
                nextLeft += 1
                updateNeighbors(maxNode, sources, sinks)
                maxNodes.clear()

        # shift ranks that are left of the mark base
        shiftBase = len(nodes) + 1
        for node in nodes:
            if node.mark < markBase:
                node.mark += shiftBase

        # process edges that point left: remove those of zero weight, reverse
        # the others
        for source in nodes:
            depIter = source.outgoing.listIterator()
            while depIter.hasNext():
                dependency = depIter.next()
                target = dependency.target

                if source.mark > target.mark:
                    depIter.remove()
                    target.incoming.remove(dependency)

                    if (dependency.weight > 0):
                        dependency.source = target
                        target.outgoing.append(dependency)
                        dependency.target = source
                        source.incoming.append(dependency)

    @staticmethod
    def updateNeighbors(node: HyperNode, sources: List[HyperNode],
                        sinks: List[HyperNode]):
        """
        Updates in-weight and out-weight values of the neighbors of the given node,
        simulating its removal from the graph. The sources and sinks lists are
        also updated.

        :param node node for which neighbors are updated
        :param sources list of sources
        :param sinks list of sinks
        """

        # process following nodes
        for dep in node.outgoing:
            if (dep.target.mark < 0 and dep.weight > 0):
                dep.target.inweight -= dep.weight
                if dep.target.inweight <= 0 and dep.target.outweight > 0:
                    sources.append(dep.target)

        # process preceding nodes
        for dep in node.incoming:
            if dep.source.mark < 0 and dep.weight > 0:
                dep.source.outweight -= dep.weight
                if dep.source.outweight <= 0 and dep.source.inweight > 0:
                    sinks.append(dep.source)

    # /
    # Topological Ordering

    @staticmethod
    def topologicalNumbering(nodes: List[HyperNode]):
        """
        Perform a topological numbering of the given hypernodes.

        :param nodes list of hypernodes
        """
        # determine sources, targets, incoming count and outgoing count targets are only
        # added to the list if they only connect westward ports (that is, if all their
        # horizontal segments point to the right)
        sources = []
        rightwardTargets = []
        for node in nodes:
            node.inweight = len(node.incoming)
            node.outweight = len(node.outgoing)

            if node.inweight == 0:
                sources.append(node)

            if node.outweight == 0 and len(node.sourcePosis) == 0:
                rightwardTargets.append(node)

        maxRank = -1

        # assign ranks using topological numbering
        while sources:
            node = sources.remove(0)
            for dep in node.outgoing:
                target = dep.target
                target.rank = max(target.rank, node.rank + 1)
                maxRank = max(maxRank, target.rank)

                target.inweight -= 1
                if target.inweight == 0:
                    sources.append(target)

        """
        If we stopped here, hyper nodes that don't have any horizontal segments pointing
        leftward would be ranked just like every other hyper node. This would move back
        edges too far away from their target node. To remedy that, we move all hyper nodes
        with horizontal segments only pointing rightwards as far right as possible.
        """
        if maxRank > -1:
            # assign all target nodes with horzizontal segments pointing to the right the
            # rightmost rank
            for node in rightwardTargets:
                node.rank = maxRank

            # let all other segments with horizontal segments pointing rightwards move as
            # far right as possible
            while rightwardTargets:
                node = rightwardTargets.remove(0)

                # The node only has connections to western ports
                for dep in node.incoming:
                    source = dep.source
                    if (source.sourcePosis.size() > 0):
                        continue

                    source.rank = min(source.rank, node.rank - 1)

                    source.outweight -= 1
                    if (source.outweight == 0):
                        rightwardTargets.append(source)

    # /
    # Utilities

    @staticmethod
    def insertSorted(list_: List[float], value: float):
        """
         * Inserts a given value into a sorted list.
         *
         * :param list sorted list
         * :param value value to insert
        """
        listIter = list.listIterator()
        while listIter.hasNext():
            next = listIter.next().floatValue()
            if (next == value):
                # an exactly equal value is already present in the list
                return
            elif next > value:
                listIter.previous()
                break

        listIter.append(value)

    def addJunctionPointIfNecessary(self, edge: LEdge, hyperNode: HyperNode,
                                    pos: Point, vertical: bool):
        """
        Add a junction point to the given edge if necessary. It is necessary to add a junction point if
        the bend point is not at one of the two end positions of the hypernode.

        :param edge: an edge
        :param hyperNode: the corresponding hypernode
        :param pos: the bend point position
        :param vertical: {@code True if the connecting segment is vertical, {@code False if it
                 is horizontal
        """
        TOLERANCE = self.TOLERANCE
        p = pos.y if vertical else pos.x

        # check if the given bend point is somewhere between the start and end
        # position of the hypernode
        if (p > hyperNode.start and p < hyperNode.end
                or hyperNode.sourcePosis and hyperNode.targetPosis
                # the bend point is at the start and joins another edge at the
                # same position
                and (abs(p - hyperNode.sourcePosis[0]) < TOLERANCE
                     and abs(p - hyperNode.targetPosis[0]) < TOLERANCE
                     # the bend point is at the end and joins another edge at
                     # the same position
                     or abs(p - hyperNode.sourcePosis[-1]) < TOLERANCE
                     and abs(p - hyperNode.targetPosis[-1]) < TOLERANCE)):

            # check whether there is already a junction point at the same
            # position
            if pos not in self.createdJunctionPoints:

                # create a new junction point for the edge at the bend point's
                # position
                junctionPoints = edge.junctionpoints
                if junctionPoints is None:
                    junctionPoints = []
                    edge.junctionPoints = junctionPoints

                jpoint = Point(pos)
                junctionPoints.append(jpoint)
                self.createdJunctionPoints.append(jpoint)


class WestToEastRoutingStrategy():
    """
     * Routing strategy for routing layers from west to east.
     *
     * @author cds
    """

    @staticmethod
    def getPortPositionOnHyperNode(port: LPort) -> float:
        return (port.getNode().getPosition().y
                + port.getPosition().y
                + port.getAnchor().y)

    def getSourcePortSide(self) -> PortSide:
        return PortSide.EAST

    def getTargetPortSide(self) -> PortSide:
        return PortSide.WEST

    def calculateBendPoints(self, hyperNode: HyperNode, startPos: float):

        # Calculate coordinates for each port's bend points
        x = startPos + hyperNode.rank * self.edgeSpacing
        TOLERANCE = self.TOLERANCE
        addJunctionPointIfNecessary = self.addJunctionPointIfNecessary

        for port in hyperNode.ports:
            sourcey = port.getAbsoluteAnchor().y

            for edge in port.outgoingEdges:
                target = edge.getTarget()
                targety = target.getAbsoluteAnchor().y
                if abs(sourcey - targety) > TOLERANCE:
                    point1 = Point(x, sourcey)
                    edge.bendPoints.append(point1)
                    addJunctionPointIfNecessary(edge, hyperNode, point1, True)

                    point2 = Point(x, targety)
                    edge.bendPoints.append(point2)
                    addJunctionPointIfNecessary(edge, hyperNode, point2, True)


class NorthToSouthRoutingStrategy():
    """
    Routing strategy for routing layers from north to south.
    """
    @staticmethod
    def getPortPositionOnHyperNode(port: LPort):
        return (port.getNode().getPosition().x +
                port.getPosition().x +
                port.getAnchor().x)

    @staticmethod
    def getSourcePortSide() -> PortSide:
        return PortSide.SOUTH

    @staticmethod
    def getTargetPortSide() -> PortSide:
        return PortSide.NORTH

    def calculateBendPoints(self, hyperNode: HyperNode, startPos: float):

        # Calculate coordinates for each port's bend points
        y = startPos + hyperNode.rank * self.edgeSpacing
        TOLERANCE = self.TOLERANCE
        addJunctionPointIfNecessary = self.addJunctionPointIfNecessary

        for port in hyperNode.ports:
            sourcex = port.getAbsoluteAnchor().x

            for edge in port.getOutgoingEdges():
                target = edge.getTarget()
                targetx = target.getAbsoluteAnchor().x
                if abs(sourcex - targetx) > TOLERANCE:
                    point1 = Point(sourcex, y)
                    edge.bendPoints.append(point1)
                    addJunctionPointIfNecessary(edge, hyperNode, point1, False)

                    point2 = Point(targetx, y)
                    edge.bendPoints.append(point2)
                    addJunctionPointIfNecessary(edge, hyperNode, point2, False)


class SouthToNorthRoutingStrategy():
    """
    Routing strategy for routing layers from south to north.
    """
    @staticmethod
    def getPortPositionOnHyperNode(port: LPort):
        return (port.getNode().getPosition().x
                + port.getPosition().x
                + port.getAnchor().x)

    @staticmethod
    def getSourcePortSide() -> PortSide:
        return PortSide.NORTH

    @staticmethod
    def getTargetPortSide() -> PortSide:
        return PortSide.SOUTH

    def calculateBendPoints(self, hyperNode: HyperNode, startPos: float):

        # Calculate coordinates for each port's bend points
        y = startPos - hyperNode.rank * self.edgeSpacing
        addJunctionPointIfNecessary = self.addJunctionPointIfNecessary
        TOLERANCE = self.TOLERANCE
        for port in hyperNode.ports:
            sourcex = port.getAbsoluteAnchor().x

            for edge in port.getOutgoingEdges():
                target = edge.getTarget()
                targetx = target.getAbsoluteAnchor().x
                if abs(sourcex - targetx) > TOLERANCE:
                    point1 = Point(sourcex, y)
                    edge.bendPoints.append(point1)
                    addJunctionPointIfNecessary(edge, hyperNode, point1, False)

                    point2 = Point(targetx, y)
                    edge.bendPoints.add(point2)
                    addJunctionPointIfNecessary(edge, hyperNode, point2, False)
