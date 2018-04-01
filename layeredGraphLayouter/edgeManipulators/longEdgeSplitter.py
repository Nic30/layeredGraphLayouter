from math import floor

from layeredGraphLayouter.containers.constants import NodeType, PortConstraints,\
    PortSide, PortType
from layeredGraphLayouter.containers.lEdge import LEdge
from layeredGraphLayouter.containers.lGraph import LGraph, LNodeLayer
from layeredGraphLayouter.containers.lNode import LNode
from layeredGraphLayouter.containers.lPort import LPort
from layeredGraphLayouter.iLayoutProcessor import ILayoutProcessor


class LongEdgeSplitter(ILayoutProcessor):
    """
    Splits the long edges of the layered graph to obtain a proper layering. For each edge that
    connects two nodes that are more than one layer apart from each other, create a dummy node to
    split the edge. The resulting layering is <i>proper</i>, i.e. all edges connect only nodes from
    subsequent layers.

    The dummy nodes retain a reference to the ports the original long edge's source and target ports.

    The actual method that splits edges is declared as a public utility method to be called from other
    processors that need to split edges.


    Precondition:
        a layered graph.

    Postcondition:
        the graph is properly layered.
    Slots:
    Before phase 3.
        Same-slot dependencies:
    {@link LayerConstraintProcessor}
    """

    def process(self, layeredGraph: LGraph):
        if len(layeredGraph.layers) <= 2:
            return

        # Iterate through the layers
        layerIter = iter(layeredGraph.layers)
        layer = next(layerIter)
        for nextLayer in layerIter:

            # Iterate through the nodes
            for node in layer:
                # Iterate through the outgoing edges
                for port in node.iterPorts():
                    # Iterate through the edges
                    for edge in port.outgoingEdges:
                        targetLayer = edge.dstNode.layer

                        # If the edge doesn't go to the current or next layer,
                        # split it
                        if targetLayer is not layer and targetLayer is not nextLayer:
                            # If there is no next layer, something is wrong
                            # Split the edge
                            self.splitEdge(layeredGraph, edge, self.createDummyNode(
                                layeredGraph, nextLayer, edge))
            layer = nextLayer

    def createDummyNode(self, layeredGraph: LGraph, targetLayer: LNodeLayer,
                        edgeToSplit: LEdge) -> LNode:
        """
        Creates a long edge dummy node to split the given edge at the given layer and adds it to the
        layer.

        :param: layeredGraph the graph.
        :param: targetLayer the layer the dummy node will be inserted into.
        :param: edgeToSplit the edge that will later be split by the dummy node. The edge will be set as
                           the dummy node's {@link InternalProperties#ORIGIN ORIGIN}.
        :return: the created dummy node.
        """

        dummyNode = layeredGraph.add_node()
        dummyNode.type = NodeType.LONG_EDGE
        dummyNode.origin = edgeToSplit
        dummyNode.portConstraints = PortConstraints.FIXED_POS
        dummyNode.setLayer(targetLayer)

        return dummyNode

    def splitEdge(self, layeredGraph: LGraph, edge: LEdge, dummyNode: LNode) -> LEdge:
        """
        Does the actual work of splitting a given edge by rerouting it to the given dummy node and
        introducing a new edge. Two ports are added to the dummy node and long edge properties are
        configured for it. Also, any head labels the old edge has are moved to the new edge.

        :param edge: the edge to be split.
        :param dummyNode: the dummy node to split the edge with.
        :return: the new edge.
        """
        oldEdgeTarget = edge.dst

        # Set thickness of the edge
        thickness = edge.edgeThickness
        if (thickness < 0):
            raise ValueError(thickness)

        dummyNode.geometry.height = thickness
        portPos = floor(thickness / 2)

        # Create dummy input and output ports
        dummyInput = LPort(dummyNode, PortType.INPUT, PortSide.WEST)
        dummyNode.west.append(dummyInput)
        dummyInput.geometry.y = portPos

        dummyOutput = LPort(dummyNode, PortType.OUTPUT, PortSide.EAST)
        dummyNode.east.append(dummyOutput)
        dummyOutput.geometry.y = portPos

        edge.setTarget(dummyInput)

        # Create a dummy edge
        dummyEdge = layeredGraph.add_edge(dummyOutput, oldEdgeTarget)
        dummyEdge.copyProperties(edge)

        self.setDummyNodeProperties(dummyNode, edge, dummyEdge)
        self.moveHeadLabels(edge, dummyEdge)

        return dummyEdge

    def setDummyNodeProperties(self, dummyNode: LNode, inEdge: LEdge, outEdge: LEdge):
        """
        Sets the {@link InternalProperties#LONG_EDGE_SOURCE LONG_EDGE_SOURCE} and
        {@link InternalProperties#LONG_EDGE_TARGET LONG_EDGE_TARGET} properties on the given dummy node.

        @param dummyNode
                   the dummy node.
        @param inEdge
                   the edge going into the dummy node.
        @param outEdge
                   the edge going out of the dummy node.
        """

        inEdgeSourceNode = inEdge.srcNode
        outEdgeTargetNode = outEdge.dstNode

        if inEdgeSourceNode.type == NodeType.LONG_EDGE:
            # The incoming edge originates from a long edge dummy node, so we
            # can just copy its properties
            dummyNode.longEdgeSource = inEdgeSourceNode.longEdgeSource
            dummyNode.longEdgeTarget = inEdgeSourceNode.longEdgeTarget
            dummyNode.longEdgeHasLabelDummies = inEdgeSourceNode.longEdgeHasLabelDummies

        elif inEdgeSourceNode.type == NodeType.LABEL:
            # The incoming edge originates from a label dummy node, so we can
            # just copy its properties
            dummyNode.longEdgeSource = inEdgeSourceNode.longEdgeSource
            dummyNode.longEdgeTarget = inEdgeSourceNode.longEdgeTarget
            dummyNode.longEdgeHasLabelDummies = True

        elif outEdgeTargetNode.type == NodeType.LABEL:
            # The outgoing edge points to a label dummy node, so we can just
            # copy its properties
            dummyNode.longEdgeSource = outEdgeTargetNode.longEdgeSource
            dummyNode.longEdgeTarget = outEdgeTargetNode.longEdgeTarget
            dummyNode.longEdgeHasLabelDummies = True

        else:
            # The source is the input edge's source port, the target is the output edge's target port. Also,
            # the long edge doesn't seem to have label dummy nodes
            dummyNode.longEdgeSource = inEdge.src
            dummyNode.longEdgeTarget = outEdge.dst

    def moveHeadLabels(self, oldEdge: LEdge, newEdge: LEdge):
        """
        Moves all head labels from a given split edge to the new edge created to split it.

        @param oldEdge
                   the old edge whose head labels are to be moved.
        @param newEdge
                   the new edge whose head labels are to be moved.
        """
        labels = oldEdge.labels
        toRemove = []
        for label in labels:
            labelPlacement = label.edgeLabelsPlacement
            if labelPlacement == EdgeLabelPlacement.HEAD:
                toRemove.append(label)
                newEdge.getLabels().add(label)

        for label in toRemove:
            labels.remove(label)
