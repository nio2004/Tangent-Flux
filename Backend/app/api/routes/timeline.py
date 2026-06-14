from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.routes.ideas import _get_idea
from app.core.database import get_db
from app.models import TimelineEntry
from app.schemas.workspace import TimelineOut
from app.services.serialization import timeline_out

router = APIRouter(prefix="/ideas", tags=["timeline"])


class TimelineCreate(BaseModel):
    text: str = Field(min_length=1)
    type: str = "journal"


@router.get("/{idea_id}/timeline", response_model=list[TimelineOut])
def list_timeline(idea_id: str, db: Session = Depends(get_db)):
    idea = _get_idea(db, idea_id)
    return [timeline_out(entry) for entry in idea.timeline_entries]


@router.post("/{idea_id}/timeline", response_model=TimelineOut)
def add_timeline(idea_id: str, payload: TimelineCreate, db: Session = Depends(get_db)):
    idea = _get_idea(db, idea_id)
    entry = TimelineEntry(idea_id=idea.id, content=payload.text, entry_type=payload.type)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return timeline_out(entry)

