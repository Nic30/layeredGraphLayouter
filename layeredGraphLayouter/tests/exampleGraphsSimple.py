from layeredGraphLayouter.containers.lGraph import LGraph
from layeredGraphLayouter.containers.constants import PortSide


def create_simpleCross(gb) -> LGraph:
    """
    *  *
     \/
     /\
    *  *

    :return: Graph of the form above.
    """
    leftNodes = gb.addNodesToLayer(2, gb.makeLayer())
    rightNodes = gb.addNodesToLayer(2, gb.makeLayer())
    gb.eastWestEdgeFromTo(leftNodes[0], rightNodes[1])
    gb.eastWestEdgeFromTo(leftNodes[1], rightNodes[0])

    return gb.graph


def create_extendedCross(gb) -> LGraph:
    """
      *  *
       \/
       /\
    *-*  *

    :return: Graph of the form above.
    """
    leftNode = gb.addNodeToLayer(gb.makeLayer())
    create_simpleCross(gb)
    middleNodes = gb.graph.layers[1]
    gb.eastWestEdgeFromTo(leftNode, middleNodes[1])

    return gb.graph


def create_dualPortCross_post(gb, fixedNodes=True) -> LGraph:
    """
    ____  *
    |  |\/
    |__|/\
          *

    :return: Graph of the form above.
    """
    leftLayer = gb.makeLayer()
    rightLayer = gb.makeLayer()

    leftNode = gb.addNodeToLayer(leftLayer)

    rightTopNode = gb.addNodeToLayer(rightLayer)
    rightBottomNode = gb.addNodeToLayer(rightLayer)

    gb.eastWestEdgeFromTo(leftNode, rightBottomNode)
    gb.eastWestEdgeFromTo(leftNode, rightTopNode)

    if fixedNodes:
        gb.setFixedOrderConstraint(leftNode)

    return gb.graph


def create_dualPortCross_pre(gb, fixedNodes=True) -> LGraph:
    """
    *  ___
     \/| |
     /\|_|
    *

    :return: Graph of the form above.
    """
    leftNodes = gb.addNodesToLayer(2, gb.makeLayer())
    rightNode = gb.addNodeToLayer(gb.makeLayer())
    gb.eastWestEdgeFromTo(leftNodes[0], rightNode)
    gb.eastWestEdgeFromTo(leftNodes[1], rightNode)
    if fixedNodes:
        gb.setFixedOrderConstraint(rightNode)
    return gb.graph


def create_dualDualCros(gb) -> LGraph:
    """
    ___  ___
    | |\/| |
    |_|/\|_|

    :return: Graph of the form above.
    """
    left = gb.addNodeToLayer(gb.makeLayer())
    right = gb.addNodeToLayer(gb.makeLayer())
    gb.eastWestEdgeFromTo(left, right)
    gb.eastWestEdgeFromTo(left, right)

    return gb.graph


def create_quadEdgeCross(gb) -> LGraph:
    """
    Constructs a cross formed graph with two edges between the corners
    Each node has two ports.

    *    *
     \\//
     //\\
    *    *
    
    :return: Graph of the form above.
    """
    leftLayer = gb.makeLayer()
    rightLayer = gb.makeLayer()

    topLeft = gb.addNodeToLayer(leftLayer)
    bottomLeft = gb.addNodeToLayer(leftLayer)
    topRight = gb.addNodeToLayer(rightLayer)
    bottomRight = gb.addNodeToLayer(rightLayer)

    topLeftTopPort = gb.addPortOnSide(topLeft, PortSide.EAST)
    topLeftBottomPort = gb.addPortOnSide(topLeft, PortSide.EAST)
    bottomRightBottomPort = gb.addPortOnSide(bottomRight, PortSide.WEST)
    bottomRightTopPort = gb.addPortOnSide(bottomRight, PortSide.WEST)
    gb.addEdgeBetweenPorts(topLeftTopPort, bottomRightTopPort)
    gb.addEdgeBetweenPorts(topLeftBottomPort, bottomRightBottomPort)

    bottomLeftTopPort = gb.addPortOnSide(bottomLeft, PortSide.EAST)
    bottomLeftBottomPort = gb.addPortOnSide(bottomLeft, PortSide.EAST)
    topRightBottomPort = gb.addPortOnSide(topRight, PortSide.WEST)
    topRightTopPort = gb.addPortOnSide(topRight, PortSide.WEST)
    gb.addEdgeBetweenPorts(bottomLeftTopPort, topRightTopPort)
    gb.addEdgeBetweenPorts(bottomLeftBottomPort, topRightBottomPort)

    return gb.graph
