from typing import Union

from layeredGraphLayouter.containers.constants import NodeType,\
    UnsupportedConfigurationException, LayeredOptions
from layeredGraphLayouter.containers.lNode import LNode


class UnspecifiedSpacingException(UnsupportedConfigurationException):
    """
    Dedicated exception indicating that no spacing value could be determined for a certain set of
    graph elements. This is probably due to a programming error.
    """
    pass


class LGraphSpacings():
    """
    Container class for a variety of spacing values that are either specified in the general
    {@link LayeredOptions class or KLay Layered's dedicated {@link LayeredOptions class.

    This class allows to either select the recorded spacing values directly or to query for spacing
    values using one of the convenience methods. The methods do not provide results for every
    combination of graph elements yet. In case it does not know the answer a
    {@link UnspecifiedSpacingException is thrown. In such a case the developer should add the
    required functionality to this class.
    """

    def __init__(self, graph: "LGraph"):
        """
        :param graph: the {@link LGraph for which to record the spacing values.
        """
        self.graph = graph
        # pre calculate the spacings between pairs of node types
        n = NodeType._VALUES_CNT.value
        self.nodeTypeSpacingOptionsHorizontal = [[0 for _ in range(n)]
                                                 for _ in range(n)]
        self.nodeTypeSpacingOptionsVertical = [[0 for _ in range(n)]
                                               for _ in range(n)]
        self.precalculateNodeTypeSpacings()

    def precalculateNodeTypeSpacings(self):
        nodeTypeSpacingVertHoriz = self.nodeTypeSpacingVertHoriz
        nodeTypeSpacingVertHorizBetween = self.nodeTypeSpacingVertHorizBetween
        nodeTypeSpacingVertBetween = self.nodeTypeSpacingVertBetween
        nodeTypeSpacingVert = self.nodeTypeSpacingVert

        # normal
        nodeTypeSpacingVertHoriz(NodeType.NORMAL,
                                 LayeredOptions.SPACING_NODE_NODE,
                                 LayeredOptions.SPACING_NODE_NODE_BETWEEN_LAYERS)
        nodeTypeSpacingVertHorizBetween(NodeType.NORMAL, NodeType.LONG_EDGE,
                                        LayeredOptions.SPACING_EDGE_NODE,
                                        LayeredOptions.SPACING_EDGE_NODE_BETWEEN_LAYERS)
        nodeTypeSpacingVertBetween(NodeType.NORMAL, NodeType.NORTH_SOUTH_PORT,
                                   LayeredOptions.SPACING_EDGE_NODE)
        nodeTypeSpacingVertBetween(NodeType.NORMAL, NodeType.EXTERNAL_PORT,
                                   LayeredOptions.SPACING_EDGE_NODE)  # TODO
        nodeTypeSpacingVertHorizBetween(NodeType.NORMAL, NodeType.LABEL,
                                        LayeredOptions.SPACING_NODE_NODE,
                                        LayeredOptions.SPACING_NODE_NODE_BETWEEN_LAYERS)
        nodeTypeSpacingVertHorizBetween(NodeType.NORMAL, NodeType.BIG_NODE,
                                        LayeredOptions.SPACING_NODE_NODE,
                                        LayeredOptions.SPACING_NODE_NODE_BETWEEN_LAYERS)

        # longedge
        nodeTypeSpacingVertHoriz(NodeType.LONG_EDGE,
                                 LayeredOptions.SPACING_EDGE_EDGE,
                                 LayeredOptions.SPACING_EDGE_EDGE_BETWEEN_LAYERS)
        nodeTypeSpacingVertBetween(NodeType.LONG_EDGE, NodeType.NORTH_SOUTH_PORT,
                                   LayeredOptions.SPACING_EDGE_EDGE)
        nodeTypeSpacingVertBetween(NodeType.LONG_EDGE, NodeType.EXTERNAL_PORT,
                                   LayeredOptions.SPACING_EDGE_EDGE)  # TODO
        nodeTypeSpacingVertHorizBetween(NodeType.LONG_EDGE, NodeType.LABEL,
                                        LayeredOptions.SPACING_EDGE_NODE,
                                        LayeredOptions.SPACING_EDGE_NODE_BETWEEN_LAYERS)
        nodeTypeSpacingVertHorizBetween(NodeType.LONG_EDGE, NodeType.BIG_NODE,
                                        LayeredOptions.SPACING_EDGE_NODE,
                                        LayeredOptions.SPACING_EDGE_NODE_BETWEEN_LAYERS)

        # northsouth
        nodeTypeSpacingVert(NodeType.NORTH_SOUTH_PORT,
                            LayeredOptions.SPACING_EDGE_EDGE)
        nodeTypeSpacingVertBetween(NodeType.NORTH_SOUTH_PORT, NodeType.EXTERNAL_PORT,
                                   LayeredOptions.SPACING_EDGE_EDGE)  # TODO
        nodeTypeSpacingVertBetween(NodeType.NORTH_SOUTH_PORT, NodeType.LABEL,
                                   LayeredOptions.SPACING_LABEL_NODE)
        nodeTypeSpacingVertBetween(NodeType.NORTH_SOUTH_PORT, NodeType.BIG_NODE,
                                   LayeredOptions.SPACING_EDGE_NODE)

        # external
        nodeTypeSpacingVert(NodeType.EXTERNAL_PORT,
                            LayeredOptions.SPACING_PORT_PORT)
        nodeTypeSpacingVertBetween(NodeType.EXTERNAL_PORT, NodeType.LABEL,
                                   LayeredOptions.SPACING_LABEL_PORT)
        nodeTypeSpacingVertBetween(NodeType.EXTERNAL_PORT, NodeType.BIG_NODE,
                                   LayeredOptions.SPACING_PORT_PORT)  # actually shouldnt exist

        # label
        nodeTypeSpacingVertHoriz(NodeType.LABEL,
                                 LayeredOptions.SPACING_EDGE_EDGE,
                                 LayeredOptions.SPACING_EDGE_EDGE)
        nodeTypeSpacingVertBetween(NodeType.LABEL, NodeType.BIG_NODE,
                                   LayeredOptions.SPACING_EDGE_NODE)

        # bignode
        nodeTypeSpacingVertHoriz(NodeType.BIG_NODE,
                                 LayeredOptions.SPACING_NODE_NODE,
                                 LayeredOptions.SPACING_NODE_NODE_BETWEEN_LAYERS)

        # breaking points
        nodeTypeSpacingVertHoriz(NodeType.BREAKING_POINT,
                                 LayeredOptions.SPACING_EDGE_EDGE,
                                 LayeredOptions.SPACING_EDGE_EDGE_BETWEEN_LAYERS)
        nodeTypeSpacingVertHorizBetween(NodeType.BREAKING_POINT, NodeType.NORMAL,
                                        LayeredOptions.SPACING_EDGE_NODE,
                                        LayeredOptions.SPACING_EDGE_NODE_BETWEEN_LAYERS)
        nodeTypeSpacingVertHorizBetween(NodeType.BREAKING_POINT, NodeType.LONG_EDGE,
                                        LayeredOptions.SPACING_EDGE_NODE,
                                        LayeredOptions.SPACING_EDGE_NODE_BETWEEN_LAYERS)

    def nodeTypeSpacingVert(self, nt: NodeType,
                            spacing: float):
        self.nodeTypeSpacingOptionsVertical[nt.value][nt.value] = spacing

    def nodeTypeSpacingVertHoriz(self, nt: NodeType,
                                 spacingVert: float, spacingHorz: float):
        self.nodeTypeSpacingOptionsVertical[nt.value][nt.value] = spacingVert
        self.nodeTypeSpacingOptionsHorizontal[nt.value][nt.value] = spacingHorz

    def nodeTypeSpacingVertBetween(self, n1: NodeType, n2: NodeType,
                                   spacing: float):
        self.nodeTypeSpacingOptionsVertical[n1.value][n2.value] = spacing
        self.nodeTypeSpacingOptionsVertical[n2.value][n1.value] = spacing

    def nodeTypeSpacingVertHorizBetween(self, n1: NodeType, n2: NodeType,
                                        spacingVert: float, spacingHorz: float):
        self.nodeTypeSpacingOptionsVertical[n1.value][n2.value] = spacingVert
        self.nodeTypeSpacingOptionsVertical[n2.value][n1.value] = spacingVert

        self.nodeTypeSpacingOptionsHorizontal[n1.value][n2.value] = spacingHorz
        self.nodeTypeSpacingOptionsHorizontal[n2.value][n1.value] = spacingHorz

    """
     * @param n1
     *            a node or a node type
     * @param n2
     *            another node or node type
     * @return the spacing to be preserved between {@code n1 and {@code n2
    """

    def getHorizontalSpacing(self, n1: Union[LNode, NodeType], n2: Union[LNode, NodeType]):
        return self.getLocalSpacing(n1, n2, self.nodeTypeSpacingOptionsHorizontal)

    """
     * @param n1
     *            a node or a node type
     * @param n2
     *            another node or node type
     * @return the spacing to be preserved between {@code n1 and {@code n2
    """

    def getVerticalSpacing(self, n1: Union[LNode, NodeType], n2: Union[LNode, NodeType]):
        return self.getLocalSpacing(n1, n2, self.nodeTypeSpacingOptionsVertical)

    def getLocalSpacing(self, n1: Union[LNode, NodeType], n2: Union[LNode, NodeType],
                        nodeTypeSpacingMapping):
        if isinstance(n1, LNode):
            t1 = n1.type
        else:
            t1 = n1

        if isinstance(n2, LNode):
            t2 = n2.type
        else:
            t2 = n2

        layoutOption = nodeTypeSpacingMapping[t1.value][t2.value]

        # get the spacing value for the first node
        s1 = self.getIndividualOrDefault(n1, layoutOption)
        s2 = self.getIndividualOrDefault(n2, layoutOption)

        return max(s1, s2)

    @staticmethod
    def getIndividualOrDefault(node: Union[LNode, NodeType], property: str):
        """
         * Returns the value of the given property as it applies to the given node. First checks whether an individual
         * override is set on the node that has the given property configured. If so, the configured value is returned.
         * Otherwise, the node's parent node, if any, is queried.
         * 
         * @param node
         *            the node whose property value to return.
         * @param property
         *            the property.
         * @return the individual override for the property or the default value inherited by the parent node.
        """
        # check for individual value
        if isinstance(node, LNode) and node.spacingIndividualOverride is not None:
            return getattr(node.spacingIndividualOverride, property)
        # use the common value
        return getattr(node.graph, property)
