from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.routes.ideas import _get_idea
from app.core.database import get_db
from app.models import AgentRun, GraphEdge, GraphNode, IdeaMemory, Resource
from app.schemas.memory import DumpRequest, DumpResponse, InitializeRequest, MemoryOut, QueryRequest, QueryResponse, ResourceCreate, ResourceOut
from app.services.memory_service import create_resource_and_chunks, dump_update, generate_tasks, initialize_memory, query_memory
from app.services.serialization import agent_run_out, graph_out, memory_out, resource_out

router = APIRouter(prefix="/ideas", tags=["memory"])


@router.post("/{idea_id}/resources", response_model=ResourceOut)
async def create_resource(idea_id: str, payload: ResourceCreate, db: Session = Depends(get_db)):
    idea = _get_idea(db, idea_id)
    try:
        if idea.memory_state == "MEMORY_READY" and idea.memory_initialized:
            await dump_update(db, idea, payload.input)
            await generate_tasks(db, idea)
            resource = db.query(Resource).filter(Resource.idea_id == idea.id).order_by(Resource.created_at.desc()).first()
            if payload.title and resource:
                resource.title = payload.title
                db.commit()
                db.refresh(resource)
            return resource_out(resource)
        resource, _ = create_resource_and_chunks(db, idea, payload.input, payload.title)
    except HTTPException:
        db.rollback()
        raise
    db.commit()
    db.refresh(resource)
    return resource_out(resource)


@router.get("/{idea_id}/resources", response_model=list[ResourceOut])
def list_resources(idea_id: str, db: Session = Depends(get_db)):
    idea = _get_idea(db, idea_id)
    return [resource_out(resource) for resource in idea.resources if resource.type not in {"image", "memory_update"}]


@router.post("/{idea_id}/initialize")
async def initialize(idea_id: str, payload: InitializeRequest, db: Session = Depends(get_db)):
    idea = _get_idea(db, idea_id)
    await initialize_memory(db, idea, payload.input)
    nodes = db.query(GraphNode).filter(GraphNode.idea_id == idea.id).all()
    edges = db.query(GraphEdge).filter(GraphEdge.idea_id == idea.id).all()
    memory = db.query(IdeaMemory).filter(IdeaMemory.idea_id == idea.id).first()
    return {"memory": memory_out(memory), "graph": graph_out(nodes, edges)}


@router.post("/{idea_id}/dump", response_model=DumpResponse)
async def dump(idea_id: str, payload: DumpRequest, db: Session = Depends(get_db)):
    idea = _get_idea(db, idea_id)
    return await dump_update(db, idea, payload.input)


@router.get("/{idea_id}/memory", response_model=MemoryOut | None)
def get_memory(idea_id: str, db: Session = Depends(get_db)):
    idea = _get_idea(db, idea_id)
    return memory_out(db.query(IdeaMemory).filter(IdeaMemory.idea_id == idea.id).first())


@router.get("/{idea_id}/graph")
def get_graph(idea_id: str, db: Session = Depends(get_db)):
    idea = _get_idea(db, idea_id)
    nodes = db.query(GraphNode).filter(GraphNode.idea_id == idea.id).all()
    edges = db.query(GraphEdge).filter(GraphEdge.idea_id == idea.id).all()
    return graph_out(nodes, edges)


@router.get("/{idea_id}/agent-runs")
def get_agent_runs(idea_id: str, db: Session = Depends(get_db)):
    idea = _get_idea(db, idea_id)
    runs = db.query(AgentRun).filter(AgentRun.idea_id == idea.id).order_by(AgentRun.created_at.desc()).all()
    return [agent_run_out(run) for run in runs]


@router.post("/{idea_id}/query", response_model=QueryResponse)
async def query(idea_id: str, payload: QueryRequest, db: Session = Depends(get_db)):
    idea = _get_idea(db, idea_id)
    output = await query_memory(db, idea, payload.question)
    return QueryResponse(answer=output.answer, sourceNodes=output.source_nodes)


@router.post("/{idea_id}/generate")
async def generate(idea_id: str, db: Session = Depends(get_db)):
    idea = _get_idea(db, idea_id)
    return (await generate_tasks(db, idea)).model_dump()
