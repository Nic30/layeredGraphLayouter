from layeredGraphLayouter.iLayoutProcessor import ILayoutProcessor
from layeredGraphLayouter.containers.lGraph import LGraph
from layeredGraphLayouter.containers.constants import InLayerConstraint


def layer_sort_key(node):
    c = node.inLayerConstraint
    if c == InLayerConstraint.NONE:
        return 1
    elif c == InLayerConstraint.TOP:
        return 0
    else:
        assert c == InLayerConstraint.BOTTOM, c
        return 2


class InLayerConstraintProcessor(ILayoutProcessor):
    """
    Makes sure that in-layer constraints are respected. This processor is only necessary
    if a crossing minimizer doesn't support in-layer constraints anyway. Crossing minimizers
    that do shouldn't include a dependency on this processor. It would need time without
    actually doing anything worthwhile.

    <p>Please note that, among top- and bottom-placed nodes, in-layer successor constraints
    are not respected by this processor. It does, however, preserve them if the crossing
    reduction phase did respect them.</p>

    Precondition:a layered graph; crossing minimization is already finished.
    Postcondition:nodes may have been reordered to match in-layer constraints.
    Slots:Before phase 4.
    Same-slot dependencies:None.
    """

    def process(self, layeredGraph: LGraph):
        for layer in layeredGraph.layers:
            layer.sort(key=layer_sort_key)
