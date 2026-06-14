from pydantic import BaseModel, Field

class ProjectMemoryEventCreate(BaseModel):
    eventType: str = Field(min_length=1, max_length=80)
    content: str = ""
    metadata: dict = Field(default_factory=dict)


class ProjectMemoryEventOut(BaseModel):
    id: str
    projectMemoryId: str
    ideaId: str
    eventType: str
    content: str
    metadata: dict = Field(default_factory=dict)
    createdAt: str


class ProjectMemoryOut(BaseModel):
    id: str
    ideaId: str
    cardId: str
    title: str
    mainTopic: str
    selectedCard: dict | None = None
    textualSummary: str
    status: str
    isActive: bool
    createdAt: str
    updatedAt: str
    lastRefreshedAt: str


class ProjectMemoryPayload(BaseModel):
    projectMemory: ProjectMemoryOut | None = None
    recentEvents: list[ProjectMemoryEventOut] = []
