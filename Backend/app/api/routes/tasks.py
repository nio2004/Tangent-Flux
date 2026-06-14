from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.routes.ideas import _get_idea
from app.core.database import get_db
from app.models import Task, TimelineEntry
from app.schemas.task import KanbanBoardOut, TaskCreate, TaskMove, TaskOut
from app.services.serialization import kanban_out, task_out
from app.services.task_service import create_task, move_task
from app.services.project_memory_service import append_project_memory_event, get_active_project_memory

router = APIRouter(tags=["tasks"])


@router.get("/ideas/{idea_id}/tasks", response_model=KanbanBoardOut)
def list_tasks(idea_id: str, db: Session = Depends(get_db)):
    idea = _get_idea(db, idea_id)
    return kanban_out(idea.tasks)


@router.post("/ideas/{idea_id}/tasks", response_model=TaskOut)
def add_task(idea_id: str, payload: TaskCreate, db: Session = Depends(get_db)):
    idea = _get_idea(db, idea_id)
    task = create_task(db, idea.id, payload)
    db.add(TimelineEntry(idea_id=idea.id, entry_type="task", content=f"Added task: {task.title}"))
    project_memory = get_active_project_memory(db, idea)
    if project_memory:
        append_project_memory_event(
            db,
            project_memory,
            "task_created",
            f"Added task '{task.title}' to {task.lane}.",
            {"task_id": task.id, "lane": task.lane, "points": task.points},
        )
    db.commit()
    db.refresh(task)
    return task_out(task)


@router.patch("/tasks/{task_id}", response_model=TaskOut)
def patch_task(task_id: str, payload: TaskCreate, db: Session = Depends(get_db)):
    task = _get_task(db, task_id)
    task.title = payload.title
    task.description = payload.description
    task.lane = payload.lane
    task.points = payload.points
    idea = _get_idea(db, task.idea_id)
    project_memory = get_active_project_memory(db, idea)
    if project_memory:
        append_project_memory_event(
            db,
            project_memory,
            "task_updated",
            f"Updated task '{task.title}' in {task.lane}.",
            {"task_id": task.id, "lane": task.lane, "points": task.points},
        )
    db.commit()
    db.refresh(task)
    return task_out(task)


@router.post("/tasks/{task_id}/move", response_model=TaskOut)
def move(task_id: str, payload: TaskMove, db: Session = Depends(get_db)):
    task = _get_task(db, task_id)
    move_task(db, task, payload)
    db.add(TimelineEntry(idea_id=task.idea_id, entry_type="task", content=f"Moved task '{task.title}' to {task.lane}."))
    idea = _get_idea(db, task.idea_id)
    project_memory = get_active_project_memory(db, idea)
    if project_memory:
        append_project_memory_event(
            db,
            project_memory,
            "task_moved",
            f"Moved task '{task.title}' to {task.lane}.",
            {"task_id": task.id, "lane": task.lane, "sort_order": task.sort_order},
        )
    db.commit()
    db.refresh(task)
    return task_out(task)


def _get_task(db: Session, task_id: str) -> Task:
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

