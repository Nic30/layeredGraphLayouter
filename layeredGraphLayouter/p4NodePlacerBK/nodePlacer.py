from _collections import defaultdict
from itertools import islice
from math import inf
from typing import List

from layeredGraphLayouter.containers.constants import NodeType, FixedAlignment
from layeredGraphLayouter.containers.lEdge import LEdge
from layeredGraphLayouter.containers.lGraph import LGraph
from layeredGraphLayouter.containers.lNode import LNode
from layeredGraphLayouter.iLayoutProcessor import ILayoutProcessor
from layeredGraphLayouter.layoutProcessorConfiguration import LayoutProcessorConfiguration
from layeredGraphLayouter.nodeManipulators.hierarchicalPortPositionProcessor import HierarchicalPortPositionProcessor
from layeredGraphLayouter.p4NodePlacerBK.alignedLayout import BKAlignedLayout,\
    VDirection, HDirection
from layeredGraphLayouter.p4NodePlacerBK.neighborhoodInformation import NeighborhoodInformation
from layeredGraphLayouter.p4NodePlacerBK.aligner import BKAligner


class BKNodePlacer(ILayoutProcessor):
    """
    :note: Ported from ELK.

    This algorithm is an implementation for solving the node placement problem
    which is posed in phase 4 of the KLay Layered algorithm. Inspired by:
        Ulrik Brandes and Boris K&oumlpf, Fast and simple horizontal coordinate assignment.
        In <i>Proceedings of the 9th International Symposium on Graph Drawing (GD'01)</i>,
        LNCS vol. 2265, pp. 33-36, Springer, 2002. 

    The original algorithm was extended to be able to cope with ports, node sizes, and node margins,
    and was made more stable in general. The algorithm is structured in five steps, which include two new
    steps which were not included in the original algorithm by Brandes and Koepf. The middle three steps
    are executed four times, traversing the graph in all combinations of TOP or BOTTOM and LEFT or
    RIGHT.

    In KLay Layered we have the general idea of layouting from left to right and
    transforming in the desired direction later. We decided to translate the terminology of the original
    algorithm which thinks of a layout from top to bottom. When placing coordinates, we have to differ
    from the original algorithm, since node placement in KLay Layered has to assign y-coordinates and not
    x-coordinates.

    The variable naming in this code is mostly chosen for an iteration direction within our
    left to right convention. Arrows describe iteration direction.

    LEFT                  RIGHT
    <----------           ------->

    UP    ^              DOWN |
          |                   |
          |                   v


    <h4>The algorithm:</h4>

    The first step checks the graphs' edges and marks short edges which cross long edges (called
    type 1 conflict). The algorithm indents to draw long edges as straight as possible, thus trying to
    solve the marked conflicts in a way which keep the long edge straight.

    ============ UP, DOWN x LEFT, RIGHT ============

    The second step traverses the graph in the given directions and tries to group connected nodes
    into (horizontal) blocks. These blocks, respectively the contained nodes, will be drawn straight when
    the algorithm is finished. Here, type 1 conflicts are resolved, so that the dummy nodes of a long
    edge share the same block if possible, such that the long edge is drawn straightly.

    The third step contains the addition of node size and port positions to the original algorithm.
    Each block is investigated from top to bottom. Nodes are moved inside the blocks, such that the port
    of the edge going to the next node is on the same level as that next node. Furthermore, the size of
    the block is calculated, regarding node sizes and new space needed due to node movement.

    In the fourth step, actual y-coordinates are determined. The blocks are placed, start block and
    direction determined by the directions of the current iteration. It is tried to place the blocks as
    compact as possible by grouping blocks.

    ======================= END =======================

    The action of the last step depends on a layout option. If "fixedAlignment" is not set to 
    BALANCED, one of the four calculated layouts is selected and applied, choosing the layout which 
    uses the least space. If it is False, a balanced layout is chosen by calculating a median layout 
    of all four layouts.

    In rare cases, it is possible that one or more layouts is not correct, e.g. having nodes which
    overlap each other or violating the layer ordering constraint. If the algorithm detects that, the
    respective layout is discarded and another one is chosen.

    Preconditions:
      The graph has a proper layering with optimized nodes ordering
      Ports are properly arranged
    Postconditions:
      Each node is assigned a vertical coordinate such that no two nodes overlap
      The size of each layer is set according to the area occupied by its nodes
      The height of the graph is set to the maximal layer height
    """
    @staticmethod
    def getLayoutProcessorConfiguration(graph: LGraph):
        if graph.p_externalPorts:
            return LayoutProcessorConfiguration(
                p5_edge_routing_before=[HierarchicalPortPositionProcessor()]
            )
        else:
            return None

    def __init__(self, debugMode=False):
        """
        :param debugMode: Flag which switches debug output of the algorithm on or off.
        """
        self.debugMode = debugMode
        # Whether to produce a balanced layout or not.
        self.produceBalancedLayout = False

    def process(self, layeredGraph: LGraph):
        self.lGraph = layeredGraph

        # List of edges involved in type 1 conflicts (see above).
        markedEdges = self.markedEdges = set()
        # Precalculate some information that we require during the
        # following processes.
        ni = self.ni = NeighborhoodInformation.buildFor(layeredGraph)

        # a balanced layout is desired if
        #  a) no specific alignment is set and straight edges are not desired
        #  b) a balanced alignment is enforced
        align = layeredGraph.nodePlacementBkFixedAlignment
        favorStraightEdges = layeredGraph.nodePlacementFavorStraightEdges
        produceBalancedLayout = (align == FixedAlignment.NONE
                                 and not favorStraightEdges) or align == FixedAlignment.BALANCED

        # Phase which marks type 1 conflicts, no difference between the directions so only
        # one run is required.
        self.markConflicts(layeredGraph)

        # Initialize four layouts which result from the two possible directions
        # respectively.
        rightdown = None
        rightup = None
        leftdown = None
        leftup = None
        # SUPPRESS CHECKSTYLE NEXT MagicNumber
        layouts = []
        if align == FixedAlignment.LEFTDOWN:
            leftdown = BKAlignedLayout(
                layeredGraph, ni.nodeCount, VDirection.DOWN, HDirection.LEFT)
            layouts.add(leftdown)
        elif align == FixedAlignment.LEFTUP:
            leftup = BKAlignedLayout(
                layeredGraph, ni.nodeCount, VDirection.UP, HDirection.LEFT)
            layouts.add(leftup)
        elif align == FixedAlignment.RIGHTDOWN:
            rightdown = BKAlignedLayout(
                layeredGraph, ni.nodeCount, VDirection.DOWN, HDirection.RIGHT)
            layouts.add(rightdown)
        elif align == FixedAlignment.RIGHTUP:
            rightup = BKAlignedLayout(
                layeredGraph, ni.nodeCount, VDirection.UP, HDirection.RIGHT)
            layouts.add(rightup)
        else:
            leftdown = BKAlignedLayout(
                layeredGraph, ni.nodeCount, VDirection.DOWN, HDirection.LEFT)
            leftup = BKAlignedLayout(
                layeredGraph, ni.nodeCount, VDirection.UP, HDirection.LEFT)
            rightdown = BKAlignedLayout(
                layeredGraph, ni.nodeCount, VDirection.DOWN, HDirection.RIGHT)
            rightup = BKAlignedLayout(
                layeredGraph, ni.nodeCount, VDirection.UP, HDirection.RIGHT)
            layouts.add(rightdown)
            layouts.add(rightup)
            layouts.add(leftdown)
            layouts.add(leftup)

        aligner = BKAligner(layeredGraph, ni)
        for bal in layouts:
            # Phase which determines the nodes' memberships in blocks. This happens in four different
            # ways, either from processing the nodes from the first layer to
            # the last or vice versa.
            aligner.verticalAlignment(bal, markedEdges)

            # Additional phase which is not included in the original Brandes-Koepf Algorithm.
            # It makes sure that the connected ports within a block are aligned to avoid unnecessary
            # bend points. Also, the required size of each block is determined.
            aligner.insideBlockShift(bal)

        compacter = BKCompactor(layeredGraph, ni)
        for bal in layouts:
            # This phase determines the y coordinates of the blocks and thus the vertical coordinates
            # of all nodes.
            compacter.horizontalCompaction(bal)

        # Debug output
        if self.debugMode:
            for bal in layouts:
                print(bal + " size is " + bal.layoutSize())

        # Choose a layout from the four calculated layouts. Layouts that contain errors are skipped.
        # The layout with the smallest size is selected. If more than one smallest layout exists,
        # the first one of the competing layouts is selected.
        chosenLayout = None

        checkOrderConstraint = self.checkOrderConstraint
        # If layout options chose to use the balanced layout, it is calculated and added here.
        # If it is broken for any reason, one of the four other layouts is selected by the
        # given criteria.
        if (produceBalancedLayout):
            balanced = self.createBalancedLayout(layouts, ni.nodeCount)
            if checkOrderConstraint(layeredGraph, balanced):
                chosenLayout = balanced

        # Either if no balanced layout is requested, or, if the balanced layout
        # violates order constraints, pick the one with the smallest height
        if (chosenLayout is None):
            for bal in layouts:
                if checkOrderConstraint(layeredGraph, bal):
                    if (chosenLayout is None or chosenLayout.layoutSize() > bal.layoutSize()):
                        chosenLayout = bal

        # If no layout is correct (which should never happen but is not strictly impossible),
        # the RIGHTDOWN layout is chosen by default.
        if (chosenLayout is None):
            # there has to be at least one layout in the list
            chosenLayout = layouts[0]

        # Apply calculated positions to nodes.
        for layer in layeredGraph.layers:
            for node in layer:
                node.geometry.y = chosenLayout.y[node] + \
                    chosenLayout.innerShift[node]

        # Debug output
        if self.debugMode:
            print("Chosen node placement: ", chosenLayout)
            print("Blocks: ", self.getBlocks(chosenLayout))
            print("Classes: ", self.getClasses(chosenLayout))
            print("Marked edges: ", self.markedEdges)

        # cleanup
        for bal in layouts:
            bal.cleanup()

        ni.cleanup()
        markedEdges.clear()

    # /
    # Conflict Detection

    """ The minimum number of layers we need to have conflicts."""
    MIN_LAYERS_FOR_CONFLICTS = 3

    def markConflicts(self, layeredGraph: LGraph):
        """
        This phase of the node placer marks all type 1 and type 2 conflicts.

        The conflict types base on the distinction of inner segments and non-inner segments of edges.
        A inner segment is present if an edge is drawn between two dummy nodes and thus is part of
        a long edge. A non-inner segment is present if one of the connected nodes is not a dummy
        node.

        Type 0 conflicts occur if two non-inner segments cross each other. Type 1 conflicts happen 
        when a non-inner segment and a inner segment cross. Type 2 conflicts are present if two
        inner segments cross.

        The markers are later used to solve conflicts in favor of long edges. In case of type 2
        conflicts, the marker favors the earlier node in layout order.

        :param layeredGraph The layered graph to be layouted
        """
        numberOfLayers = len(layeredGraph.layers)
        incidentToInnerSegment = self.incidentToInnerSegment

        # Check if there are enough layers to detect conflicts
        if (numberOfLayers < self.MIN_LAYERS_FOR_CONFLICTS):
            return

        markedEdges = self.markedEdges
        ni = self.ni
        # We'll need the number of nodes in the different layers quite often in this method, so save
        # them up front
        layerSize = [len(layer) for layer in layeredGraph.layers]

        # The following call succeeds since there are at least 3 layers in the
        # graph
        layerIterator = islice(layeredGraph.layers, 2, None)
        for i in range(1, numberOfLayers - 1):
            # The variable naming here follows the notation of the corresponding paper
            # Normally, underscores are not allowed in local variable names, but since there
            # is no way of properly writing indices beside underscores, Checkstyle will be
            # disabled here and in future methods containing indexed variables
            # CHECKSTYLEOFF Local Variable Names
            currentLayer = next(layerIterator)
            nodeIterator = iter(currentLayer)

            k_0 = 0
            la = 0

            for l_1 in range(layerSize[i + 1]):
                # In the paper, l and i are indices for the layer and the
                # position in the layer
                v_l_i = next(nodeIterator)  # currentLayer.getNodes().get(l_1)

                if l_1 == ((layerSize[i + 1]) - 1) or incidentToInnerSegment(v_l_i, i + 1, i):
                    k_1 = layerSize[i] - 1
                    if incidentToInnerSegment(v_l_i, i + 1, i):
                        k_1 = ni.nodeIndex[ni.leftNeighbors[v_l_i][0][0]]

                    while la <= l_1:
                        v_l = currentLayer[la]

                        if not incidentToInnerSegment(v_l, i + 1, i):
                            for upperNeighborNode, upperNeighborEdge in ni.leftNeighbors[v_l]:
                                k = ni.nodeIndex[upperNeighborNode]

                                if k < k_0 or k > k_1:
                                    # Marked edge can't return None here, because the upper neighbor
                                    # relationship between v_l and upperNeighbor enforces the existence
                                    # of at least one edge between the two
                                    # nodes
                                    markedEdges.append(upperNeighborEdge)
                        la += 1
                    k_0 = k_1

    # /
    # Layout Balancing

    def createBalancedLayout(self, layouts: List[BKAlignedLayout], nodeCount: int) -> BKAlignedLayout:
        """
        Calculates a balanced layout by determining the median of the four layouts.

        First, the layout with the smallest height, meaning the difference between the highest and the
        lowest y-coordinate placement, is used as a starting point. Then, the median position of each of
        the four layouts is used to determine the position.

        During this process, a node's inner shift value is regarded.

        :param layouts The four calculated layouts
        :param nodeCount The number of nodes in the graph
        :return: A balanced layout, the median of the four layouts
        """
        balanced = BKAlignedLayout(self.lGraph, nodeCount, None, None)
        width = []
        min_ = []
        max_ = []
        minWidthLayout = 0

        # Find the smallest layout
        for _ in range(len(layouts)):
            min_.append(inf)
            max_.append(-inf)

        for i, bal in enumerate(layouts):
            width[i] = bal.layoutSize()
            if width[minWidthLayout] > width[i]:
                minWidthLayout = i

            for layer in self.lGraph.layers:
                for n in layer:
                    nodePosY = bal.y[n] + bal.innerShift[n]
                    min_[i] = min(min[i], nodePosY)
                    max_[i] = max(max[i], nodePosY + n.geometry.height)

        # Find the shift between the smallest and the four layouts
        shift = []
        for i, bal in enumerate(layouts):
            if bal.vdir == VDirection.DOWN:
                shift[i] = min_[minWidthLayout] - min_[i]
            else:
                shift[i] = max_[minWidthLayout] - max_[i]

        # Calculated y-coordinates for a balanced placement
        calculatedYs = [0.0 for _ in range(len(layouts))]
        for layer in self.lGraph.layers:
            for node in layer:
                for i, bal in enumerate(layouts):
                    # it's important to include the innerShift here!
                    calculatedYs[i] = bal.y[node] + \
                        bal.innerShift[node] + shift[i]

                calculatedYs.sort()
                balanced.y[node] = (calculatedYs[1] + calculatedYs[2]) / 2.0
                # since we include the inner shift in the calculation of a balanced y
                # coordinate we don't need it any more
                # note that after this step no further processing of the graph that
                # would include the inner shift is possible
                balanced.innerShift[node] = 0

        return balanced

    # /
    # Utility Methods

    def incidentToInnerSegment(self, node: LNode, layer1: int, layer2: int) -> bool:
        """
        Checks whether the given node is part of a long edge between the two given layers.
        At this 'layer2' is left, or before, 'layer1'.

        :param node Possible long edge node
        :param layer1 The first layer, the layer of the node
        :param layer2 The second layer
        :return: True if the node is part of a long edge between the layers, False else
        """
        ni = self.ni
        # consider that big nodes include their respective start and end node.
        if (node.type == NodeType.BIG_NODE):
            # all nodes should be placed straightly
            for edge in node.getIncomingEdges():
                source = edge.srcNode
                if ((source.type == NodeType.BIG_NODE or source.bigNodeInitial)
                        and ni.layerIndex[edge.srcNode.layer] == layer2
                        and ni.layerIndex[node.layer] == layer1):
                    return True

        if (node.type == NodeType.LONG_EDGE):
            for edge in node.getIncomingEdges():
                sourceNodeType = edge.srcNode.type

                if (sourceNodeType == NodeType.LONG_EDGE
                        and ni.layerIndex[edge.srcNode.layer] == layer2
                        and ni.layerIndex[node.layer] == layer1):
                    return True
        return False

    @staticmethod
    def getEdge(source: LNode, target: LNode) -> LEdge:
        """
        Find an edge between two given nodes.

        :param source The source node of the edge
        :param target The target node of the edge
        :return: The edge between source and target, or None if there is none
        """
        for edge in source.getOutgoingEdges():
            # [TODO] or is suspicious
            if (edge.dstNode is target) or (edge.srcNode is target):
                return edge

        return None

    @staticmethod
    def getBlocks(bal: BKAlignedLayout):
        """
         * Finds all blocks of a given layout.
         * 
         * :param bal The layout of which the blocks shall be found
         * :return: The blocks of the given layout
        """
        blocks = defaultdict(list)

        for layer in bal.layeredGraph.layers:
            for node in layer:
                root = bal.root[node]
                blockContents = blocks[root]
                blockContents.append(node)

        return blocks

    @staticmethod
    def getClasses(bal: BKAlignedLayout):
        """
        Finds all classes of a given layout. Only used for debug output.

        :param bal The layout whose classes to find
        :return: The classes of the given layout
        """
        classes = defaultdict(list)

        # We need to enumerate all block roots
        roots = set(bal.root)
        for root in roots:
            if root is None:
                print("There are no classes in a balanced layout.")
                break

            sink = bal.sink[root]
            classContents = classes[sink]
            classContents.append(root)

        return classes

    def checkOrderConstraint(self, layeredGraph: LGraph, bal: BKAlignedLayout):
        """
        Checks whether all nodes are placed in the correct order in their layers and do not overlap
        each other.

        :param layeredGraph the containing layered graph.
        :param bal the layout which shall be checked.
        :return: {@code True if the order is preserved and no nodes overlap, {@code False otherwise.
        """

        # Flag indicating whether the layout is feasible or not
        feasible = True

        # Iterate over the layers
        for layer in layeredGraph.layers:
            # Current Y position in the layer
            pos = -inf

            # We remember the previous node for debug output
            previous = None

            # Iterate through the layer's nodes
            for node in layer:
                # For the layout to be correct, both the node's top border and its bottom border must
                # be beyond the current position in the layer
                top = bal.y[node] + bal.innerShift[node] - node.getMargin().top
                bottom = bal.y[node] + bal.innerShift[node] + node.getSize().y \
                    + node.getMargin().bottom

                if (top > pos and bottom > pos):
                    previous = node

                    # Update the position inside the layer
                    pos = bal.y[node] + bal.innerShift[node] + node.getSize().y\
                        + node.getMargin().bottom
                else:
                    # We've found an overlap
                    feasible = False
                    if self.debugMode:
                        print("bk node placement breaks on " + node
                              + " which should have been after " + previous)

                    break

            # Don't bother continuing if we've already determined that the
            # layout is infeasible
            if not feasible:
                break

        if self.debugMode:
            print(bal + " is feasible: " + feasible)

        return feasible
