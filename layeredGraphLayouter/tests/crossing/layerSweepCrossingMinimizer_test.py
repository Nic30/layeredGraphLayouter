from typing import List
import unittest

from layeredGraphLayouter.containers.constants import PortSide
from layeredGraphLayouter.containers.lGraph import LGraph
from layeredGraphLayouter.containers.lNode import LNode
from layeredGraphLayouter.containers.lPort import LPort
from layeredGraphLayouter.crossing.barycenterHeuristic import BarycenterHeuristic
from layeredGraphLayouter.crossing.layerSweepCrossingMinimizer import LayerSweepCrossingMinimizer
from layeredGraphLayouter.tests.testGraphCreator import TestGraphCreator,\
    MockRandom


def makeNestedTwoNodeGraphWithEasternPorts(gb: TestGraphCreator,
                                           leftOuterNode: LNode,
                                           leftOuterPorts: List[LPort]) -> LGraph:
    leftInnerGraph = gb.nestedGraph(leftOuterNode)
    leftInnerNodes = gb.addNodesToLayer(2, gb.makeLayer(leftInnerGraph))
    leftInnerDummyNodes = gb.addExternalPortDummiesToLayer(
        gb.makeLayer(leftInnerGraph),
        leftOuterPorts)
    gb.eastWestEdgeFromTo(leftInnerNodes[0], leftInnerDummyNodes[0])
    gb.eastWestEdgeFromTo(leftInnerNodes[1], leftInnerDummyNodes[1])
    return leftInnerGraph


def makeNestedTwoNodeGraphWithWesternPorts(gb: TestGraphCreator,
                                           rightOuterNode: LNode,
                                           rightOuterPorts: List[LPort]) -> LGraph:
    rightInnerGraph = gb.nestedGraph(rightOuterNode)
    rightInnerDummyNodes = gb.addExternalPortDummiesToLayer(
        gb.makeLayer(rightInnerGraph),
        rightOuterPorts)
    rightInnerNodes = gb.addNodesToLayer(2, gb.makeLayer(rightInnerGraph))
    gb.eastWestEdgeFromTo(rightInnerDummyNodes[0], rightInnerNodes[0])
    gb.eastWestEdgeFromTo(rightInnerDummyNodes[1], rightInnerNodes[1])
    return rightInnerGraph


