from pydantic import BaseModel, Field


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


class ChatResponseOut(BaseModel):
    session: ChatSessionOut
    userMessage: ChatMessageOut
    assistantMessage: ChatMessageOut
