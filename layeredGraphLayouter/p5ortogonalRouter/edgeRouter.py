from layeredGraphLayouter.iLayoutProcessor import ILayoutProcessor
from layeredGraphLayouter.p5ortogonalRouter.routingGenerator import OrthogonalRoutingGenerator,\
    RoutingDirection
from layeredGraphLayouter.containers.lGraph import LGraph
from layeredGraphLayouter.layoutProcessorConfiguration import LayoutProcessorConfiguration


class OrthogonalEdgeRouter(ILayoutProcessor):
    """
    Edge routing implementation that creates orthogonal bend points. Inspired by
    Georg Sander, Layout of directed hypergraphs with orthogonal hyperedges. In
    Proceedings of the 11th International Symposium on Graph Drawing (GD '03),
    LNCS vol. 2912, pp. 381-386, Springer, 2004.
    Giuseppe di Battista, Peter Eades, Roberto Tamassia, Ioannis G. Tollis,
    Graph Drawing: Algorithms for the Visualization of Graphs,
    Prentice Hall, New Jersey, 1999 (Section 9.4, for cycle breaking in the
    hyperedge segment graph)

    Precondition:the graph has a proper layering with
    assigned node and port positions the size of each layer is
    correctly set edges connected to ports on strange sides were
    processed

    Postcondition:each node is assigned a horizontal coordinate
    the bend points of each edge are set the width of the whole graph is set

    The basic processing strategy for this phase is empty. Depending on the graph features,
    dependencies on intermediate processors are added dynamically as follows:

    Before phase 1:
      - None.

    Before phase 2:
      - For center edge labels:
         - LABEL_DUMMY_INSERTER

    Before phase 3:
      - For non-free ports:
        - NORTH_SOUTH_PORT_PREPROCESSOR
        - INVERTED_PORT_PROCESSOR

      - For self-loops:
        - SELF_LOOP_PROCESSOR

      - For hierarchical ports:
        - HIERARCHICAL_PORT_CONSTRAINT_PROCESSOR

      - For center edge labels:
        - LABEL_DUMMY_SWITCHER

    Before phase 4:
      - For hyperedges:
        - HYPEREDGE_DUMMY_MERGER

      - For hierarchical ports:
        - HIERARCHICAL_PORT_DUMMY_SIZE_PROCESSOR

      - For edge labels:
        - LABEL_SIDE_SELECTOR

      - For end edge labels:
        - END_LABEL_PREPROCESSOR

    Before phase 5:

    After phase 5:
      - For non-free ports:
        - NORTH_SOUTH_PORT_POSTPROCESSOR

      - For hierarchical ports:
        - HIERARCHICAL_PORT_ORTHOGONAL_EDGE_ROUTER

      - For center edge labels:
        - LABEL_DUMMY_REMOVER

      - For end edge labels:
        - END_LABEL_POSTPROCESSOR
    """

    @classmethod
    def getLayoutProcessorConfiguration(cls, graph: LGraph):


        """ additional processor dependencies for graphs with possible inverted ports."""
        INVERTED_PORT_PROCESSING_ADDITIONS = LayoutProcessorConfiguration(
            p3_node_ordering_before=[INVERTED_PORT_PROCESSOR()])

        # Basic configuration
        configuration = LayoutProcessorConfiguration()

        # Additional dependencies
        if graph.p_hyperedges:
            # additional processor dependencies for graphs with hyperedges.
            HYPEREDGE_PROCESSING_ADDITIONS = LayoutProcessorConfiguration(
                p4_node_placement_before=[HYPEREDGE_DUMMY_MERGER()])
            configuration.addAll(HYPEREDGE_PROCESSING_ADDITIONS)
            configuration.addAll(INVERTED_PORT_PROCESSING_ADDITIONS)

        if graph.p_nonFreePorts or graph.feedbackEdges:
            configuration.addAll(INVERTED_PORT_PROCESSING_ADDITIONS)

            if graph.p_northSouthPorts:
                # additional processor dependencies for graphs with northern / southern non-free ports.
                NORTH_SOUTH_PORT_PROCESSING_ADDITIONS = LayoutProcessorConfiguration(
                    P3_NODE_ORDERING_before=[NORTH_SOUTH_PORT_PREPROCESSOR()],
                    P5_EDGE_ROUTING_after=[NORTH_SOUTH_PORT_POSTPROCESSOR()])
                configuration.addAll(NORTH_SOUTH_PORT_PROCESSING_ADDITIONS)

        if graph.p_externalPorts:
            """ additional processor dependencies for graphs with hierarchical ports."""
            HIERARCHICAL_PORT_PROCESSING_ADDITIONS = LayoutProcessorConfiguration(
                P3_NODE_ORDERING_before=[HIERARCHICAL_PORT_CONSTRAINT_PROCESSOR()],
                P4_NODE_PLACEMENT_before=[
                    HIERARCHICAL_PORT_DUMMY_SIZE_PROCESSOR()],
                P5_EDGE_ROUTING_after=[HIERARCHICAL_PORT_ORTHOGONAL_EDGE_ROUTER()])
            configuration.addAll(HIERARCHICAL_PORT_PROCESSING_ADDITIONS)

        if graph.p_selfLoops:
            #additional processor dependencies for graphs with self-loops."""
            SELF_LOOP_PROCESSING_ADDITIONS = LayoutProcessorConfiguration(
                    P3_NODE_ORDERING_before=[SELF_LOOP_PROCESSOR()])
            configuration.addAll(SELF_LOOP_PROCESSING_ADDITIONS)

        if graph.p_hypernodes:
            # additional processor dependencies for graphs with hypernodes."""
            HYPERNODE_PROCESSING_ADDITIONS = LayoutProcessorConfiguration(
                P5_EDGE_ROUTING_after=[HYPERNODE_PROCESSOR()])
            configuration.addAll(HYPERNODE_PROCESSING_ADDITIONS)

        if graph.p_centerLabels:
            # additional processor dependencies for graphs with center edge labels.
            CENTER_EDGE_LABEL_PROCESSING_ADDITIONS = LayoutProcessorConfiguration(
                P2_LAYERING_before=[LABEL_DUMMY_INSERTER()],
                P4_NODE_PLACEMENT_before=[LABEL_DUMMY_SWITCHER()],
                P4_NODE_PLACEMENT_before=[LABEL_SIDE_SELECTOR()],
                P5_EDGE_ROUTING_after=[LABEL_DUMMY_REMOVER()])
            configuration.addAll(CENTER_EDGE_LABEL_PROCESSING_ADDITIONS)

        if graph.p_endLabels:
            """ additional processor dependencies for graphs with head or tail edge labels."""
            END_EDGE_LABEL_PROCESSING_ADDITIONS = LayoutProcessorConfiguration(
                P4_NODE_PLACEMENT_before=[LABEL_SIDE_SELECTOR()],
                P4_NODE_PLACEMENT_before=[END_LABEL_PREPROCESSOR()],
                P5_EDGE_ROUTING_after =[END_LABEL_POSTPROCESSOR()])
            configuration.addAll(END_EDGE_LABEL_PROCESSING_ADDITIONS)

        return configuration

    def process(self, layeredGraph: LGraph):
        # Retrieve some generic values
        spacings = layeredGraph.spacings
        nodeNodeSpacing = layeredGraph.spacingNodeNodeBetweenLayers
        edgeEdgeSpacing = layeredGraph.spacingEdgeEdgeBetweenLayers
        edgeNodeSpacing = layeredGraph.spacingEdgeNodeBetweenLayers
        debug = layeredGraph.debugMode

        # Prepare for iterationnot
        routingGenerator = OrthogonalRoutingGenerator(
            RoutingDirection.WEST_TO_EAST, edgeEdgeSpacing, "phase5" if debug else None)
        xpos = 0.0
        layerIter = iter(layeredGraph.layers)
        leftLayer = None
        rightLayer = None
        leftLayerNodes = None
        rightLayerNodes = None
        leftLayerIndex = -1
        rightLayerIndex = -1

        # Iteratenot
        while True:
            # Fetch the next layer, if any
            rightLayer = layerIter.next() if layerIter.hasNext() else None
            rightLayerNodes = None if rightLayer is None else rightLayer.getNodes()
            rightLayerIndex = layerIter.previousIndex()

            # Place the left layer's nodes, if any
            if leftLayer is not None:
                LGraphUtil.placeNodesHorizontally(leftLayer, xpos)
                xpos += leftLayer.getSize().x

            # Route edges between the two layers
            startPos = xpos if leftLayer is None else xpos + edgeNodeSpacing
            slotsCount = routingGenerator.routeEdges(layeredGraph, leftLayerNodes, leftLayerIndex,
                                                     rightLayerNodes, startPos)

            isLeftLayerExternal = leftLayer is None or Iterables.all(leftLayerNodes,
                                                                     PolylineEdgeRouter.PRED_EXTERNAL_WEST_OR_EAST_PORT)
            isRightLayerExternal = rightLayer is None or Iterables.all(rightLayerNodes,
                                                                       PolylineEdgeRouter.PRED_EXTERNAL_WEST_OR_EAST_PORT)

            if slotsCount > 0:
                # The space between each pair of edge segments, and between
                # nodes and edges
                increment = edgeNodeSpacing + \
                    (slotsCount - 1) * edgeEdgeSpacing
                if rightLayer is not None:
                    increment += edgeNodeSpacing

                # If we are between two layers, make sure their minimal spacing
                # is preserved
                if increment < nodeNodeSpacing and not isLeftLayerExternal and not isRightLayerExternal:
                    increment = nodeNodeSpacing

                xpos += increment
            elif not isLeftLayerExternal and not isRightLayerExternal:
                # If all edges are straight, use the usual spacing
                xpos += nodeNodeSpacing

            leftLayer = rightLayer
            leftLayerNodes = rightLayerNodes
            leftLayerIndex = rightLayerIndex
            if rightLayer is None:
                break

        layeredGraph.getSize().x = xpos
