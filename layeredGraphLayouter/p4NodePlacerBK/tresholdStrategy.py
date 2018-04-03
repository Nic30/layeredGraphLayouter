from math import inf, isfinite, isclose
from _collections import deque
from layeredGraphLayouter.p4NodePlacerBK.alignedLayout import BKAlignedLayout,\
    VDirection, HDirection
from layeredGraphLayouter.p4NodePlacerBK.neighborhoodInformation import NeighborhoodInformation
from layeredGraphLayouter.containers.lNode import LNode
from layeredGraphLayouter.containers.lEdge import LEdge


class Postprocessable():
    """
    Represents a unit to be post-processed. 
    :ivar free: the node whose block can potentially be moved. */
    :ivar isRoot: whether {@code free} is the root node of its block. */
    :ivar hasEdges: whether {@code free} has edges. */
    :ivar edge: the edge that was selected to be straightened. */
    """

    def __init__(self, free: LNode, isRoot: bool):
        self.free = free
        self.isRoot = isRoot
        self.hasEdges = False
        self.edge = None


class AbstractThresholdStrategy():

    # TODO make this an option?!
    THRESHOLD = inf

    EPSILON = 0.0001

    # SUPPRESS CHECKSTYLE NEXT 24 VisibilityModifier
    """
    :ivar bal: BKAlignedLayout instance. The currently processed layout with its iteration directions.
    :ivar ni: NeighborhoodInformation instance. The precalculated neighborhood information.
    :ivar blockFinished: We keep track of which blocks have been completely finished.
    :ivar postProcessablesQueue: A queue with blocks that are postponed during compaction.
    :ivra postProcessablesStack: A stack that is used to treat postponed nodes in reversed order.
    """
    """
     * Resets the internal state.
     * 
     * @param theBal
     *            The currently processed layout with its iteration directions.
     * @param theNi
     *            The precalculated neighborhood information of the graph.
    """

    def init(self, bal: BKAlignedLayout, ni: NeighborhoodInformation):
        self.bal = bal
        self.ni = ni
        self.blockFinished = set()
        self.postProcessablesQueue = deque()
        self.postProcessablesStack = []

    def finishBlock(self, n: LNode):
        """
        Marks the block of which {@code n} is the root to be completely placed.

        @param n
                   the root of a block.
        """
        self.blockFinished.add(n)

    #------------------------------------------------
    # Methods to be implemented by deriving classes.
    #------------------------------------------------

    def calculateThreshold(self, oldThresh: float, blockRoot: LNode, currentNode: LNode) -> float:
        """
        @param oldThresh
                   an old, previously calculated threshold value
        @param blockRoot
                   the root node of the current block being placed
        @param currentNode
                   the currently processed node of a block. This can be equal to
                   {@code blockRoot}.
        @return a threshold value representing a bound that would allow an additional edge to be
                drawn straight.
        """
        raise NotImplementedError()

    def postProcess(self):
        """
        Handle nodes that have been marked as having potential to 
        lead to further straight edges after all blocks were initially placed.
        """
        raise NotImplementedError()

    # SUPPRESS CHECKSTYLE NEXT 20 VisibilityModifier
    def getOther(self, edge: LEdge, n: LEdge) -> LNode:
        """
        @param edge
                   the edge for which the node is requested.
        @param n
                   a node edge is connected to.
        @return for an edge {@code (o,n)}, return {@code o}.
        """
        if (edge.srcNode == n):
            return edge.dstNode
        elif (edge.dstNode == n):
            return edge.srcNode
        else:
            ValueError(
                "Node %r is neither source nor target of edge %r", n, edge)


"""
 * {@link ThresholdStrategy} for the classic compaction phase of the original bk algorithm.
 * 
 * It calculates a threshold value such that it has no effect.
"""


class NullThresholdStrategy(AbstractThresholdStrategy):
    """
     * {@inheritDoc}
    """

    def calculateThreshold(self, oldThresh: float, blockRoot: LNode,
                           currentNode: LNode):
        if (self.bal.vdir == VDirection.UP):
            # new value calculated using min(a,thresh) --> thresh = +infty has
            # no effect
            return inf
        else:
            return -inf

    def postProcess(self):
        pass


