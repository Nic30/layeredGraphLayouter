

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

    def reverse(self):
        self.src.outgoingEdges.remove(self)
        self.dst.incomingEdges.remove(self)
        self.src, self.dst = self.dst, self.src
        self.src.outgoingEdges.append(self)
        self.dst.incomingEdges.append(self)

        self.srcNode, self.dstNode = self.dstNode, self.srcNode
        self.reversed = not self.reversed

    def setTarget(self, dst: "LPort"):
        self.dst = dst
        self.dstNode = dst.getNode()
        dst.incomingEdges.append(self)
        self.isSelfLoop = self.srcNode is self.dstNode

    def setSource(self, src: "LPort"):
        self.src = src
        self.srcNode = src.getNode()
        src.outgoingEdges.append(self)
        self.isSelfLoop = self.srcNode is self.dstNode

    def __repr__(self):
        if self.reversed:
            return "<%sm reversed, %r -> %r>" % (self.__class__.__name__, self.dst, self.src)
        else:
            return "<%s, %r -> %r>" % (self.__class__.__name__, self.src, self.dst)
