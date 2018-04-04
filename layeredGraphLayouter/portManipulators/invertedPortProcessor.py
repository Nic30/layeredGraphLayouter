
from layeredGraphLayouter.iLayoutProcessor import ILayoutProcessor
from layeredGraphLayouter.containers.constants import NodeType, PortType,\
    PortSide, PortConstraints
from layeredGraphLayouter.containers.lNode import LNode
from copy import copy
from layeredGraphLayouter.containers.lGraph import LGraph
from layeredGraphLayouter.containers.lPort import LPort
from layeredGraphLayouter.containers.lEdge import LEdge
from typing import List


class InvertedPortProcessor(ILayoutProcessor):
    """
    Inserts dummy nodes to cope with inverted ports.
    
    The problem is with edges coming from the left of a node being connected to a port that's on its
    right side, or the other way around. Let a node of that kind be in layer {@code i. This
    processor now takes the offending edge and connects it to adummy node, also in layer
    {@code i. Finally, the dummy is connected with the offending port. This means that once one of
    these cases occurs in the graph, the layering is not proper anymore.
    
    The dummy nodes are decorated with a
    {@link org.eclipse.elk.alg.layered.options.LayeredOptions#NODE_TYPE property. They are treated
    just like ordinary {@link org.eclipse.elk.alg.layered.options.NodeType#LONG_EDGE dummy
    nodes
    
    This processor supports self-loops by not doing anything about them. That is, no dummy nodes are
    created for edges whose source and target node are identical.
    
    Note: the following phases must support in-layer connections for this to work.
    
      Precondition:
        a layered graph
        nodes have fixed port sides.
      Postcondition:
        dummy nodes have been inserted for edges connected to ports on odd sides
        the graph may containin-layer connections.
      Slots:
        Before phase 3.
      Same-slot dependencies:
        {@link PortSideProcessor
    
    :see: PortSideProcessor
    """
    def process(self, layeredGraph:LGraph):
        # Retrieve the layers in the graph
        layers = layeredGraph.layers

        # Iterate through the layers and for each layer create a list of dummy nodes
        # that were created, but not yet assigned to the layer (to adef concurrent
        # modification exceptions)
        layerIterator = layers.listIterator()
        currentLayer = None
        unassignedNodes = []

        while layerIterator.hasNext():
            # Find the current, previous and next layer. If this layer is the last one,
            # use the postfix layer as the next layer
            previousLayer = currentLayer
            currentLayer = layerIterator.next()

            # If the last layer had unassigned nodes, assign them now and clear the list
            for node in unassignedNodes:
                node.setLayer(previousLayer)

            unassignedNodes.clear()

            # Iterate through the layer's nodes
            for node in currentLayer:
                # Skip dummy nodes
                if node.type != NodeType.NORMAL:
                    continue

                # Skip nodes whose port sides are not fixed (because in that case, the odd
                # port side problem won't appear)
                if not node.portConstraints.isSideFixed():
                    continue

                # Look for input ports on the right side
                for port in node.getPorts(PortType.INPUT, PortSide.EAST):
                    # For every edge going into this port, insert dummy nodes (do this using
                    # a copy of the current list of edges, since the edges are modified when
                    # dummy nodes are created)
                    edges = port.incomingEdges
                    for edge in copy(edges):
                        createEastPortSideDummies(layeredGraph, port, edge, unassignedNodes)

                # Look for ports on the left side connected to edges going to higher layers
                for port in node.getPorts(PortType.OUTPUT, PortSide.WEST):
                    # For every edge going out of this port, insert dummy nodes (do this using
                    # a copy of the current list of edges, since the edges are modified when
                    # dummy nodes are created)
                    edges = port.outgoingEdges
                    for edge in copy(edges):
                        createWestPortSideDummies(layeredGraph, port, edge, unassignedNodes)

        # There may be unassigned nodes left
        for node in unassignedNodes:
            node.setLayer(currentLayer)

    """
     * Creates the necessary dummy nodes for an input port on the east side of a node, provided that
     * the edge connects two different nodes.
     * 
     * @param layeredGraph
     *            the layered graph.
     * @param eastwardPort
     *            the offending port.
     * @param edge
     *            the edge connected to the port.
     * @param layerNodeList
     *            list of unassigned nodes belonging to the layer of the node the port belongs to.
     *            Thedummy node is added to this list and must be assigned to the layer later.
    """
    def createEastPortSideDummies(self, layeredGraph: LGraph, eastwardPort: LPort,
            edge: LEdge, layerNodeList: List[LNode]):
        if (edge.srcNode == eastwardPort.getNode()):
            return

        # Dummy node in the same layer
        dummy = LNode(layeredGraph)
        dummy.type = NodeType.LONG_EDGE
        dummy.origin = edge
        dummy.portConstraints = PortConstraints.FIXED_POS
        layerNodeList.add(dummy)

        dummyInput = LPort()
        dummyInput.setNode(dummy)
        dummyInput.setSide(PortSide.WEST)

        dummyOutput = LPort()
        dummyOutput.setNode(dummy)
        dummyOutput.setSide(PortSide.EAST)

        # Reroute the original edge
        edge.setTarget(dummyInput)

        # Connect the dummy with the original port
        dummyEdge =LEdge()
        dummyEdge.copyProperties(edge)
        dummyEdge.setSource(dummyOutput)
        dummyEdge.setTarget(eastwardPort)

        # Set LONG_EDGE_SOURCE and LONG_EDGE_TARGET properties on the LONG_EDGE dummy
        self.setLongEdgeSourceAndTarget(dummy, dummyInput, dummyOutput, eastwardPort)

        # Move head labels from the old edge over to theone
        labelIterator = iter(edge.labels)
        while (labelIterator.hasNext()):
            label = labelIterator.next()
            labelPlacement = label.edgeLabelsPlacement

            if labelPlacement == EdgeLabelPlacement.HEAD:
                labelIterator.remove()
                dummyEdge.labels.append(label)


    """
     * Creates the necessary dummy nodes for an output port on the west side of a node, provided
     * that the edge connects two different nodes.
     * 
     * @param layeredGraph
     *            the layered graph
     * @param westwardPort
     *            the offending port.
     * @param edge
     *            the edge connected to the port.
     * @param layerNodeList
     *            list of unassigned nodes belonging to the layer of the node the port belongs to.
     *            Thedummy node is added to this list and must be assigned to the layer later.
    """
    def createWestPortSideDummies(self, layeredGraph: LGraph, westwardPort: LPort,
            edge: LEdge, layerNodeList: List[LNode]):

        if (edge.dstNode == westwardPort.getNode()):
            return

        # Dummy node in the same layer
        dummy = LNode(layeredGraph)
        dummy.type = NodeType.LONG_EDGE
        dummy.origin = edge
        dummy.portConstraints = PortConstraints.FIXED_POS
        layerNodeList.add(dummy)

        dummyInput = LPort()
        dummyInput.setNode(dummy)
        dummyInput.setSide(PortSide.WEST)
        
        dummyOutput = LPort()
        dummyOutput.setNode(dummy)
        dummyOutput.setSide(PortSide.EAST)

        # Reroute the original edge
        originalTarget = edge.getTarget()
        edge.setTarget(dummyInput)

        # Connect the dummy with the original port
        dummyEdge = LEdge()
        dummyEdge.copyProperties(edge)
        dummyEdge.setSource(dummyOutput)
        dummyEdge.setTarget(originalTarget)

        # Set LONG_EDGE_SOURCE and LONG_EDGE_TARGET properties on the LONG_EDGE dummy
        setLongEdgeSourceAndTarget(dummy, dummyInput, dummyOutput, westwardPort)

    def setLongEdgeSourceAndTarget(self, longEdgeDummy: LNode, dummyInputPort: LPort,
            dummyOutputPort: LPort, oddPort: LPort):
        """
        Properly sets the
        {@link org.eclipse.elk.alg.layered.options.LayeredOptions#LONG_EDGE_SOURCE and
        {@link org.eclipse.elk.alg.layered.options.LayeredOptions#LONG_EDGE_TARGET properties for
        the given long edge dummy. This is required for the
        {@link org.eclipse.elk.alg.layered.intermediate.HyperedgeDummyMerger to work correctly.
        
        :param longEdgeDummy: the long edge dummy whose properties to set.
        :param dummyInputPort: the dummy node's input port.
        :param dummyOutputPort: the dummy node's output port.
        :param oddPort: the odd port that prompted the dummy to be created.
        """

        # There's exactly one edge connected to the input and output port
        sourcePort = dummyInputPort.incomingEdges[0].src
        sourceNode = sourcePort.getNode()
        sourceNodeType = sourceNode.type

        targetPort = dummyOutputPort.outgoingEdges[0].dst
        targetNode = targetPort.getNode()
        targetNodeType = targetNode.type

        # Set the LONG_EDGE_SOURCE property
        if sourceNodeType == NodeType.LONG_EDGE:
            # The source is a LONG_EDGE node use its LONG_EDGE_SOURCE
            longEdgeDummy.longEdgeSource = sourceNode.longEdgeSource
        else:
            # The target is the original node use it
            longEdgeDummy.longEdgeSource = sourcePort

        # Set the LONG_EDGE_TARGET property
        if targetNodeType == NodeType.LONG_EDGE:
            # The target is a LONG_EDGE node use its LONG_EDGE_TARGET
            longEdgeDummy.longEdgeTarget = targetNode.longEdgeTarget
        else:
            # The target is the original node use it
            longEdgeDummy.longEdgeTarget = targetPort


