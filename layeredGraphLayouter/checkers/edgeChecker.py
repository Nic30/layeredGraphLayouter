from layeredGraphLayouter.iLayoutProcessor import ILayoutProcessor
from layeredGraphLayouter.containers.lGraph import LGraph
from itertools import chain


class EdgeChecker(ILayoutProcessor):
    def process(self, graph: LGraph):
        for e in graph.edges:
            try:
                assert e.src is not None, e
                assert e.srcNode is not None, e
                assert e.srcNode is e.src.getNode(), e
                assert e.dst is not None, e
                assert e.dstNode is not None, e
                assert e.dstNode is e.dst.getNode() is not None, e
                assert e.isSelfLoop == (e.srcNode is e.dstNode), e
            except AssertionError:
                raise
        edgesInGraph = set()
        for layer in graph.layers:
            for n in layer:
                for p in n.iterPorts():
                    for e in chain(p.incomingEdges, p.outgoingEdges):
                        edgesInGraph.add(e)
        edges = set(graph.edges)
        diff = edges.difference(edges)
        assert not diff, diff
