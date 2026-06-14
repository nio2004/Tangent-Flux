from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.routes.ideas import _get_idea
from app.core.database import get_db
from app.models import IdeaNote, TimelineEntry
from app.schemas.workspace import NoteOut, NoteUpdate, WorkspaceOut
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
    note = idea.notes[0] if idea.notes else IdeaNote(idea_id=idea.id)
    note.title = payload.title
    note.markdown = payload.markdown
    db.add(note)
    db.add(TimelineEntry(idea_id=idea.id, entry_type="note", content="Updated idea dump."))
    db.commit()
    db.refresh(note)
    await sync_context_to_memory_and_tasks(db, idea, payload.markdown)
    return NoteOut(id=note.id, title=note.title, markdown=note.markdown)

