from datetime import datetime

from sqlalchemy.orm import Session

<<<<<<< HEAD
from app.models import AgentRun, Artifact, GraphEdge, GraphNode, Idea, IdeaMemory, Resource, Task, TimelineEntry
from app.schemas.graph import GraphEdgeOut, GraphNodeOut, GraphOut
=======
from app.models import AgentRun, Artifact, Chunk, GraphEdge, GraphNode, Idea, IdeaMemory, Resource, Task, TimelineEntry
from app.schemas.graph import GraphEdgeOut, GraphEvidenceOut, GraphNodeOut, GraphOut
>>>>>>> 6f1c767a5b6ce400673ed3b3987875468dd9fa04
from app.schemas.idea import IdeaOut
from app.schemas.memory import MemoryOut, ResourceOut
from app.schemas.task import KanbanBoardOut, TaskOut
from app.schemas.workspace import AgentRunOut, ArtifactOut, TimelineOut
from app.utils import iso, loads


def idea_out(db: Session, idea: Idea) -> IdeaOut:
    return IdeaOut(
        id=idea.id,
        title=idea.title,
        status=idea.status,
        description=idea.description,
        tags=loads(idea.tags_json, []),
        progress=idea.progress,
<<<<<<< HEAD
        resources=db.query(Resource).filter(Resource.idea_id == idea.id, Resource.type != "image").count(),
=======
        resources=db.query(Resource).filter(Resource.idea_id == idea.id, Resource.type.notin_(["image", "memory_update"])).count(),
>>>>>>> 6f1c767a5b6ce400673ed3b3987875468dd9fa04
        notes=len(idea.notes),
        updated=_friendly_updated(idea.updated_at),
        activity=idea.activity,
        code=idea.code,
        importance=idea.importance,
        texture=idea.texture,
        problem=idea.problem,
        memoryState=idea.memory_state,
<<<<<<< HEAD
    )


def graph_out(nodes: list[GraphNode], edges: list[GraphEdge]) -> GraphOut:
=======
        coverUrl=idea.cover_url,
    )


def graph_out(nodes: list[GraphNode], edges: list[GraphEdge], db: Session | None = None) -> GraphOut:
    evidence_by_chunk = _evidence_by_chunk(db, nodes) if db else {}
>>>>>>> 6f1c767a5b6ce400673ed3b3987875468dd9fa04
    return GraphOut(
        nodes=[
            GraphNodeOut(
                id=node.id,
                label=node.label,
                summary=node.summary,
                memberCount=node.member_count,
<<<<<<< HEAD
=======
                sourceIds=loads(node.source_chunk_ids_json, []),
                evidence=[
                    evidence_by_chunk[chunk_id]
                    for chunk_id in loads(node.source_chunk_ids_json, [])[:8]
                    if chunk_id in evidence_by_chunk
                ],
>>>>>>> 6f1c767a5b6ce400673ed3b3987875468dd9fa04
                createdBy=node.created_by,
            )
            for node in nodes
        ],
        edges=[
            GraphEdgeOut(
                id=edge.id,
                source=edge.source_node_id,
                target=edge.target_node_id,
                edgeType=edge.edge_type,
                weight=edge.weight,
                reason=edge.reason,
<<<<<<< HEAD
=======
                sharedEvidenceCount=_shared_evidence_count(nodes, edge),
>>>>>>> 6f1c767a5b6ce400673ed3b3987875468dd9fa04
            )
            for edge in edges
        ],
    )


<<<<<<< HEAD
=======
def _evidence_by_chunk(db: Session | None, nodes: list[GraphNode]) -> dict[str, GraphEvidenceOut]:
    if not db:
        return {}
    chunk_ids = {
        chunk_id
        for node in nodes
        for chunk_id in loads(node.source_chunk_ids_json, [])
    }
    if not chunk_ids:
        return {}
    chunks = db.query(Chunk).filter(Chunk.id.in_(chunk_ids)).all()
    resources = {
        resource.id: resource
        for resource in db.query(Resource).filter(Resource.id.in_({chunk.resource_id for chunk in chunks})).all()
    }
    result = {}
    for chunk in chunks:
        resource = resources.get(chunk.resource_id)
        if not resource:
            continue
        result[chunk.id] = GraphEvidenceOut(
            chunkId=chunk.id,
            resourceId=resource.id,
            resourceTitle=resource.title,
            resourceType=resource.type,
            sourceUrl=resource.source_url,
            position=chunk.position,
            preview=chunk.text[:220],
        )
    return result


def _shared_evidence_count(nodes: list[GraphNode], edge: GraphEdge) -> int:
    by_id = {node.id: set(loads(node.source_chunk_ids_json, [])) for node in nodes}
    return len(by_id.get(edge.source_node_id, set()) & by_id.get(edge.target_node_id, set()))


>>>>>>> 6f1c767a5b6ce400673ed3b3987875468dd9fa04
def memory_out(memory: IdeaMemory | None) -> MemoryOut | None:
    if not memory:
        return None
    return MemoryOut(textualSummary=memory.textual_summary, conceptMap=loads(memory.concept_map_json, {}))


def task_out(task: Task) -> TaskOut:
    return TaskOut(
        id=task.id,
        title=task.title,
        points=task.points,
        lane=task.lane,
        sortOrder=task.sort_order,
        description=task.description,
    )


def kanban_out(tasks: list[Task]) -> KanbanBoardOut:
    board = {"todo": [], "progress": [], "completed": []}
    for task in sorted(tasks, key=lambda item: item.sort_order):
        board.setdefault(task.lane, []).append(task_out(task))
    return KanbanBoardOut(**board)


def resource_out(resource: Resource) -> ResourceOut:
    return ResourceOut(
        id=resource.id,
        type=resource.type,
        title=resource.title,
        meta=f"{resource.type} / {resource.status}",
        description=(resource.clean_content or resource.error_message or "")[:180],
        sourceUrl=resource.source_url,
        status=resource.status,
    )


def timeline_out(entry: TimelineEntry) -> TimelineOut:
    return TimelineOut(id=entry.id, time=entry.created_at.strftime("%H:%M"), text=entry.content, type=entry.entry_type)


def artifact_out(artifact: Artifact) -> ArtifactOut:
    return ArtifactOut(
        id=artifact.id,
        title=artifact.title,
        caption=artifact.caption,
        art=artifact.art,
        assetUrl=artifact.asset_url,
    )


def agent_run_out(run: AgentRun) -> AgentRunOut:
    return AgentRunOut(
        id=run.id,
        agentType=run.agent_type,
        status=run.status,
        output=loads(run.output_json, {}),
        errorMessage=run.error_message,
        createdAt=iso(run.created_at) or "",
    )


def _friendly_updated(value: datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M")