class SimpleThresholdStrategy(AbstractThresholdStrategy):
    """
    * Only calculates threshold for the first and last node of a block.</li>
    * Picks the first edge it encounters that is valid.</li>
    """

    def calculateThreshold(self, oldThresh: bool,
                           blockRoot: LNode, currentNode: LNode):

        # just the root or last node of a block
        bal = self.bal
        # Remember that for blocks with a single node both flags can be True
        isRoot = blockRoot.equals(currentNode)
        isLast = bal.align[currentNode].equals(blockRoot)

        if not (isRoot or isLast):
            return oldThresh

        # Remember two things:
        #  1) it is not guaranteed that adjacent nodes are already placed
        #  2) blocks can consist of a single node implying that the current
        #     node is both the root and the last node

        t = oldThresh
        if bal.hdir == HDirection.RIGHT:
            if isRoot:
                t = self.getBound(blockRoot, True)

            if not isfinite(t) and isLast:
                t = self.getBound(currentNode, False)

        else:  # LEFT
            if isRoot:
                t = self.getBound(blockRoot, True)

            if not isfinite(t) and isLast:
                t = self.getBound(currentNode, False)

        return t

    """
    Only regards for root and last nodes of a block.
    
    @param bal
    @param currentNode
               a node of the block
    @param isRoot
               whether {@code currentNode} is considered to be the root node of the current
               block. For a block that consists of a single node it is important to be able
               to regard it as root as well as as last node of a block.
    
    @return a pair with an {@link LEdge} and a {@link Boolean}. If no valid edge was picked,
            the pair's first element is {@code None} and the second element indicates if
            there are possible candidate edges that might become valid at a later stage.
    """

    def pickEdge(self, pp: Postprocessable) -> Postprocessable:
        bal = self.bal
        blockFinished = self.blockFinished
        getOther = self.getOther

        if (pp.isRoot):
            if bal.hdir == HDirection.RIGHT:
                edges = pp.free.getIncomingEdges()
            else:
                edges = pp.free.getOutgoingEdges()
        else:
            if bal.hdir == HDirection.LEFT:
                edges = pp.free.getIncomingEdges()
            else:
                edges = pp.free.getOutgoingEdges()

        hasEdges = False
        for e in edges:
            # ignore in-layer edges unless the block is solely connected by in-layer edges
            #  rationale: With self-loops and feedback edges it can happen that blocks contain only dummy nodes
            #  are not connected to other blocks by non-inlayer edges. To avoid unnecessarily long edges such
            #  blocks are allowed to be handled here as well
            onlyDummies = bal.od[bal.root[pp.free]]
            if not onlyDummies and e.isInLayerEdge():
                continue

            # in order to straighten 'e' the block represented by 'pp.free'
            # would have to be moved. However, since that block is already
            # part of a straightened edge, it cannot be moved again
            if bal.su[bal.root[pp.free]] or bal.su[bal.root[pp.free]]:
                continue

            hasEdges = True
            # if the other node does not have a position yet, ignore this edge
            if bal.root[getOther(e, pp.free)] in blockFinished:
                pp.hasEdges = True
                pp.edge = e
                return pp

        # no edge picked
        pp.hasEdges = hasEdges
        pp.edge = None
        return pp

    def getBound(self, blockNode: LNode, isRoot: bool):
        bal = self.bal
        pickEdge = self.pickEdge

        invalid = inf if bal.vdir == VDirection.UP else -inf
        pick = pickEdge(Postprocessable(blockNode, isRoot))

        # if edges exist but we couldn't find a good one
        if (pick.edge is None and pick.hasEdges):
            self.postProcessablesQueue.append(pick)
            return invalid
        elif pick.edge is not None:
            left = pick.edge.src
            right = pick.edge.dst

            if isRoot:
                # We handle the root (first) node of a block here
                rootPort = right if bal.hdir == HDirection.RIGHT else left
                otherPort = left if bal.hdir == HDirection.RIGHT else right

                otherRoot = bal.root[otherPort.getNode()]
                threshold = (bal.y[otherRoot]
                             + bal.innerShift[otherPort.getNode()]
                             + otherPort.getPosition().y
                             + otherPort.getAnchor().y
                             # root node
                             - bal.innerShift[rootPort.getNode()]
                             - rootPort.getPosition().y
                             - rootPort.getAnchor().y)
            else:
                # ... and the last node of a block here
                rootPort = right if bal.hdir == HDirection.LEFT else left
                otherPort = left if bal.hdir == HDirection.LEFT else right

                threshold = (bal.y[bal.root[otherPort.getNode()]]
                             + bal.innerShift[otherPort.getNode()]
                             + otherPort.getPosition().y
                             + otherPort.getAnchor().y
                             # root node
                             - bal.innerShift[rootPort.getNode()]
                             - rootPort.getPosition().y
                             - rootPort.getAnchor().y)

            # we are not allowed to move this block anymore
            # in order to straighten another edge
            bal.su[bal.root[left.getNode()]] = True
            bal.su[bal.root[right.getNode()]] = True

            return threshold

        return invalid

    def postProcess(self):
        postProcessablesQueue = self.postProcessablesQueue
        pickEdge = self.pickEdge
        bal = self.bal
        process = self.process
        postProcessablesStack = self.postProcessablesStack

        # try original iteration order
        while postProcessablesQueue:
            # first is the node, second whether it is regarded as root
            pp = postProcessablesQueue.popleft()
            pick = pickEdge(pp)

            if (pick.edge is None):
                continue

            edge = pick.edge

            # ignore in-layer edges
            onlyDummies = bal.od[bal.root[pp.free]]
            if not onlyDummies and edge.isInLayerEdge():
                continue

            # try to straighten the edge ...
            moved = process(pp)
            # if it wasn't possible try again later in the opposite iteration
            # direction
            if not moved:
                postProcessablesStack.append(pp)

        # reversed iteration order
        while postProcessablesStack:
            process(postProcessablesStack.pop())

    def process(self, pp: Postprocessable):
        assert pp.edge is not None
        bal = self.bal

        edge = pp.edge
        if (edge.srcNode == pp.free):
            fix = edge.dst
        else:
            fix = edge.src

        if (edge.srcNode == pp.free):
            block = edge.src
        else:
            block = edge.dst

        # t has to be the root node of a different block
        delta = bal.calculateDelta(fix, block)

        if (delta > 0 and delta < self.THRESHOLD):
            # target y larger than source y --> shift upwards?
            availableSpace = bal.checkSpaceAbove(block.getNode(), delta)
            assert isclose(availableSpace, 0,
                           rel_tol=0, abs_tol=self.EPSILON) or availableSpace >= 0
            bal.shiftBlock(block.getNode(), -availableSpace)
            return availableSpace > 0
        elif delta < 0 and -delta < self.THRESHOLD:
            # direction is up, we possibly shifted some blocks too far upward
            # for an edge to be straight, so check if we can shift down again
            availableSpace = bal.checkSpaceBelow(block.getNode(), -delta)
            assert isclose(availableSpace, 0,
                           rel_tol=0, abs_tol=self.EPSILON) or availableSpace >= 0
            bal.shiftBlock(block.getNode(), availableSpace)
            return availableSpace > 0

        return False
