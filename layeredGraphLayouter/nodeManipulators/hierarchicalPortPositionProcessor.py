from layeredGraphLayouter.containers.constants import NodeType, PortSide,\
    PortConstraints
from layeredGraphLayouter.containers.lGraph import LGraph, LNodeLayer
from layeredGraphLayouter.iLayoutProcessor import ILayoutProcessor


class HierarchicalPortPositionProcessor(ILayoutProcessor):
    """
    Sets the y coordinate of external node dummies representing eastern or western hierarchical ports. Note that due to
    additional space required to route edges connected to northern external ports, the y coordinate set here may become
    invalid and may need to be fixed later. That fixing is part of what {@link HierarchicalPortOrthogonalEdgeRouter}
    does.

    This processor is only necessary for node placers that do not respect the
    {@link InternalProperties#PORT_RATIO_OR_POSITION} property themselves.

    Note that this code involves a few subtleties with the graph's offset. The vertical offset is calculated by the
    {@link LayerSizeAndGraphHeightCalculator}, which is executed before this processor has fixed the positions of the
    external port dummies of eastern and western ports. However, those dummies were most likely not placed at a smaller
    y coordinate than other nodes. This processor either moves dummies downwards, which has no influence on the graph's
    offset, or upwards. If this had an influence on the offset, external ports could not be placed outside their border,
    which is a perfectly valid configuration. We thus do not touch the offset again after moving the dummies around.


    Precondition:
      A layered graph with finished node placement.
      The graph's vertical coordinate offset is correct.
      External port dummies of eastern and western ports appear in their layer's node list in the order they
          will later appear on their node side in.
    Postcondition:
      External node dummies representing western or eastern ports have a correct y coordinate.
    Slots:
      Before phase 5.
    Same-slot dependencies:
      {@link LayerSizeAndGraphHeightCalculator}

    :see: HierarchicalPortConstraintProcessor
    :see: HierarchicalPortDummySizeProcessor
    :see: HierarchicalPortOrthogonalEdgeRouter
    """

    def process(self, layeredGraph: LGraph):
        layers = layeredGraph.layers

        # We're interested in EAST and WEST external port dummies only since they can only be in
        # the first or last layer, only fix coordinates of nodes in those two
        # layers
        if len(layers) > 0:
            self.fixCoordinates(layers[0], layeredGraph)

            if len(layers) > 1:
                self.fixCoordinates(layers[-1], layeredGraph)

    def fixCoordinates(self, layer: LNodeLayer, layeredGraph: LGraph):
        """
        Fixes the y coordinates of external port dummies in the given layer.

        :param layer: the layer.
        :param layeredGraph: the layered graph.
        :param portConstraints: the port constraints that apply to external ports.
        :param graphHeight: height of the graph.
        """
        portConstraints = layeredGraph.portConstraints
        if not (portConstraints.isRatioFixed() or portConstraints.isPosFixed()):
            # If coordinates are free to be set, we're done
            return

        graphHeight = self.layeredGraph.getActualSize().y

        # Iterate over the layer's nodes
        for node in layer:
            # We only care about external port dummies...
            if node.type != NodeType.EXTERNAL_PORT:
                continue

            # ...representing eastern or western ports.
            extPortSide = node.extPortSide
            if extPortSide != PortSide.EAST and extPortSide != PortSide.WEST:
                continue

            finalYCoordinate = node.portRatioOrPosition

            if portConstraints == PortConstraints.FIXED_RATIO:
                # finalYCoordinate is a ratio that must be multiplied with the
                # graph's height
                finalYCoordinate *= graphHeight

            # Apply the node's new Y coordinate
            node.geometry.y = finalYCoordinate - node.portAnchor.y
            node.borderToContentAreaCoordinates(False, True)
