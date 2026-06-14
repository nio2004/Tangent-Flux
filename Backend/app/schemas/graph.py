from pydantic import BaseModel


<<<<<<< HEAD
=======
class GraphEvidenceOut(BaseModel):
    chunkId: str
    resourceId: str
    resourceTitle: str
    resourceType: str
    sourceUrl: str | None = None
    position: int
    preview: str


>>>>>>> 6f1c767a5b6ce400673ed3b3987875468dd9fa04
class GraphNodeOut(BaseModel):
    id: str
    label: str
    summary: str
    memberCount: int
<<<<<<< HEAD
=======
    sourceIds: list[str] = []
    evidence: list[GraphEvidenceOut] = []
>>>>>>> 6f1c767a5b6ce400673ed3b3987875468dd9fa04
    createdBy: str


class GraphEdgeOut(BaseModel):
    id: str
    source: str
    target: str
    edgeType: str
    weight: float
    reason: str
<<<<<<< HEAD
=======
    sharedEvidenceCount: int = 0
>>>>>>> 6f1c767a5b6ce400673ed3b3987875468dd9fa04


class GraphOut(BaseModel):
    nodes: list[GraphNodeOut]
    edges: list[GraphEdgeOut]

