from pydantic import BaseModel, Field

from app.schemas.task import TaskOut
from app.schemas.project_memory import ProjectMemoryOut


class ChatSessionCreate(BaseModel):
    title: str | None = Field(default=None, max_length=180)


class ChatSessionOut(BaseModel):
    id: str
    ideaId: str
    title: str
    createdAt: str
    updatedAt: str
    messageCount: int = 0


class ChatSourceOut(BaseModel):
    kind: str
    id: str
    title: str
    excerpt: str


class ChatMessageOut(BaseModel):
    id: str
    role: str
    content: str
    sources: list[ChatSourceOut] = []
    createdAt: str


class ChatSessionDetailOut(BaseModel):
    session: ChatSessionOut
    messages: list[ChatMessageOut]


class ChatMessageCreate(BaseModel):
    content: str = Field(min_length=1)
    projectMemoryId: str | None = None


class ChatResponseOut(BaseModel):
    session: ChatSessionOut
    userMessage: ChatMessageOut
    assistantMessage: ChatMessageOut


class IdeaCardTaskOut(BaseModel):
    title: str
    description: str = ""
    points: int = 1


class IdeaAgentCardOut(BaseModel):
    id: str
    title: str
    mainTopic: str
    summary: str
    whyNow: str
    fitReason: str
    evidence: list[str] = []
    risks: list[str] = []
    firstTasks: list[IdeaCardTaskOut] = []
    score: float = 0.0


class IdeaCardGenerateRequest(BaseModel):
    prompt: str = Field(min_length=1)


class IdeaCardGenerateResponse(BaseModel):
    cards: list[IdeaAgentCardOut]
    grounding: list[ChatSourceOut] = []


class IdeaCardSelectRequest(BaseModel):
    card: IdeaAgentCardOut


class IdeaCardDetailRequest(BaseModel):
    prompt: str = Field(min_length=1)
    card: IdeaAgentCardOut


class IdeaCardDetailResponse(BaseModel):
    card: IdeaAgentCardOut
    grounding: list[ChatSourceOut] = []


class IdeaCardSelectResponse(BaseModel):
    card: IdeaAgentCardOut
    tasks: list[TaskOut]
    projectMemory: ProjectMemoryOut
