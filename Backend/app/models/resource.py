import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Resource(Base):
    __tablename__ = "resources"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    idea_id: Mapped[str] = mapped_column(String, ForeignKey("ideas.id"), nullable=False)
    type: Mapped[str] = mapped_column(String(40), default="raw_text")
    status: Mapped[str] = mapped_column(String(40), default="parsed")
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    title: Mapped[str] = mapped_column(String(240), default="Untitled resource")
    raw_content: Mapped[str] = mapped_column(Text, default="")
    clean_content: Mapped[str] = mapped_column(Text, default="")
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    idea = relationship("Idea", back_populates="resources")
