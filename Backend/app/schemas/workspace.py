from pydantic import BaseModel

from app.schemas.graph import GraphOut
from app.schemas.idea import IdeaOut
from app.schemas.memory import MemoryOut, ResourceOut
from app.schemas.task import KanbanBoardOut


class NoteOut(BaseModel):
    id: str
    title: str
    markdown: str


<<<<<<< HEAD
=======
class NoteUpdate(BaseModel):
    markdown: str
    title: str = "Research brief"


class CoverUpdate(BaseModel):
    coverUrl: str | None = None


>>>>>>> 6f1c767a5b6ce400673ed3b3987875468dd9fa04
class TimelineOut(BaseModel):
    id: str
    time: str
    text: str
    type: str


class ArtifactOut(BaseModel):
    id: str
    title: str
    caption: str
    art: str
    assetUrl: str | None = None


class AgentRunOut(BaseModel):
    id: str
    agentType: str
    status: str
    output: dict
    errorMessage: str | None = None
    createdAt: str


class WorkspaceOut(BaseModel):
    idea: IdeaOut
    notes: list[NoteOut]
    resources: list[ResourceOut]
    tasks: KanbanBoardOut
    timeline: list[TimelineOut]
    artifacts: list[ArtifactOut]
    coverUrl: str | None = None
    memory: MemoryOut | None = None
    graph: GraphOut
    agentRuns: list[AgentRunOut]
