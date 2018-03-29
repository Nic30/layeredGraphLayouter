import unittest
from layeredGraphLayouter.tests.testGraphCreator import TestGraphCreator
from layeredGraphLayouter.edgeManipulators.longEdgeSplitter import LongEdgeSplitter
from layeredGraphLayouter.containers.constants import NodeType


class LongEdgeSplitterTC(unittest.TestCase):
    def setUp(self):
        self.gb = TestGraphCreator()

    def test_simple(self):
        gb = self.gb
        node0 = gb.addNodeToLayer(gb.makeLayer())
        gb.makeLayer()
        node1 = gb.addNodeToLayer(gb.makeLayer())

        origE = gb.eastWestEdgeFromTo(node0, node1)

        sp = LongEdgeSplitter()
        sp.process(gb.graph)

        self.assertEqual(len(gb.graph.edges), 2)
        self.assertEqual(len(gb.graph.nodes), 3)

        layers = gb.graph.layers
        self.assertSequenceEqual(layers[0], [node0])

        self.assertEqual(len(layers[1]), 1)
        splitNode = layers[1][0]
        self.assertEqual(splitNode.type, NodeType.LONG_EDGE)
        self.assertEqual(len(splitNode.west), 1)
        self.assertEqual(len(splitNode.east), 1)

        self.assertSequenceEqual(layers[2], [node1])


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(AbstractBarycenterPortDistributorTC('test_distributePortsOfGraph_GivenInLayerEdgePortOrderCrossing_ShouldRemoveIt'))
    suite.addTest(unittest.makeSuite(LongEdgeSplitterTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)