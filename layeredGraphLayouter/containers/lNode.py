from itertools import chain
from typing import List, Generator

from layeredGraphLayouter.containers.constants import PortSide, PortType,\
    NodeType, PortConstraints, LayerConstraint, InLayerConstraint
from layeredGraphLayouter.containers.geometry import LRectangle
from layeredGraphLayouter.containers.lPort import LPort
from layeredGraphLayouter.containers.sizeConfig import UNIT_HEADER_OFFSET,\
    PORT_HEIGHT, width_of_str


class LNode(LRectangle):
    """
    Component for component diagram

    :ivar originObj: original object which this node represents
    :ivar name: name of this unit
    :ivar class_name: name of class of this unit

    :ivar north: list of LPort for on  top side.
    :ivar east: list of LPort for on right side.
    :ivar south: list of LPort for on bottom side.
    :ivar west: list of LPort for on left side.
    """

    def __init__(self, graph: "LGraph", name: str= None, originObj=None):
        super(LNode, self).__init__()
        if name is not None:
            assert isinstance(name, str)
        self.originObj = originObj
        self.name = name

        self.west = []
        self.east = []
        self.north = []
        self.south = []

        self.parent = None

        # {PortItem: LPort}
        self.graph = graph
        self.childGraphs = []

        # used by cycle breaker
        self.indeg = 0
        self.outdeg = 0
        self.mark = 0
        # used by layerer
        self.normHeight = None
        self.nestedGraph = None
        self.type = NodeType.NORMAL

        self.layer = None
        self.inLayerSuccessorConstraint = []
        self.inLayerConstraint = InLayerConstraint.NONE
        self.layeringLayerConstraint = LayerConstraint.NONE
        self.portConstraints = PortConstraints.UNDEFINED
        self.inLayerLayoutUnit = self
        self.nestedLgraph = None
        self.compoundNode = False
        self.origin = None
        self.extPortSide = None
        self.barycenterAssociates = None
        self.longEdgeHasLabelDummies = False

    def iterPorts(self) -> Generator[LPort, None, None]:
        return chain(self.north, self.east, self.south, self.west)

    def iterPortsReversed(self):
        return chain(reversed(self.west),
                     reversed(self.south),
                     reversed(self.east),
                     reversed(self.north))

    def iterSides(self):
        yield self.north
        yield self.east
        yield self.south
        yield self.west

    def initPortDegrees(self):
        indeg = 0
        outdeg = 0
        for p in self.iterPorts():
            for e in p.incomingEdges:
                if not e.isSelfLoop:
                    indeg += 1

            for e in p.outgoingEdges:
                if not e.isSelfLoop:
                    outdeg += 1

        self.indeg = indeg
        self.outdeg = outdeg

    def initDim(self, x=0, y=0):
        label_w = width_of_str(self.name)
        port_w = max(*map(lambda p: width_of_str(p.name),
                          self.iterPorts()),
                     label_w / 2)
        width = max(port_w, label_w)
        height = UNIT_HEADER_OFFSET + \
            max(len(self.west), len(self.east)) * PORT_HEIGHT
        self.possition.x += x
        self.possition.y += y
        self.size.x = width
        self.size.y = height

        if self.south or self.north:
            raise NotImplementedError()

        port_width = width / 2
        _y = y
        if self.name:
            _y += UNIT_HEADER_OFFSET

        for i in self.east:
            _y = i.initDim(port_width, x=x + port_width, y=_y)

        _y = y
        if self.name:
            _y += UNIT_HEADER_OFFSET
        for o in self.west:
            _y = o.initDim(port_width, x=x, y=_y)

    def translate(self, x, y):
        self.possition.x += x
        self.possition.y += y
        for p in self.iterPorts():
            p.translate(x, y)

    def addPort(self, name, direction: PortType, side: PortSide):
        port = LPort(self, direction, side, name=name)
        self.getPortSideView(side).append(port)
        return port

    def getPortsByType(self, type_) -> Generator[LPort, None, None]:
        o = PortType.OUTPUT
        assert type_ in (o, PortType.INPUT)
        for p in self.iterPorts():
            if type_ == o:
                if p.outgoingEdges:
                    yield p
            else:
                if p.incomingEdges:
                    yield p

    def getPortSideView(self, side) -> List["LPort"]:
        """
        Returns a sublist view for all ports of given side.

        :attention: Use this only after port sides are fixed!

        This is currently the case after running the {@link org.eclipse.elk.alg.layered.intermediate.PortListSorter}.
        Non-structural changes to this list are reflected in the original list. A structural modification is any
        operation that adds or deletes one or more elements; merely setting the value of an element is not a structural
        modification. Sublist indices can be cached using {@link LNode#cachePortSides()}.

        :param side: a port side
        :return: an iterable for the ports of given side
        """
        if side == PortSide.WEST:
            return self.west
        elif side == PortSide.EAST:
            return self.east
        elif side == PortSide.NORTH:
            return self.north
        elif side == PortSide.SOUTH:
            return self.south
        else:
            raise ValueError(side)

        # if not self.portSidesCached:
        #    # If not explicitly cached, this will be repeated each time.
        #    # However, this has the same complexity as filtering by side.
        #    self.findPortIndices()
        #
        #indices = self.portSideIndices[side]
        # if indices is None:
        #    return []
        # else:
        #    # We must create a new sublist each time,
        #    # because the order of the ports on one side can change.
        #    return self.ports[indices[0]:indices[1]]

    def getOutgoingEdges(self):
        """
        :return: a generator or all outgoing edges.
        """
        for port in self.iterPorts():
            yield from port.outgoingEdges

    def getIncomingEdges(self):
        for port in self.iterPorts():
            yield from port.incomingEdges

    def getConnectedEdges(self):
        for port in self.iterPorts():
            yield from port.iterEdges()

    def setLayer(self, layer):
        if self.layer is layer:
            return
        if self.layer:
            self.layer.remove(self)
        self.layer = layer
        self.layer.append(self)

    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self.name)


class LayoutExternalPort(LNode):
    def __init__(self, graph: "LGraph", name: str=None, direction=None):
        super(LayoutExternalPort, self).__init__(graph, name)
        self.direction = direction
        self.type = NodeType.EXTERNAL_PORT
        if direction == PortType.INPUT:
            self.layeringLayerConstraint = LayerConstraint.FIRST
        elif direction == PortType.OUTPUT:
            self.layeringLayerConstraint = LayerConstraint.LAST
        else:
            raise ValueError(direction)