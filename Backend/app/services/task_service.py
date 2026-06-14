from sqlalchemy.orm import Session

from app.models import Task
from app.schemas.task import TaskCreate, TaskMove


def create_task(db: Session, idea_id: str, payload: TaskCreate, source_agent_run_id: str | None = None) -> Task:
    task = Task(
        idea_id=idea_id,
        title=payload.title,
        description=payload.description,
        lane=payload.lane,
        points=payload.points,
        sort_order=1000,
        source_agent_run_id=source_agent_run_id,
    )
    db.add(task)
    db.flush()
    return task


def move_task(db: Session, task: Task, payload: TaskMove) -> Task:
    task.lane = payload.lane
    task.sort_order = payload.sortOrder
    db.flush()
    return task

