from typing import Literal

from pydantic import BaseModel, Field


Lane = Literal["todo", "progress", "completed"]


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=220)
    description: str = ""
    lane: Lane = "todo"
    points: int = 1


class TaskMove(BaseModel):
    lane: Lane
    sortOrder: int = 1000


class TaskOut(BaseModel):
    id: str
    title: str
    points: int
    lane: Lane
    sortOrder: int
    description: str = ""


class KanbanBoardOut(BaseModel):
    todo: list[TaskOut]
    progress: list[TaskOut]
    completed: list[TaskOut]

