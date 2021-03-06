from random import Random
from typing import List, Union
from layeredGraphLayouter.containers.lGraph import LGraph, LNodeLayer
from layeredGraphLayouter.containers.constants import EdgeRouting, PortSide, PortConstraints,\
    NodeType
from layeredGraphLayouter.containers.lNode import LNode
from layeredGraphLayouter.containers.lEdge import LEdge
from layeredGraphLayouter.containers.lPort import LPort
from layeredGraphLayouter.tests.exampleGraphsSimple import create_dualPortCross_post,\
    create_simpleCross, create_quadEdgeCross


class MockRandom(Random):
    def __init__(self):
        self.current = 0
        self.changeBy = 0.0001
        self.nextBoolean = True

    def getrandbits(self, cnt):
        assert cnt == 1
        return int(self.nextBoolean)

    def random(self):
        self.current += self.changeBy
        return self.current

    def setNextBoolean(self, nextBoolean):
        self.nextBoolean = nextBoolean

    def setChangeBy(self, changeBy):
        self.changeBy = changeBy

    def setCurrent(self, current):
        self.current = current


class TestGraphCreator():
    """
    Use to create test graphs.
    :attention: Layout algorithm assumes the ports to be
        ordered in a clockwise manner. You must think about this yourself when
        constructing a test graph. This means that the methods for creating edges
        cannot be used in every case.
    [TODO] consider moving all downward into base
    """

    def __init__(self):
        self.portId = 0
        self.nodeId = 0
        self.edgeId = 0
        self.random = MockRandom()
        self.graph = LGraph()
        self.setUpGraph(self.graph)

    def getGraph(self, graph):
        self.setUpGraph(graph)
        return graph

    def setUpGraph(self, g: LGraph):
        g.edgeRouting = EdgeRouting.ORTHOGONAL
        g.random = self.random
        return g

    def getEmptyGraph(self) -> LGraph:
        """
        Creates empty graph.

        :return: empty graph
        """
        graph = LGraph()
        self.setUpGraph(graph)
        return graph

    def getTwoNodesNoConnectionGraph(self) -> LGraph:
        """
        Creates two nodes with no connection between them.

        :return: graph with two nodes with no connection between them.
        """
        layer = self.makeLayer()
        self.addNodeToLayer(layer)
        self.addNodeToLayer(layer)
        return self.graph

    def getCrossFormedGraph(self):
        """
        *  *
         \/
         /\
        *  *

        :return: Graph of the form above.
        """
        return create_simpleCross(self)

    def multipleEdgesAndSingleEdge(self) -> LGraph:
        """
        *
         \\
          \\
        *---*

        :return: Graph of the form above.
        """
        makeLayer = self.makeLayer
        addNodeToLayer = self.addNodeToLayer
        eastWestEdgeFromTo = self.eastWestEdgeFromTo
        graph = self.graph

        leftLayer = makeLayer(graph)
        rightLayer = makeLayer(graph)

        topLeft = addNodeToLayer(leftLayer)
        bottomLeft = addNodeToLayer(leftLayer)
        bottomRight = addNodeToLayer(rightLayer)

        eastWestEdgeFromTo(topLeft, bottomRight)
        eastWestEdgeFromTo(topLeft, bottomRight)
        eastWestEdgeFromTo(bottomLeft, bottomRight)
        return graph

    def getCrossFormedGraphWithConstraintsInSecondLayer(self):
        """
        *  *  <- this node must be ...
         \/
         /\
        *  *  <- before this node.

        :return: Graph of the form above.
        """
        self.getCrossFormedGraph()
        layerOne = self.graph.layers[1]
        topNode = layerOne[0]
        secondNode = layerOne[1]
        self.setInLayerOrderConstraint(topNode, secondNode)

        return self.graph

    def getCrossFormedGraphConstraintsPreventAnySwitch(self):
        """
        this node must be.. -> *  *  <- and this node must be ...
                                \/
                                /\
           before this node -> *  *  <- before this node.

        :return: Graph of the form above.
        """
        makeLayer = self.makeLayer
        addNodeToLayer = self.addNodeToLayer
        eastWestEdgeFromTo = self.eastWestEdgeFromTo
        graph = self.graph
        setInLayerOrderConstraint = self.setInLayerOrderConstraint

        leftLayer = makeLayer(graph)
        rightLayer = makeLayer(graph)

        topLeft = addNodeToLayer(leftLayer)
        bottomLeft = addNodeToLayer(leftLayer)
        topRight = addNodeToLayer(rightLayer)
        bottomRight = addNodeToLayer(rightLayer)

        eastWestEdgeFromTo(topLeft, bottomRight)
        eastWestEdgeFromTo(bottomLeft, topRight)
        setInLayerOrderConstraint(topRight, bottomRight)
        setInLayerOrderConstraint(topLeft, bottomLeft)

        return graph

    def getOneNodeGraph(self):
        """
        Creates graph with only one node.

        :return: graph with only one node.
        """
        layer = self.makeLayer()
        self.addNodeToLayer(layer)

        return self.graph

    def getInLayerEdgesGraph(self):
        """
          --*
          |
        *-+-*-*
          |
          --*

        :return: graph of the form above
        """
        graph = self.graph
        makeLayer = self.makeLayer
        addNodeToLayer = self.addNodeToLayer
        eastWestEdgeFromTo = self.eastWestEdgeFromTo
        leftLayer = makeLayer(graph)
        middleLayer = makeLayer(graph)
        rightLayer = makeLayer(graph)

        leftNode = addNodeToLayer(leftLayer)
        middleNodes = self.addNodesToLayer(3, middleLayer)
        rightNode = addNodeToLayer(rightLayer)

        # add east side ports first to get expected port ordering
        eastWestEdgeFromTo(middleNodes[1], rightNode)
        eastWestEdgeFromTo(leftNode, middleNodes[1])
        self.addInLayerEdge(middleNodes[0], middleNodes[2], PortSide.WEST)

        return graph

    def getInLayerEdgesGraphWhichResultsInCrossingsWhenSwitched(self):
        """
          --*
          |
          --*

         *--*

        :return: graph of the form above
        """
        graph = self.graph
        makeLayer = self.makeLayer
        addNodeToLayer = self.addNodeToLayer
        addNodesToLayer = self.addNodesToLayer

        leftLayer = makeLayer(graph)
        rightLayer = makeLayer(graph)

        leftNode = addNodeToLayer(leftLayer)
        rightNodes = addNodesToLayer(3, rightLayer)

        self.addInLayerEdge(rightNodes[0], rightNodes[1], PortSide.WEST)
        self.eastWestEdgeFromTo(leftNode, rightNodes[2])

        return graph

    def getMultipleEdgesBetweenSameNodesGraph(self):
        """
        Constructs a cross formed graph with two edges between the corners

        *    *
         \\//
         //\\
        *    *

        :return: Graph of the form above.
        """
        return create_quadEdgeCross(self)

    def getCrossWithExtraEdgeInBetweenGraph(self):
        """
        *   *
         \ /
        *-+-*
         / \
        *   *
        .
        </pre>

        :return: graph of the form above
        """
        graph = self.graph
        makeLayer = self.makeLayer
        eastWestEdgeFromTo = self.eastWestEdgeFromTo
        addNodesToLayer = self.addNodesToLayer

        leftLayer = makeLayer()
        rightLayer = makeLayer()

        leftNodes = addNodesToLayer(3, leftLayer)
        rightNodes = addNodesToLayer(3, rightLayer)

        eastWestEdgeFromTo(leftNodes[0], rightNodes[2])
        eastWestEdgeFromTo(leftNodes[1], rightNodes[1])
        eastWestEdgeFromTo(leftNodes[2], rightNodes[0])

        return graph

    def getCrossWithManySelfLoopsGraph(self) -> LGraph:
        """
        Cross formed graph, but each node has three extra self loop edges.

        *  *
         \/
         /\
        *  *

        :return: Graph of the form above.
        """
        graph = self.graph
        makeLayer = self.makeLayer
        addNodeToLayer = self.addNodeToLayer
        addPortOnSide = self.addPortOnSide
        selfLoopOn = self.selfLoopOn
        addEdgeBetweenPorts = self.addEdgeBetweenPorts

        leftLayer = makeLayer()
        rightLayer = makeLayer()

        topLeft = addNodeToLayer(leftLayer)
        bottomLeft = addNodeToLayer(leftLayer)
        topRight = addNodeToLayer(rightLayer)
        bottomRight = addNodeToLayer(rightLayer)

        topLeftPort = addPortOnSide(topLeft, PortSide.EAST)
        bottomLeftPort = addPortOnSide(bottomLeft, PortSide.EAST)

        selfLoopCrossGraph = graph
        for layer in selfLoopCrossGraph.layers:
            for node in layer:
                for _ in range(3):
                    selfLoopOn(node, PortSide.EAST)
                for _ in range(3):
                    selfLoopOn(node, PortSide.WEST)

        topRightPort = addPortOnSide(topRight, PortSide.WEST)
        bottomRightPort = addPortOnSide(bottomRight, PortSide.WEST)

        addEdgeBetweenPorts(topLeftPort, bottomRightPort)
        addEdgeBetweenPorts(bottomLeftPort, topRightPort)
        return selfLoopCrossGraph

    def selfLoopOn(self, node: LNode, side: PortSide) -> None:
        """
        Test for self loop.
        """
        self.addEdgeBetweenPorts(
            self.addPortOnSide(node, side),
            self.addPortOnSide(node, side))

    def getMoreComplexThreeLayerGraph(self):
        """
        *\  --*
          \/ /
        *-*===*
         + /
        * * --*

        :return: Graph of the form above.
        """
        makeLayer = self.makeLayer
        graph = self.graph
        addNodesToLayer = self.addNodesToLayer
        addPortOnSide = self.addPortOnSide
        addEdgeBetweenPorts = self.addEdgeBetweenPorts
        eastWestEdgeFromTo = self.eastWestEdgeFromTo

        leftLayer = makeLayer()
        middleLayer = makeLayer()
        rightLayer = makeLayer()

        leftNodes = addNodesToLayer(3, leftLayer)
        middleNodes = addNodesToLayer(2, middleLayer)
        rightNodes = addNodesToLayer(3, rightLayer)

        leftMiddleNodePort = addPortOnSide(leftNodes[1], PortSide.EAST)
        middleLowerNodePortEast = addPortOnSide(middleNodes[1], PortSide.EAST)
        middleUpperNodePortEast = addPortOnSide(middleNodes[0], PortSide.EAST)
        rightUpperNodePort = addPortOnSide(rightNodes[0], PortSide.WEST)
        rightMiddleNodePort = addPortOnSide(rightNodes[1], PortSide.WEST)

        addEdgeBetweenPorts(middleUpperNodePortEast, rightUpperNodePort)
        addEdgeBetweenPorts(middleUpperNodePortEast, rightMiddleNodePort)
        addEdgeBetweenPorts(middleUpperNodePortEast, rightMiddleNodePort)
        eastWestEdgeFromTo(middleLowerNodePortEast, rightNodes[2])
        eastWestEdgeFromTo(leftMiddleNodePort, middleNodes[0])
        eastWestEdgeFromTo(middleNodes[1], rightUpperNodePort)
        eastWestEdgeFromTo(leftMiddleNodePort, middleNodes[1])
        eastWestEdgeFromTo(leftNodes[2], middleNodes[0])
        eastWestEdgeFromTo(leftNodes[0], middleNodes[0])

        return graph

    def getFixedPortOrderGraph(self):
        """
        ____  *
        |  |\/
        |__|/\
              *

        Port order fixed.

        :return: Graph of the form above.
        """
        return create_dualPortCross_post(self, fixedNodes=True)

    def getGraphNoCrossingsDueToPortOrderNotFixed(self):
        """
        ____  *
        |  |\/
        |__|/\
              *

        Port order not fixed

        :return: Graph of the form above.
        """
        return create_dualPortCross_post(self, fixedNodes=False)

    def getSwitchOnlyOneSided(self):
        """
        *  *---*
         \/
         /\
        *  *---*

        :return: Graph of the form above.
        """
        graph = self.graph
        makeLayers = self.makeLayers
        addNodesToLayer = self.addNodesToLayer
        eastWestEdgeFromTo = self.eastWestEdgeFromTo

        layers = makeLayers(3)

        leftNodes = addNodesToLayer(2, layers[0])
        middleNodes = addNodesToLayer(2, layers[1])
        rightNodes = addNodesToLayer(2, layers[2])

        eastWestEdgeFromTo(middleNodes[0], rightNodes[0])
        eastWestEdgeFromTo(middleNodes[1], rightNodes[1])
        eastWestEdgeFromTo(leftNodes[0], middleNodes[1])
        eastWestEdgeFromTo(leftNodes[1], middleNodes[0])

        return graph

    def getSwitchOnlyEastOneSided(self):
        """
        *--*  *
            \/
            /\
        *--*  *

        :return: Graph of the form above.
        """
        graph = self.graph
        makeLayers = self.makeLayers
        addNodesToLayer = self.addNodesToLayer
        eastWestEdgeFromTo = self.eastWestEdgeFromTo

        layers = makeLayers(3)

        leftNodes = addNodesToLayer(2, layers[0])
        middleNodes = addNodesToLayer(2, layers[1])
        rightNodes = addNodesToLayer(2, layers[2])

        eastWestEdgeFromTo(leftNodes[0], middleNodes[0])
        eastWestEdgeFromTo(leftNodes[1], middleNodes[1])
        eastWestEdgeFromTo(middleNodes[0], rightNodes[1])
        eastWestEdgeFromTo(middleNodes[1], rightNodes[0])

        return graph

    def getFixedPortOrderInLayerEdgesDontCrossEachOther(self):
        """
        ____
        |  |----
        |__|\  |
        ____ | |
        |  |/  |
        |__|---|

        Port order fixed.

        :return: Graph of the form above.
        """
        graph = self.graph
        makeLayer = self.makeLayer
        addNodesToLayer = self.addNodesToLayer
        addEdgeBetweenPorts = self.addEdgeBetweenPorts
        addPortOnSide = self.addPortOnSide
        setFixedOrderConstraint = self.setFixedOrderConstraint

        layer = makeLayer(graph)
        nodes = addNodesToLayer(2, layer)
        setFixedOrderConstraint(nodes[0])
        setFixedOrderConstraint(nodes[1])
        # must add ports and edges manually, due to clockwise port ordering
        upperPortUpperNode = addPortOnSide(nodes[0], PortSide.EAST)
        lowerPortUpperNode = addPortOnSide(nodes[0], PortSide.EAST)
        upperPortLowerNode = addPortOnSide(nodes[1], PortSide.EAST)
        lowerPortLowerNode = addPortOnSide(nodes[1], PortSide.EAST)
        addEdgeBetweenPorts(upperPortUpperNode, lowerPortLowerNode)
        addEdgeBetweenPorts(lowerPortUpperNode, upperPortLowerNode)

        return graph

    def getFixedPortOrderInLayerEdgesWithCrossings(self):
        """
        ____
        |  |----
        |__|\  |
        ____ | |
        |  |-+--
        |__|-|

        Port order fixed.

        :return: Graph of the form above.
        """
        graph = self.graph
        makeLayer = self.makeLayer
        addNodesToLayer = self.addNodesToLayer
        addInLayerEdge = self.addInLayerEdge
        setFixedOrderConstraint = self.setFixedOrderConstraint

        layer = makeLayer(graph)
        nodes = addNodesToLayer(2, layer)
        setFixedOrderConstraint(nodes[0])
        setFixedOrderConstraint(nodes[1])
        addInLayerEdge(nodes[0], nodes[1], PortSide.EAST)
        addInLayerEdge(nodes[0], nodes[1], PortSide.EAST)

        return graph

    def getMoreComplexInLayerGraph(self):
        """
             ____
           / |  |
        *-+--|  |\
          | /|  |-+-*
        *-++-|__| |
          ||      |
          || ___  |
          | \| | /
        *-+--| |/
        *-+--|_|
           \
            \
             *

        Port order fixed.

        :return: Graph of the form above.
        """
        makeLayers = self.makeLayers
        addNodesToLayer = self.addNodesToLayer
        addNodeToLayer = self.addNodeToLayer
        eastWestEdgeFromTo = self.eastWestEdgeFromTo
        addInLayerEdge = self.addInLayerEdge
        setFixedOrderConstraint = self.setFixedOrderConstraint

        layers = makeLayers(3)
        leftNodes = addNodesToLayer(4, layers[0])
        middleNodes = addNodesToLayer(3, layers[1])
        rightNode = addNodeToLayer(layers[2])
        setFixedOrderConstraint(middleNodes[0])
        setFixedOrderConstraint(middleNodes[1])

        eastWestEdgeFromTo(leftNodes[1], middleNodes[0])

        eastWestEdgeFromTo(leftNodes[3], middleNodes[1])
        eastWestEdgeFromTo(leftNodes[2], middleNodes[1])
        addInLayerEdge(middleNodes[0], middleNodes[1], PortSide.WEST)
        eastWestEdgeFromTo(leftNodes[0], middleNodes[0])
        addInLayerEdge(middleNodes[0], middleNodes[2], PortSide.WEST)

        addInLayerEdge(middleNodes[0], middleNodes[1], PortSide.EAST)
        eastWestEdgeFromTo(middleNodes[0], rightNode)

        return self.graph

    def getGraphWhichCouldBeWorsenedBySwitch(self):
        """
        *==*  *
            \/
            /\
        *==*  *

        First Layer and last layer in fixed order.

        :return: graph of the form above.
        """
        makeLayers = self.makeLayers
        addNodesToLayer = self.addNodesToLayer
        eastWestEdgeFromTo = self.eastWestEdgeFromTo
        setInLayerOrderConstraint = self.setInLayerOrderConstraint

        layers = makeLayers(3)
        leftNodes = addNodesToLayer(2, layers[0])
        middleNodes = addNodesToLayer(2, layers[1])
        rightNodes = addNodesToLayer(2, layers[2])

        setInLayerOrderConstraint(leftNodes[0], leftNodes[1])
        setInLayerOrderConstraint(rightNodes[0], rightNodes[1])

        eastWestEdgeFromTo(middleNodes[0], rightNodes[1])
        eastWestEdgeFromTo(middleNodes[1], rightNodes[0])
        eastWestEdgeFromTo(leftNodes[0], middleNodes[0])
        eastWestEdgeFromTo(leftNodes[0], middleNodes[0])
        eastWestEdgeFromTo(leftNodes[1], middleNodes[1])
        eastWestEdgeFromTo(leftNodes[1], middleNodes[1])

        return self.graph

    def getNodesInDifferentLayoutUnitsPreventSwitch(self):
        """
            * <-- this ...
           /
        *-+-* <-- cannot switch with this
         / _|__
        *  |  |
           |__|

        :return: graph of the form above.
        """
        makeLayers = self.makeLayers
        addNodesToLayer = self.addNodesToLayer
        eastWestEdgeFromTo = self.eastWestEdgeFromTo
        addNorthSouthEdge = self.addNorthSouthEdge

        layers = makeLayers(2)
        leftNodes = addNodesToLayer(2, layers[0])
        rightNodes = addNodesToLayer(3, layers[1])

        eastWestEdgeFromTo(leftNodes[0], rightNodes[1])

        addNorthSouthEdge(
            PortSide.EAST, rightNodes[2], rightNodes[1], leftNodes[0], True)

        rightNodes[1].inLayerLayoutUnit = rightNodes[2]
        rightNodes[2].inLayerLayoutUnit = rightNodes[2]

        return self.graph

    def multipleInBetweenLayerEdgesIntoNodeWithNoFixedPortOrder(self):
        """
         ---*
         |
         | ____
        *+-|  |
        *+-|  |
          \|__|
        Port order not fixed.

        :return: Graph of the form above.
        """
        graph = self.graph
        makeLayer = self.makeLayer
        addNodesToLayer = self.addNodesToLayer
        eastWestEdgeFromTo = self.eastWestEdgeFromTo

        leftLayer = makeLayer(graph)
        leftNodes = addNodesToLayer(2, leftLayer)
        rightLayer = makeLayer(graph)
        rightNodes = addNodesToLayer(2, rightLayer)

        self.addInLayerEdge(rightNodes[0], rightNodes[1], PortSide.WEST)
        eastWestEdgeFromTo(leftNodes[0], rightNodes[1])
        eastWestEdgeFromTo(leftNodes[0], rightNodes[1])

        return graph

    def multipleInBetweenLayerEdgesIntoNodeWithNoFixedPortOrderCauseCrossings(self):
        """
         ---*
         |
         | ____
        *+-|  |
        *+-|  |
         | |__|
          \
           *
        Port order not fixed.

        :return: Graph of the form above.
        """
        graph = self.graph
        makeLayer = self.makeLayer
        addNodesToLayer = self.addNodesToLayer
        eastWestEdgeFromTo = self.eastWestEdgeFromTo

        leftLayer = makeLayer(graph)
        leftNodes = addNodesToLayer(2, leftLayer)
        rightLayer = makeLayer(graph)
        rightNodes = addNodesToLayer(3, rightLayer)

        self.addInLayerEdge(rightNodes[0], rightNodes[2], PortSide.WEST)
        eastWestEdgeFromTo(leftNodes[0], rightNodes[1])
        eastWestEdgeFromTo(leftNodes[0], rightNodes[1])

        return graph

    def getSwitchedProblemGraph(self):
        """
        *----*
         \\
          \--*
           --*
        *---/
         \---*

        :return: Graph of the form above.
        """
        graph = self.graph
        makeLayer = self.makeLayer
        addNodesToLayer = self.addNodesToLayer
        eastWestEdgeFromTo = self.eastWestEdgeFromTo

        leftNodes = addNodesToLayer(2, makeLayer(graph))
        rightNodes = addNodesToLayer(4, makeLayer(graph))

        eastWestEdgeFromTo(leftNodes[1], rightNodes[2])
        eastWestEdgeFromTo(leftNodes[1], rightNodes[3])

        eastWestEdgeFromTo(leftNodes[0], rightNodes[0])
        eastWestEdgeFromTo(leftNodes[0], rightNodes[1])
        eastWestEdgeFromTo(leftNodes[0], rightNodes[2])

        return graph

    def twoEdgesIntoSamePort(self):
        """
        *   *<- Into same port
         \//
         //\
        *   *

        :return: Graph of the form above.
        """
        graph = self.graph
        makeLayer = self.makeLayer
        eastWestEdgeFromTo = self.eastWestEdgeFromTo
        addNodeToLayer = self.addNodeToLayer
        addPortOnSide = self.addPortOnSide
        addEdgeBetweenPorts = self.addEdgeBetweenPorts

        leftLayer = makeLayer(graph)
        rightLayer = makeLayer(graph)

        topLeft = addNodeToLayer(leftLayer)
        bottomLeft = addNodeToLayer(leftLayer)
        topRight = addNodeToLayer(rightLayer)
        bottomRight = addNodeToLayer(rightLayer)

        eastWestEdgeFromTo(topLeft, bottomRight)
        bottomLeftFirstPort = addPortOnSide(bottomLeft, PortSide.EAST)
        bottomLeftSecondPort = addPortOnSide(bottomLeft, PortSide.EAST)
        topRightFirstPort = addPortOnSide(topRight, PortSide.WEST)
        topRightSecondPort = addPortOnSide(topRight, PortSide.WEST)

        addEdgeBetweenPorts(bottomLeftFirstPort, topRightFirstPort)
        addEdgeBetweenPorts(bottomLeftSecondPort, topRightSecondPort)

        return graph

    def twoEdgesIntoSamePortCrossesWhenSwitched(self):
        """
        *---* <- Into same port
          /
         /
        *---*

        :return: Graph of the form above.
        """
        graph = self.graph
        makeLayer = self.makeLayer
        eastWestEdgeFromTo = self.eastWestEdgeFromTo
        addNodeToLayer = self.addNodeToLayer
        addPortOnSide = self.addPortOnSide
        addEdgeBetweenPorts = self.addEdgeBetweenPorts

        leftLayer = makeLayer(graph)
        rightLayer = makeLayer(graph)

        topLeft = addNodeToLayer(leftLayer)
        bottomLeft = addNodeToLayer(leftLayer)
        topRight = addNodeToLayer(rightLayer)
        bottomRight = addNodeToLayer(rightLayer)

        topRightPort = addPortOnSide(topRight, PortSide.WEST)
        bottomLeftPort = addPortOnSide(bottomLeft, PortSide.EAST)
        addEdgeBetweenPorts(bottomLeftPort, topRightPort)

        topLeftPort = addPortOnSide(topLeft, PortSide.EAST)
        addEdgeBetweenPorts(topLeftPort, topRightPort)

        eastWestEdgeFromTo(bottomLeft, bottomRight)

        return graph

    def twoEdgesIntoSamePortResolvesCrossingWhenSwitched(self):
        """
        *  *
         \/
         /\
        *--*<- Into same port

        :return: Graph of the form above.
        """
        graph = self.graph
        makeLayer = self.makeLayer
        eastWestEdgeFromTo = self.eastWestEdgeFromTo
        addNodeToLayer = self.addNodeToLayer
        addPortOnSide = self.addPortOnSide
        addEdgeBetweenPorts = self.addEdgeBetweenPorts

        leftLayer = makeLayer(graph)
        rightLayer = makeLayer(graph)

        topLeft = addNodeToLayer(leftLayer)
        bottomLeft = addNodeToLayer(leftLayer)
        topRight = addNodeToLayer(rightLayer)
        bottomRight = addNodeToLayer(rightLayer)

        topLeftPort = addPortOnSide(topLeft, PortSide.EAST)
        bottomLeftPort = addPortOnSide(bottomLeft, PortSide.EAST)
        bottomRightPort = addPortOnSide(bottomRight, PortSide.WEST)

        addEdgeBetweenPorts(topLeftPort, bottomRightPort)
        addEdgeBetweenPorts(bottomLeftPort, bottomRightPort)

        eastWestEdgeFromTo(bottomLeft, topRight)

        return graph

    """
    *---* <- into same port
      /
     /
    *---*
    ^
    |
    Two edges into same port.

    :return: Graph of the form above.
     """

    def twoEdgesIntoSamePortFromEastWithFixedPortOrder(self):
        graph = self.graph
        makeLayer = self.makeLayer
        addNodeToLayer = self.addNodeToLayer
        addPortOnSide = self.addPortOnSide
        addEdgeBetweenPorts = self.addEdgeBetweenPorts
        setFixedOrderConstraint = self.setFixedOrderConstraint

        leftLayer = makeLayer(graph)
        rightLayer = makeLayer(graph)

        topLeft = addNodeToLayer(leftLayer)
        bottomLeft = addNodeToLayer(leftLayer)
        topRight = addNodeToLayer(rightLayer)
        bottomRight = addNodeToLayer(rightLayer)

        setFixedOrderConstraint(bottomLeft)
        setFixedOrderConstraint(topRight)

        topLeftPort = addPortOnSide(topLeft, PortSide.EAST)
        bottomLeftPort = addPortOnSide(bottomLeft, PortSide.EAST)
        topRightPort = addPortOnSide(topRight, PortSide.WEST)
        bottomRightPort = addPortOnSide(bottomRight, PortSide.WEST)

        addEdgeBetweenPorts(bottomLeftPort, bottomRightPort)
        addEdgeBetweenPorts(bottomLeftPort, topRightPort)
        addEdgeBetweenPorts(topLeftPort, topRightPort)

        return graph

    def getCurrentOrder(self, g: LGraph):
        """
        :return: nodes as 2d array.
        """
        nodeOrder = []
        for nodes in g.layers:
            nodeOrder.append(nodes[:])

        return nodeOrder

    def addNorthSouthEdge(self, side: PortSide,
                          nodeWithNSPorts: LNode,
                          northSouthDummy: LNode,
                          nodeWithEastWestPorts: LNode,
                          nodeWithEastWestPortsIsOrigin: bool):
        addPortOnSide = self.addPortOnSide
        addEdgeBetweenPorts = self.addEdgeBetweenPorts
        layers = nodeWithEastWestPorts.graph.layers
        i0 = layers.index(nodeWithEastWestPorts.layer)
        i1 = layers.index(nodeWithNSPorts.layer)
        normalNodeEastOfNsPortNode = i0 < i1
        direction = PortSide.WEST if normalNodeEastOfNsPortNode else PortSide.EAST

        targetNodePortSide = PortSide.opposite(direction)
        normalNodePort = addPortOnSide(
            nodeWithEastWestPorts, targetNodePortSide)

        dummyNodePort = addPortOnSide(northSouthDummy, direction)

        if nodeWithEastWestPortsIsOrigin:
            addEdgeBetweenPorts(normalNodePort, dummyNodePort)
        else:
            addEdgeBetweenPorts(dummyNodePort, normalNodePort)

        northSouthDummy.inLayerLayoutUnit = nodeWithNSPorts
        northSouthDummy.origin = nodeWithNSPorts

        self.setAsNorthSouthNode(northSouthDummy)

        originPort = addPortOnSide(nodeWithNSPorts, side)
        dummyNodePort.origin = originPort
        originPort.portDummy = northSouthDummy

        baryAssoc = [northSouthDummy, ]

        otherBaryAssocs = nodeWithNSPorts.barycenterAssociates
        if otherBaryAssocs is None:
            nodeWithNSPorts.barycenterAssociates = baryAssoc
        else:
            otherBaryAssocs.extend(baryAssoc)

        if side == PortSide.NORTH:
            northSouthDummy.inLayerSuccessorConstraint.append(nodeWithNSPorts)
        else:
            nodeWithNSPorts.inLayerSuccessorConstraint.append(northSouthDummy)

    def makeLayers(self, amount: int):
        return self.makeLayersInGraph(amount, self.graph)

    def makeLayer(self, graph=None):
        if graph is None:
            graph = self.graph
        return self.makeLayerInGraph(graph)

    @staticmethod
    def makeLayerInGraph(g: LGraph):
        layer = LNodeLayer(g)
        return layer

    def addNodeToLayer(self, layer) -> LNode:
        node = LNode(layer.graph, "%d" % len(layer.graph.nodes))
        node.type = NodeType.NORMAL
        node.inLayerLayoutUnit = node
        node.setLayer(layer)
        layer.graph.nodes.append(node)
        return node

    def eastWestEdgeFromTo(self, left: Union[LNode, LPort],
                           right: Union[LNode, LPort]) -> LEdge:
        if isinstance(left, LPort):
            leftPort = left
        else:
            leftPort = self.addPortOnSide(left, PortSide.EAST)

        if isinstance(right, LPort):
            rightPort = right
        else:
            rightPort = self.addPortOnSide(right, PortSide.WEST)

        return self.addEdgeBetweenPorts(leftPort, rightPort)

    def addEdgeBetweenPorts(self, from_: LPort, to: LPort) -> LEdge:
        edge = self.graph.add_edge(from_, to)
        return edge

    def addPortOnSide(self, node: LNode, portSide: PortSide) -> LPort:
        """
        Sets port constraints to fixed!

        :param node:
        :param portSide:
        :return: newly created port
        """
        side = node.getPortSideView(portSide)
        port = LPort(node, None, side=portSide, name="port%d" % len(side))
        side.append(port)

        if not node.portConstraints.isSideFixed():
            node.portConstraints = PortConstraints.FIXED_SIDE

        return port

    def addPortsOnSide(self, n: int, node: LNode, portSide: PortSide) -> List[LPort]:
        return [self.addPortOnSide(node, portSide) for _ in range(n)]

    def multipleEdgesIntoOnePortAndFreePortOrder(self):
        """
            ____
            |  |
        ----0  | <--- two edges into one port
        | / |  |
        | +-0  |
        |/| |__|
        ||\
        ||  *
        | \
        ----*

        Port order not fixed.

        :return: Graph of the form above.
        """
        addNodesToLayer = self.addNodesToLayer
        makeLayer = self.makeLayer
        addInLayerEdge = self.addInLayerEdge
        addPortOnSide = self.addPortOnSide
        addEdgeBetweenPorts = self.addEdgeBetweenPorts

        nodes = addNodesToLayer(3, makeLayer(self.graph))
        addInLayerEdge(nodes[0], nodes[2], PortSide.WEST)
        portUpperNode = addPortOnSide(nodes[0], PortSide.WEST)
        addEdgeBetweenPorts(
            portUpperNode, addPortOnSide(nodes[2], PortSide.WEST))
        addEdgeBetweenPorts(
            portUpperNode, addPortOnSide(nodes[1], PortSide.WEST))

        return self.graph

    def getOnlyCorrectlyImprovedByBestOfForwardAndBackwardSweepsInSingleLayer(self):
        """
        ___
        | |\    *
        | |\\  /
        |_|-++-+*
            || \
            ====*

        left Node has fixed Port Order.

        :return: Graph of the form above.
         """
        graph = self.graph
        eastWestEdgeFromTo = self.eastWestEdgeFromTo

        leftNode = self.addNodeToLayer(self.makeLayer(graph))
        self.setFixedOrderConstraint(leftNode)
        rightNodes = self.addNodesToLayer(3, self.makeLayer(graph))
        eastWestEdgeFromTo(leftNode, rightNodes[2])
        eastWestEdgeFromTo(leftNode, rightNodes[2])
        eastWestEdgeFromTo(leftNode, rightNodes[1])
        self.addInLayerEdge(rightNodes[0], rightNodes[2], PortSide.WEST)

        return graph

    def addExternalPortDummyNodeToLayer(self, layer, port: LPort):
        node = self.addNodeToLayer(layer)
        node.origin = port
        node.type = NodeType.EXTERNAL_PORT
        node.extPortSide = port.side
        port.portDummy = node
        port.insideConnections = True
        node.graph.p_externalPorts = True
        return node

    def addExternalPortDummiesToLayer(self, layer, ports: List[LPort]):
        nodes = []
        side = ports[0].side
        for i in range(len(ports)):
            portIndex = i if side == PortSide.EAST else len(ports) - 1 - i
            obj = self.addExternalPortDummyNodeToLayer(layer, ports[portIndex])
            nodes.append(obj)

        return nodes

    def nestedGraph(self, node: LNode):
        node.compoundNode = True
        nestedGraph = node.nestedLgraph
        if (nestedGraph is None):
            nestedGraph = LGraph()
            self.setUpGraph(nestedGraph)
            node.nestedLgraph = nestedGraph
            nestedGraph.parentLnode = node

        return nestedGraph

    def switchOrderOfNodesInLayer(self, nodeOne: int, nodeTwo: int, layer):
        firstNode = layer[nodeOne]
        secondNode = layer[nodeTwo]
        switchedList = list(layer)
        switchedList[nodeOne] = secondNode
        switchedList[nodeTwo] = firstNode
        return switchedList

    def copyOfNodesInLayer(self, layerIndex: int):
        return self.graph.layers[layerIndex][:]

    def copyOfSwitchOrderOfNodesInLayer(self, nodeOne: int, nodeTwo: int, layerIndex: int):
        layer = self.copyOfNodesInLayer(layerIndex)
        return self.getCopyWithSwitchedOrder(nodeOne, nodeTwo, layer)

    def eastWestEdgesFromTo(self, *args):
        if len(args) == 2:
            return self.eastWestEdgeFromTo_base(*args)
        else:
            return self.eastWestEdgesFromTo_many(*args)

    def eastWestEdgesFromTo_many(self, numberOfNodes: int, left: LNode, right: LNode):
        for _ in range(numberOfNodes):
            self.eastWestEdgeFromTo_base(left, right)

    def eastWestEdgeFromTo_base(self, left: Union[LPort, LNode], right: Union[LPort, LNode]):
        if isinstance(left, LNode):
            lPort = self.addPortOnSide(left, PortSide.EAST)
        else:
            lPort = left

        if isinstance(right, LNode):
            rPort = self.addPortOnSide(right, PortSide.WEST)
        else:
            rPort = right

        self.addEdgeBetweenPorts(lPort, rPort)

    @staticmethod
    def copyPortsInIndexOrder(node: LNode, *indices):
        res = []
        ports = list(node.iterPorts())
        for i in indices:
            res.append(ports[i])

        return res

    def setRandom(self, random: MockRandom):
        self.random = random

    @staticmethod
    def setFixedOrderConstraint(node: LNode):
        node.portConstraints = PortConstraints.FIXED_ORDER

    def setFixedOrderConstraint_many(self, nodes):
        for n in nodes:
            self.setFixedOrderConstraint(n)

    @staticmethod
    def getListCopyInIndexOrder(li: list, *_is):
        list_ = []
        for i in _is:
            list_.add(li[i])

        return list

    @staticmethod
    def getArrayInIndexOrder(arr, *_is):
        return [arr[i] for i in _is]

    @staticmethod
    def copyOfListSwitchingOrder(i: int, j: int, list_: list):
        listCopy = list_[:]
        first = listCopy[i]
        second = listCopy[j]
        listCopy[i] = second
        listCopy[j] = first
        return listCopy

    @staticmethod
    def switchOrderInArray(i: int, j: int, arr: list):
        copy_ = arr[:]
        first = arr[i]
        snd = arr[j]
        copy_[j] = first
        copy_[i] = snd
        return copy_

    @staticmethod
    def getCopyWithSwitchedOrder(nodeOne: int, nodeTwo: int, layer):
        firstNode = layer[nodeOne]
        secondNode = layer[nodeTwo]
        switchedList = layer[:]
        switchedList[nodeOne] = secondNode
        switchedList[nodeTwo] = firstNode
        return switchedList

    @staticmethod
    def setAsNorthSouthNode(node: LNode):
        node.type = NodeType.NORTH_SOUTH_PORT

    @staticmethod
    def setInLayerOrderConstraint(thisNode: LNode, beforeThisNode: LNode):
        scndNodeAsList = beforeThisNode[:]
        thisNode.inLayerSuccessorConstraint = scndNodeAsList

    @staticmethod
    def setAsLongEdgeDummy(node: LNode):
        node.type = NodeType.LONG_EDGE
        node.inLayerLayoutUnit = None

    @staticmethod
    def setPortOrderFixed(node: LNode):
        node.portConstraints = PortConstraints.FIXED_ORDER
        node.getGraph().p_nonFreePorts = True

    def makeLayersInGraph(self, amount: int, g: LGraph):
        return [self.makeLayerInGraph(g) for _ in range(amount)]

    def addInLayerEdge_NodeNodeSide(self, nodeOne: LNode, nodeTwo: LNode, portSide: PortSide):
        portOne = self.addPortOnSide(nodeOne, portSide)
        portTwo = self.addPortOnSide(nodeTwo, portSide)
        return self.addEdgeBetweenPorts(portOne, portTwo)

    def addInLayerEdge_NodePortSide(self, nodeOne: LNode, portTwo: LPort, portSide: PortSide):
        portOne = self.addPortOnSide(nodeOne, portSide)
        self.addEdgeBetweenPorts(portOne, portTwo)

    def addInLayerEdge_PortNode(self, portOne: LPort, nodeTwo: LNode):
        portSide = portOne.side
        portTwo = self.addPortOnSide(nodeTwo, portSide)
        self.addEdgeBetweenPorts(portOne, portTwo)

    def addInLayerEdge(self, *args):
        if len(args) == 2:
            return self.addInLayerEdge_PortNode(*args)
        elif isinstance(args[1], LNode):
            return self.addInLayerEdge_NodeNodeSide(*args)
        else:
            return self.addInLayerEdge_NodePortSide(*args)

    def addNodesToLayer(self, amountOfNodes: int, leftLayer: LNodeLayer):
        return [self.addNodeToLayer(leftLayer) for _ in range(amountOfNodes)]

    def iterAllGraphs(self, root: LGraph):
        yield root

        for node in root.nodes:
            if node.nestedLgraph:
                yield from self.iterAllGraphs(node.nestedLgraph)
