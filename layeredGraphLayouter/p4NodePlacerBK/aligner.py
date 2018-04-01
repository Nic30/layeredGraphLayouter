from math import inf, ceil, floor
from typing import Set

from layeredGraphLayouter.containers.constants import NodeType
from layeredGraphLayouter.containers.lEdge import LEdge
from layeredGraphLayouter.containers.lGraph import LGraph
from layeredGraphLayouter.p4NodePlacerBK.alignedLayout import BKAlignedLayout,\
    HDirection, VDirection
from layeredGraphLayouter.p4NodePlacerBK.neighborhoodInformation import NeighborhoodInformation


class BKAligner():
    """
     For documentation see `BKNodePlacer`.

    :ivar layeredGraph: The graph to process.
    :ivar ni: Information about a node's neighbors and index within its layer.
    """

    def __init__(self, layeredGraph: LGraph, ni: NeighborhoodInformation):
        """
        @param layeredGraph the graph to handle.
        @param ni the precalculated neighbor information
        """
        self.layeredGraph = layeredGraph
        self.ni = ni

    # /
    # Block Building and Inner Shifting

    """
     * The graph is traversed in the given directions and nodes a grouped into blocks. The nodes in these
     * blocks will later be placed such that the edges connecting them will be straight lines.
     * 
     * <p>Type 1 conflicts are resolved, so that the dummy nodes of a long edge share the same block if
     * possible, such that the long edge is drawn straightly.</p>
     * 
     * @param bal One of the four layouts which shall be used in this step 
     * @param markedEdges List with all edges that were marked as type 1 conflicts
    """

    def verticalAlignment(self, bal: BKAlignedLayout, markedEdges: Set[LEdge]):
        # Initialize root and align maps
        for layer in self.layeredGraph.layers:
            for v in layer:
                bal.root[v] = v
                bal.align[v] = v
                bal.innerShift[v] = 0.0

        layers = self.layeredGraph.layers
        ni = self.ni
        # If the horizontal direction is LEFT, the layers are traversed from
        # right to left, thus a reverse iterator is needed
        if bal.hdir == HDirection.LEFT:
            layers = reversed(layers)

        for layer in layers:
            # r denotes the position in layer order where the last block was found
            # It is initialized with -1, since nothing is found and the
            # ordering starts with 0
            r = -1
            nodes = layer

            if bal.vdir == VDirection.UP:
                # If the alignment direction is UP, the nodes in a layer are traversed
                # reversely, thus we start at INT_MAX and with the reversed
                # list of nodes.
                r = inf
                nodes = reversed(nodes)

            # Variable names here are again taken from the paper mentioned above.
            # i denotes the index of the layer and k the position of the node within the layer.
            # m denotes the position of a neighbor in the neighbor list of a node.
            # CHECKSTYLEOFF Local Variable Names
            for v_i_k in nodes:
                if bal.hdir == HDirection.LEFT:
                    neighbors = ni.rightNeighbors.get(v_i_k)
                else:
                    neighbors = ni.leftNeighbors.get(v_i_k)

                if neighbors:

                    # When a node has many upper neighbors, consider only the (two) nodes in the
                    # middle.
                    d = len(neighbors)
                    low = int(floor(((d + 1.0) / 2.0))) - 1
                    high = int(ceil(((d + 1.0) / 2.0))) - 1

                    if bal.vdir == VDirection.UP:
                        # Check, whether v_i_k can be added to a block of its
                        # upper/lower neighbor(s)
                        for m in range(high, low - 1, -1):
                            if bal.align[v_i_k].equals(v_i_k):
                                u_m, u_m_edge = neighbors[m]

                                # Again, getEdge won't return null because the neighbor relationship
                                # ensures that at least one edge exists
                                if (not markedEdges.contains(u_m_edge)
                                        and r > ni.nodeIndex[u_m]):
                                    bal.align[u_m] = v_i_k
                                    bal.root[v_i_k] = bal.root[u_m]
                                    bal.align[v_i_k] = bal.root[v_i_k]
                                    bal.od[bal.root[v_i_k]
                                           ] &= v_i_k.type == NodeType.LONG_EDGE

                                    r = ni.nodeIndex[u_m]
                    else:
                        # Check, whether vik can be added to a block of its
                        # upper/lower neighbor(s)
                        for m in range(low, high + 1):
                            if bal.align[v_i_k] == v_i_k:
                                um, um_edge = neighbors[m]

                                if (not markedEdges.contains(um_edge)
                                        and r < ni.nodeIndex[um]):
                                    bal.align[um] = v_i_k
                                    bal.root[v_i_k] = bal.root[um]
                                    bal.align[v_i_k] = bal.root[v_i_k]
                                    bal.od[bal.root[v_i_k]
                                           ] &= v_i_k.type == NodeType.LONG_EDGE
                                    r = ni.nodeIndex[um]

    """
     * This phase moves the nodes inside a block, ensuring that all edges inside a block can be drawn
     * as straight lines. It is not included in the original algorithm and adds port and node size
     * handling.
     * 
     * @param bal One of the four layouts which shall be used in this step
    """

    def insideBlockShift(self, bal: BKAlignedLayout):
        blocks = self.getBlocks(bal)
        getEdge = self.getEdge

        for root in blocks.keys():
            # For each block, we place the top left corner of the root node at coordinate (0,0). We
            # then calculate the space required above the top left corner (due to other nodes placed
            # above and to top margins of nodes, including the root node) and the space required below
            # the top left corner. The sum of both becomes the block size, and the y coordinate of each
            # node relative to the block's top border becomes the inner shift
            # of that node.

            spaceAbove = 0.0
            spaceBelow = 0.0

            # Reserve space for the root node
            spaceAbove = root.getMargin().top
            spaceBelow = root.getSize().y + root.getMargin().bottom
            bal.innerShift[root] = 0.0

            # Iterate over all other nodes of the block
            current = root
            nextN = None
            while True:
                nextN = bal.align[current]
                if nextN == root:
                    break
                # Find the edge between the current and the next node
                edge = getEdge(current, nextN)

                # Calculate the y coordinate difference between the two nodes required to straighten
                # the edge
                portPosDiff = 0.0
                if bal.hdir == HDirection.LEFT:
                    portPosDiff = (edge.dst.getPosition().y + edge.dst.getAnchor().y
                                   - edge.src.getPosition().y - edge.src.getAnchor().y)
                else:
                    portPosDiff = (edge.src.getPosition().y + edge.src.getAnchor().y
                                   - edge.dst.getPosition().y - edge.dst.getAnchor().y)

                # The current node already has an inner shift value that we need to use as the basis
                # to calculate the next node's inner shift
                nextInnerShift = bal.innerShift[current] + portPosDiff
                bal.innerShift[nextN] = nextInnerShift

                # Update the space required above and below the root node's top
                # left corner
                spaceAbove = max(spaceAbove,
                                 nextN.getMargin().top - nextInnerShift)
                spaceBelow = max(spaceBelow,
                                 nextInnerShift + nextN.getSize().y + nextN.getMargin().bottom)

                # The next node is the current node in the next iteration
                current = nextN

            # Adjust each node's inner shift by the space required above the root node's top left
            # corner (which the inner shifts are relative to at the moment)
            current = root
            while True:
                bal.innerShift[current] = bal.innerShift[current] + spaceAbove
                current = bal.align[current]
                if current == root:
                    break
            # Remember the block size
            bal.blockSize[root] = spaceAbove + spaceBelow
