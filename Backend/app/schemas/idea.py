from typing import Literal

from pydantic import BaseModel, Field


IdeaStatus = Literal[
    "Prototype",
    "Incubating",
    "Exploration",
    "Pinned",
    "Research",
    "Buildable",
    "Experimental",
    "Capture",
    "Archive",
]
Activity = Literal["hot", "active", "quiet", "new"]


class IdeaCreate(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    description: str = ""
    problem: str = ""
    tags: list[str] = []
    status: IdeaStatus = "Capture"
    source: str | None = None
    quick_note: str | None = None


class IdeaUpdate(BaseModel):
    title: str | None = None
    status: IdeaStatus | None = None
    description: str | None = None
    problem: str | None = None
    tags: list[str] | None = None
    progress: int | None = None
    activity: Activity | None = None
    importance: int | None = None
    texture: str | None = None


class IdeaOut(BaseModel):
    id: str
    title: str
    status: IdeaStatus
    description: str
    tags: list[str]
    progress: int
    resources: int
    notes: int
    updated: str
    activity: Activity
    code: str
    importance: int
    texture: str
    problem: str
    memoryState: str
<<<<<<< HEAD
=======
    coverUrl: str | None = None
>>>>>>> 6f1c767a5b6ce400673ed3b3987875468dd9fa04

