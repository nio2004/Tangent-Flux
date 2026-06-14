import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Artifact(Base):
    __tablename__ = "artifacts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    idea_id: Mapped[str] = mapped_column(String, ForeignKey("ideas.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    caption: Mapped[str] = mapped_column(Text, default="")
    art: Mapped[str] = mapped_column(String(60), default="mesh")
    asset_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    idea = relationship("Idea", back_populates="artifacts")
