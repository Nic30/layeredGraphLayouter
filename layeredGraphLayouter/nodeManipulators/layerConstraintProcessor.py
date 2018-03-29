from layeredGraphLayouter.containers.lGraph import LGraph, LNodeLayer
from layeredGraphLayouter.containers.lNode import LNode
from layeredGraphLayouter.containers.constants import LayerConstraint, NodeType
from layeredGraphLayouter.containers.lEdge import LEdge


class LayerConstraintProcessor():
    """
    Moves nodes with layer constraints to the appropriate layers. To meet the preconditions of
    this processor, the {@link EdgeAndLayerConstraintEdgeReverser can be used.
    Precondition:
      a layered graph.
      nodes with {@code FIRST_SEPARATE layer constraint have only outgoing edges.
      nodes with {@code FIRST layer constraint have only outgoing edges, except for edges incoming from
          {@code FIRST_SEPARATE nodes or label dummy nodes
      nodes with {@code LAST_SEPARATE layer constraint have only incoming edges.
      nodes with {@code LAST layer constraint have only incoming edges, except for edges outgoing to
          {@code LAST_SEPARATE nodes or label dummy nodes
    Postcondition:
      nodes with layer constraints have been placed in the appropriate layers.
    Slots:
      Before phase 3.
    Same-slot dependencies:
      {@link HierarchicalPortConstraintProcessor
    """

    def process(self, layeredGraph: LGraph):
        layers = layeredGraph.layers
        if not layers:
            return

        # Retrieve the current first and last layers
        firstLayer = layers[0]
        lastLayer = layers[-1]

        # Create the new first and last layers, in case they will be needed
        veryFirstLayer = LNodeLayer(layeredGraph)
        veryLastLayer = LNodeLayer(layeredGraph)

        # We may also need label dummy layers between the very first / last
        # layers and the first / last layers
        firstLabelLayer = LNodeLayer(layeredGraph)
        lastLabelLayer = LNodeLayer(layeredGraph)

        # Iterate through the current list of layers
        for layer in layers:
            # Iterate through a node array to avoid
            # ConcurrentModificationExceptions
            nodes = list(layer)

            for node in nodes:
                constraint = node.layeringLayerConstraint
                # Check if there is a layer constraint
                if constraint == LayerConstraint.FIRST:
                    node.setLayer(firstLayer)
                    self.throwUpUnlessNoIncomingEdges(node, True)
                    self.moveLabelsToLabelLayer(node, True, firstLabelLayer)

                elif constraint == LayerConstraint.FIRST_SEPARATE:
                    node.setLayer(veryFirstLayer)
                    self.throwUpUnlessNoIncomingEdges(node, False)

                elif constraint == LayerConstraint.LAST:
                    node.setLayer(lastLayer)
                    self.throwUpUnlessNoOutgoingEdges(node, True)
                    self.moveLabelsToLabelLayer(node, False, lastLabelLayer)

                elif constraint == LayerConstraint.LAST_SEPARATE:
                    node.setLayer(veryLastLayer)
                    self.throwUpUnlessNoOutgoingEdges(node, False)

        # If there is a second first layer. To be allowed to move all first layer's nodes to the second
        # layer, we need to check 2 things:
        # - if any of the first layer's nodes has outgoing edges to the second layer
        #      (In this case, we obviously can't move the nodes.)
        # - if any of the first layer's nodes has no layer constraint set
        #      (In this case, we are not allowed to move the node by definition.)
        if len(layers.size()) >= 2:
            moveAllowed = True
            sndFirstLayer = layers[1]
            for node in firstLayer:
                if node.layeringLayerConstraint == LayerConstraint.NONE:
                    moveAllowed = False
                    break

                for edge in node.outgoingEdges:
                    if edge.dstNode.layer is sndFirstLayer:
                        moveAllowed = False
                        break

                if not moveAllowed:
                    break

            if moveAllowed:
                # Iterate through a node array to avoid
                # ConcurrentModificationExceptions
                nodes = list(firstLayer)
                for node in nodes:
                    node.setLayer(sndFirstLayer)

                layers.remove(firstLayer)
                firstLayer = sndFirstLayer

        # same description as above
        if len(layers) >= 2:
            moveAllowed = True
            sndLastLayer = layers[len(layers) - 2]
            for node in lastLayer:
                if node.layeringLayerConstraint == LayerConstraint.NONE:
                    moveAllowed = False
                    break

                for edge in node.incomingEdges:
                    if edge.srcNode.layer is sndLastLayer:
                        moveAllowed = False
                        break

                if not moveAllowed:
                    break

            if moveAllowed:
                # Iterate through a node array to avoid
                # ConcurrentModificationExceptions
                nodes = list(lastLayer)
                for node in nodes:
                    node.setLayer(sndLastLayer)

                layers.remove(lastLayer)
                lastLayer = sndLastLayer

        if len(layers) == 1 and not layers[0]:
            layers.remove(0)

        # Add non-empty new first and last (label) layers
        if firstLabelLayer:
            layers.insert(0, firstLabelLayer)

        if veryFirstLayer:
            layers.insert(0, veryFirstLayer)

        if lastLabelLayer:
            layers.append(lastLabelLayer)

        if veryLastLayer:
            layers.append(veryLastLayer)

    def moveLabelsToLabelLayer(self, node: LNode, incoming: bool, labelLayer: LNodeLayer):
        """
         * Moves the label dummies coming in to the given node or going out from the given node to the given label dummy
         * layer.
         * 
         * @param node
         *            the node whose adjacent label dummies to move.
         * @param incoming
         *            {@code True if label dummies on incoming edges should be moved, {@code False if label dummies on
         *            outgoing edges should be moved.
         * @param labelLayer
         *            the layer to move the label dummies to.
        """
        if incoming:
            edges = node.incomingEdges
        else:
            edges = node.outgoingEdges

        for edge in edges:
            if incoming:
                possibleLableDummy = edge.srcNode
            else:
                possibleLableDummy = edge.dstNode

            if possibleLableDummy.type == NodeType.LABEL:
                possibleLableDummy.setLayer(labelLayer)

    ########################################################
    # FIRST(_SEPARATE) Node Checks
    """
     * Check that the node has no incoming edges, and fail if it has any. Edges that connect two hierarchical port
     * dummies are always allowed.
     * 
     * @param node
     *            a node.
     * @param allowFromFirstSeparate
     *            {@code True if incoming connections from {@code FIRST_SEPARATE nodes are allowed.
    """

    def throwUpUnlessNoIncomingEdges(self, node: LNode, allowFromFirstSeparate: bool):
        for port in node.iterPorts():
            for incoming in port.incomingEdges:
                if not self.isAcceptableIncomingEdge(incoming):
                    if (allowFromFirstSeparate):
                        raise UnsupportedConfigurationException("Node '" + node.getDesignation()
                                                                + "' has its layer constraint set to FIRST, but has at least one incoming edge that "
                                                                + " does not come from a FIRST_SEPARATE node. That must not happen.")
                    else:
                        raise UnsupportedConfigurationException("Node '" + node.getDesignation()
                                                                + "' has its layer constraint set to FIRST_SEPARATE, but has at least one incoming "
                                                                + "edge. FIRST_SEPARATE nodes must not have incoming edges.")

    def isAcceptableIncomingEdge(self, edge: LEdge):
        """
        Checks whether or not the given edge incoming to a {@code FIRST layer node is allowed to do so.
        """
        sourceNode = edge.srcNode
        targetNode = edge.dstNode

        # If both nodes are external port dummies, that's fine
        if (sourceNode.type == NodeType.EXTERNAL_PORT and targetNode.type == NodeType.EXTERNAL_PORT):
            return True

        # Otherwise, the target node is expected to be in the FIRST layer
        assert targetNode.layeringLayerConstraint == LayerConstraint.FIRST

        # If the source node is in the very first layer, that's okay
        if (sourceNode.layeringLayerConstraint == LayerConstraint.FIRST_SEPARATE):
            return True

        # If the source node is a label dummy, that's okay too
        return sourceNode.type == NodeType.LABEL

    ########################################################
    # LAST(_SEPARATE) Node Checks
    def throwUpUnlessNoOutgoingEdges(self, node: LNode, allowToLastSeparate: bool):
        """
         * Check that the node has no outgoing edges, and fail if it has any.
         * 
         * @param node
         *            a node
         * @param allowToLastSeparate
         *            {@code True if outgoing connections to {@code LAST_SEPARATE nodes are allowed.
        """
        for port in node.iterPorts():
            for outgoing in port.outgoingEdges:
                if not self.isAcceptableOutgoingEdge(outgoing):
                    if (allowToLastSeparate):
                        raise NotImplementedError("Node '" + node.getDesignation()
                                                  + "' has its layer constraint set to LAST, but has at least one outgoing edge that "
                                                  + " does not go to a LAST_SEPARATE node. That must not happen.")
                    else:
                        raise NotImplementedError("Node '" + node.getDesignation()
                                                  + "' has its layer constraint set to LAST_SEPARATE, but has at least one outgoing "
                                                  + "edge. LAST_SEPARATE nodes must not have outgoing edges.")

    def isAcceptableOutgoingEdge(self, edge: LEdge) -> bool:
        """
         * Checks whether or not the given edge leacing a {@code LAST layer node is allowed to do so.
        """
        sourceNode = edge.srcNode
        targetNode = edge.dstNode

        # If both nodes are external port dummies, that's fine
        if (sourceNode.type == NodeType.EXTERNAL_PORT and targetNode.type == NodeType.EXTERNAL_PORT):
            return True

        # Otherwise, the source node is expected to be in the LAST layer
        assert sourceNode.layeringLayerConstraint == LayerConstraint.LAST
        # If the target node is in the very last layer, that's okay
        if (targetNode.layeringLayerConstraint == LayerConstraint.LAST_SEPARATE):
            return True

        # If the target node is a label dummy, that's okay too
        return targetNode.type == NodeType.LABEL
