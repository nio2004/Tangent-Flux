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
        sort_order=_next_lane_sort_order(db, idea_id, payload.lane),
        source_agent_run_id=source_agent_run_id,
    )
    db.add(task)
    db.flush()
    return task


def move_task(db: Session, task: Task, payload: TaskMove) -> Task:
    task.lane = payload.lane
    task.sort_order = _next_lane_sort_order(db, task.idea_id, payload.lane, exclude_task_id=task.id)
    db.flush()
    return task


def _next_lane_sort_order(db: Session, idea_id: str, lane: str, exclude_task_id: str | None = None) -> int:
    query = db.query(Task).filter(Task.idea_id == idea_id, Task.lane == lane)
    if exclude_task_id:
        query = query.filter(Task.id != exclude_task_id)

    max_sort_order = max((task.sort_order for task in query.all()), default=0)
    return max_sort_order + 1

