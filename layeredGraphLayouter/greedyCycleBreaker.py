from layeredGraphLayouter.containers.lNode import LNode
from layeredGraphLayouter.uniqList import UniqList


class GreedyCycleBreaker():
    """
    :note: ported from ELK
    """

    def initDegrees(self):
        add_unresolved = self.unresolved.add
        add_sink = self.sinks.append
        add_source = self.sources.append
        for n in self.nodes:
            n.initPortDegrees()
            if n.indeg and n.outdeg == 0:
                add_sink(n)
            elif n.indeg == 0 and n.outdeg:
                add_source(n)
            else:
                add_unresolved(n)

    def process(self, graph):
        nodes = self.nodes = graph.getLayerlessNodes()
        # list of sink nodes.
        sinks = self.sinks = UniqList()
        # list of source nodes
        sources = self.sources = UniqList()
        unresolved = self.unresolved = set()
        # mark for the nodes, inducing an ordering of the nodes.
        self.initial_order = {n: i for i, n in enumerate(self.nodes)}

        self.initDegrees()

        # next rank values used for sinks and sources (from right and from
        # left)
        nextRight = -1
        nextLeft = 1

        # assign marks to all nodes
        while sinks or sources or unresolved:
            # sinks are put to the right --> assign negative rank, which is
            # later shifted to positive
            while sinks:
                sink = sinks.pop()
                sink.mark = nextRight
                nextRight -= 1
                self.updateNeighbors(sink)

            # sources are put to the left --> assign positive rank
            while sources:
                source = sources.pop()
                source.mark = nextLeft
                nextLeft += 1
                self.updateNeighbors(source)

            # while there are unprocessed nodes left that are neither sinks nor
            # sources...
            if not sinks and not sources and unresolved:
                # find the set of unprocessed node (=> mark == 0), with the largest out flow
                # randomly select a node from the ones with maximal outflow and
                # put it left
                maxNode = max(
                    unresolved,
                    key=lambda n: (n.outdeg - n.indeg, self.initial_order[n]))
                maxNode.mark = nextLeft
                unresolved.remove(maxNode)
                nextLeft += 1
                self.updateNeighbors(maxNode)

        # shift negative ranks to positive; this applies to sinks of the graph
        shiftBase = len(nodes) + 1
        for n in nodes:
            if n.mark < 0:
                n.mark += shiftBase

        # reverse edges that point left
        for node in nodes:
            # look at the node's outgoing edges
            for port in node.iterPorts():
                for edge in port.outgoingEdges:
                    if node.mark > edge.dstNode.mark:
                        edge.reverse()

    def updateNeighbors(self, node: LNode):
        """
        Updates indegree and outdegree values of the neighbors of the given node,
        simulating its removal from the graph. the sources and sinks lists are
        also updated.

        :param node: node for which neighbors are updated
        """
        sources_add = self.sources.append
        sinks_add = self.sinks.append
        unresolved_discard = self.unresolved.discard

        for p in node.iterPorts():
            isOutput = bool(p.outgoingEdges)
            for e in p.iterEdges(filterSelfLoops=True):
                if e.srcNode is node:
                    other = e.dstNode
                else:
                    other = e.srcNode

                if other.mark == 0:
                    if isOutput:
                        other.indeg -= 1
                        if other.indeg <= 0 and other.outdeg > 0:
                            unresolved_discard(other)
                            sources_add(other)
                    else:
                        other.outdeg -= 1
                        if other.outdeg <= 0 and other.indeg > 0:
                            unresolved_discard(other)
                            sinks_add(other)
