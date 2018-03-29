from itertools import chain
from typing import List

from layeredGraphLayouter.containers.geometry import GeometryRect
from layeredGraphLayouter.containers.sizeConfig import PORT_HEIGHT


class LPort():
    """
    Port for component in component diagram

    :ivar originObj: original object which this node represents
    :ivar parent: parent unit of this port
    :ivar name: name of this port
    :ivar direction: direction of this port
    :ivar geometry: absolute geometry in layout
    :ivar children: list of children ports, before interface connecting phase
            (when routing this list is empty and children are directly on parent LNode)
    """

    def __init__(self, parent: "LNode", direction, side, name: str=None):
        self.originObj = None
        self.parent = parent
        self.name = name
        self.direction = direction
        self.geometry = GeometryRect(0, 0, 0, 0)
        self.outgoingEdges = []
        self.incomingEdges = []
        self.children = []
        self.side = side

        self.portDummy = None
        self.insideConnections = False
        self.inputCollect = False

    def getDegree(self) -> int:
        """
        Returns this port's degree, that is, the number of edges connected to it.

        @return the number of edges connected to this port.
        """
        return len(self.incomingEdges) + len(self.outgoingEdges)

    def getNetFlow(self) -> int:
        """
        Returns the number of incoming edges minus the number of outgoing edges. This
        is the net flow of the port.

        :return: the port's net flow.
        """
        return len(self.incomingEdges) - len(self.outgoingEdges)

    def getNode(self):
        p = self
        while True:
            p = p.parent
            if not isinstance(p, LPort):
                return p

    def iterEdges(self, filterSelfLoops=False):
        it = chain(self.incomingEdges, self.outgoingEdges)
        if filterSelfLoops:
            for e in it:
                if not e.isSelfLoop:
                    yield e
        else:
            yield from it

    def initDim(self, width, x=0, y=0):
        g = self.geometry
        g.x += x
        g.y += y
        g.width = width

        if self.name:
            g.height = PORT_HEIGHT

        return g.y + g.height

    def translate(self, x, y):
        self.geometry.x += x
        self.geometry.y += y
        assert not self.children

    def _getDebugName(self) -> List[str]:
        names = []
        p = self
        while True:
            if p is None:
                break
            names.append(p.name)
            p = p.parent
        return list(reversed(names))

    def getPredecessorPorts(self):
        for e in self.incomingEdges:
            yield e.src

    def getSuccessorPorts(self):
        for e in self.outgoingEdges:
            yield e.dst

    def getConnectedPorts(self):
        yield from self.getPredecessorPorts()
        yield from self.getSuccessorPorts()

    def __repr__(self):
        return "<%s %s>" % (
            self.__class__.__name__, ".".join(self._getDebugName()))
