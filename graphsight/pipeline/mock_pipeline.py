from __future__ import annotations

from pathlib import Path

from PIL import Image

from graphsight.confidence.engine import ConfidenceEngine
from graphsight.core.gir import (
    GIR,
    BBox,
    Connector,
    DocumentInfo,
    Edge,
    Evidence,
    Label,
    Node,
    PageInfo,
    Point,
)
from graphsight.verification.engine import VerificationEngine


class MockDiagramPipeline:
    def analyze(self, document: DocumentInfo, image_path: Path) -> GIR:
        with Image.open(image_path) as image:
            width, height = image.size

        y = height * 0.45
        boxes = [
            ("router_a", "router", "Router A", BBox(x=width * 0.08, y=y, width=120, height=70)),
            ("firewall_b", "firewall", "Firewall B", BBox(x=width * 0.38, y=y, width=130, height=70)),
            ("server_c", "server", "Server C", BBox(x=width * 0.70, y=y, width=120, height=70)),
        ]
        evidence: list[Evidence] = []
        labels: list[Label] = []
        nodes: list[Node] = []
        for node_id, node_type, label, bbox in boxes:
            ev = Evidence(
                type="object_detection",
                source="mock_detector",
                confidence=0.92,
                bbox=bbox,
                metadata={"mode": "demo_mock"},
            )
            label_ev = Evidence(
                type="ocr",
                source="mock_ocr",
                confidence=0.88,
                bbox=bbox,
                metadata={"text": label, "mode": "demo_mock"},
            )
            evidence.extend([ev, label_ev])
            labels.append(Label(text=label, bbox=bbox, confidence=0.88, evidence_ids=[label_ev.id]))
            nodes.append(
                Node(
                    id=node_id,
                    type=node_type,
                    label=label,
                    bbox=bbox,
                    confidence=0.91,
                    evidence_ids=[ev.id, label_ev.id],
                )
            )

        confidence = ConfidenceEngine()
        connectors: list[Connector] = []
        edges: list[Edge] = []
        for source, target in [("router_a", "firewall_b"), ("firewall_b", "server_c")]:
            start_node = next(node for node in nodes if node.id == source)
            end_node = next(node for node in nodes if node.id == target)
            start = Point(x=start_node.bbox.x + start_node.bbox.width, y=start_node.bbox.center[1])
            end = Point(x=end_node.bbox.x, y=end_node.bbox.center[1])
            ev = Evidence(
                type="pixel_connector",
                source="mock_connector_detector",
                confidence=0.9,
                geometry={"points": [start.model_dump(), end.model_dump()]},
                metadata={"mode": "demo_mock"},
            )
            evidence.append(ev)
            connector = Connector(
                points=[start, end],
                start=start,
                end=end,
                arrow_direction="forward",
                confidence=0.9,
                evidence_ids=[ev.id],
            )
            connectors.append(connector)
            edges.append(
                Edge(
                    source=source,
                    target=target,
                    confidence=confidence.calculate(
                        {"detector": 0.91, "ocr": 0.88, "connector": 0.9, "arrow": 0.84, "rules": 1.0}
                    ),
                    evidence_ids=[ev.id],
                )
            )

        gir = GIR(
            document=document,
            pages=[PageInfo(page=1, width=width, height=height)],
            nodes=nodes,
            edges=edges,
            labels=labels,
            connectors=connectors,
            evidence=evidence,
            metadata={"pipeline": "mock", "warning": "Demo mock output, not model inference."},
        )
        return VerificationEngine().verify(gir)
