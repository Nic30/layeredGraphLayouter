from layeredGraphLayouter.p4NodePlacerBK.alignedLayout import HDirection,\
    BKAlignedLayout, VDirection
from math import inf
from layeredGraphLayouter.p4NodePlacerBK.neighborhoodInformation import NeighborhoodInformation
from layeredGraphLayouter.containers.lNode import LNode
from _collections import deque
from layeredGraphLayouter.containers.lGraph import LGraph
from layeredGraphLayouter.containers.constants import EdgeStraighteningStrategy
from layeredGraphLayouter.p4NodePlacerBK.tresholdStrategy import SimpleThresholdStrategy,\
    NullThresholdStrategy


class ClassNode():
    """
     * A node of the class graph.
    """

    def __init__(self):
        self.classShift = None
        self.node = None
        self.outgoing = []
        self.indegree = 0

    def addEdge(self, target: "ClassNode", separation: float):
        se = ClassEdge(target, separation)
        target.indegree += 1
        self.outgoing.append(se)


class ClassEdge():
    """
    An edge of the class graph, holds the required separation
    between the connected classes.
    """

    def __init__(self, target: ClassNode, separation: int):
        self.separation = separation
        self.target = target


class BKCompactor():
    """
    :note: Ported from ELK

    For documentation see {@link BKNodePlacer.

    As opposed to the default {@link BKCompactor this version
    trades maximal compactness with straight edges. In other words,
    where possible it favors additional straight edges over compactness. 

    :ivar layeredGraph: The graph to process.
    :ivar threshStrategy: Specific {@link ThresholdStrategy to be used for execution.
    :ivar ni: Information about a node's neighbors and index within its layer.
    :ivar sinkNodes: Representation of the class graph.
    """

    def __init__(self, layeredGraph: LGraph, ni: NeighborhoodInformation):
        """
        :param layeredGraph: the graph to handle.
        :param ni: precalculated information about a node's neighbors.
        """
        self.layeredGraph = layeredGraph
        self.ni = ni
        self.spacings = layeredGraph.spacings

        # configure the requested threshold strategy
        if (layeredGraph.nodePlacementBkEdgeStraightening
                == EdgeStraighteningStrategy.IMPROVE_STRAIGHTNESS):
            self.threshStrategy = SimpleThresholdStrategy()
        else:
            # mimics the original compaction strategy without additional
            # straightening
            self.threshStrategy = NullThresholdStrategy()
        self.sinkNodes = {}

    # /
    # Block Placement
    def horizontalCompaction(self, bal: BKAlignedLayout):
        """
         * In this step, actual coordinates are calculated for blocks and its nodes.
         * 
         * <p>First, all blocks are placed, trying to avoid any crossing of the blocks. Then, the blocks are
         * shifted towards each other if there is any space for compaction.</p>
         * 
         * @param bal One of the four layouts which shall be used in this step
        """
        # Initialize fields with basic values, partially depending on the
        # direction
        for layer in self.layeredGraph.layers:
            for node in layer:
                bal.sink[node] = node
                if bal.vdir == VDirection.UP:
                    s = -inf
                else:
                    s = inf
                bal.shift[node] = s
        # clear any previous sinks
        self.sinkNodes.clear()

        # If the horizontal direction is LEFT, the layers are traversed from right to left, thus
        # a reverse iterator is needed (note that this does not change the
        # original list of layers)
        layers = self.layeredGraph.layers
        if bal.hdir == HDirection.LEFT:
            layers = reversed(layers)

        # init threshold strategy
        self.threshStrategy.init(bal, self.ni)
        # mark all blocks as unplaced
        y = bal.y
        for i in range(len(y)):
            y[i] = None

        placeBlock = self.placeBlock
        for layer in layers:
            # As with layers, we need a reversed iterator for blocks for
            # different directions
            nodes = layer
            if bal.vdir == VDirection.UP:
                nodes = reversed(nodes)

            # Do an initial placement for all blocks
            for v in nodes:
                if bal.root[v] == v:
                    placeBlock(v, bal)

        # Try to compact classes by shifting them towards each other if there is space between them.
        # Other than the original algorithm we use a "class graph" here in conjunction with a longest
        # path layering based on previously calculated separations between any pair of adjacent classes.
        # This allows to have different node sizes and disconnected graphs.
        self.placeClasses(bal)

        # apply coordinates
        for layer in layers:
            for v in layer:
                bal.y[v] = bal.y[bal.root[v]]

                # If this is the root node of the block, check if the whole block can be shifted to
                # further compact the drawing (the block's non-root nodes will be processed later by
                # this loop and will thus use the updated y position calculated
                # here)
                if (v == bal.root[v]):
                    sinkShift = bal.shift[bal.sink[v]]

                    if ((bal.vdir == VDirection.UP and sinkShift > -inf)
                            or (bal.vdir == VDirection.DOWN and sinkShift < inf)):
                        bal.y[v] = bal.y[v] + sinkShift

        # all blocks were placed, shift latecomers
        self.threshStrategy.postProcess()

    # SUPPRESS CHECKSTYLE NEXT 1 MethodLength
    def placeBlock(self, root: LNode, bal: BKAlignedLayout):
        """
        Blocks are placed based on their root node. This is done by going through all layers the block
        occupies and moving the whole block upwards / downwards if there are blocks that it overlaps
        with.

        :param root: The root node of the block (usually called {@code v)
        :param bal: One of the four layouts which shall be used in this step
        """
        # Skip if the block was already placed
        if bal.y[root] is not None:
            return

        # Initial placement
        # As opposed to the original algorithm we cannot rely on the fact that
        #  0.0 as initial block position is always feasible. This is due to
        #  the inside shift allowing for negative block positions in conjunction with
        #  a RIGHT (bottom-to-top) traversal direction. Computing the minimum with
        #  an initial position of 0.0 thus leads to wrong results.
        # The wrong behavior is documented in KIPRA-1426
        isInitialAssignment = True
        bal.y[root] = 0.0

        # Iterate through block and determine, where the block can be placed (until we arrive at the
        # block's root node again)
        currentNode = root
        thresh = -inf if bal.vdir == VDirection.DOWN else inf
        placeBlock = self.placeBlock
        ni = self.ni
        threshStrategy = self.threshStrategy
        spacings = self.spacings
        getOrCreateClassNode = self.getOrCreateClassNode
        layeredGraph = self.layeredGraph
        while True:
            currentIndexInLayer = ni.nodeIndex[currentNode]
            currentLayerSize = len(currentNode.layer)

            # If the node is the top or bottom node of its layer, it can be placed safely since it is
            # the first to be placed in its layer. If it's not, we'll have to
            # check its neighbours
            if ((bal.vdir == VDirection.DOWN and currentIndexInLayer > 0)
                    or (bal.vdir == VDirection.UP and currentIndexInLayer < (currentLayerSize - 1))):

                # Get the node which is above / below the current node as well
                # as the root of its block
                if (bal.vdir == VDirection.UP):
                    neighbor = currentNode.layer[currentIndexInLayer + 1]
                else:
                    neighbor = currentNode.layer[currentIndexInLayer - 1]
                neighborRoot = bal.root[neighbor]
                # Ensure the neighbor was already placed
                placeBlock(neighborRoot, bal)
                # calculate threshold value for additional straight edges
                # this call has to be _after_ place block, otherwise the
                # order of the elements in the postprocessing queue is wrong
                thresh = threshStrategy.calculateThreshold(
                    thresh, root, currentNode)
                # Note that the two nodes and their blocks form a unit called class in the original
                # algorithm. These are combinations of blocks which play a role
                # in the compaction
                if (bal.sink[root].equals(root)):
                    bal.sink[root] = bal.sink[neighborRoot]

                # Check if the blocks of the two nodes are members of the same
                # class
                if (bal.sink[root].equals(bal.sink[neighborRoot])):
                    # They are part of the same class
                    # The minimal spacing between the two nodes depends on
                    # their node type
                    spacing = spacings.getVerticalSpacing(
                        currentNode, neighbor)
                    # Determine the block's position
                    if (bal.vdir == VDirection.UP):
                        currentBlockPosition = bal.y[root]
                        newPosition = (bal.y[neighborRoot]
                                       + bal.innerShift[neighbor]
                                       - neighbor.getMargin().top
                                       - spacing
                                       - currentNode.getMargin().bottom
                                       - currentNode.getSize().y
                                       - bal.innerShift[currentNode])

                        if isInitialAssignment:
                            isInitialAssignment = False
                            bal.y[root] = min(newPosition, thresh)
                        else:
                            bal.y[root] = min(currentBlockPosition,
                                              min(newPosition, thresh))
                    else:  # DOWN
                        currentBlockPosition = bal.y[root]
                        newPosition = (bal.y[neighborRoot]
                                       + bal.innerShift[neighbor]
                                       + neighbor.getSize().y
                                       + neighbor.getMargin().bottom
                                       + spacing
                                       + currentNode.getMargin().top
                                       - bal.innerShift[currentNode])

                        if isInitialAssignment:
                            isInitialAssignment = False
                            bal.y[root] = max(newPosition, thresh)
                        else:
                            bal.y[root] = max(currentBlockPosition,
                                              max(newPosition, thresh))
                else:  # CLASSES
                    # They are not part of the same class. Compute how the two classes can be compacted
                    # later. Hence we determine a minimal required space between the two classes
                    # relative two the two class sinks.
                    spacing = layeredGraph.spacingNodeNode
                    sinkNode = getOrCreateClassNode(bal.sink[root], bal)
                    neighborSink = getOrCreateClassNode(
                        bal.sink[neighborRoot], bal)
                    if bal.vdir == VDirection.UP:
                        #  possible setup:
                        #  root         --> currentNode
                        #  neighborRoot --> neighbor
                        requiredSpace = (
                            bal.y[root]
                            + bal.innerShift[currentNode]
                            + currentNode.getSize().y
                            + currentNode.getMargin().bottom
                            + spacing
                            - (bal.y[neighborRoot]
                               + bal.innerShift[neighbor]
                               - neighbor.getMargin().top
                               )
                        )
                        # add an edge to the class graph
                        sinkNode.addEdge(neighborSink, requiredSpace)
                        # original algorithms procedure here:
                        # bal.shift[bal.sink[neighborRoot]] =
                        # max(bal.shift[bal.sink[neighborRoot]], requiredSpace)

                    else:  # DOWN
                        #  possible setup:
                        #  neighborRoot --> neighbor
                        #  root         --> currentNode
                        requiredSpace = (
                            bal.y[root]
                            + bal.innerShift[currentNode]
                            - currentNode.getMargin().top
                            - bal.y[neighborRoot]
                            - bal.innerShift[neighbor]
                            - neighbor.getSize().y
                            - neighbor.getMargin().bottom
                            - spacing)
                        # add an edge to the class graph
                        sinkNode.addEdge(neighborSink, requiredSpace)
                        # original algorithms procedure here:
                        # bal.shift[bal.sink[neighborRoot]] =
                        # min(bal.shift[bal.sink[neighborRoot]], requiredSpace)
            else:
                thresh = threshStrategy.calculateThreshold(
                    thresh, root, currentNode)
            # Get the next node in the block
            currentNode = bal.align[currentNode]
            if currentNode == root:
                break

        threshStrategy.finishBlock(root)

    # /
    # Class Placement

    def placeClasses(self, bal: BKAlignedLayout):
        # collect sinks of the class graph
        sinks = deque()
        for n in self.sinkNodes.values():
            if (n.indegree == 0):
                sinks.append(n)

        # propagate shifts in a longest path layering fashion
        while sinks:
            n = sinks.popleft()

            # position the root of the class node tree
            if (n.classShift is None):
                n.classShift = 0

            for e in n.outgoing:
                # initial position of a target does not depend on previous positions
                # (we need this as we cannot assume the top-most position to be 0)
                if (e.target.classShift is None):
                    e.target.classShift = n.classShift + e.separation
                elif (bal.vdir == VDirection.DOWN):
                    e.target.classShift = min(
                        e.target.classShift, n.classShift + e.separation)
                else:
                    e.target.classShift = max(
                        e.target.classShift, n.classShift + e.separation)

                e.target.indegree -= 1

                if e.target.indegree == 0:
                    sinks.append(e.target)

        # remember shifts for all classes such that they
        # can be applied as absolute coordinates
        for n in self.sinkNodes.values():
            bal.shift[n.node] = n.classShift

    def getOrCreateClassNode(self, sinkNode: LNode, bal: BKAlignedLayout) -> ClassNode:
        node = self.sinkNodes[sinkNode]
        if node is None:
            node = ClassNode()
            node.node = sinkNode
            self.sinkNodes[node.node] = node

        return node
