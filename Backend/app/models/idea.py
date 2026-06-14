import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Idea(Base):
    __tablename__ = "ideas"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="Capture")
    description: Mapped[str] = mapped_column(Text, default="")
    problem: Mapped[str] = mapped_column(Text, default="")
    tags_json: Mapped[str] = mapped_column(Text, default="[]")
    progress: Mapped[int] = mapped_column(Integer, default=0)
    activity: Mapped[str] = mapped_column(String(20), default="new")
    code: Mapped[str] = mapped_column(String(16), default="TF")
    importance: Mapped[int] = mapped_column(Integer, default=3)
    texture: Mapped[str] = mapped_column(Text, default="")
    cover_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    memory_state: Mapped[str] = mapped_column(String(40), default="EMPTY")
    agent_1_validated: Mapped[bool] = mapped_column(Boolean, default=False)
    agent_2_validated: Mapped[bool] = mapped_column(Boolean, default=False)
    memory_initialized: Mapped[bool] = mapped_column(Boolean, default=False)
    last_memory_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    initialized_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    notes = relationship("IdeaNote", back_populates="idea", cascade="all, delete-orphan")
    resources = relationship("Resource", back_populates="idea", cascade="all, delete-orphan")
    chunks = relationship("Chunk", back_populates="idea", cascade="all, delete-orphan")
    memory = relationship("IdeaMemory", back_populates="idea", uselist=False, cascade="all, delete-orphan")
    project_memories = relationship("ProjectMemory", back_populates="idea", cascade="all, delete-orphan")
    graph_nodes = relationship("GraphNode", back_populates="idea", cascade="all, delete-orphan")
    graph_edges = relationship("GraphEdge", back_populates="idea", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="idea", cascade="all, delete-orphan")
    timeline_entries = relationship("TimelineEntry", back_populates="idea", cascade="all, delete-orphan")
    artifacts = relationship("Artifact", back_populates="idea", cascade="all, delete-orphan")
    agent_runs = relationship("AgentRun", back_populates="idea", cascade="all, delete-orphan")


class IdeaNote(Base):
    __tablename__ = "idea_notes"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    idea_id: Mapped[str] = mapped_column(String, ForeignKey("ideas.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(180), default="Research brief")
    markdown: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    idea = relationship("Idea", back_populates="notes")
