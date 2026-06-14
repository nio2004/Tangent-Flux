from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.routes.ideas import _get_idea
from app.core.database import get_db
from app.schemas.workspace import WorkspaceOut
from app.services.workspace_service import hydrate_workspace

router = APIRouter(prefix="/ideas", tags=["workspace"])


@router.get("/{idea_id}/workspace", response_model=WorkspaceOut)
def get_workspace(idea_id: str, db: Session = Depends(get_db)):
    idea = _get_idea(db, idea_id)
    return hydrate_workspace(db, idea)

