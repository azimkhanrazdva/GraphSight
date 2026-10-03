from graphsight.core.gir import GIR, BBox, DocumentInfo, Edge, Node, PageInfo
from graphsight.query.engine import GraphQueryEngine


def test_shortest_path_query() -> None:
    gir = GIR(
        document=DocumentInfo(id="doc", filename="demo.png", mime_type="image/png", sha256="x"),
        pages=[PageInfo(page=1, width=800, height=400)],
        nodes=[
            Node(id="a", type="router", label="Router A", bbox=BBox(x=0, y=0, width=1, height=1), confidence=1),
            Node(id="b", type="firewall", label="Firewall B", bbox=BBox(x=0, y=0, width=1, height=1), confidence=1),
            Node(id="c", type="server", label="Server C", bbox=BBox(x=0, y=0, width=1, height=1), confidence=1),
        ],
        edges=[
            Edge(id="ab", source="a", target="b", confidence=1),
            Edge(id="bc", source="b", target="c", confidence=1),
        ],
    )

    result = GraphQueryEngine(gir).answer("What path connects Router A to Server C?")

    assert result.answer == "Router A -> Firewall B -> Server C"
    assert result.edge_ids == ["ab", "bc"]

