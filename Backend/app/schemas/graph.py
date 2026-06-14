from pydantic import BaseModel


class GraphEvidenceOut(BaseModel):
    chunkId: str
    resourceId: str
    resourceTitle: str
    resourceType: str
    sourceUrl: str | None = None
    position: int
    preview: str


class GraphNodeOut(BaseModel):
    id: str
    label: str
    summary: str
    memberCount: int
    sourceIds: list[str] = []
    evidence: list[GraphEvidenceOut] = []
    createdBy: str


class GraphEdgeOut(BaseModel):
    id: str
    source: str
    target: str
    edgeType: str
    weight: float
    reason: str
    sharedEvidenceCount: int = 0


class GraphOut(BaseModel):
    nodes: list[GraphNodeOut]
    edges: list[GraphEdgeOut]

