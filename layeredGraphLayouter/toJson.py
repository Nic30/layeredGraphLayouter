from layeredGraphLayouter.containers.constants import PortType


class ToJson():
    def LPort_toJson(self, lp):
        return {"id": lp.id,
                "geometry": self.toJson(lp.geometry),
                "name": lp.name}

    def LNode_toJson(self, lu):
        toJson = self.toJson
        return {"name": lu.name,
                "id": lu.id,
                "isExternalPort": False,
                "geometry": toJson(lu.geometry),
                "inputs":  [toJson(i)
                            for i in self.inputs],
                "outputs": [toJson(o)
                            for o in self.outputs]
                }

    def LayoutExternalPort_toJson(self, lep):
        j = self.LNode_toJson(lep)
        j["direction"] = PortType.opposite(
            lep.direction).toStr()
        j["isExternalPort"] = True
        return j

    def LEdge_toJson(self, ln):
        j = {}
        if ln.name:
            j['name'] = ln.name
        j['source'] = ln.source.id
        j['endpoints'] = list(map(lambda t: t.id, self.endpoints))

        return j

    def LGraph_toJson(self, la):
        # nets = sorted(nets , key=lambda x : x.name)
        n2j = self.LNode_toJson
        e2j = self.LEdge_toJson
        return {"nodes": [n2j(n) for n in la.nodes],
                "edges": [e2j(n) for n in la.nets]}

    def GeometryRect_toJson(self, gr):
        return {
            "x": gr.x,
            "y": gr.y,
            "width": gr.width,
            "height": gr.height
        }
