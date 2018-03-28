from random import Random
from typing import Dict
import unittest

from layeredGraphLayouter.containers.constants import PortSide
from layeredGraphLayouter.containers.lPort import LPort
from layeredGraphLayouter.crossing.crossingCounter import CrossingsCounter
from layeredGraphLayouter.crossing.graphInfoHolder import GraphInfoHolder
from layeredGraphLayouter.tests.inLayerEdgeTestGraphCreator import InLayerEdgeTestGraphCreator
from layeredGraphLayouter.crossing.barycenterHeuristic import BarycenterHeuristic
from layeredGraphLayouter.crossing.nodeRelativePortDistributor import NodeRelativePortDistributor
from layeredGraphLayouter.tests.exampleGraphsSimple import create_dualDualCros,\
    create_quadEdgeCross, create_dualPortCross_post, create_dualPortCross_pre


class CrossingsCounterTC(unittest.TestCase):
    def setUp(self):
        self.gb = InLayerEdgeTestGraphCreator()

    def getInitPortOrder(self) -> Dict[LPort, int]:
        def iterPorts():
            for layer in self.order():
                for n in layer:
                    for p in n.iterPorts():
                        yield p

        return {p: 0 for p in iterPorts()}

    def test_countCrossingsBetweenLayers_fixedPortOrderCrossingOnTwoNodes(self):
        """
        ___  ___
        | |\/| |
        |_|/\|_|
        """
        gb = self.gb
        create_dualDualCros(gb)

        self.counter = CrossingsCounter(self.getInitPortOrder())

        order = self.order
        self.assertEqual(self.counter.countCrossingsBetweenLayers(
            order()[0], order()[1]), 1)

    def test_longInLayerCrossings(self):
        """
        *
         \
         /
        *
         \
        *+--
         | |
        * /
        *
        """
        gb = self.gb
        order = self.order

        nodes = gb.addNodesToLayer(5, gb.makeLayer())
        gb.addInLayerEdge(nodes[0], nodes[1], PortSide.EAST)
        gb.addInLayerEdge(nodes[1], nodes[3], PortSide.EAST)
        gb.addInLayerEdge(nodes[2], nodes[4], PortSide.EAST)

        counter = CrossingsCounter(self.getInitPortOrder())

        self.assertEqual(counter.countInLayerCrossingsOnSide(
            order()[0], PortSide.EAST), 1)

    def test_countCrossingsBetweenLayers_crossFormed(self):
        """
        *  *
         \/
         /\
        *  *
        """
        gb = self.gb
        gb.getCrossFormedGraph()

        self.counter = CrossingsCounter(self.getInitPortOrder())

        order = self.order
        self.assertEqual(self.counter.countCrossingsBetweenLayers(
            order()[0], order()[1]), 1)

    def order(self):
        return self.gb.graph.layers

    def test_countCrossingsBetweenLayers_crossFormedMultipleEdgesBetweenSameNodes(self):
        """
        Constructs a cross formed graph with two edges between the corners

        *    *
         \\//
         //\\
        *    *
        """
        gb = self.gb
        order = self.order
        create_quadEdgeCross(gb)

        gd = GraphInfoHolder(gb.graph, BarycenterHeuristic,
                             NodeRelativePortDistributor, None)
        gd.portDistributor.distributePortsWhileSweeping(order(), 1, True)
        counter = CrossingsCounter(self.getInitPortOrder())

        self.assertEqual(counter.countCrossingsBetweenLayers(
            order()[0], order()[1]), 4)

    def test_countCrossingsBetweenLayers_crossWithExtraEdgeInBetween(self):
        gb = self.gb
        gb.getCrossWithExtraEdgeInBetweenGraph()
        counter = CrossingsCounter(self.getInitPortOrder())
        order = self.order
        self.assertEqual(counter.countCrossingsBetweenLayers(
            order()[0], order()[1]), 3)

    def test_countCrossingsBetweenLayers_ignoreSelfLoops(self):
        gb = self.gb
        order = self.order

        gb.getCrossWithManySelfLoopsGraph()
        counter = CrossingsCounter(self.getInitPortOrder())
        cnt = counter.countCrossingsBetweenLayers(
            order()[0], order()[1])
        self.assertEqual(cnt, 1)

    def test_countCrossingsBetweenLayers_moreComplexThreeLayerGraph(self):
        gb = self.gb
        order = self.order

        gb.getMoreComplexThreeLayerGraph()
        gd = GraphInfoHolder(gb.graph, BarycenterHeuristic,
                             NodeRelativePortDistributor, None)
        gd.portDistributor.distributePortsWhileSweeping(order(), 1, True)
        counter = CrossingsCounter(self.getInitPortOrder())
        self.assertEqual(counter.countCrossingsBetweenLayers(
            order()[0], order()[1]), 1)

    def test_countCrossingsBetweenLayers_fixedPortOrder(self):
        order = self.order

        self.gb.getFixedPortOrderGraph()
        counter = CrossingsCounter(self.getInitPortOrder())
        self.assertEqual(counter.countCrossingsBetweenLayers(
            order()[0], order()[1]), 1)

    def test_countCrossingsBetweenLayers_intoSamePort(self):
        """
        *   *<- Into same port
         \//
         //\
        *   *
        """
        gb = self.gb
        order = self.order

        leftLayer = gb.makeLayer()
        rightLayer = gb.makeLayer()

        topLeft = gb.addNodeToLayer(leftLayer)
        bottomLeft = gb.addNodeToLayer(leftLayer)
        topRight = gb.addNodeToLayer(rightLayer)
        bottomRight = gb.addNodeToLayer(rightLayer)

        gb.eastWestEdgeFromTo(topLeft, bottomRight)
        bottomLeftFirstPort = gb.addPortOnSide(bottomLeft, PortSide.EAST)
        bottomLeftSecondPort = gb.addPortOnSide(bottomLeft, PortSide.EAST)
        topRightFirstPort = gb.addPortOnSide(topRight, PortSide.WEST)

        gb.addEdgeBetweenPorts(bottomLeftFirstPort, topRightFirstPort)
        gb.addEdgeBetweenPorts(bottomLeftSecondPort, topRightFirstPort)

        counter = CrossingsCounter(self.getInitPortOrder())

        self.assertEqual(counter.countCrossingsBetweenLayers(
            order()[0], order()[1]), 2)

    def test_countCrossingsBetweenPorts_givenWesternCrossings_OnlyCountsForGivenPorts(self):
        """
        *   /*
        |  /
        \ /____
         x/|  |
        |/\|  |
        *  |__|
        """
        gb = self.gb
        leftNodes = gb.addNodesToLayer(2, gb.makeLayer())
        rightNodes = gb.addNodesToLayer(2, gb.makeLayer())
        gb.eastWestEdgeFromTo(leftNodes[0], rightNodes[1])
        gb.eastWestEdgeFromTo(leftNodes[1], rightNodes[1])
        gb.eastWestEdgeFromTo(leftNodes[1], rightNodes[0])

        counter = CrossingsCounter(self.getInitPortOrder())
        counter.initForCountingBetween(leftNodes, rightNodes)
        ports = list(rightNodes[1].iterPorts())
        crossings = counter.countCrossingsBetweenPortsInBothOrders(
            ports[1],
            ports[0])
        self.assertEqual(crossings[0], 1)

    def test_countCrossingsBetweenPorts_GivenCrossingsOnEasternSide(self):
        """
        ___
        | |\/*
        |_|/\*
        """
        gb = self.gb
        create_dualPortCross_post(gb)
        leftNodes, rightNodes = gb.graph.layers

        counter = CrossingsCounter(self.getInitPortOrder())
        counter.initForCountingBetween(leftNodes, rightNodes)
        ports = list(leftNodes[0].iterPorts())
        crossings = counter.countCrossingsBetweenPortsInBothOrders(
            ports[0],
            ports[1]
        )
        self.assertEqual(crossings[0], 1)

    def test_countingTwoDifferentGraphs_DoesNotInterfereWithEachOther(self):
        """
        *---         *---
        ___ \       ___  \
        | |\/* and: | |--*
        | |/\*      | |--*
        |_|         |_|
        """
        gb = self.gb
        leftNodes = gb.addNodesToLayer(3, gb.makeLayer())
        rightNodes = gb.addNodesToLayer(3, gb.makeLayer())
        leftNode = leftNodes[1]
        leftPorts = gb.addPortsOnSide(2, leftNode, PortSide.EAST)
        gb.eastWestEdgeFromTo(leftNodes[2], rightNodes[1])
        gb.eastWestEdgeFromTo(leftPorts[0], rightNodes[1])
        gb.eastWestEdgeFromTo(leftPorts[1], rightNodes[0])
        gb.eastWestEdgeFromTo(leftNodes[0], rightNodes[0])

        self.counter = CrossingsCounter(self.getInitPortOrder())
        self.counter.initForCountingBetween(leftNodes, rightNodes)

        ports = list(leftNode.iterPorts())
        self.assertEqual(self.counter
                         .countCrossingsBetweenPortsInBothOrders(
                             ports[0],
                             ports[1]
                         )[0], 1)

        self.counter.switchPorts(leftPorts[0], leftPorts[1])
        leftNode.east[0] = leftPorts[1]
        leftNode.east[0] = leftPorts[0]

        ports = list(leftNode.iterPorts())
        self.assertEqual(self.counter
                         .countCrossingsBetweenPortsInBothOrders(
                             ports[0],
                             ports[1]
                         )[0], 0)

    def test_countCrossingsBetweenPorts_twoEdgesIntoSamePort(self):
        """
        *   *
         \//
         //\
        *   *
        ^Into same port
        """
        gb = self.gb
        order = self.order

        leftLayer = gb.makeLayer()
        rightLayer = gb.makeLayer()

        topLeft = gb.addNodeToLayer(leftLayer)
        bottomLeft = gb.addNodeToLayer(leftLayer)
        topRight = gb.addNodeToLayer(rightLayer)
        bottomRight = gb.addNodeToLayer(rightLayer)

        gb.eastWestEdgeFromTo(topLeft, bottomRight)
        bottomLeftPort = gb.addPortOnSide(bottomLeft, PortSide.EAST)
        topRightPort = gb.addPortOnSide(topRight, PortSide.WEST)

        gb.addEdgeBetweenPorts(bottomLeftPort, topRightPort)
        gb.addEdgeBetweenPorts(bottomLeftPort, topRightPort)

        self.counter = CrossingsCounter(self.getInitPortOrder())
        self.counter.initForCountingBetween(order()[0], order()[1])

        ports = list(topLeft.iterPorts())
        self.assertEqual(self.counter.countCrossingsBetweenPortsInBothOrders(
            bottomLeftPort,
            ports[0])[0],
            2)

    #@Ignore
    # def benchmark():
    #    makeTwoLayerRandomGraphWithNodesPerLayer(6000, 6)
    #
    #    counter = CrossingsCounter(self.getInitPortOrder())
    #    System.out.println("Starting")
    #    length = 400
    #    times = new long[length]
    #    for (int i = 0 i < length i++):
    #        long tick = new Date().getTime()
    #        counter.countCrossingsBetweenLayers(order()[0], order()[1])
    #        times[i] = new Date().getTime() - tick
    #
    #    System.out.println(Arrays.stream(times).min())
    #

    def test_dualPortCross_pre_and_unconnected(self):
        """
        *  ___
         \/| |
         /\|_|
        *  ___
           |_|
        """
        gb = self.gb
        order = self.order
        graph = create_dualPortCross_pre(gb)
        gb.addNodeToLayer(graph.layers[1])

        self.counter = CrossingsCounter(self.getInitPortOrder())
        self.counter.initForCountingBetween(order()[0], order()[1])
        ports = list(graph.layers[1][0].iterPorts())
        crossings = self.counter.countCrossingsBetweenPortsInBothOrders(
            ports[0],
            ports[1]
        )
        self.assertEqual(crossings[0], 1)

    def makeTwoLayerRandomGraphWithNodesPerLayer(self, numNodes: int, edgesPerNode: int):
        gb = self.gb
        leftNodes = gb.addNodesToLayer(numNodes, gb.makeLayer())
        rightNodes = gb.addNodesToLayer(numNodes, gb.makeLayer())
        random = Random(0)
        for i in range(edgesPerNode * numNodes):
            if random.randbits(1):
                left = leftNodes[random.nextInt(numNodes)]
                right = rightNodes[random.nextInt(numNodes)]
                gb.eastWestEdgeFromTo(left, right)
            else:
                gb.addInLayerEdge(leftNodes[random.nextInt(numNodes)],
                                  leftNodes[random.nextInt(numNodes)],
                                  PortSide.EAST)

        for node in rightNodes:
            node.cachePortSides()

        for node in leftNodes:
            node.cachePortSides()


if __name__ == "__main__":
    suite = unittest.TestSuite()
    #suite.addTest(CrossingsCounterTC(
    #    'test_countCrossingsBetweenPorts_GivenCrossingsOnEasternSide'))
    suite.addTest(unittest.makeSuite(CrossingsCounterTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
