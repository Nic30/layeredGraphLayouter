import unittest

from layeredGraphLayouter.tests.testGraphCreator import TestGraphCreator
from layeredGraphLayouter.containers.constants import PortSide
from layeredGraphLayouter.crossing.graphInfoHolder import GraphInfoHolder
from layeredGraphLayouter.crossing.barycenterHeuristic import BarycenterHeuristic
from layeredGraphLayouter.crossing.nodeRelativePortDistributor import NodeRelativePortDistributor
from layeredGraphLayouter.tests.exampleGraphsSimple import create_dualPortCross_pre,\
    create_dualPortCross_post


class AbstractBarycenterPortDistributorTC(unittest.TestCase):
    def setUp(self):
        self.gb = TestGraphCreator()

    def test_distributePortsOnSide_GivenCrossOnWesternSide_ShouldRemoveCrossing(self):
        """
        *  ___
         \/| |
         /\| |
        *  |_|
        """
        gb = self.gb
        rightNode = create_dualPortCross_pre(gb, fixedNodes=False).layers[1][0]
        _ports = rightNode.west
        expectedPortOrderRightNode = [_ports[1], _ports[0]]

        self.distributePortsInCompleteGraph(4)

        self.assertSequenceEqual(rightNode.west, expectedPortOrderRightNode)

    def test_distributePortsOfGraph_GivenCrossOnBothSides_ShouldRemoveCrossin(self):
        """
        *  ___  *
         \/| |\/
         /\| |/\
        *  |_|  *
        """
        gb = self.gb

        leftNodes = gb.addNodesToLayer(2, gb.makeLayer())
        middleNode = gb.addNodeToLayer(gb.makeLayer())
        rightNodes = gb.addNodesToLayer(2, gb.makeLayer())
        gb.eastWestEdgeFromTo(middleNode, rightNodes[1])
        gb.eastWestEdgeFromTo(middleNode, rightNodes[0])
        gb.eastWestEdgeFromTo(leftNodes[0], middleNode)
        gb.eastWestEdgeFromTo(leftNodes[1], middleNode)

        expectedPortOrderMiddleNode = gb.copyPortsInIndexOrder(
            middleNode, 1, 0, 3, 2)

        self.distributePortsInCompleteGraph(8)

        self.assertSequenceEqual(list(middleNode.iterPorts()),
                                 expectedPortOrderMiddleNode)

    def distributePortsInCompleteGraph(self, numberOfPorts: int):
        gb = self.gb
        gd = GraphInfoHolder(gb.graph, BarycenterHeuristic,
                             NodeRelativePortDistributor, None)
        layers = gb.graph.layers
        for i in range(len(layers)):
            gd.portDistributor.distributePortsWhileSweeping(layers, i, True)

        for i in range(0, len(layers) - 1, -1):
            gd.portDistributor.distributePortsWhileSweeping(layers, i, False)

    def test_distributePortsOfGraph_GivenCrossOnEasternSide_ShouldRemoveCrossing(self):
        """
        ___
        | |\ /-*
        | | x
        |_|/ \-*
        """
        gb = self.gb
        leftNode = create_dualPortCross_post(gb, fixedNodes=False).layers[0][0]

        expectedPortOrderLeftNode = gb.copyPortsInIndexOrder(leftNode, 1, 0)

        self.distributePortsInCompleteGraph(4)

        self.assertSequenceEqual(
            list(leftNode.iterPorts()), expectedPortOrderLeftNode)

    def test_distributePortsOfGraph_GivenInLayerEdgePortOrderCrossing_ShouldRemoveIt(self):
        """
            *-----
            *-\  |
          ____ | |
        * |  |-+--
          |__|-|
        """
        gb = self.gb

        gb.addNodeToLayer(gb.makeLayer())
        nodes = gb.addNodesToLayer(3, gb.makeLayer())
        gb.addInLayerEdge(nodes[0], nodes[2], PortSide.EAST)
        gb.addInLayerEdge(nodes[1], nodes[2], PortSide.EAST)

        expectedPortOrderLowerNode = gb.copyPortsInIndexOrder(nodes[2], 1, 0)

        self.distributePortsInCompleteGraph(4)

        self.assertSequenceEqual(list(nodes[2].iterPorts()),
                                 expectedPortOrderLowerNode)

    def test_distributePortsOfGraph_GivenNorthSouthPortOrderCrossing_ShouldSwitchPortOrder(self):
        """
           *-->*
           |
         *-+-->*
         | |
        _|_|_
        |   |
        |___|
        .
        """
        gb = self.gb

        leftNodes = gb.addNodesToLayer(3, gb.makeLayer())
        rightNodes = gb.addNodesToLayer(2, gb.makeLayer())

        gb.addNorthSouthEdge(
            PortSide.NORTH, leftNodes[2], leftNodes[1], rightNodes[1], False)
        gb.addNorthSouthEdge(
            PortSide.NORTH, leftNodes[2], leftNodes[0], rightNodes[0], False)

        _ports = list(leftNodes[2].iterPorts())
        expectedPortOrderLowerNode = [_ports[1], _ports[0]]

        self.distributePortsInCompleteGraph(6)

        self.assertSequenceEqual(
            list(leftNodes[2].iterPorts()), expectedPortOrderLowerNode)

    #def test_distributePortsWhileSweeping_givenSimpleCross_ShouldRemoveCrossing(self):
    #    """
    #     ___  ____
    #     | |\/|  |
    #     |_|/\|  |
    #          |--|
    #    """
    #    gb = self.gb
    #
    #    leftNode = gb.addNodeToLayer(gb.makeLayer())
    #    rightNode = gb.addNodeToLayer(gb.makeLayer())
    #    gb.eastWestEdgeFromTo(leftNode, rightNode)
    #    gb.eastWestEdgeFromTo(leftNode, rightNode)
    #    expectedPortRightNode = gb.copyPortsInIndexOrder(rightNode, 1, 0)
    #    nodeArray = gb.graph.layers
    #    portDist = LayerTotalPortDistributor(len(nodeArray))
    #    portDist.distributePortsWhileSweeping(nodeArray, 1, True)
    #
    #    self.assertSequenceEqual(list(rightNode.getPorts()),
    #                            expectedPortRightNode)
    #
    # TODO this is a problem which currently cannot be solved by our algorithm :-(
    # def distributePortsOnSide_partlyCrossHierarchicalEdges_CrossHierarchyStaysOuterChanges(self):
    #   """
    #    * <pre>
    #    * ____
    #    * | *+--  *
    #    * |  |  \/
    #    * |  |\ /\
    #    * | *+-x  *
    #    * |__|  \
    #    *        -*
    #    * </pre>
    #   """
    #    leftOuterNode = addNodeToLayer(makeLayer())
    #    rightNodes = addNodesToLayer(3, makeLayer())
    #    LPort[] leftOuterPorts = addPortsOnSide(3, leftOuterNode, PortSide.EAST)
    #    LGraph leftInnerGraph = nestedGraph(leftOuterNode)
    #    leftInnerNodes = addNodesToLayer(2, makeLayer(leftInnerGraph))
    #    leftInnerDummyNodes = new LNode[2]
    #    Layer dummyLayer = makeLayer()
    #    leftInnerDummyNodes[0] = addExternalPortDummyNodeToLayer(dummyLayer, leftOuterPorts[0])
    #    leftInnerDummyNodes[1] = addExternalPortDummyNodeToLayer(dummyLayer, leftOuterPorts[2])
    #    eastWestEdgeFromTo(leftInnerNodes[0], leftInnerDummyNodes[0])
    #    eastWestEdgeFromTo(leftInnerNodes[1], leftInnerDummyNodes[1])
    #    eastWestEdgeFromTo(leftOuterPorts[0], rightNodes[1])
    #    eastWestEdgeFromTo(leftOuterPorts[1], rightNodes[2])
    #    eastWestEdgeFromTo(leftOuterPorts[2], rightNodes[0])
    #    # leftOuterNode.setProperty(InternalProperties.HAS_HIERARCHICAL_AND_NORMAL_PORTS, True)
    #    setPortOrderFixed(leftOuterNode)
    #
    #    expectedOrder = Lists.newArrayList(switchOrderInArray(1, 2, leftOuterPorts))
    #
    #    distributePortsInCompleteGraph(8)
    #
    #    assertThat(leftOuterNode.getPorts(), is(expectedOrder))


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(AbstractBarycenterPortDistributorTC('test_distributePortsOfGraph_GivenInLayerEdgePortOrderCrossing_ShouldRemoveIt'))
    suite.addTest(unittest.makeSuite(AbstractBarycenterPortDistributorTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
