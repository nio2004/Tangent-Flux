from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.routes.ideas import _get_idea
from app.core.database import get_db
from app.models import Artifact, TimelineEntry
from app.schemas.workspace import ArtifactOut
from app.services.serialization import artifact_out

router = APIRouter(prefix="/ideas", tags=["artifacts"])


class ArtifactCreate(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    caption: str = ""
    art: str = "mesh"
    assetUrl: str | None = None


@router.get("/{idea_id}/artifacts", response_model=list[ArtifactOut])
def list_artifacts(idea_id: str, db: Session = Depends(get_db)):
    idea = _get_idea(db, idea_id)
    artifacts = db.query(Artifact).filter(Artifact.idea_id == idea.id).order_by(Artifact.created_at.desc()).all()
    return [artifact_out(artifact) for artifact in artifacts]


@router.post("/{idea_id}/artifacts", response_model=ArtifactOut)
def create_artifact(idea_id: str, payload: ArtifactCreate, db: Session = Depends(get_db)):
    idea = _get_idea(db, idea_id)
    artifact = Artifact(
        idea_id=idea.id,
        title=payload.title,
        caption=payload.caption,
        art=payload.art,
        asset_url=payload.assetUrl,
    )
    db.add(artifact)
    db.add(TimelineEntry(idea_id=idea.id, entry_type="artifact", content=f"Created artifact: {artifact.title}"))
    db.commit()
    db.refresh(artifact)
    return artifact_out(artifact)
