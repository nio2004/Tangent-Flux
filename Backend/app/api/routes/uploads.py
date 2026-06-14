from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.routes.ideas import _get_idea
from app.core.database import get_db
from app.models import Artifact, Chunk, Resource, TimelineEntry
from app.services.chunk_service import chunk_text, rough_token_count
from app.services.embedding_service import embedding_service
from app.services.image_service import data_url_for_image, ingest_image
from app.services.memory_service import sync_context_to_memory_and_tasks
from app.services.serialization import artifact_out
from app.utils import dumps

router = APIRouter(tags=["uploads"])


@router.post("/ideas/{idea_id}/cover")
def upload_cover_stub(idea_id: str):
    return {
        "coverUrl": None,
        "message": "Cover upload storage is reserved for the next pass; current frontend can keep local data URLs.",
    }


@router.post("/ideas/{idea_id}/artifacts/image")
async def upload_image_artifact(idea_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    idea = _get_idea(db, idea_id)
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=422, detail="Upload must be an image file.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=422, detail="Image file is empty.")

    filename = file.filename or "uploaded image"
    description = ingest_image(content, file.content_type, filename)
    data_url = data_url_for_image(content, file.content_type)
    title = filename

    resource = Resource(
        idea_id=idea.id,
        type="image",
        status="parsed",
        title=title,
        raw_content=title,
        clean_content=description,
        metadata_json=dumps({"content_type": file.content_type, "vision_ingested": True, "filename": filename}),
    )
    db.add(resource)
    db.flush()

    for position, text in enumerate(chunk_text(description)):
        db.add(
            Chunk(
                idea_id=idea.id,
                resource_id=resource.id,
                text=text,
                token_count=rough_token_count(text),
                embedding_json=dumps(embedding_service.embed(text)),
                position=position,
            )
        )

    artifact = Artifact(
        idea_id=idea.id,
        title=title,
        caption=description[:700],
        art="uploaded",
        asset_url=data_url,
    )
    db.add(artifact)
    db.add(TimelineEntry(idea_id=idea.id, entry_type="artifact", content=f"Uploaded and ingested image: {title}"))
    db.commit()
    db.refresh(artifact)
    await sync_context_to_memory_and_tasks(db, idea, description)
    return artifact_out(artifact)
