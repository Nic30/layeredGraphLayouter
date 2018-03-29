#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import unittest

from layeredGraphLayouter.tests.crossing.abstractBarycenterPortDistributor_test import AbstractBarycenterPortDistributorTC
from layeredGraphLayouter.tests.crossing.barycenterHeuristic_test import BarycenterHeuristicTC
from layeredGraphLayouter.tests.crossing.binaryIndexedTree_test import BinaryIndexedTreeTC
from layeredGraphLayouter.tests.crossing.crossingCounter_test import CrossingsCounterTC
from layeredGraphLayouter.tests.crossing.layerSweepCrossingMinimizer_test import LayerSweepCrossingMinimizerTC
from layeredGraphLayouter.tests.cycleBreaker_test import CycleBreakerTC
from layeredGraphLayouter.tests.edgeManipulators.longEdgeSplitter_test import LongEdgeSplitterTC
from layeredGraphLayouter.tests.layer_test import LayerTC


TCS = [
    CycleBreakerTC,
    LayerTC,

    BinaryIndexedTreeTC,
    AbstractBarycenterPortDistributorTC,
    BarycenterHeuristicTC,
    CrossingsCounterTC,
    LongEdgeSplitterTC,
    LayerSweepCrossingMinimizerTC,
]

if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(AbstractBarycenterPortDistributorTC('test_distributePortsOfGraph_GivenInLayerEdgePortOrderCrossing_ShouldRemoveIt'))
    for tc in TCS:
        suite.addTest(unittest.makeSuite(tc))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
