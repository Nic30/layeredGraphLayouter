from layeredGraphLayouter.iLayoutProcessor import ILayoutProcessor
from layeredGraphLayouter.containers.lNode import LNode
from layeredGraphLayouter.containers.constants import NodeType
from layeredGraphLayouter.containers.lGraph import LGraph


class LongEdgeJoiner(ILayoutProcessor):
    """
    Removes dummy nodes due to edge splitting (dummy nodes that have the node type
    {@link NodeType#LONG_EDGE}). If an edge is split into a
    chain of edges <i>e1, e2, ..., ek</i>, the first edge <i>e1</i> is retained, while the other
    edges <i>e2, ..., ek</i> are discarded. This fact should be respected by all processors that
    create dummy nodes: they should always put the original edge as first edge in the chain of edges,
    so the original edge is restored.

    The actual implementation that joins long edges is provided by this class as a public utility method
    to be used by other processors.

      Preconditions:
        a layered graph
        nodes are placed
        edges are routed.
      Postconditions:
        there are no dummy nodes of type {@link NodeType#LONG_EDGE} in the graph's layers.
        the dummy nodes' {@link LNode#getLayer() layer} fields 
            have <strong>not</strong> been set to {@code null} though.
      Slots:
        After phase 5.
      Same-slot dependencies:
        {@link HierarchicalPortOrthogonalEdgeRouter}

    """

    def process(self, layeredGraph: LGraph):
        addUnnecessaryBendpoints = layeredGraph.unnecessaryBendpoints
        joinAt = self.joinAt

        for layer in layeredGraph.layers:
            toRemoveIndexes = []
            for i, node in enumerate(layer):
                # Check if it's a dummy edge we're looking for
                if node.type == NodeType.LONG_EDGE:
                    joinAt(layeredGraph, node, addUnnecessaryBendpoints)
                    toRemoveIndexes.append(i)

            for i in reversed(toRemoveIndexes):
                del layer[i]

    @staticmethod
    def joinAt(layeredGraph: LGraph, longEdgeDummy: LNode, addUnnecessaryBendpoints: bool):
        """
        Joins the edges connected to the given dummy node. The dummy node is then ready to be removed
        from the graph.

        :param longEdgeDummy: the dummy node whose incident edges to join.
        :param addUnnecessaryBendpoints: {@code true} if a bend point should be added to the edges at the position of the
                   dummy node.
        """
        # Get the input and output port (of which we assume to have only one, on the western side and
        # on the eastern side, respectively) the incoming edges are retained, and the outgoing edges
        # are discarded
        inputPortEdges = longEdgeDummy.west[0].incomingEdges
        outputPortEdges = longEdgeDummy.east[0].outgoingEdges
        edgeCount = len(inputPortEdges)

        # If we are to add unnecessary bend points, we need to know where. We take the position of the
        # first port we find. (It doesn't really matter which port we're using, so we opt to keep it
        # surprisingly simple.)
        unnecessaryBendpoint = longEdgeDummy.west[0].geometry.getAbsoluteAnchor()

        # The following code assumes that edges with the same indices in the two lists originate from
        # the same long edge, which is true for the current implementation of LongEdgeSplitter and
        # HyperedgeDummyMerger
        while edgeCount > 0:
            edgeCount -= 1
            # Get the two edges
            survivingEdge = inputPortEdges[0]
            droppedEdge = outputPortEdges[0]

            # The surviving edge's target needs to be set to the old target of the dropped edge.
            # However, this doesn't replace the dropped edge with the surviving edge in the list of
            # incoming edges of the (new) target port, but instead appends the surviving edge. That in
            # turn messes with the implicit assumption that edges with the same index on input and
            # output ports of long edge dummies belong to each other. Thus, we need to ensure that the
            # surviving edge is at the correct index in the list of incoming edges. Hence the
            # complicated code below. (KIPRA-1670)
            targetIncomingEdges = droppedEdge.dst.incomingEdges
            droppedEdgeListIndex = targetIncomingEdges.index(droppedEdge)
            survivingEdge.setTargetAndInsertAtIndex(
                droppedEdge.dst, droppedEdgeListIndex)

            # Remove the dropped edge from the graph
            droppedEdge.setSource(None)
            droppedEdge.setTarget(None)
            layeredGraph.edges.remove(droppedEdge)

            # Join their bend points and add possibly an unnecessary one
            survivingBendPoints = survivingEdge.bendPoints

            if addUnnecessaryBendpoints:
                survivingBendPoints.append(unnecessaryBendpoint[:])

            for bendPoint in droppedEdge.bendPoints:
                survivingBendPoints.append(bendPoint[:])

            # Join their labels
            survivingLabels = survivingEdge.labels
            for label in droppedEdge.labels:
                survivingLabels.append(label)

            # Join their junction points
            survivingJunctionPoints = survivingEdge.junctionPoints
            droppedJunctionsPoints = droppedEdge.junctionPoints
            if (droppedJunctionsPoints is not None):
                if (survivingJunctionPoints is None):
                    survivingJunctionPoints = []
                    survivingEdge.junctionPoints = survivingJunctionPoints
                for jp in droppedJunctionsPoints:
                    survivingJunctionPoints.add(jp[:])
