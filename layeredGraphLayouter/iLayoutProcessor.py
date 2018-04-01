from typing import Optional
from layeredGraphLayouter.containers.lGraph import LGraph
from layeredGraphLayouter.layoutProcessorConfiguration import LayoutProcessorConfiguration


class ILayoutProcessor():
    @staticmethod
    def getLayoutProcessorConfiguration(graph: LGraph) -> Optional[LayoutProcessorConfiguration]:
        return None

    def process(self, graph: LGraph):
        raise NotImplementedError()