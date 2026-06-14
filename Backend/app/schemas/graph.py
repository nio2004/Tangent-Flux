from pydantic import BaseModel


class GraphNodeOut(BaseModel):
    id: str
    label: str
    summary: str
    memberCount: int
    createdBy: str


class GraphEdgeOut(BaseModel):
    id: str
    source: str
    target: str
    edgeType: str
    weight: float
    reason: str


class GraphOut(BaseModel):
    nodes: list[GraphNodeOut]
    edges: list[GraphEdgeOut]

