from layeredGraphLayouter.containers.constants import NodeType
from layeredGraphLayouter.containers.lNode import LNode

class UnspecifiedSpacingException(Exception):
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
        n = NodeType.values().length
        self.nodeTypeSpacingOptionsHorizontal = [[0 for _ in range(n)] for _ in range(n)]
        self.nodeTypeSpacingOptionsVertical = [[0 for _ in range(n)] for _ in range(n)]
        self.precalculateNodeTypeSpacings()
        
    def precalculateNodeTypeSpacings(self):
        nodeTypeSpacing = self.nodeTypeSpacing

        # normal
        nodeTypeSpacing(NodeType.NORMAL, 
                LayeredOptions.SPACING_NODE_NODE,
                LayeredOptions.SPACING_NODE_NODE_BETWEEN_LAYERS)
        nodeTypeSpacing(NodeType.NORMAL, NodeType.LONG_EDGE,
                LayeredOptions.SPACING_EDGE_NODE,
                LayeredOptions.SPACING_EDGE_NODE_BETWEEN_LAYERS)
        nodeTypeSpacing(NodeType.NORMAL, NodeType.NORTH_SOUTH_PORT,
                LayeredOptions.SPACING_EDGE_NODE)
        nodeTypeSpacing(NodeType.NORMAL, NodeType.EXTERNAL_PORT,
                LayeredOptions.SPACING_EDGE_NODE) # TODO
        nodeTypeSpacing(NodeType.NORMAL, NodeType.LABEL,
                LayeredOptions.SPACING_NODE_NODE,
                LayeredOptions.SPACING_NODE_NODE_BETWEEN_LAYERS)
        nodeTypeSpacing(NodeType.NORMAL, NodeType.BIG_NODE,
                LayeredOptions.SPACING_NODE_NODE,
                LayeredOptions.SPACING_NODE_NODE_BETWEEN_LAYERS)
        
        # longedge
        nodeTypeSpacing(NodeType.LONG_EDGE, 
                LayeredOptions.SPACING_EDGE_EDGE,
                LayeredOptions.SPACING_EDGE_EDGE_BETWEEN_LAYERS)
        nodeTypeSpacing(NodeType.LONG_EDGE, NodeType.NORTH_SOUTH_PORT, 
                LayeredOptions.SPACING_EDGE_EDGE)
        nodeTypeSpacing(NodeType.LONG_EDGE, NodeType.EXTERNAL_PORT, 
                LayeredOptions.SPACING_EDGE_EDGE) # TODO
        nodeTypeSpacing(NodeType.LONG_EDGE, NodeType.LABEL, 
                LayeredOptions.SPACING_EDGE_NODE,
                LayeredOptions.SPACING_EDGE_NODE_BETWEEN_LAYERS)
        nodeTypeSpacing(NodeType.LONG_EDGE, NodeType.BIG_NODE, 
                LayeredOptions.SPACING_EDGE_NODE,
                LayeredOptions.SPACING_EDGE_NODE_BETWEEN_LAYERS)  

        # northsouth
        nodeTypeSpacing(NodeType.NORTH_SOUTH_PORT, 
                LayeredOptions.SPACING_EDGE_EDGE)
        nodeTypeSpacing(NodeType.NORTH_SOUTH_PORT, NodeType.EXTERNAL_PORT, 
                LayeredOptions.SPACING_EDGE_EDGE) # TODO
        nodeTypeSpacing(NodeType.NORTH_SOUTH_PORT, NodeType.LABEL, 
                LayeredOptions.SPACING_LABEL_NODE)
        nodeTypeSpacing(NodeType.NORTH_SOUTH_PORT, NodeType.BIG_NODE, 
                LayeredOptions.SPACING_EDGE_NODE)

        # external
        nodeTypeSpacing(NodeType.EXTERNAL_PORT, 
                LayeredOptions.SPACING_PORT_PORT)
        nodeTypeSpacing(NodeType.EXTERNAL_PORT, NodeType.LABEL, 
                LayeredOptions.SPACING_LABEL_PORT)
        nodeTypeSpacing(NodeType.EXTERNAL_PORT, NodeType.BIG_NODE, 
                LayeredOptions.SPACING_PORT_PORT) # actually shouldnt exist
        
        # label
        nodeTypeSpacing(NodeType.LABEL,
                LayeredOptions.SPACING_EDGE_EDGE,
                LayeredOptions.SPACING_EDGE_EDGE) 
        nodeTypeSpacing(NodeType.LABEL, NodeType.BIG_NODE, 
                LayeredOptions.SPACING_EDGE_NODE)
        
        # bignode
        nodeTypeSpacing(NodeType.BIG_NODE, 
                LayeredOptions.SPACING_NODE_NODE,
                LayeredOptions.SPACING_NODE_NODE_BETWEEN_LAYERS)
        
        # breaking points
        nodeTypeSpacing(NodeType.BREAKING_POINT, 
                LayeredOptions.SPACING_EDGE_EDGE,
                LayeredOptions.SPACING_EDGE_EDGE_BETWEEN_LAYERS)
        nodeTypeSpacing(NodeType.BREAKING_POINT, NodeType.NORMAL, 
                LayeredOptions.SPACING_EDGE_NODE,
                LayeredOptions.SPACING_EDGE_NODE_BETWEEN_LAYERS)
        nodeTypeSpacing(NodeType.BREAKING_POINT, NodeType.LONG_EDGE, 
                LayeredOptions.SPACING_EDGE_NODE,
                LayeredOptions.SPACING_EDGE_NODE_BETWEEN_LAYERS)

    def nodeTypeSpacing(self, nt: NodeType, spacing):
        self.nodeTypeSpacingOptionsVertical[nt.value][nt.value] = spacing

    def nodeTypeSpacing(self, nt: NodeType, spacingVert, spacingHorz):
        self.nodeTypeSpacingOptionsVertical[nt.value][nt.value] = spacingVert
        self.nodeTypeSpacingOptionsHorizontal[nt.value][nt.value] = spacingHorz
    

    def nodeTypeSpacing(self, n1: NodeType, n2: NodeType, spacing):
        self.nodeTypeSpacingOptionsVertical[n1.value][n2.value] = spacing
        self.nodeTypeSpacingOptionsVertical[n2.value][n1.value] = spacing
    

    def nodeTypeSpacing(self, n1: NodeType, n2: NodeType, spacingVert, spacingHorz):
        nodeTypeSpacingOptionsVertical[n1.value][n2.value] = spacingVert
        nodeTypeSpacingOptionsVertical[n2.value][n1.value] = spacingVert

        nodeTypeSpacingOptionsHorizontal[n1.value][n2.value] = spacingHorz
        nodeTypeSpacingOptionsHorizontal[n2.value][n1.value] = spacingHorz
    
    """
     * @param n1
     *            a node
     * @param n2
     *            another node
     * @return the spacing to be preserved between {@code n1 and {@code n2
    """
    def getHorizontalSpacing(self, n1: LNode, n2: LNode):
        return getLocalSpacing(n1, n2, nodeTypeSpacingOptionsHorizontal)
    
    """
     * @param nt1
     *            a node type
     * @param nt2
     *            another node type
     * @return the spacing to be preserved between {@code nt1 and {@code nt2
    """
    def getHorizontalSpacing(self, nt1: NodeType, nt2: NodeType):
        return getLocalSpacing(nt1, nt2, nodeTypeSpacingOptionsHorizontal)
    
    """
     * @param n1
     *            a node
     * @param n2
     *            another node
     * @return the spacing to be preserved between {@code n1 and {@code n2
    """
    def getVerticalSpacing(n1: LNode, n2: LNode):
        return getLocalSpacing(n1, n2, nodeTypeSpacingOptionsVertical)

    """
     * @param nt1
     *            a node
     * @param nt2
     *            another node
     * @return the spacing to be preserved between {@code n1 and {@code n2
    """
    def getVerticalSpacing(NodeType nt1, NodeType nt2):
        return getLocalSpacing(nt1, nt2, nodeTypeSpacingOptionsVertical)

    def getLocalSpacing(self, n1: LNode, n2: LNode, nodeTypeSpacingMapping):
        t1 = n1.type
        t2 = n2.type
        layoutOption = nodeTypeSpacingMapping[t1.value][t2.value]

        # get the spacing value for the first node
        s1 = self.getIndividualOrDefault(n1, layoutOption) 
        s2 = self.getIndividualOrDefault(n2, layoutOption)

        return max(s1, s2)

    def getLocalSpacing(self, nt1: NodeType, nt2: NodeType, nodeTypeSpacingMapping):
        layoutOption = nodeTypeSpacingMapping[nt1.value][nt2.value]
        return self.graph.getProperty(layoutOption)

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
    def getIndividualOrDefault(self, node: LNode, property):
        result = None
        # check for individual value
        if (node.hasProperty(LayeredOptions.SPACING_INDIVIDUAL_OVERRIDE)):
            individualSpacings = node.getProperty(LayeredOptions.SPACING_INDIVIDUAL_OVERRIDE)
            if (individualSpacings.hasProperty(property)):
                result = individualSpacings.getProperty(property)
        # use the common value
        if result is None:
            result = node.graph.getProperty(property)
        
        return result

