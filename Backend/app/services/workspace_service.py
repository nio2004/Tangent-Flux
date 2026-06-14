from sqlalchemy.orm import Session

from app.models import AgentRun, Artifact, GraphEdge, GraphNode, Idea, IdeaMemory, Resource, Task, TimelineEntry
from app.schemas.graph import GraphOut
from app.schemas.workspace import NoteOut, WorkspaceOut
from app.services.serialization import (
    agent_run_out,
    artifact_out,
    graph_out,
    idea_out,
    kanban_out,
    memory_out,
    resource_out,
    timeline_out,
)


def hydrate_workspace(db: Session, idea: Idea) -> WorkspaceOut:
    nodes = db.query(GraphNode).filter(GraphNode.idea_id == idea.id).all()
    edges = db.query(GraphEdge).filter(GraphEdge.idea_id == idea.id).all()
    memory = db.query(IdeaMemory).filter(IdeaMemory.idea_id == idea.id).first()
    tasks = db.query(Task).filter(Task.idea_id == idea.id).all()
    resources = (
        db.query(Resource)
        .filter(Resource.idea_id == idea.id, Resource.type != "image")
        .order_by(Resource.created_at.desc())
        .all()
    )
    timeline = db.query(TimelineEntry).filter(TimelineEntry.idea_id == idea.id).order_by(TimelineEntry.created_at.desc()).all()
    artifacts = db.query(Artifact).filter(Artifact.idea_id == idea.id).order_by(Artifact.created_at.desc()).all()
    agent_runs = db.query(AgentRun).filter(AgentRun.idea_id == idea.id).order_by(AgentRun.created_at.desc()).limit(10).all()
    return WorkspaceOut(
        idea=idea_out(db, idea),
        notes=[NoteOut(id=note.id, title=note.title, markdown=note.markdown) for note in idea.notes],
        resources=[resource_out(resource) for resource in resources],
        tasks=kanban_out(tasks),
        timeline=[timeline_out(entry) for entry in timeline],
        artifacts=[artifact_out(artifact) for artifact in artifacts],
        coverUrl=idea.cover_url,
        memory=memory_out(memory),
        graph=graph_out(nodes, edges, db) if nodes else GraphOut(nodes=[], edges=[]),
        agentRuns=[agent_run_out(run) for run in agent_runs],
    )
