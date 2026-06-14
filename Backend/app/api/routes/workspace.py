from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.routes.ideas import _get_idea
from app.core.database import get_db
from app.models import IdeaNote, TimelineEntry
from app.schemas.workspace import CoverUpdate, NoteOut, NoteUpdate, WorkspaceOut
from app.services.memory_service import sync_context_to_memory_and_tasks
from app.services.workspace_service import hydrate_workspace

router = APIRouter(prefix="/ideas", tags=["workspace"])


@router.get("/{idea_id}/workspace", response_model=WorkspaceOut)
def get_workspace(idea_id: str, db: Session = Depends(get_db)):
    idea = _get_idea(db, idea_id)
    return hydrate_workspace(db, idea)


@router.put("/{idea_id}/notes", response_model=NoteOut)
async def save_notes(idea_id: str, payload: NoteUpdate, db: Session = Depends(get_db)):
    idea = _get_idea(db, idea_id)
    note = db.query(IdeaNote).filter(IdeaNote.idea_id == idea.id).order_by(IdeaNote.created_at.asc()).first()
    if note:
        note.title = payload.title
        note.markdown = payload.markdown
    else:
        note = IdeaNote(idea_id=idea.id, title=payload.title, markdown=payload.markdown)
    db.add(note)
    db.add(TimelineEntry(idea_id=idea.id, entry_type="note", content="Saved idea dump."))
    db.commit()
    db.refresh(note)
    await sync_context_to_memory_and_tasks(db, idea, payload.markdown)
    return NoteOut(id=note.id, title=note.title, markdown=note.markdown)


@router.put("/{idea_id}/cover")
def save_cover(idea_id: str, payload: CoverUpdate, db: Session = Depends(get_db)):
    idea = _get_idea(db, idea_id)
    idea.cover_url = payload.coverUrl
    db.add(idea)
    db.commit()
    db.refresh(idea)
    return {"coverUrl": idea.cover_url}

