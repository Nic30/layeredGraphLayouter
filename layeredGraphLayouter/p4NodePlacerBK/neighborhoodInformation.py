from layeredGraphLayouter.containers.lGraph import LGraph


class NeighborhoodInformation():
    """
    Class holds neighborhood information for a layered graph that is used during bk node placing.
    Since this information is required multiple times but does not change during processing we
    precalculate it in this class.
    """

    # Allow the fields of this container to be accessed from package siblings.
    def __init__(self):
        """ Number of nodes in the graph."""
        self.nodeCount = 0
        """ For a layer l the entry at layerIndex[l.id] holds the index of layer l."""
        self.layerIndex = {}
        """ For a node n the entry at nodeIndex[n.id] holds the index of n in its layer."""
        self.nodeIndex = {}
        """
         * For a node n holds leftNeighbors.get(n.id) holds a list with all left neighbors along with
         * any edge that connects n to its neighbor.
        """
        self.leftNeighbors = {}
        """ See doc of {@link #leftNeighbors}."""
        self.rightNeighbors = {}

    def neighborSortKey(self, neighborPair):
        return self.nodeIndex[neighborPair[0]]

    def cleanup(self):
        """
         * Release allocated resources.
        """
        self.layerIndex = None
        self.nodeIndex = None
        self.leftNeighbors.clear()
        self.rightNeighbors.clear()

    @classmethod
    def buildFor(cls, graph: LGraph) -> "NeighborhoodInformation":
        """
        Creates and properly initializes the neighborhood information required by the
        {@link BKNodePlacer}. This includes:
        * calculating the number of nodes in the graph</li>
        * assigning a unique id to every layer and node</li>
        * recording the index of every node in its layer</li>
        * calculating left and right neighbors for every node</li>

        @param graph
                   the underlying graph
        @return a properly initialized instance
        """
        ni = NeighborhoodInformation()
        ni.nodeCount = 0
        for layer in graph.layers:
            ni.nodeCount += len(layer)

        # cache indexes of layers and of nodes
        ni.layerIndex = {}
        ni.nodeIndex = {}
        for lIndex, layer in enumerate(graph.layers):
            ni.layerIndex[layer] = lIndex
            for nIndex, n in enumerate(layer):
                ni.nodeIndex[n] = nIndex

        # determine all left and right neighbors of the graph's nodes
        ni.leftNeighbors = {}
        cls.determineAllLeftNeighbors(ni, graph)
        ni.rightNeighbors = {}
        cls.determineAllRightNeighbors(ni, graph)

        return ni

    @staticmethod
    def determineAllRightNeighbors(ni: "NeighborhoodInformation", graph: LGraph):
        """
         * Give all right neighbors (originally known as lower neighbors) of a given node. A lower
         * neighbor is a node in a following layer that has an edge coming from the given node.
        """
        for layer in graph.layers:
            for n in layer:
                result = []
                maxPriority = 0

                for edge in n.getOutgoingEdges():
                    if edge.isSelfLoop or edge.isInLayerEdge():
                        continue
                    edgePrio = edge.priorityStraightness
                    if edgePrio > maxPriority:
                        maxPriority = edgePrio
                        result.clear()
                    if edgePrio == maxPriority:
                        result.append((edge.dstNode, edge))

                result.sort(key=ni.neighborSortKey)

                ni.rightNeighbors[n] = result

    @staticmethod
    def determineAllLeftNeighbors(ni: "NeighborhoodInformation", graph: LGraph):
        """
         * Gives all left neighbors (originally known as upper neighbors) of a given node. An upper
         * neighbor is a node in a previous layer that has an edge pointing to the given node.
        """
        for layer in graph.layers:
            for n in layer:
                result = []
                maxPriority = 0

                for edge in n.getIncomingEdges():
                    if edge.isSelfLoop or edge.isInLayerEdge():
                        continue
                    edgePrio = edge.priorityStraightness
                    if edgePrio > maxPriority:
                        maxPriority = edgePrio
                        result.clear()
                    if edgePrio == maxPriority:
                        result.append((edge.srcNode, edge))

                result.sort(key=ni.neighborSortKey)
                ni.leftNeighbors[n] = result
