from _collections import defaultdict
from layeredGraphLayouter.containers.lNode import LNode
from layeredGraphLayouter.containers.lEdge import LEdge


def getEdge(source: LNode, target: LNode) -> LEdge:
    """
    Find an edge between two given nodes.

    :param source The source node of the edge
    :param target The target node of the edge
    :return: The edge between source and target, or None if there is none
    """
    for edge in source.getConnectedEdges():
        # [TODO] or is suspicious
        if (edge.dstNode is target) or (edge.srcNode is target):
            return edge

    return None


def getBlocks(bal: "BKAlignedLayout"):
    """
    Finds all blocks of a given layout.

    :param bal The layout of which the blocks shall be found
    :return: The blocks of the given layout
    """
    blocks = defaultdict(list)

    for layer in bal.layeredGraph.layers:
        for node in layer:
            root = bal.root[node]
            blockContents = blocks[root]
            blockContents.append(node)

    return blocks


def getClasses(bal: "BKAlignedLayout"):
    """
    Finds all classes of a given layout. Only used for debug output.

    :param bal The layout whose classes to find
    :return: The classes of the given layout
    """
    classes = defaultdict(list)

    # We need to enumerate all block roots
    roots = set(bal.root)
    for root in roots:
        if root is None:
            print("There are no classes in a balanced layout.")
            break

        sink = bal.sink[root]
        classContents = classes[sink]
        classContents.append(root)

    return classes
