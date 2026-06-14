from typing import Any

from pydantic import BaseModel, Field

from app.schemas.agent import MemoryDecision
from app.schemas.graph import GraphOut


class ResourceCreate(BaseModel):
    input: str = Field(min_length=1)
    title: str | None = None


class ResourceOut(BaseModel):
    id: str
    type: str
    title: str
    meta: str
    description: str
    sourceUrl: str | None = None
    status: str


class InitializeRequest(BaseModel):
    input: str | None = None


class DumpRequest(BaseModel):
    input: str = Field(min_length=1)


class DumpResponse(BaseModel):
    decision: MemoryDecision
    primaryNodeId: str | None
    secondaryNodeId: str | None = None
    newNodeId: str | None = None
    confidence: float
    actionsTaken: list[str]
    reason: str
    updatedGraph: GraphOut


class MemoryOut(BaseModel):
    textualSummary: str
    conceptMap: dict[str, Any]


class QueryRequest(BaseModel):
    question: str = Field(min_length=1)


class QueryResponse(BaseModel):
    answer: str
    sourceNodes: list[str]

