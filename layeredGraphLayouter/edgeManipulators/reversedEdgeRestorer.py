from layeredGraphLayouter.containers.lGraph import LGraph
from layeredGraphLayouter.iLayoutProcessor import ILayoutProcessor


class ReversedEdgeRestorer(ILayoutProcessor):
    """
    Restores the direction of reversed edges. (edges with the property
    {@link org.eclipse.elk.alg.layered.options.LayeredOptions#REVERSED set to {@code true)

    All edges are traversed to look for reversed edges. If such edges are found,
    they are restored, the ports they are connected to being restored as well.

    Precondition:a layered graph.
    Postcondition:Reversed edges are restored to their original direction.
    Slots:After phase 5.
    Same-slot dependencies:None.
    """

    def process(self, layeredGraph: LGraph):

        # Iterate through the edges
        for edge in layeredGraph.edges:
            if edge.reversed:
                edge.reverse(layeredGraph, False)
