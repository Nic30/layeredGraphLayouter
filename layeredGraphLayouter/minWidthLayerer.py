from math import inf
from typing import Optional

from layeredGraphLayouter.containers.constants import PortType
from layeredGraphLayouter.containers.lNode import LNode
from layeredGraphLayouter.containers.lGraph import LGraph
from layeredGraphLayouter.layoutProcessorConfiguration import LayoutProcessorConfiguration
from layeredGraphLayouter.edgeManipulators.edgeAndLayerConstraintEdgeReverser import EdgeAndLayerConstraintEdgeReverser


LAYERING_MIN_WIDTH_UPPER_BOUND_ON_WIDTH = 10
LAYERING_MIN_WIDTH_UPPER_LAYER_ESTIMATION_SCALING_FACTOR = 1
SPACING_EDGE_EDGE = 5
UPPERBOUND_ON_WIDTH_RANGE = (1, 4)
COMPENSATOR_RANGE = (1, 2)


class MinWidthLayerer():
    """
    :note: ported from ELK

    Implementation of the heuristic MinWidth for solving the NP-hard minimum-width layering problem
    with consideration of dummy nodes. MinWidth is based on the longest-path algorithm, which finds
    layerings with the minimum height, but doesn't consider the width of the graph. MinWidth also
    considers an upper bound on the width of a given graph. The upper bound isn't a "bound" in a
    strict sense, as some layers might exceed its limit, if certain conditions are met.

    Details are described in

    Nikola S. Nikolov, Alexandre Tarassov, and Jürgen Branke. 2005. In search for efficient
    heuristics for minimum-width graph layering with consideration of dummy nodes. J. Exp.
    Algorithmics 10, Article 2.7 (December 2005). DOI=10.1145/1064546.1180618
    http://doi.acm.org/10.1145/1064546.1180618.

    MinWidth takes two additional parameters, which can be configured as a property:

    Upper Bound On Width {@link LayeredOptions#UPPER_BOUND_ON_WIDTH} – Defines a loose upper bound on
    the width of the MinWidth layerer. Defaults to -1 (special value for using both 1, 2, 3 and 4 as
    values and choosing the narrowest layering afterwards), lower bound is 1.
    Upper Layer Estimation Scaling Factor
    {@link LayeredOptions#UPPER_LAYER_ESTIMATION_SCALING_FACTOR} – Multiplied with
    {@link LayeredOptions#UPPER_BOUND_ON_WIDTH} for defining an upper bound on the width of layers which
    haven't been placed yet, but whose maximum width had been (roughly) estimated by the MinWidth
    algorithm. Compensates for too high estimations. Defaults to -1 (special value for using both 1
    and 2 as values and choosing the narrowest layering afterwards), lower bound is 1.

    This version of the algorithm, however, differs from the one described in the paper as it
    considers the actual size of the nodes of the graph in order to handle real world use cases of
    graphs a little bit better. The approach is based on Marc Adolf's version in his implementation
    of the heuristic {@link StretchWidthLayerer}. Some changes include:

    estimating the sizes of dummy nodes by taking the edge spacing of the {@link LGraph} into
    account,
    finding the narrowest real node of the graph and normalizing all the widths of the nodes of
    the graph (real and dummy) in relation to this node,
    computing the average size of all real nodes (we don't know the number of dummy nodes in
    advance),
    using this average as a factor for the ubw-value given by the user in order to adjust the
    boundary to our new approach (using the result of this multiplication instead of the given value
    of ubw thus changes the condition to start a new layer from the paper slightly).

    Precondition:
        the graph has no cycles, but might contain self-loops
    Postcondition:
        all nodes have been assigned a layer such that edges connect only nodes from layers with
    increasing indices

    Recommended values for the algorithm suggested bei Nikolov et al. after a parameter study,
    see:

    Alexandre Tarassov, Nikola S. Nikolov, and Jürgen Branke. 2004. A Heuristic for
    Minimum-Width Graph Layering with Consideration of Dummy Nodes. Experimental and Efficient
    Algorithms, Third International Workshop, WEA 2004, Lecture Notes in Computer Science 3059.
    Springer-Verlag, New York, 570-583. DOI=10.1007/978-3-540-24838-5_42
    http://dx.doi.org/10.1007/978-3-540-24838-5_42.
    """

    @staticmethod
    def getLayoutProcessorConfiguration(graph: LGraph) -> LayoutProcessorConfiguration:
        return LayoutProcessorConfiguration(
            p1_cycle_breaking_before=[EdgeAndLayerConstraintEdgeReverser],
            p3_node_ordering_before=[LayerConstraintProcessor])

    def precalculateConstants(self, notInserted):
        # Compute the minimum nodes size (of the real nodes). We're going to use this value in the
        # next step to normalize the different node sizes.
        minimumNodeSize = min(
            notInserted, key=lambda node: node.geometry.height)
        # The minimum nodes size might be zero. If This is the case, then simply don't normalize
        # the node sizes.
        minimumNodeSize = max(1, minimumNodeSize.geometry.height)

        # We initialize the nodes' id and use it to refer to its in- and out-degree stored each in
        # an array. We also compute the size of each node in relation to the smallest real node in
        # the graph (normalized size) and store it in the same way.
        avgSize = 0
        for node in notInserted:
            node.initPortDegrees()
            node.normHeight = node.geometry.height / minimumNodeSize
            # The average size of a node will also be based on the normalized
            # size.
            avgSize += node.normHeight

        # First step to consider the real size of nodes: Initialize the dummy size with the spacing
        # properties
        dummySize = SPACING_EDGE_EDGE
        # normalize dummy size, too:
        self.dummySize = dummySize / minimumNodeSize
        # Divide sum of normalized node sizes by the number of nodes to get an
        # actual mean.
        self.avgSize = avgSize / len(notInserted)

    def process(self, graph):
        notInserted = graph.getLayerlessNodes()

        # The algorithm requires DAG G = (V, E). In this version self-loops are allowed (as we're
        # going to filter them). Additional properties as described above (called UBW and c in the
        # original paper):
        upperBoundOnWidth = LAYERING_MIN_WIDTH_UPPER_BOUND_ON_WIDTH
        compensator = LAYERING_MIN_WIDTH_UPPER_LAYER_ESTIMATION_SCALING_FACTOR

        self.precalculateConstants(notInserted)

        # Precalculate the successors of all nodes (as a Set) and put them in a
        # list.
        self.successors = self.precalcSuccessors(notInserted)

        # Guarantee ConditionSelect from the paper, which states that nodes with maximum out-degree
        # should be preferred during layer placement, by ordering the nodes by descending maximum
        # out-degree in advance.
        notInserted.sort(key=lambda node: node.outdeg)

        # minimum width of a layer of maximum size in a computed layering (primary criterion used
        # for comparison, if more than one layering is computed). It's a double as it takes in
        # account the actual width based on the normalized size of the nodes.
        minWidth = inf
        # minimum number of layers in a computed layering {@code minWidth} (secondary
        # criterion used for comparison, if more than one layering is
        # computed).
        minNumOfLayers = inf
        # holding the currently chosen candidate for the final layering as a
        # List
        candidateLayering = None

        # At first blindly set the parameters for the loose upper bound and the compensator to the
        # exact values, which have been configured via their respective properties, so that only
        # one layering will be computed
        ubwStart = upperBoundOnWidth
        ubwEnd = upperBoundOnWidth
        cStart = compensator
        cEnd = compensator

        # ... then check, whether any special values (i.e. negative values, which aren't valid)
        # have been used for the properties. In that case use the recommended ranges
        # described above
        if upperBoundOnWidth < 0:
            ubwStart, ubwEnd = UPPERBOUND_ON_WIDTH_RANGE

        if compensator < 0:
            cStart, cEnd = COMPENSATOR_RANGE

        # … Depending on the start- and end-values, this nested for-loop will last for up to 8
        # iterations resulting in one, two, four or eight different layerings.
        for ubw in range(ubwStart, ubwEnd + 1):
            for c in range(cStart, cEnd + 1):
                newWidth, layering = self.computeMinWidthLayering(
                    ubw, c, notInserted)

                # Important if more than one layering is computed: replace the current candidate
                # layering with a newly computed one, if it is narrower or has the same maximum
                # width but less layers.
                newNumOfLayers = len(layering)
                if (newWidth < minWidth
                        or (newWidth == minWidth and newNumOfLayers < minNumOfLayers)):
                    minWidth = newWidth
                    minNumOfLayers = newNumOfLayers
                    candidateLayering = layering

        # Finally, add the winning layering to the Klay layered data
        # structures.
        # The algorithm constructs the layering bottom up, but ElkLayered expects the list of
        # layers to be ordered top down.
        for layerList in reversed(candidateLayering):
            graph.append_layer(layerList)

    def computeMinWidthLayering(self, upperBoundOnWidth, compensator, nodes):
        """"
        Computes a layering (as a List of Lists) for a given Iterable of {@link LNode} according to
        the MinWidth-heuristic and considering actual node sizes.

        :param upperBoundOnWidth: Defines a loose upper bound on the width of the MinWidth layerer.
                   Uses integer values as in the original approach described in the paper,
                   as this bound will automatically be multiplied internally with the average
                   normalized node size as part of the new approach considering the actual
                   sizes of nodes.
        :param compensator: Multiplied with upperBoundOnWidth for defining an upper bound
                   on the width of layers which haven't been determined yet, but whose maximum
                   width had been (roughly) estimated by the MinWidth algorithm. Compensates
                   for too high estimations.
        :param nodes: Iterable of all nodes of the Graph. The {@code id} of the nodes
                   have to be set to the index where the respective Set of successor-nodes
                   are stored in the List nodeSuccessors.
        :return: a pair of a double representing the maximum width of the resulting layering
                (normalized by the smallest real node) and the layering itself as a list of list of
                nodes
        """
        layers = []
        unplacedNodes = set(nodes)

        # One of the deviations from the paper is, that our upper bound is taking node sizes into
        # account:
        ubwConsiderSize = upperBoundOnWidth * self.avgSize

        # in- and out-degree of the currently considered node, see while-loop
        # below
        inDeg = 0
        outDeg = 0

        # The actual algorithm from the paper begins here:
        # In the Paper the first Set contains all nodes, which have already been placed (in this
        # version we consider only the nodes already placed in the current layer), and the
        # second contains all nodes already placed in layers which have been determined before the
        # currentLayer.
        alreadyPlacedInCurrentLayer = set()
        alreadyPlacedInOtherLayers = set()

        # Set up the first layer (algorithm is bottom up, so the List layer is going to be reversed
        # at the end.
        currentLayer = []

        # Initial values for the width of the current layer and the estimated width of the coming
        # layers
        widthCurrent = 0
        widthUp = 0

        # Parameters needed for computing the width of a layering including
        # dummy nodes:
        maxWidth = 0
        realWidth = 0
        # Number of "started" edges that did not "finish" yet (now multiplied with the normalized
        # dummy size to consider actual node sizes)
        currentSpanningEdges = 0
        goingOutFromThisLayer = 0
        # No need for a variable "comingIntoThisLayer" as "widthUp" already
        # gets the job done.

        dummySize = self.dummySize
        while unplacedNodes:
            # Find a node, whose edges only point to nodes in the Set alreadyPlacedInOtherLayers
            # will return {@code null} if such a node doesn't exist.
            currentNode = self.selectNode(unplacedNodes,
                                          alreadyPlacedInOtherLayers)
            assert currentLayer or currentNode is not None, (
                "Cycle in graph", self.successors)

            # If a node is found in the previous step:
            if currentNode is not None:
                unplacedNodes.remove(currentNode)
                currentLayer.append(currentNode)
                alreadyPlacedInCurrentLayer.add(currentNode)

                outDeg = currentNode.outdeg
                # Take node sizes in account: use the normalized size of current node and the
                # normalized dummy size for each edge
                widthCurrent += currentNode.normHeight - outDeg * dummySize

                inDeg = currentNode.indeg
                # Take node sizes in account: use the normalized normalized dummy size for each
                # edge
                widthUp += inDeg * dummySize
                goingOutFromThisLayer += outDeg * dummySize
                realWidth += currentNode.normHeight

            # Go to the next layer if,
            # 1) no current node has been selected,
            # 2) there are no unplaced nodes left (last iteration of the while-loop),
            # 3) The conditionGoUp from the paper (with the difference of ubw being multiplied with
            # the
            # average normalized node size) is satisfied, i.e.
            # 3.1) the width of the current layer is greater than the upper bound on the width and
            # the number of dummy nodes in the layer can't be reduced, as only nodes with no
            # outgoing edges are left for being considered for the current layer or:
            # 3.2) The estimated width of the not yet determined layers is greater than the
            # scaling factor/compensator times the upper bound on the width.
            if (currentNode is None or not unplacedNodes
                    or (widthCurrent >= ubwConsiderSize
                        and currentNode.normHeight > outDeg * dummySize)
                    or widthUp >= compensator * ubwConsiderSize):
                layers.append(currentLayer)
                currentLayer = []
                alreadyPlacedInOtherLayers.update(alreadyPlacedInCurrentLayer)
                alreadyPlacedInCurrentLayer.clear()

                # Remove all edges from the dummy node count, which are starting at a node placed
                # in this layer …
                currentSpanningEdges -= goingOutFromThisLayer
                # … Now we have the actual dummy node count (or rather the sum of their widths) for
                # this layer and can add it to the real nodes for comparing the
                # width.
                maxWidth = max(maxWidth, currentSpanningEdges *
                               dummySize + realWidth)
                # In the next iteration we have to consider new dummy nodes from edges coming into
                # the layer we've just finished.
                currentSpanningEdges += widthUp

                widthCurrent = widthUp
                widthUp = 0
                goingOutFromThisLayer = 0
                realWidth = 0

        return maxWidth, layers

    def selectNode(self, nodes, targets) -> Optional[LNode]:
        """
        Returns the first node in the given Set, whose outgoing edges end only
        in nodes of the Set targets. Self-loops are ignored.

        :warning: Returns None, if such a node doesn't exist.

        :param nodes: Set to choose node from
        :param targets: Set of nodes
        :return: Chosen node from nodes, whose outgoing edges all end in a node
                contained in targets. Returns None, if such a node doesn't exist.
        """
        suc = self.successors
        for node in nodes:
            if suc[node].issubset(targets):
                return node

        return None

    def precalcSuccessors(self, nodes):
        """
        Calculates for a given Collection of nodes all its successors
        (i.e. a Set of nodes without self-loops.

        :param nodes: a Collection of nodes
        :return: dict {node: Set of successor}
        """
        successors = {}

        for node in nodes:
            outNodes = set()
            for o in node.iterPorts():
                for edge in o.iterEdges(filterSelfLoops=True):
                    d = o.direction
                    if d == PortType.OUTPUT and not edge.reversed \
                            or d == PortType.INPUT and edge.reversed:
                        outNodes.add(edge.dstNode)

            successors[node] = outNodes
        return successors
