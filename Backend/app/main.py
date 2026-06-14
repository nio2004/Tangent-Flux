from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import artifacts, chat, graph_overview, ideas, memory, tasks, timeline, uploads, workspace
from app.core.config import get_settings
from app.core.database import Base, SessionLocal, engine
from app.models import *  # noqa: F401,F403
from app.services.seed_service import seed_if_empty

settings = get_settings()

app = FastAPI(title="Tangent-Flux Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1):\d+$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ideas.router, prefix="/api")
app.include_router(graph_overview.router, prefix="/api")
app.include_router(workspace.router, prefix="/api")
app.include_router(memory.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(timeline.router, prefix="/api")
app.include_router(artifacts.router, prefix="/api")
app.include_router(uploads.router, prefix="/api")
app.include_router(chat.router, prefix="/api")


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_if_empty(db)
    finally:
        db.close()


@app.get("/health")
def health():
    return {"ok": True, "service": "tangent-flux-backend"}
