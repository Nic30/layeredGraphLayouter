from layeredGraphLayouter.containers.constants import PortSide, PortType


class LEdge():
    """
    Edge in layout graph

    :ivar name: name of this edge (label)
    :ivar originObj: optional object which was this edge generated for
    :ivar src: LPort instance where this edge starts
    :ivar srcNode: node of src (used as cache)
    :ivar dst: LPort instance where this edge ends
    :ivar dstNode: node of dst (used as cache)
    :ivar reversed: If True this edge has src,srcNode/dst,dstNode in reversed order
    :ivar isSelfLoop: flag, if True this edge starts and ends on same node
    """
    def __init__(self, name: str=None, originObj=None):
        if name is not None:
            assert isinstance(name, str)
        self.name = name
        self.originObj = originObj
        self.src = None
        self.srcNode = None
        self.dst = None
        self.dstNode = None
        self.reversed = False
        self.isSelfLoop = None
        self.junctionPoints = None
        self.edgeThickness = 1.5
        self.labels = []

    def copyProperties(self, other: "LEdge"):
        self.edgeThickness = other.edgeThickness

    def setSrcDst(self, src: "LPort", dst: "LPort"):
        self.setSource(src)
        self.setTarget(dst)

    def reverse(self, layeredGraph: "LGraph", adaptPorts: bool):
        """
        Reverses the edge, including its bend points. Negates the {@code REVERSED} property. (an
        edge that was marked as being reversed is then unmarked, and the other way around) This
        does not change any properties on the connected ports. End labels are reversed as well (
        {@code HEAD} labels become {@code TAIL} labels and vice versa).

        @param layeredGraph
                the layered graph
        @param adaptPorts
                If true and a connected port is a collector port (a port used to merge edges),
                the corresponding opposite port is used instead of the original one.
        """
        if adaptPorts:
            oldSrc = self.src
            oldDst = self.dst
            self.setSrcDst(None, None)
            if oldDst.inputCollect:
                newSrc = LGraphUtil.provideCollectorPort(layeredGraph, oldDst.getNode(),
                    PortType.OUTPUT, PortSide.EAST)
            else:
                newSrc = oldDst

            self.setSource(newSrc)

            if oldSrc.inputCollect:
                newDst = LGraphUtil.provideCollectorPort(layeredGraph, oldSrc.getNode(),
                    PortType.INPUT, PortSide.WEST)
            else:
                newDst = oldSrc

            self.setTarget(newDst)
        else:
            self.src.outgoingEdges.remove(self)
            self.dst.incomingEdges.remove(self)
            self.src, self.dst = self.dst, self.src
            self.src.outgoingEdges.append(self)
            self.dst.incomingEdges.append(self)

            self.srcNode, self.dstNode = self.dstNode, self.srcNode
        self.reversed = not self.reversed

        # Switch end labels
        for label in self.labels:
            labelPlacement = label.edgeLabelsPlacement

            if labelPlacement == EdgeLabelPlacement.TAIL:
                label.edgeLabelsPlacement = EdgeLabelPlacement.HEAD
            elif labelPlacement == EdgeLabelPlacement.HEAD:
                label.edgeLabelsPlacement = EdgeLabelPlacement.TAIL

    def setTarget(self, dst: "LPort"):
        self.dst = dst
        if dst is None:
            self.dstNode = None
            self.isSelfLoop = False
        else:
            self.dstNode = dst.getNode()
            dst.incomingEdges.append(self)
            self.isSelfLoop = self.srcNode is self.dstNode

    def setSource(self, src: "LPort"):
        self.src = src
        if src is None:
            self.srcNode = None
            self.isSelfLoop = False
        else:
            self.srcNode = src.getNode()
            src.outgoingEdges.append(self)
            self.isSelfLoop = self.srcNode is self.dstNode

    def __repr__(self):
        if self.reversed:
            return "<%sm reversed, %r -> %r>" % (self.__class__.__name__, self.dst, self.src)
        else:
            return "<%s, %r -> %r>" % (self.__class__.__name__, self.src, self.dst)
