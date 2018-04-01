from layeredGraphLayouter.containers.lGraph import LGraph
from layeredGraphLayouter.layoutProcessorConfiguration import LayoutProcessorConfiguration


class LayoutProcessor():
    def __init__(self, graph: LGraph, config: LayoutProcessorConfiguration):
        self.graph = graph
        config.load(graph)
        self.config = config

    def run(self):
        for proc in self.config.iterProcessors():
            proc.process(self.graph)

        return self.graph