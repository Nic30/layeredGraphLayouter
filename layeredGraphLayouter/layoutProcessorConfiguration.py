from layeredGraphLayouter.containers.lGraph import LGraph


class LayoutProcessorConfiguration():
    """
    Configuration LayoutProcessor
    * contains list of graph sub processors for each phase of layout generation

    Phases are:
        P1_CYCLE_BREAKING
        Elimination of cycles through edge reversal.

        P2_LAYERING
        Division of nodes into distinct layers.

        P3_NODE_ORDERING
        * Computation of an order of nodes in each layer, usually to reduce crossings.

        P4_NODE_PLACEMENT
        * Assignment of y coordinates.

        P5_EDGE_ROUTING
        * Edge routing and assignment of x coordinates.
    """
    MAIN_PHASE_NAMES = [
        "p1_cycle_breaking",
        "p2_layering",
        "p3_node_ordering",
        "p4_node_placement",
        "p5_edge_routing"
    ]

    def __init__(self,
                 p1_cycle_breaking_before=None, p1_cycle_breaking=None, p1_cycle_breaking_after=None,
                 p2_layering_before=None, p2_layering=None, p2_layering_after=None,
                 p3_node_ordering_before=None, p3_node_ordering=None, p3_node_ordering_after=None,
                 p4_node_placement_before=None, p4_node_placement=None, p4_node_placement_after=None,
                 p5_edge_routing_before=None, p5_edge_routing=None, p5_edge_routing_after=None):
        self.loaded = False

        self.p1_cycle_breaking_before = p1_cycle_breaking_before
        self.p1_cycle_breaking = p1_cycle_breaking
        self.p1_cycle_breaking_after = p1_cycle_breaking_after

        self.p2_layering_before = p2_layering_before
        self.p2_layering = p2_layering
        self.p2_layering_after = p2_layering_after

        self.p3_node_ordering_before = p3_node_ordering_before
        self.p3_node_ordering = p3_node_ordering
        self.p3_node_ordering_after = p3_node_ordering_after

        self.p4_node_placement_before = p4_node_placement_before
        self.p4_node_placement = p4_node_placement
        self.p4_node_placement_after = p4_node_placement_after

        self.p5_edge_routing_before = p5_edge_routing_before
        self.p5_edge_routing = p5_edge_routing
        self.p5_edge_routing_after = p5_edge_routing_after

    def iterProcessors(self):
        for phaseName in self.MAIN_PHASE_NAMES:
            for subPhaseName in ["_before", "", "_after"]:
                phase = getattr(self, phaseName + subPhaseName)
                if phase:
                    yield from phase

    def load(self, graph: LGraph):
        """Load nestested sub processors"""
        assert not self.loaded
        for proc in self.iterProcessors():
            subConfig = proc.getLayoutProcessorConfiguration(graph)
            if subConfig:
                subConfig.load(graph)
                self.merge(subConfig)

        self.loaded = True

    def _merge(self, other, propName):
        myProp = getattr(self, propName)
        otherProp = getattr(other, propName)
        if not otherProp:
            return
        elif not myProp:
            setattr(self, propName, otherProp[:])
        else:
            myProp.extend(otherProp)

    def _merge_triplet(self, other, propName):
        self._merge(other, propName + "_before")
        self._merge(other, propName)
        self._merge(other, propName + "_after")

    def merge(self, other: "LayoutProcessorConfiguration"):
        """Merge this configuration with other to this instance"""
        for phase in self.MAIN_PHASE_NAMES:
            self._merge_triplet(other, phase)

        return self
