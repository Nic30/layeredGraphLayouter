from random import Random

from layeredGraphLayouter.containers.constants import PortConstraints,\
    HierarchyHandling, FixedAlignment
from layeredGraphLayouter.containers.lEdge import LEdge
from layeredGraphLayouter.containers.lNode import LNode
from layeredGraphLayouter.containers.lPort import LPort
from layeredGraphLayouter.containers.spacings import LGraphSpacings


class LNodeLayer(list):
    def __init__(self, graph: "LGraph" = None, registerOnGraph=True):
        self.graph = graph
        if registerOnGraph:
            self.graph.layers.append(self)

    def append(self, v):
        v.layer = self
        return list.append(self, v)

    def extend(self, iterable):
        for v in iterable:
            self.append(v)

    def __eq__(self, other):
        return self is other

    def __hash__(self):
        return id(self)


class LGraph():
    def __init__(self):
        self.edges = []
        self.nodes = []
        self.layers = []

        # node to layout node
        self._node2lnode = {}
        self.childGraphs = []
        self.parent = None
        self.parentLnode = None
        self.graphProperties = set()
        self.edgeRouting = None
        self.random = Random()

        self.thoroughness = 1
        self.crossingMinimizationHierarchicalSweepiness = 1

        # The graph contains comment boxes.
        self.p_comments = False
        # The graph contains dummy nodes representing external ports.
        self.p_externalPorts = False
        # The graph contains hyperedges.
        self.p_hyperedges = False
        # The graph contains hypernodes (nodes that are marked as such).
        self.p_hypernodes = False
        # The graph contains ports that are not free for positioning.
        self.p_nonFreePorts = False
        # The graph contains ports on the northern or southern side.
        self.p_northSouthPorts = False
        # The graph contains self-loops.
        self.p_selfLoops = False
        # The graph contains node labels.
        self.p_centerLabels = False
        # The graph contains head or tail edge labels.
        self.p_endLabels = False
        # The graph's nodes are partitioned.
        self.p_partitions = False
        self.hierarchyHandling = HierarchyHandling.INCLUDE_CHILDREN
        self.unnecessaryBendpoints = False
        self.nodePlacementBkFixedAlignment = FixedAlignment.NONE
        self.nodePlacementFavorStraightEdges = True
        self.spacings = LGraphSpacings()

    def getLayerlessNodes(self):
        """
        Returns the list of nodes that are not currently assigned to a layer.
        """
        return self.nodes

    def add_node(self, name: str=None, originObj=None,
                 portConstraint=PortConstraints.FIXED_ORDER) -> LNode:
        n = LNode(self, name=name, originObj=originObj)
        n.portConstraints = portConstraint
        self._node2lnode[originObj] = n
        self.nodes.append(n)
        return n

    def add_edge(self, src: LPort, dst: LPort, name=None, originObj=None):
        e = LEdge(name, originObj=originObj)
        e.setSrcDst(src, dst)
        self.edges.append(e)
        return e

    def append_layer(self, nodes):
        layer = LNodeLayer(self)
        for n in nodes:
            n.setLayer(layer)
        return layer
