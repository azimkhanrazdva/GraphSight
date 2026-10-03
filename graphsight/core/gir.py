from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


class BBox(BaseModel):
    x: float
    y: float
    width: float
    height: float

    @property
    def center(self) -> tuple[float, float]:
        return (self.x + self.width / 2, self.y + self.height / 2)


class Point(BaseModel):
    x: float
    y: float


class VerificationStatus(StrEnum):
    VERIFIED = "verified"
    PROBABLE = "probable"
    UNCERTAIN = "uncertain"
    CONFLICT = "conflict"
    REJECTED = "rejected"
    HUMAN_VERIFIED = "human_verified"


class Evidence(BaseModel):
    id: str = Field(default_factory=lambda: new_id("ev"))
    type: Literal[
        "object_detection",
        "ocr",
        "pixel_connector",
        "arrow_detection",
        "vlm",
        "graph_rule",
        "human",
        "cross_document",
    ]
    source: str
    confidence: float = Field(ge=0, le=1)
    page: int = 1
    bbox: BBox | None = None
    geometry: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Label(BaseModel):
    id: str = Field(default_factory=lambda: new_id("label"))
    text: str
    bbox: BBox
    page: int = 1
    confidence: float = Field(ge=0, le=1)
    evidence_ids: list[str] = Field(default_factory=list)


class Connector(BaseModel):
    id: str = Field(default_factory=lambda: new_id("conn"))
    points: list[Point]
    start: Point
    end: Point
    arrow_direction: Literal["forward", "backward", "none", "unknown"] = "unknown"
    confidence: float = Field(ge=0, le=1)
    page: int = 1
    evidence_ids: list[str] = Field(default_factory=list)


class Node(BaseModel):
    id: str = Field(default_factory=lambda: new_id("node"))
    type: str
    label: str
    properties: dict[str, Any] = Field(default_factory=dict)
    bbox: BBox
    page: int = 1
    confidence: float = Field(ge=0, le=1)
    evidence_ids: list[str] = Field(default_factory=list)


class VerificationCheck(BaseModel):
    name: str
    passed: bool
    confidence: float = Field(ge=0, le=1)
    message: str


class Edge(BaseModel):
    id: str = Field(default_factory=lambda: new_id("edge"))
    source: str
    target: str
    type: str = "connection"
    directed: bool = True
    confidence: float = Field(ge=0, le=1)
    evidence_ids: list[str] = Field(default_factory=list)
    verification_status: VerificationStatus = VerificationStatus.UNCERTAIN
    checks: list[VerificationCheck] = Field(default_factory=list)


class Conflict(BaseModel):
    id: str = Field(default_factory=lambda: new_id("conflict"))
    type: str
    severity: Literal["low", "medium", "high"]
    candidates: list[dict[str, Any]]
    message: str


class Uncertainty(BaseModel):
    id: str = Field(default_factory=lambda: new_id("uncertain"))
    target_id: str
    reason: str
    severity: Literal["low", "medium", "high"] = "medium"


class DocumentInfo(BaseModel):
    id: str
    filename: str
    mime_type: str
    sha256: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PageInfo(BaseModel):
    page: int
    width: int
    height: int
    coordinate_system: str = "original_image_pixels"


class GIR(BaseModel):
    gir_version: str = "1.0"
    document: DocumentInfo
    pages: list[PageInfo]
    nodes: list[Node] = Field(default_factory=list)
    edges: list[Edge] = Field(default_factory=list)
    groups: list[dict[str, Any]] = Field(default_factory=list)
    labels: list[Label] = Field(default_factory=list)
    connectors: list[Connector] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    conflicts: list[Conflict] = Field(default_factory=list)
    uncertainties: list[Uncertainty] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def evidence_by_id(self) -> dict[str, Evidence]:
        return {item.id: item for item in self.evidence}

