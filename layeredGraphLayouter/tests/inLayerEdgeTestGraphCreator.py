from layeredGraphLayouter.tests.testGraphCreator import TestGraphCreator
from layeredGraphLayouter.containers.lGraph import LGraph
from layeredGraphLayouter.containers.constants import PortSide


class InLayerEdgeTestGraphCreator(TestGraphCreator):
    """
    :note: Ported from ELK.
    """

    def getInLayerEdgesGraphWithCrossingsToBetweenLayerEdgeWithFixedPortOrder(self) -> LGraph:
        """"
        ____   _____
        |  |---|   |
        |  |---|   |
        |  |   |   |
        |  |  /|   |
        |__|--+|___|
              |
              \
               *

        :return: Graph of the form above.
        """
        layers = self.makeLayers(2)

        leftNode = self.addNodeToLayer(layers[0])
        rightNodes = self.addNodesToLayer(2, layers[1])

        self.setPortOrderFixed(rightNodes[0])

        # since we expect bottom up ordering of western ports, the order of
        # adding edges is
        # important
        self.eastWestEdgeFromTo(leftNode, rightNodes[0])
        self.addInLayerEdge(rightNodes[0], rightNodes[1], PortSide.WEST)
        self.eastWestEdgeFromTo(leftNode, rightNodes[0])
        self.eastWestEdgeFromTo(leftNode, rightNodes[0])
        return self.graph

    def getInLayerEdgesWithFixedPortOrderAndNormalEdgeCrossings(self) -> LGraph:
        """"
              ___
           ---| |
           |  | |  <- switch this
        ---+--|_|
        |  |
        *--|--*  <- with this
           |
           ---*

        With fixed Port PortOrder.

        :return: Graph of the form above.
        """
        layer = self.makeLayers(2)
        leftNode = self.addNodeToLayer(layer[0])
        rightNodes = self.addNodesToLayer(3, layer[1])
        self.setFixedOrderConstraint(rightNodes[0])
        self.eastWestEdgeFromTo(leftNode, rightNodes[0])
        self.addInLayerEdge(rightNodes[0], rightNodes[2], PortSide.WEST)
        self.eastWestEdgeFromTo(leftNode, rightNodes[1])

        return self.graph

    def getInLayerEdgesCrossingsButNoFixedOrder(self) -> LGraph:
        """"
            ____
           /|  |
        *-+-|__|
          | ____
        *-+-|  |
           \|__|

        Port order not fixed.

        :return: Graph of the form above.
        """
        layer = self.makeLayers(2)
        leftNodes = self.addNodesToLayer(2, layer[0])
        rightNodes = self.addNodesToLayer(2, layer[1])

        self.eastWestEdgeFromTo(leftNodes[0], rightNodes[0])
        self.addInLayerEdge(rightNodes[0], rightNodes[1], PortSide.WEST)
        self.eastWestEdgeFromTo(leftNodes[1], rightNodes[1])

        return self.graph

    def getInLayerEdgesCrossingsNoFixedOrderNoEdgeBetweenUpperAndLower(self) -> LGraph:
        """"
             *
          //
        *-++-*
          || ____
        *-++-|  |
           \\|  |
             |__|

        Port order not fixed.

        :return: Graph of the form above.
        """
        layer = self.makeLayers(2)
        leftNodes = self.addNodesToLayer(2, layer[0])
        rightNodes = self.addNodesToLayer(3, layer[1])

        self.eastWestEdgeFromTo(leftNodes[1], rightNodes[1])
        self.addInLayerEdge(rightNodes[0], rightNodes[2], PortSide.WEST)
        self.addInLayerEdge(rightNodes[0], rightNodes[2], PortSide.WEST)
        self.eastWestEdgeFromTo(leftNodes[1], rightNodes[2])

        return self.graph

    def getInLayerEdgesCrossingsNoFixedOrderNoEdgeBetweenUpperAndLowerUpsideDown(self) -> LGraph:
        """"
             *
            /____
            \|  |
           //|  |
        *-++-|  |
          || |__|
          ||
        *-++-*
           \\
             *

        Port order not fixed.

        :return: Graph of the form above.
        """
        layer = self.makeLayers(2)
        leftNodes = self.addNodesToLayer(2, layer[0])
        rightNodes = self.addNodesToLayer(4, layer[1])

        self.eastWestEdgeFromTo(leftNodes[0], rightNodes[1])
        self.addInLayerEdge(rightNodes[0], rightNodes[1], PortSide.WEST)
        self.addInLayerEdge(rightNodes[1], rightNodes[3], PortSide.WEST)
        self.addInLayerEdge(rightNodes[1], rightNodes[3], PortSide.WEST)
        self.eastWestEdgeFromTo(leftNodes[1], rightNodes[2])

        return self.graph

    def getInLayerCrossingsOnBothSides(self) -> LGraph:
        """"
          --*--
          |   |
        *-+-*-+-*
          |   |
          --*--

        :return: self.graph of the form above
        """
        layers = self.makeLayers(3)
        leftNode = self.addNodeToLayer(layers[0])
        middleNodes = self.addNodesToLayer(3, layers[1])
        rightNode = self.addNodeToLayer(layers[2])

        self.addInLayerEdge(middleNodes[0], middleNodes[2], PortSide.EAST)
        self.addInLayerEdge(middleNodes[0], middleNodes[2], PortSide.WEST)
        self.eastWestEdgeFromTo(middleNodes[1], rightNode)
        self.eastWestEdgeFromTo(leftNode, middleNodes[1])
        return self.graph

    def getInLayerEdgesFixedPortOrderInLayerAndInBetweenLayerCrossing(self) -> LGraph:
        """"
          --*
          | ____
          |/|  |
          /\|  |
          | |  |
        *-+-|__|
          |
           \
            *

        Port order fixed.

        :return: Graph of the form above.
        """
        layers = self.makeLayers(2)
        leftNode = self.addNodeToLayer(layers[0])
        rightNodes = self.addNodesToLayer(3, layers[1])

        self.setFixedOrderConstraint(rightNodes[1])

        self.eastWestEdgeFromTo(leftNode, rightNodes[1])
        self.addInLayerEdge(rightNodes[0], rightNodes[1], PortSide.WEST)
        self.addInLayerEdge(rightNodes[1], rightNodes[2], PortSide.WEST)

        return self.graph

    def getInLayerEdgesFixedPortOrderInLayerCrossing(self) -> LGraph:
        """"
          --*
          | ____
          |/|  |
          /\|  |
          | |  |
          | |__|
          |
           \
            *

        Port order fixed.

        :return: Graph of the form above.
        """
        nodes = self.addNodesToLayer(3, self.makeLayer())

        self.setFixedOrderConstraint(nodes[1])

        self.addInLayerEdge(nodes[0], nodes[1], PortSide.WEST)
        self.addInLayerEdge(nodes[1], nodes[2], PortSide.WEST)

        return self.graph

    def getFixedPortOrderTwoInLayerEdgesCrossEachOther(self) -> LGraph:
        """"
            ____
           /|  |
          / |  |
        --+-|  |
        | | |__|
        | |
        \  \
         \  *
          \
            *

        Port order fixed.

        :return: Graph of the form above.
        """
        nodes = self.addNodesToLayer(3, self.makeLayer())

        self.setFixedOrderConstraint(nodes[0])

        self.addInLayerEdge(nodes[0], nodes[2], PortSide.WEST)
        self.addInLayerEdge(nodes[0], nodes[1], PortSide.WEST)

        return self.graph

    def getInLayerEdgesDownwardGraphNoFixedOrder(self) -> LGraph:
        """"
          --*
          | ____
          |/|  |
          /\|  |
          | |  |
        *-+-|__|
          |
           \
            *

        Port order not fixed.

        :return: Graph of the form above.
        """
        layers = self.makeLayers(2)
        leftNode = self.addNodeToLayer(layers[0])
        rightNodes = self.addNodesToLayer(3, layers[1])

        self.eastWestEdgeFromTo(leftNode, rightNodes[1])
        self.addInLayerEdge(rightNodes[0], rightNodes[1], PortSide.WEST)
        self.addInLayerEdge(rightNodes[1], rightNodes[2], PortSide.WEST)

        return self.graph

    def getInLayerEdgesMultipleEdgesIntoSinglePort(self) -> LGraph:
        """"
           --*
           |
           |/*
          /|
        *+--*  <-In-layer and normal edge into port.
          \
           \
            \
             *

        :return: Graph of the form above.
        """
        layerTwo = self.makeLayer(self.graph)
        leftNode = self.addNodeToLayer(layerTwo)
        layerOne = self.makeLayer(self.graph)
        rightNodes = self.addNodesToLayer(4, layerOne)

        self.addInLayerEdge(rightNodes[1], rightNodes[3], PortSide.WEST)

        leftPort = self.addPortOnSide(leftNode, PortSide.EAST)
        rightTopPort = self.addPortOnSide(rightNodes[0], PortSide.WEST)
        rightMiddlePort = self.addPortOnSide(rightNodes[2], PortSide.WEST)
        self.addEdgeBetweenPorts(leftPort, rightMiddlePort)
        self.addEdgeBetweenPorts(rightTopPort, rightMiddlePort)
        return self.graph

    def getOneLayerWithInLayerCrossings(self) -> LGraph:
        """"
          --*
          |
          |/*
         /|
        | --*
         \
          \
           \
            *

        :return: Graph of the form above.
        """
        layer = self.makeLayer()
        nodes = self.addNodesToLayer(4, layer)
        self.addInLayerEdge(nodes[0], nodes[2], PortSide.WEST)
        self.addInLayerEdge(nodes[1], nodes[3], PortSide.WEST)
        return self.graph

    def getInLayerOneLayerNoCrossings(self) -> LGraph:
        """"
        |---*
        |
        | --*
        | |
        | --*
         \
          \
           \
            *

        :return: Graph of the form above.
        """
        layer = self.makeLayer(self.graph)
        nodes = self.addNodesToLayer(4, layer)
        self.addInLayerEdge(nodes[0], nodes[3], PortSide.WEST)
        self.addInLayerEdge(nodes[1], nodes[2], PortSide.WEST)
        return self.graph
