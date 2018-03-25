import unittest
from layeredGraphLayouter.tests.testGraphCreator import TestGraphCreator


class LayerTC(unittest.TestCase):
    def setUp(self):
        self.gb = TestGraphCreator()
        self.random = self.gb.random


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(AbstractBarycenterPortDistributorTC('test_distributePortsOfGraph_GivenInLayerEdgePortOrderCrossing_ShouldRemoveIt'))
    suite.addTest(unittest.makeSuite(LayerTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)