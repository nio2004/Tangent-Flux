from datetime import datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Idea, ProjectMemory, ProjectMemoryEvent
from app.schemas.chat import IdeaAgentCardOut
from app.schemas.project_memory import ProjectMemoryEventOut, ProjectMemoryOut, ProjectMemoryPayload
from app.utils import dumps, iso, loads


def get_active_project_memory(db: Session, idea: Idea) -> ProjectMemory | None:
    return (
        db.query(ProjectMemory)
        .filter(ProjectMemory.idea_id == idea.id, ProjectMemory.is_active.is_(True))
        .order_by(ProjectMemory.updated_at.desc())
        .first()
    )


def get_project_memory(db: Session, idea: Idea, project_memory_id: str) -> ProjectMemory:
    project_memory = (
        db.query(ProjectMemory)
        .filter(ProjectMemory.id == project_memory_id, ProjectMemory.idea_id == idea.id)
        .first()
    )
    if not project_memory:
        raise HTTPException(status_code=404, detail="Project memory not found.")
    return project_memory


def create_project_memory_for_card(
    db: Session,
    idea: Idea,
    card: IdeaAgentCardOut,
    tasks: list[Any],
    grounding: list[Any] | None = None,
) -> ProjectMemory:
    for existing in db.query(ProjectMemory).filter(ProjectMemory.idea_id == idea.id, ProjectMemory.is_active.is_(True)).all():
        existing.is_active = False
        existing.status = "INACTIVE"

    task_payload = [_task_payload(task) for task in tasks]
    selected_card = card.model_dump()
    project_memory = ProjectMemory(
        idea_id=idea.id,
        card_id=card.id,
        title=card.title,
        main_topic=card.mainTopic,
        selected_card_json=dumps(selected_card),
        textual_summary=_initial_summary(card, task_payload),
        status="ACTIVE",
        is_active=True,
        last_refreshed_at=datetime.utcnow(),
    )
    db.add(project_memory)
    db.flush()
    append_project_memory_event(
        db,
        project_memory,
        "selected_card",
        f"Selected project card '{card.title}' under {card.mainTopic}.",
        {"card": selected_card, "grounding": grounding or []},
        refresh=False,
    )
    append_project_memory_event(
        db,
        project_memory,
        "generated_tasks",
        f"Created {len(task_payload)} TODO tasks from selected card.",
        {"tasks": task_payload},
        refresh=True,
    )
    return project_memory


def append_project_memory_event(
    db: Session,
    project_memory: ProjectMemory,
    event_type: str,
    content: str,
    metadata: dict | None = None,
    refresh: bool = True,
) -> ProjectMemoryEvent:
    event = ProjectMemoryEvent(
        project_memory_id=project_memory.id,
        idea_id=project_memory.idea_id,
        event_type=event_type,
        content=content,
        metadata_json=dumps(metadata or {}),
    )
    project_memory.updated_at = datetime.utcnow()
    db.add(event)
    db.flush()
    if refresh:
        refresh_project_memory_summary(db, project_memory)
    return event


def refresh_project_memory_summary(db: Session, project_memory: ProjectMemory) -> ProjectMemory:
    events = (
        db.query(ProjectMemoryEvent)
        .filter(ProjectMemoryEvent.project_memory_id == project_memory.id)
        .order_by(ProjectMemoryEvent.created_at.desc())
        .limit(12)
        .all()
    )
    card = loads(project_memory.selected_card_json, {})
    parts = [
        f"Project: {project_memory.title}",
        f"Topic: {project_memory.main_topic or card.get('mainTopic', 'Selected idea card')}",
    ]
    summary = card.get("summary")
    if summary:
        parts.append(f"Card summary: {summary}")
    if card.get("fitReason"):
        parts.append(f"Fit: {card['fitReason']}")
    recent = [f"- {event.event_type}: {event.content}" for event in reversed(events) if event.content]
    if recent:
        parts.append("Recent captured activity:\n" + "\n".join(recent[-8:]))
    project_memory.textual_summary = "\n".join(parts)[:4000]
    project_memory.last_refreshed_at = datetime.utcnow()
    db.add(project_memory)
    db.flush()
    return project_memory


def project_memory_payload(db: Session, idea: Idea) -> ProjectMemoryPayload:
    project_memory = get_active_project_memory(db, idea)
    if not project_memory:
        return ProjectMemoryPayload()
    events = recent_project_memory_events(db, project_memory)
    return ProjectMemoryPayload(projectMemory=project_memory_out(project_memory), recentEvents=[project_memory_event_out(event) for event in events])


def recent_project_memory_events(db: Session, project_memory: ProjectMemory, limit: int = 8) -> list[ProjectMemoryEvent]:
    return (
        db.query(ProjectMemoryEvent)
        .filter(ProjectMemoryEvent.project_memory_id == project_memory.id)
        .order_by(ProjectMemoryEvent.created_at.desc())
        .limit(limit)
        .all()
    )


def project_memory_out(project_memory: ProjectMemory) -> ProjectMemoryOut:
    selected_card = None
    card_payload = loads(project_memory.selected_card_json, {})
    if card_payload:
        selected_card = card_payload
    return ProjectMemoryOut(
        id=project_memory.id,
        ideaId=project_memory.idea_id,
        cardId=project_memory.card_id,
        title=project_memory.title,
        mainTopic=project_memory.main_topic,
        selectedCard=selected_card,
        textualSummary=project_memory.textual_summary,
        status=project_memory.status,
        isActive=project_memory.is_active,
        createdAt=iso(project_memory.created_at) or "",
        updatedAt=iso(project_memory.updated_at) or "",
        lastRefreshedAt=iso(project_memory.last_refreshed_at) or "",
    )


def project_memory_event_out(event: ProjectMemoryEvent) -> ProjectMemoryEventOut:
    return ProjectMemoryEventOut(
        id=event.id,
        projectMemoryId=event.project_memory_id,
        ideaId=event.idea_id,
        eventType=event.event_type,
        content=event.content,
        metadata=loads(event.metadata_json, {}),
        createdAt=iso(event.created_at) or "",
    )


def _initial_summary(card: IdeaAgentCardOut, tasks: list[dict]) -> str:
    task_lines = "\n".join(f"- {task['title']}" for task in tasks[:8])
    return (
        f"Project: {card.title}\n"
        f"Topic: {card.mainTopic}\n"
        f"Card summary: {card.summary}\n"
        f"Why now: {card.whyNow}\n"
        f"Fit: {card.fitReason}\n"
        f"Initial TODOs:\n{task_lines or '- No tasks generated yet.'}"
    )[:4000]


def _task_payload(task: Any) -> dict:
    return {
        "id": getattr(task, "id", None),
        "title": getattr(task, "title", ""),
        "description": getattr(task, "description", ""),
        "lane": getattr(task, "lane", ""),
        "points": getattr(task, "points", 0),
    }
