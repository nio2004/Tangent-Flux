import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class GraphNode(Base):
    __tablename__ = "graph_nodes"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    idea_id: Mapped[str] = mapped_column(String, ForeignKey("ideas.id"), nullable=False)
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="")
    centroid_embedding_json: Mapped[str] = mapped_column(Text, default="[]")
    member_count: Mapped[int] = mapped_column(Integer, default=0)
    source_chunk_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    created_by: Mapped[str] = mapped_column(String(40), default="AGENT_2")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    idea = relationship("Idea", back_populates="graph_nodes")


class GraphEdge(Base):
    __tablename__ = "graph_edges"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    idea_id: Mapped[str] = mapped_column(String, ForeignKey("ideas.id"), nullable=False)
    source_node_id: Mapped[str] = mapped_column(String, ForeignKey("graph_nodes.id"), nullable=False)
    target_node_id: Mapped[str] = mapped_column(String, ForeignKey("graph_nodes.id"), nullable=False)
    edge_type: Mapped[str] = mapped_column(String(40), default="SIMILARITY")
    weight: Mapped[float] = mapped_column(Float, default=0.0)
    reason: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    idea = relationship("Idea", back_populates="graph_edges", foreign_keys=[idea_id])
