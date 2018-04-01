from enum import Enum
from layeredGraphLayouter.containers.lGraph import LGraph
from math import inf
from layeredGraphLayouter.containers.lPort import LPort
from layeredGraphLayouter.containers.lNode import LNode


class VDirection(Enum):
    """
    Vertical direction enumeration.
    """
    # Iteration direction top-down.
    DOWN = 0
    # Iteration direction bottom-up.
    UP = 1


class HDirection(Enum):
    """
     * Horizontal direction enumeration.
    """
    # Iterating from right to left."""
    RIGHT = 0
    """ Iterating from left to right."""
    LEFT = 1


class BKAlignedLayout():
    """
    :note: Ported from ELK.

    Class which holds all information about a layout in one of the four direction
    combinations.

    :ivar root: The root node of each node in a block.
    :ivar blockSize: The size of a block.
    :ivar align: The next node in a block, or the first if the current node is the last, forming a ring.
    :ivar innerShift: The value by which a node must be shifted to stay straight inside a block.
    :ivar sink: The root node of a class, mapped from block root nodes to class root nodes.
    :ivar shift: The value by which a block must be shifted for a more compact placement.
    :ivar y: The y-coordinate of every node, forming the layout.
    :ivar vdir: The vertical direction of the current layout.
    :ivar hdir: The horizontal direction of the current layout.
    :ivar su: Flags blocks, represented by their root node, that are part of a straightened edge.
    :ivar od: Flags blocks, represented by their root node, that they are solely made up of dummy nodes.
    :ivar layeredGraph: The graph to process.
    :ivar spacings: Spacing values.
    """

    def __init__(self, layeredGraph: LGraph, nodeCount: int,
                 vdir: VDirection, hdir: HDirection):
        """
         * Basic constructor for a layout.
         * 
         * @param layeredGraph
         *            the layered graph.
         * @param nodeCount
         *            number of nodes in this layout
         * @param vdir
         *            vertical traversal direction of the algorithm
         * @param hdir
         *            horizontal traversal direction of the algorithm
        """

        self.layeredGraph = layeredGraph
        # Initialize spacing value from layout options.
        self.spacings = layeredGraph.spacings
        self.root = [None for _ in range(nodeCount)]
        self.blockSize = [0 for _ in range(nodeCount)]
        self.align = [None for _ in range(nodeCount)]
        self.innerShift = [0 for _ in range(nodeCount)]
        self.sink = [None for _ in range(nodeCount)]
        self.shift = [0 for _ in range(nodeCount)]
        self.y = [0 for _ in range(nodeCount)]
        self.su = [False for _ in range(nodeCount)]
        self.od = [True for _ in range(nodeCount)]
        self.vdir = vdir
        self.hdir = hdir

    """
     * Explicitly release any allocated resources.
    """

    def cleanup(self):
        self.root = None
        self.blockSize = None
        self.align = None
        self.innerShift = None
        self.sink = None
        self.shift = None
        self.y = None

    """
     * Calculate the layout size for comparison.
     * 
     * @return The size of the layout
    """

    def layoutSize(self):
        min_ = inf
        max_ = -inf
        # Prior to KIPRA-1426 the size of the layout was determined
        # only based on y coordinates, neglecting any block sizes.
        # We now determine the maximal extend of the layout based on
        # the minimum y coordinate of any node and the maximum
        # y coordinate _plus_ the size of any block.
        y = self.y
        blockSize = self.blockSize
        root = self.root
        for layer in self.layeredGraph.layers:
            for n in layer:
                yMin = y[n]
                yMax = yMin + blockSize[root[n]]
                min_ = min(min_, yMin)
                max_ = max(max_, yMax)
        return max_ - min_

    """
     * @param src
     *            source port of the tested edge
     * @param tgt
     *            target port of the tested edge
     * @return A delta larger than 0 if the {@code tgt} port has a larger y coordinate than
     *         {@code src} and a delta smaller than zero if {@code src} has the larger y coordinate.
     *         This means that for {@code delta > 0} the target node has to be shifted upwards to
     *         straighten the edge.
    """

    def calculateDelta(self, src: LPort, tgt: LPort):
        y = self.y
        innerShift = self.innerShift
        srcPos = (y[src.getNode()] + innerShift[src.getNode()]
                  + src.getPosition().y + src.getAnchor().y)
        tgtPos = (y[tgt.getNode()] + innerShift[tgt.getNode()]
                  + tgt.getPosition().y + tgt.getAnchor().y)
        return tgtPos - srcPos

    def shiftBlock(self, rootNode: LNode, delta: float):
        """
         * Shifts the y-coordinates of all nodes of the block represented by {@code root} by the
         * specified {@code delta}.
         * 
         * @param rootNode
         *            root node of the block.
         * @param delta
         *            the delta by which the node should be move. Can be either positive or negative.
        """
        current = rootNode
        y = self.y
        align = self.align
        while True:
            newPos = y[current] + delta
            y[current] = newPos
            current = align[current]
            if current == rootNode:
                break

    def checkSpaceAbove(self, blockRoot: LNode, delta: float) -> float:
        """
         * Checks whether a block with root node {@code blockRoot} can be shifted upwards by
         * {@code delta} without overlapping any of the block's nodes upper neighbors.
         * 
         * @param blockRoot
         *            root node of a block
         * @param delta
         *            a positive value
         * @return A value smaller or equal to {@code delta} indicating the maximal distance the
         *         block can be moved upward.
        """

        availableSpace = delta
        rootNode = blockRoot
        # iterate through the block
        current = rootNode
        align = self.align
        getMinY = self.getMinY
        getMaxY = self.getMaxY
        getUpperNeighbor = self.getUpperNeighbor
        spacings = self.spacings

        while True:
            current = align[current]
            # get minimum possible position of the current node
            minYCurrent = getMinY(current)

            neighbor = getUpperNeighbor(
                current, current.getIndex())  # FIXME getindex SLOW
            if neighbor is not None:
                maxYNeighbor = getMaxY(neighbor)
                # minimal position at which the current block node could
                # validly be placed
                availableSpace = min(availableSpace,
                                     minYCurrent
                                     - (maxYNeighbor + spacings.getVerticalSpacing(current, neighbor)))
            # until we wrap around
            if rootNode == current:
                break

        return availableSpace

    def checkSpaceBelow(self, blockRoot: LNode, delta: float):
        """
         * Checks whether a block with root node {@code blockRoot} can be shifted downwards by
         * {@code delta} without overlapping any of the block's nodes lower neighbors.
         * 
         * @param blockRoot
         *            root node of a block
         * @param delta
         *            a positive value
         * @return A value smaller or equal to {@code delta} indicating the maximal distance the
         *         block can be moved upward.
        """

        availableSpace = delta
        rootNode = blockRoot
        # iterate through the block
        current = rootNode
        align = self.align
        getMinY = self.getMinY
        getMaxY = self.getMaxY
        getLowerNeighbor = self.getLowerNeighbor
        spacings = self.spacings

        while True:
            current = align[current]
            # get maximum possible position of the current node
            maxYCurrent = getMaxY(current)

            # get the lower neighbor and check its position allows shifting
            neighbor = getLowerNeighbor(
                current, current.getIndex())  # FIXME getindex SLOW
            if neighbor is not None:
                minYNeighbor = getMinY(neighbor)

                # minimal position at which the current block node could
                # validly be placed
                availableSpace = min(availableSpace,
                                     minYNeighbor
                                     - (maxYCurrent + spacings.getVerticalSpacing(current, neighbor)))
            # until we wrap around
            if rootNode == current:
                break

        return availableSpace

    def getMinY(self, n: LNode) -> float:
        """
         * Returns the minimum position of node {@code n} and its margins, that is,
         * {@code node.y + node.innerShift - node.margin.top}. Note that no spacing is accounted for.
         * 
         * @param n
         *            a node
         * @return the minimum position.
        """
        # node size + margins + inside shift etc
        rootNode = self.root[n]
        return (self.y[rootNode]
                + self.innerShift[n]
                - n.getMargin().top)

    def getMaxY(self, n: LNode) -> float:
        """
         * Returns the maximum position of node {@code n} and its margins, that is,
         * {@code node.y + node.innerShift + node.size + node.margin.bottom}. Note that no spacing is
         * accounted for.
         * 
         * @param n
         *            a node
         * @return the minimum position.
        """
        # node size + margins + inside shift etc
        rootNode = self.root[n]
        return (self.y[rootNode]
                + self.innerShift[n]
                + n.getSize().y
                + n.getMargin().bottom)

    @staticmethod
    def getLowerNeighbor(n: LNode, layerIndex: int) -> LNode:
        """
         * @param n
         *            the node for which the neighbor is requested.
         * @param layerIndex
         *            the index of {@code n} within its layer.
         * @return the node with a <b>larger</b> y than {@code n} within {@code n}'s layer if it exists,
         *         otherwise {@code None}.
        """
        la = n.layer
        if layerIndex < len(la) - 1:
            return la[layerIndex + 1]
        return None

    @staticmethod
    def getUpperNeighbor(n: LNode, layerIndex: int) -> LNode:
        """
         * @param n
         *            the node for which the neighbor is requested.
         * @param layerIndex
         *            the index of {@code n} within its layer.
         * @return the node with a <b>smaller</b> y than {@code n} within {@code n}'s layer if it
         *         exists, otherwise {@code None}.
        """
        if layerIndex > 0:
            return n.layer[layerIndex - 1]
        return None

    def __repr__(self):
        return self.hdir.name + "-" + self.vdir.name