class LayerSweepCrossingMinimizerTC(unittest.TestCase):
    def setUp(self):
        self.random = MockRandom()
        self.crossMin = LayerSweepCrossingMinimizer()
        self.crossMin.random = self.random
        self.gb = TestGraphCreator()

    def setUpAndMinimizeCrossings(self):
        # if self.crossMinCls == BarycenterHeuristic:
        self.gb.graph.thoroughness = 1
        self.crossMin.process(self.gb.graph)

    def test_givenCompoundGraphWhereOrderIsOnlyCorrectedOnForwardSweep_RemovesCrossing(self):
        """
        ________
        |___  *|
        || |\/ |
        || |/\ |
        ||_|  *|
        |------|

        Sweep backward first.
        """
        gb = self.gb
        node = gb.addNodeToLayer(gb.makeLayer())
        innerGraph = gb.nestedGraph(node)
        leftInnerNode = gb.addNodeToLayer(gb.makeLayer(innerGraph))
        gb.setFixedOrderConstraint(leftInnerNode)
        rightInnerNodes = gb.addNodesToLayer(2, gb.makeLayer(innerGraph))
        gb.eastWestEdgeFromTo(leftInnerNode, rightInnerNodes[1])
        gb.eastWestEdgeFromTo(leftInnerNode, rightInnerNodes[0])

        rightInnerLayer = innerGraph.layers[1]
        expectedOrderRightInner = gb.switchOrderOfNodesInLayer(
            0, 1, rightInnerLayer)
        expectedPortOrderLeft = gb.copyPortsInIndexOrder(leftInnerNode, 0, 1)

        gb.random.setNextBoolean(False)
        self.setUpAndMinimizeCrossings()

        self.assertSequenceEqual(
            list(leftInnerNode.iterPorts()), expectedPortOrderLeft)
        self.assertSequenceEqual(rightInnerLayer, expectedOrderRightInner)

    def givenSingleHierarchicalNodeWithCross_RemovesCrossing(self):
        """
        ______
        |*  *|
        | \/ |
        | /\ |
        |*  *|
        |----|
        """
        gb = self.gb
        node = gb.addNodeToLayer(gb.makeLayer())
        innerGraph = gb.nestedGraph(node)
        innerNodesleft = gb.addNodesToLayer(2, gb.makeLayer(innerGraph))
        innerNodesRight = gb.addNodesToLayer(2, gb.makeLayer(innerGraph))
        gb.eastWestEdgeFromTo(innerNodesleft[0], innerNodesRight[1])
        gb.eastWestEdgeFromTo(innerNodesleft[1], innerNodesRight[0])

        expectedOrderRightBaryCenter = gb.switchOrderOfNodesInLayer(
            0, 1,
            innerGraph.layers[1])

        self.setUpAndMinimizeCrossings()

        self.assertSequenceEqual(
            innerGraph.layers[1], expectedOrderRightBaryCenter)

    def test_givenSimpleHierarchicalCross_ShouldResultInNoCrossing(self):
        """
        ____  ____
        |*-+  +-*|
        |  |\/|  |
        |*-+/\+-*|
        |--|  |--|
        """
        gb = self.gb
        leftOuterNode = gb.addNodeToLayer(gb.makeLayer())
        rightOuterNode = gb.addNodeToLayer(gb.makeLayer())
        leftOuterPorts = gb.addPortsOnSide(2, leftOuterNode, PortSide.EAST)
        rightOuterPorts = gb.addPortsOnSide(2, rightOuterNode, PortSide.WEST)

        gb.addEdgeBetweenPorts(leftOuterPorts[0], rightOuterPorts[0])
        gb.addEdgeBetweenPorts(leftOuterPorts[1], rightOuterPorts[1])

        makeNestedTwoNodeGraphWithEasternPorts(
            gb, leftOuterNode, leftOuterPorts)

        rightInnerGraph = makeNestedTwoNodeGraphWithWesternPorts(gb,
                                                                 rightOuterNode,
                                                                 rightOuterPorts)

        expectedExternalDummyOrderRight = gb.switchOrderOfNodesInLayer(
            0, 1, rightInnerGraph.layers[0])
        expectedNormalNodeOrderRight = gb.switchOrderOfNodesInLayer(
            0, 1, rightInnerGraph.layers[1])

        expectedOrderOfPortsRight = [rightOuterPorts[1],
                                     rightOuterPorts[0]]

        for g in gb.iterAllGraphs(gb.graph):
            g.crossingMinimizationHierarchical_sweepiness = 0.1

        self.setUpAndMinimizeCrossings()
        actualExternalDummyOrderRight = rightInnerGraph.layers[0]
        self.assertSequenceEqual(
            actualExternalDummyOrderRight, expectedExternalDummyOrderRight)
        self.assertSequenceEqual(
            rightOuterNode.iterPorts(), expectedOrderOfPortsRight)

        actualNormalOrderRight = rightInnerGraph.layers[1]
        self.assertSequenceEqual(
            actualNormalOrderRight, expectedNormalNodeOrderRight)

    def test_givenSimpleHierarchicalCrossSweepingFromRightToLeft_ShouldResultInNoCrossing(self):
        """
        ____  ____
        |*-+  +-*|
        |  |\/|  |
        |*-+/\+-*|
        |--|  |--|
        """
        gb = self.gb

        leftOuterNode = gb.addNodeToLayer(gb.makeLayer())
        rightOuterNode = gb.addNodeToLayer(gb.makeLayer())
        leftOuterPorts = gb.addPortsOnSide(2, leftOuterNode, PortSide.EAST)
        rightOuterPorts = gb.addPortsOnSide(2, rightOuterNode, PortSide.WEST)
        gb.addEdgeBetweenPorts(leftOuterPorts[0], rightOuterPorts[0])
        gb.addEdgeBetweenPorts(leftOuterPorts[1], rightOuterPorts[1])

        leftInnerGraph = makeNestedTwoNodeGraphWithEasternPorts(
            gb, leftOuterNode, leftOuterPorts)

        makeNestedTwoNodeGraphWithWesternPorts(
            gb, rightOuterNode, rightOuterPorts)

        expectedNodeOrderLeft = gb.switchOrderOfNodesInLayer(
            0, 1, leftInnerGraph.layers[0])

        expectedOrderOfPortsLeft = [leftOuterPorts[1], leftOuterPorts[0]]

        self.random.setNextBoolean(False)
        self.setUpAndMinimizeCrossings()

        self.assertSequenceEqual(
            list(leftOuterNode.iterPorts()), expectedOrderOfPortsLeft)
        self.assertSequenceEqual(
            leftInnerGraph.layers[0], expectedNodeOrderLeft)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    #suite.addTest(LayerSweepCrossingMinimizerTC('givenSingleHierarchicalNodeWithCross_RemovesCrossing'))
    suite.addTest(unittest.makeSuite(LayerSweepCrossingMinimizerTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
