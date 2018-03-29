
class LayoutProcessorConfiguration():
    def __init__(self,
                 p1_cycle_breaking_before=None, p1_cycle_breaking=None, p1_cycle_breaking_after=None,

                 p3_node_ordering_before=None, p3_node_ordering=None, p3_node_ordering_after=None):
        self.p1_cycle_breaking_before = p1_cycle_breaking_before
        self.p1_cycle_breaking = p1_cycle_breaking
        self.p1_cycle_breaking_after = p1_cycle_breaking_after

        self.p3_node_ordering_before = p3_node_ordering_before
        self.p3_node_ordering = p3_node_ordering
        self.p3_node_ordering_after = p3_node_ordering_after