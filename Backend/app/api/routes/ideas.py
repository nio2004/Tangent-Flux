from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Idea, IdeaNote, Resource
from app.schemas.idea import IdeaCreate, IdeaOut, IdeaUpdate
from app.services.memory_service import create_resource_and_chunks
from app.services.serialization import idea_out
from app.utils import dumps

router = APIRouter(prefix="/ideas", tags=["ideas"])


@router.get("", response_model=list[IdeaOut])
def list_ideas(query: str | None = None, filter: str | None = None, db: Session = Depends(get_db)):
    ideas = db.query(Idea).order_by(Idea.updated_at.desc()).all()
    result = []
    for idea in ideas:
        item = idea_out(db, idea)
        haystack = " ".join([item.title, item.description, *item.tags]).lower()
        if query and query.lower() not in haystack:
            continue
        if filter and filter != "All Signals" and filter.lower() not in [idea.status.lower(), *[tag.lower() for tag in item.tags]]:
            continue
        result.append(item)
    return result


@router.post("", response_model=IdeaOut)
def create_idea(payload: IdeaCreate, db: Session = Depends(get_db)):
    code = "".join(word[0] for word in payload.title.split()[:3]).upper() or "TF"
    idea = Idea(
        title=payload.title,
        status=payload.status,
        description=payload.description or payload.quick_note or "",
        problem=payload.problem or payload.description or "",
        tags_json=dumps(payload.tags),
        code=code[:6],
        activity="new",
        progress=0,
        importance=3,
    )
    db.add(idea)
    db.flush()
    if payload.quick_note:
        db.add(IdeaNote(idea_id=idea.id, markdown=payload.quick_note))
    if payload.source:
        create_resource_and_chunks(db, idea, payload.source)
    db.commit()
    db.refresh(idea)
    return idea_out(db, idea)


@router.get("/{idea_id}", response_model=IdeaOut)
def get_idea(idea_id: str, db: Session = Depends(get_db)):
    idea = _get_idea(db, idea_id)
    return idea_out(db, idea)


@router.patch("/{idea_id}", response_model=IdeaOut)
def update_idea(idea_id: str, payload: IdeaUpdate, db: Session = Depends(get_db)):
    idea = _get_idea(db, idea_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        if field == "tags":
            idea.tags_json = dumps(value)
        else:
            setattr(idea, field, value)
    db.commit()
    db.refresh(idea)
    return idea_out(db, idea)


@router.delete("/{idea_id}")
def delete_idea(idea_id: str, db: Session = Depends(get_db)):
    idea = _get_idea(db, idea_id)
    db.delete(idea)
    db.commit()
    return {"ok": True}


def _get_idea(db: Session, idea_id: str) -> Idea:
    idea = db.query(Idea).filter(Idea.id == idea_id).first()
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    return idea

