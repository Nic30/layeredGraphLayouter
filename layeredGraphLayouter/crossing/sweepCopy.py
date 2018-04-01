from typing import List

from layeredGraphLayouter.containers.constants import NodeType, PortSide
from layeredGraphLayouter.containers.lGraph import LNodeLayer
from layeredGraphLayouter.crossing.graphInfoHolder import GraphInfoHolder
from layeredGraphLayouter.containers.lNode import LNode


class SweepCopy():
    """
    :note: Ported from ELK.

    Stores node and port order for a sweep.
    """

    def __init__(self, nodeOrderIn):
        # Saves a copy of the node order.
        self.nodeOrder = [layer[:] for layer in nodeOrderIn]
        # Saves a copy of the orders of the ports on each node, because they
        # are reordered in each sweep. */
        self.portOrders = {}

    def __len__(self):
        return len(self.nodeOrder)

    def __getitem__(self, index):
        return self.nodeOrder[index]

    def __setitem__(self, index, item):
        self.nodeOrder[index] = item

    @classmethod
    def from_order(cls, nodeOrderIn: List[LNodeLayer]):
        # Copies on construction.
        self = cls()
        self.nodeOrder = [list(layer) for layer in nodeOrderIn]
        po = self.portOrders
        for layer in nodeOrderIn:
            for node in layer:
                po[node] = list(node.iterPorts())

    def transferNodeAndPortOrdersToGraph(self, g: GraphInfoHolder)-> None:
        """
        the 'NORTH_OR_SOUTH_PORT' option allows the crossing minimizer to decide
        the side a corresponding dummy node is placed on in order to reduce the number of crossings
        as a consequence the configured port side may not be valid anymore and has to be corrected
        """
        northSouthPortDummies = []
        # updatePortOrder = set()

        # iterate the layers
        for i, layer in enumerate(g.lGraph.layers):
            northSouthPortDummies.clear()
            templateLayer = self.nodeOrder[i]
            # iterate and order the nodes within the layer
            for j, _ in enumerate(layer):
                node = templateLayer[j]
                # use the id field to remember the order within the layer
                if node.type == NodeType.NORTH_SOUTH_PORT:
                    northSouthPortDummies.append(node)

                layer[j] = node
                assert node.layer is layer

                # order ports as computed
                # node.getPorts().clear()
                # node.getPorts().extend(portOrders.get(i).get(j))

        # assert that the port side is set properly
        for dummy in northSouthPortDummies:
            origin = self.assertCorrectPortSides(dummy)
            #updatePortOrder.add(origin)
            #updatePortOrder.add(dummy)
        #
        # since the side of certain ports may have changed at this point,
        # the list of ports must be re-sorted (see PortListSorter)
        # and the port list views must be re-cached.
        # for node in updatePortOrder:
        #    Collections.sort(node.getPorts(), PortListSorter.DEFAULT_SORT_COMPARATOR)
        #    node.cachePortSides()

    def assertCorrectPortSides(self, dummy: LNode) -> LNode:
        """
        Corrects the {@link PortSide} of dummy's origin.

        :return: The {@link LNode} ('origin') whose port {@code dummy} represents.
        """
        assert dummy.getType() == NodeType.NORTH_SOUTH_PORT

        origin = dummy.in_layer_layout_unit

        # a north south port dummy has exactly one port
        dummyPorts = dummy.getPorts()
        dummyPort = dummyPorts[0]

        # find the corresponding port on the regular node
        for port in origin.iterPorts():
            if port is dummyPort.origin:
                # switch the port's side if necessary
                if ((port.side == PortSide.NORTH) and (dummy.id > origin.id)):
                    origin.nort.remove(port)
                    port.side = PortSide.SOUTH
                    origin.south.append(port)
                elif ((port.side == PortSide.SOUTH) and (origin.id > dummy.id)):
                    origin.south.remove(port)
                    port.side = PortSide.NORTH
                    origin.north.append(port)
                break
        return origin
