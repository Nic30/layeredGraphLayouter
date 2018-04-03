from layeredGraphLayouter.containers.lEdge import LEdge
from layeredGraphLayouter.containers.lGraph import LGraph
from layeredGraphLayouter.containers.lNode import LNode, LayoutExternalPort
from layeredGraphLayouter.containers.lPort import LPort
from layeredGraphLayouter.containers.sizeConfig import PORT_HEIGHT, UNIT_HEADER_OFFSET
import xml.etree.ElementTree as etree


class GeometryRect():
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    @classmethod
    def fromLRectangle(cls, rect):
        return cls(rect.possition.x, rect.possition.y, rect.size.x, rect.size.y)

    def __repr__(self):
        return "<%s, x:%f, y:%f, width:%f, height:%f>" % (
            self.__class__.__name__, self.x, self.y, self.width, self.height)


class LayoutIdCtx(dict):
    # {LayoutObj: int}
    def __getitem__(self, obj):
        try:
            return dict.__getitem__(self, obj)
        except KeyError:
            pass

        return self._register(obj)

    def _register(self, obj) -> int:
        i = len(self)
        self[obj] = i
        return i


def mxCell(**kvargs):
    return etree.Element("mxCell", attrib=kvargs)


class ToMxGraph():
    def __init__(self):
        self.id_ctx = LayoutIdCtx()

        self._toMxGraph = {
            LNode: self.LNode_toMxGraph,
            LEdge: self.LEdge_toMxGraph,
            LayoutExternalPort: self.LayoutExternalPort_toMxGraph,
            LGraph: self.LGraph_toMxGraph,
            GeometryRect: self.GeometryRect_toMxGraph
        }

    def LPort_coordinates(self, lp):
        p = lp.getNode()
        ch = lp

        if p.size.x == 0:
            #assert g.x - p.x == 0, (g.possition.x, p.x)
            x_rel = 0
        else:
            x_rel = (ch.possition.x - p.possition.x) / p.size.x
            assert x_rel >= 0.0 and x_rel <= 1.0, x_rel

        if p.size.y == 0:
            #assert g.y - p.y == 0, (g.y, p.y)
            y_rel = 0
        else:
            y_rel = (ch.possition.y - p.possition.y + ch.size.y / 2) / p.size.y
            assert y_rel >= 0.0 and y_rel <= 1.0, y_rel

        if x_rel >= 0.5:
            x_rel = 1

        return x_rel, y_rel

    def getMxGraphId(self, obj):
        return str(self.id_ctx[obj] + 2)

    def LNode_toMxGraph(self, lu: LNode):
        _id = self.getMxGraphId(lu)
        c = mxCell(
            value="",
            id=_id,
            style="rounded=0;whiteSpace=wrap;html=1;",
            parent="1", vertex="1")
        g = GeometryRect.fromLRectangle(lu)
        c.append(self.GeometryRect_toMxGraph(g))
        yield c

        if lu.name:
            label = mxCell(
                id=self.getMxGraphId((lu, lu.name)),
                value=lu.name,
                style=("text;html=1;resizable=0;points=[];autosize=1;align=left;"
                       "verticalAlign=top;spacingTop=0;"),
                vertex="1",
                parent=_id,
            )
            lg = GeometryRect(0, 0, g.width, UNIT_HEADER_OFFSET)
            label.append(self.GeometryRect_toMxGraph(lg))
            yield label

        for lp in lu.iterPorts():
            yield from self.LPort_toMxGraph(lp, _id, g)

    def LPort_toMxGraph(self, lp: LPort, parentId, parentGeom):
        name = lp.name
        if not name:
            name = ""

        p = mxCell(
            value=name,
            id=self.getMxGraphId(lp),
            style="rounded=0;whiteSpace=wrap;html=1;",
            parent=parentId, vertex="1")
        g = GeometryRect.fromLRectangle(lp)
        g = GeometryRect(g.x - parentGeom.x, g.y -
                         parentGeom.y, g.width, g.height)
        p.append(self.GeometryRect_toMxGraph(g))
        yield p

    def LayoutExternalPort_toMxGraph(self, lep):
        if len(lep.west) + len(lep.east) == 1:
            c = mxCell(id=self.getMxGraphId(lep),
                       value=lep.name,
                       style="rounded=0;whiteSpace=wrap;html=1;",
                       vertex="1",
                       parent="1")
            g = GeometryRect.fromLRectangle(lep)
            c.append(self.GeometryRect_toMxGraph(g))

            yield c
        else:
            yield from self.LNode_toMxGraph(lep)

    def LEdge_toMxGraph(self, e: LEdge):
        if e.reversed:
            _src = e.dst
            _dst = e.src
        else:
            _src = e.src
            _dst = e.dst

        srcId = self.getMxGraphId(_src.getNode())
        srcX, srcY = self.LPort_coordinates(_src)
        dstId = self.getMxGraphId(_dst.getNode())
        dstX, dstY = self.LPort_coordinates(_dst)

        c = mxCell(
            id=self.getMxGraphId(e),
            style=("edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;" +
                   "exitX=%f;exitY=%f;entryX=%f;entryY=%f;"
                   % (srcX, srcY, dstX, dstY) +
                   "jettySize=auto;orthogonalLoop=1;"),
            edge="1",
            parent="1",
            source=srcId,
            target=dstId,
        )
        c.append(etree.Element("mxGeometry", {
                 "relative": "1", "as": "geometry"}))
        yield c

    def LGraph_toMxGraph(self, la) -> etree.Element:
        gm = etree.Element("mxGraphModel", {
            "dx": "0",
            "dy": "0",
            "grid": "1",
            "gridSize": "10",
            "guides": "1",
            "tooltips": "1",
            "connect": "1",
            "arrows": "1",
            "fold": "1",
            "page": "1",
            "pageScale": "1",
            # "pageWidth":"0",
            # "pageHeight":"0"
            "background": "#ffffff",
            "math": "0",
            "shadow": "0"
        })
        root = etree.Element("root")
        gm.append(root)
        topCell = mxCell(id="0")
        mainCell = mxCell(id="1", parent="0")
        root.extend([topCell, mainCell])

        for n in la.nodes:
            for obj in self.toMxGraph(n):
                root.append(obj)

        for n in la.edges:
            for l in self.toMxGraph(n):
                root.append(l)

        return gm

    def GeometryRect_toMxGraph(self, g, as_="geometry"):
        return etree.Element(
            "mxGeometry",
            {"x": str(g.x),
             "y": str(g.y),
             "width": str(g.width),
             "height": str(g.height),
             "as": as_})

    def toMxGraph(self, obj):
        yield from self._toMxGraph[obj.__class__](obj)
