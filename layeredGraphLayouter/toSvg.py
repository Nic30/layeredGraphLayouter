from layeredGraphLayouter.containers.geometry import LRectangle
from layeredGraphLayouter.containers.lEdge import LEdge
from layeredGraphLayouter.containers.lGraph import LGraph
from layeredGraphLayouter.containers.lNode import LNode, LayoutExternalPort
from layeredGraphLayouter.containers.lPort import LPort
from layeredGraphLayouter.containers.sizeConfig import PORT_HEIGHT
from layeredGraphLayouter.toMxGraph import LayoutIdCtx
import xml.etree.ElementTree as etree


EXTERNAL_PORT_FILL = "mediumpurple"
COMPONENT_FILL = "cornflowerblue"


def svg_rect_from_lrectangle(rect: LRectangle, label=None, fill=COMPONENT_FILL):
    g = etree.Element("g")
    r = svg_rect(rect.possition.x, rect.possition.y,
                 rect.size.x, rect.size.y, fill=fill)
    g.append(r)
    if label is not None:
        g.append(svg_text(rect.possition.x + rect.size.x / 2,
                          # center text in the middle
                          rect.possition.y + PORT_HEIGHT * 0.7, label))
    return g


def svg_rect(x, y, width, height, fill=COMPONENT_FILL):
    return etree.Element("rect", attrib={
        "style": "fill:%s;stroke:black;stroke-width:2;" % fill,
        "x": str(x),
        "y": str(y),
        "width": str(width),
        "height": str(height)
    })


def svg_text(x, y, text):
    t = etree.Element("text", attrib={"x": str(x),
                                      "y": str(y),
                                      "fill": "black",
                                      "text-anchor": "middle"})
    t.text = text
    return t


def svg_line(points, stroke="black"):
    p_str = " ".join("%r,%r" % p for p in points)
    return etree.Element("polyline", attrib={
        "points": p_str,
        "style": "fill:none;stroke:%s;stroke-width:2" % stroke,
        #"marker-start": "url(#markerCircle)",
        "marker-end": "url(#markerArrow)",
    })


class ToSvg():
    def __init__(self, reversed_edge_stroke="black"):
        self.reversed_edge_stroke = reversed_edge_stroke
        self.id_ctx = LayoutIdCtx()

        self._toSvg = {
            LNode: self.LNode_toSvg,
            LEdge: self.LEdge_toSvg,
            LayoutExternalPort: self.LayoutExternalPort_toSvg,
            LGraph: self.LGraph_toSvg,
        }

    def LPort_coordinates(self, lp: LPort):
        p = lp.getNode()
        ch = lp
        is_on_right = p.possition.x >= p.possition.x + p.possition.x / 2
        if is_on_right:
            x = p.possition.x + p.size.x
        else:
            x = p.possition.x

        y = (ch.possition.y + PORT_HEIGHT / 2)

        return x, y

    def getSvgId(self, obj):
        return str(self.id_ctx[obj] + 2)

    def LNode_toSvg(self, lu: LNode, fill=COMPONENT_FILL):
        n = svg_rect_from_lrectangle(lu, label=lu.name, fill=fill)

        for lp in lu.iterPorts():
            for obj in self.LPort_toSvg(lp):
                n.append(obj)
        yield n

    def LPort_toSvg(self, lp: LPort):
        yield svg_rect_from_lrectangle(lp, label=lp.name)

    def LayoutExternalPort_toSvg(self, lep: LayoutExternalPort):
        if len(lep.west) + len(lep.east) == 1:
            yield svg_rect_from_lrectangle(lep,
                                           label=lep.name,
                                           fill=EXTERNAL_PORT_FILL)
        else:
            yield from self.LNode_toSvg(lep, fill=EXTERNAL_PORT_FILL)

    def LEdge_toSvg(self, ln: LNode):
        if ln.reversed:
            _src = ln.dst
            _dst = ln.src
            stroke = self.reversed_edge_stroke
        else:
            _src = ln.src
            _dst = ln.dst
            stroke = "black"

        srcX, srcY = self.LPort_coordinates(_src)
        dstX, dstY = self.LPort_coordinates(_dst)
        points = [(srcX, srcY), (dstX, dstY)]

        yield svg_line(points, stroke=stroke)

    def LGraph_toSvg(self, la: LGraph) -> etree.Element:
        svg = etree.Element("svg", {
            "width": str(la.size.x),
            "height": str(la.size.y),
        })
        defs = etree.fromstring(
            """
            <defs>
                <marker id="markerCircle" markerWidth="8" markerHeight="8" refX="5" refY="5">
                    <circle cx="2" cy="2" r="2" style="stroke: none; fill:#000000;"/>
                </marker>
                <marker id="markerArrow" viewBox="0 0 10 10" refX="1" refY="5" 
                      markerUnits="strokeWidth" markerWidth="5" markerHeight="5"
                      orient="auto">
                    <path d="M 0 0 L 10 5 L 0 10 z" fill="context-stroke"/>
                </marker>
            </defs>""".replace("  ", ""))
        svg.append(defs)

        for n in la.nodes:
            for obj in self.toSvg(n):
                svg.append(obj)

        for n in la.edges:
            for l in self.toSvg(n):
                svg.append(l)

        return svg

    def toSvg(self, obj):
        yield from self._toSvg[obj.__class__](obj)
