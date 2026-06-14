from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.routes.ideas import _get_idea
from app.core.database import get_db
from app.models import IdeaNote, TimelineEntry
from app.schemas.workspace import NoteOut, NoteUpdate, WorkspaceOut
from app.services.workspace_service import hydrate_workspace

router = APIRouter(prefix="/ideas", tags=["workspace"])


@router.get("/{idea_id}/workspace", response_model=WorkspaceOut)
def get_workspace(idea_id: str, db: Session = Depends(get_db)):
    idea = _get_idea(db, idea_id)
    return hydrate_workspace(db, idea)


@router.put("/{idea_id}/notes", response_model=NoteOut)
def save_idea_note(idea_id: str, payload: NoteUpdate, db: Session = Depends(get_db)):
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
    return NoteOut(id=note.id, title=note.title, markdown=note.markdown)

