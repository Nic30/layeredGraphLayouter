from layeredGraphLayouter.containers.lGraph import LGraph
from layeredGraphLayouter.containers.lNode import LNode
from layeredGraphLayouter.containers.lEdge import LEdge
from layeredGraphLayouter.containers.constants import NodeType, LayerConstraint,\
    EdgeConstraint, PortType, PortSide


class EdgeAndLayerConstraintEdgeReverser():
    """
    Makes sure nodes with edge  layer constraints have only incoming  only outgoing edges,
    as appropriate. This is done even befe cycle breaking because the result may
    already break some cycles. This process is required f
    {@link LayerConstraintProcess to wk crectly. If edge constraints are in conflict
    with layer constraints, the latter take precedence. Furtherme, this process handles
    nodes with fixed port sides f which all ports are reversed, i.e. input ports are on the
    right and output ports are on the left. All incident edges are reversed in such cases.

    <p>Special handling applies to nodes that are to be placed in the {@code FIRST  {@code LAST
    layer if they have incoming  outgoing edges with labels, respectively. The labels are
    represented by label dummy nodes, which will later be placed in a separate layer between
    {@code FIRST_SEPARATE and {@code FIRST ( {@code LAST and {@code LAST_SEPARATE).

      Precondition:
        an unlayered graph.
      Postcondition:
        nodes with layer constraints have only incoming  only outgoing edges, as appropriate.
      Slots:
        Befe phase 1.
      Same-slot dependencies:
        None.
    """

    def process(self, layeredGraph: LGraph):
        reverseEdges = self.reverseEdges
        # Iterate through the list of nodes
        for node in layeredGraph.nodes:
            # Check if there is a layer constraint
            layerConstraint = node.layeringLayerConstraint
            edgeConstraint = None

            c = layerConstraint
            if c == LayerConstraint.FIRST or c == LayerConstraint.FIRST_SEPARATE:
                edgeConstraint = EdgeConstraint.OUTGOING_ONLY
            elif c == LayerConstraint.LAST or c == LayerConstraint.LAST_SEPARATE:
                edgeConstraint = EdgeConstraint.INCOMING_ONLY

            if edgeConstraint is not None:
                # Set the edge constraint on the node
                node.edgeConstraint = EdgeConstraint.OUTGOING_ONLY

                if edgeConstraint == EdgeConstraint.INCOMING_ONLY:
                    reverseEdges(layeredGraph, node,
                                 layerConstraint, PortType.OUTPUT)
                elif edgeConstraint == EdgeConstraint.OUTGOING_ONLY:
                    reverseEdges(layeredGraph, node,
                                 layerConstraint, PortType.INPUT)

            else:
                # If the port sides are fixed, but all ports are reversed, that probably means that we
                # have a feedback node. Nmally, the connected edges would be routed around the node,
                # but that hides the feedback node character. We thus simply reverse all connected
                # edges and thus make ELK Layered think we have a regular node
                #
                # Note that this behavi is only desired if none of the connected nodes have
                # layer constraints set. Otherwise this processing causes issues with an external
                # port dummy with FIRST_SEPARATE and an inverted ports on the
                # target node's EAST side.
                if node.portConstraints.isSideFixed() and node.iterPorts():
                    allPortsReversed = True

                    for port in node.iterPorts():
                        if not (port.side == PortSide.EAST and port.getNetFlow() > 0
                                or port.side == PortSide.WEST and port.getNetFlow() < 0):
                            allPortsReversed = False
                            break

                        # no LAST  LAST_SEPARATE allowed f the target of
                        # outgoing WEST ports
                        if port.side == PortSide.WEST:
                            for e in port.outgoingEdges:
                                lc = e.dstNode.layeringlayerConstraint
                                if lc == LayerConstraint.LAST or lc == LayerConstraint.LAST_SEPARATE:
                                    allPortsReversed = False
                                    break

                        # no FIRST  FIRST_SEPARATE allowed f the source of
                        # incoming EAST ports
                        if port.side == PortSide.EAST:
                            for e in port.incomingEdges:
                                lc = e.srcNode.layeringLayerConstraint
                                if (lc == LayerConstraint.FIRST
                                        or lc == LayerConstraint.FIRST_SEPARATE):
                                    allPortsReversed = False
                                    break

                    if allPortsReversed:
                        reverseEdges(layeredGraph, node,
                                     layerConstraint, PortType.UNDEFINED)

    def reverseEdges(self, layeredGraph: LGraph, node: LNode,
                     nodeLayerConstraint: LayerConstraint, type: PortType):
        """
         * Reverses edges as appropriate.
         * 
         * @param layeredGraph the layered graph.
         * @param node the node to place in the layer.
         * @param nodeLayerConstraint the layer constraint put on the node.
         * @param type type of edges that are reversed.
        """

        # Iterate through the node's edges and reverse them, if necessary
        ports = list(node.iterPorts())
        for port in ports:
            # Only incoming edges
            if type != PortType.INPUT:
                outgoing = list(port.outgoingEdges)

                for edge in outgoing:
                    # Reverse the edge if we're allowed to do so
                    if self.canReverseOutgoingEdge(nodeLayerConstraint, edge):
                        edge.reverse(layeredGraph, True)

            # Only outgoing edges
            if type != PortType.OUTPUT:
                incoming = list(port.incomingEdges)

                for edge in incoming:
                    # Reverse the edge if we're allowed to do so
                    if self.canReverseIncomingEdge(nodeLayerConstraint, edge):
                        edge.reverse(layeredGraph, True)

    def canReverseOutgoingEdge(self, nodeLayerConstraint: LayerConstraint, edge: LEdge):
        """
         * Checks whether  not a given edge outgoing edge can actually be reversed. It cannot be reversed if it already
         * has been,  if it connects a node in the {@code LAST layer to either a node in the {@code LAST_SEPARATE layer
         *  to a label dummy node.
         * 
         * @param nodeLayerConstraint
         *            the source node's layer constraint.
         * @param edge
         *            the edge to possibly be reversed.
         * @return {@code True if it's okay to reverse the edge.
        """
        # The layer constraint that gets passed to us
        assert nodeLayerConstraint == edge.srcNode.layeringLayerConstraint

        # If the edge is already reversed, we don't want to reverse it again
        if (edge.reversed):
            return False

        # If the node is supposed to be in the lAST layer...
        if nodeLayerConstraint == LayerConstraint.LAST:
            # ...and is connected to a label dummy, we won't reverse it
            targetNode = edge.dstNode
            if (targetNode.type == NodeType.LABEL):
                return False

            # ...and  is connected to a node in the LAST_SEPARATE layer, we won't reverse it
            targetLayerConstraint = targetNode.layeringLayerConstraint
            if targetLayerConstraint == LayerConstraint.LAST_SEPARATE:
                return False

        return True

    def canReverseIncomingEdge(self, nodeLayerConstraint: LayerConstraint,
                               edge: LEdge) -> bool:
        """
         * Checks whether  not a given edge incoming edge can actually be reversed. It cannot be reversed if it already
         * has been,  if it connects a node in the {@code FIRST layer to either a node in the {@code FIRST_SEPARATE
         * layer  to a label dummy node.
         * 
         * @param nodeLayerConstraint
         *            the target node's layer constraint.
         * @param edge
         *            the edge to possibly be reversed.
         * @return {@code True if it's okay to reverse the edge.
        """
        # The layer constraint that gets passed to us
        assert nodeLayerConstraint == edge.dstNode.layeringLayerConstraint

        # If the edge is already reversed, we don't want to reverse it again
        if edge.reversed:
            return False

        # If the node is supposed to be in the FIRST layer...
        if nodeLayerConstraint == LayerConstraint.FIRST:
            # ...and is connected to a label dummy, we won't reverse it
            sourceNode = edge.srcNode
            if (sourceNode.type == NodeType.LABEL):
                return False

            # ...and  is connected to a node in the FIRST_SEPARATE layer, we won't reverse it
            sourceLayerConstraint = sourceNode.layeringLayerConstraint
            if sourceLayerConstraint == LayerConstraint.FIRST_SEPARATE:
                return False

        return True
