import unittest

from layeredGraphLayouter.greedyCycleBreaker import GreedyCycleBreaker
from layeredGraphLayouter.tests.testGraphCreator import TestGraphCreator


class CycleBreakerTC(unittest.TestCase):
    def setUp(self):
        self.gb = TestGraphCreator()
        self.random = self.gb.random
        self.cb = GreedyCycleBreaker()

    def test_direct(self):
        """
        ____     ____
        |__|---->|__|
        """
        gb = self.gb
        leftNode = gb.addNodeToLayer(gb.makeLayer())
        rightNode = gb.addNodeToLayer(gb.makeLayer())
        e = gb.eastWestEdgeFromTo(leftNode, rightNode)

        self.assertFalse(e.reversed)
        self.cb.process(gb.graph)
        self.assertFalse(e.reversed)

    def test_direct_back(self):
        """
        ____     ____
        |__|<----|__|
        """
        gb = self.gb
        leftNode = gb.addNodeToLayer(gb.makeLayer())
        rightNode = gb.addNodeToLayer(gb.makeLayer())
        e = gb.eastWestEdgeFromTo(rightNode, leftNode)

        self.assertFalse(e.reversed)
        self.cb.process(gb.graph)
        self.assertFalse(e.reversed)

    def test_direct_circle(self):
        """
        ____     ____
        |  |---->|  |
        |__|<----|__|
        """

        gb = self.gb
        leftNode = gb.addNodeToLayer(gb.makeLayer())
        rightNode = gb.addNodeToLayer(gb.makeLayer())
        e0 = gb.eastWestEdgeFromTo(leftNode, rightNode)
        e1 = gb.eastWestEdgeFromTo(rightNode, leftNode)

        self.cb.process(gb.graph)
        self.assertTrue(e0.reversed)
        self.assertFalse(e1.reversed)

    def test_3_circle_direct(self):
        """
        ____     ____      ____
        |  |---->|  |----->|  |
        |__|<----|__|      |__|
        """

        gb = self.gb
        leftNode = gb.addNodeToLayer(gb.makeLayer())
        centerNode = gb.addNodeToLayer(gb.makeLayer())
        rightNode = gb.addNodeToLayer(gb.makeLayer())
        e0 = gb.eastWestEdgeFromTo(leftNode, centerNode)
        e1 = gb.eastWestEdgeFromTo(centerNode, leftNode)
        e2 = gb.eastWestEdgeFromTo(centerNode, rightNode)

        self.cb.process(gb.graph)
        self.assertTrue(e0.reversed)
        self.assertFalse(e1.reversed)
        self.assertFalse(e2.reversed)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    #suite.addTest(CycleBreakerTC('test_direct_circle'))
    suite.addTest(unittest.makeSuite(CycleBreakerTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
