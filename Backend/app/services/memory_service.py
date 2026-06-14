import time
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.agents.agent1_schema import run_agent1
from app.agents.agent2_memory import run_agent2_text_memory
from app.agents.agent3_update import run_agent3_summary
from app.agents.agent4_generate import run_agent4_generate, run_agent4_query
from app.models import AgentRun, Chunk, GraphEdge, GraphNode, Idea, IdeaMemory, Resource, Task, TimelineEntry
from app.schemas.agent import Agent1Output
from app.schemas.memory import DumpResponse
from app.schemas.task import TaskCreate
from app.services.chunk_service import chunk_text, rough_token_count
from app.services.embedding_service import embedding_service
from app.services.graph_service import create_similarity_edges, get_graph, upsert_bridge_edge
from app.services.parser_service import ParseError, parse_input
from app.services.serialization import graph_out
from app.services.similarity_service import cosine_similarity, mean_embedding, running_mean
from app.services.task_service import create_task
from app.utils import dumps, loads


def create_resource_and_chunks(
    db: Session,
    idea: Idea,
    input_value: str,
    title: str | None = None,
    fail_soft: bool = False,
) -> tuple[Resource, list[Chunk]]:
    try:
        parsed = parse_input(input_value, title)
        resource = Resource(
            idea_id=idea.id,
            type=parsed.source_type,
            status="parsed",
            source_url=parsed.source_url,
            title=parsed.title,
            raw_content=input_value,
            clean_content=parsed.clean_content,
            metadata_json=dumps(parsed.metadata or {}),
        )
    except ParseError as exc:
        resource = Resource(
            idea_id=idea.id,
            type="failed",
            status="failed",
            title=title or "Failed resource",
            raw_content=input_value,
            clean_content="",
            error_message=str(exc),
        )
        db.add(resource)
        db.flush()
        if fail_soft:
            return resource, []
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    db.add(resource)
    db.flush()
    chunks: list[Chunk] = []
    for position, text in enumerate(chunk_text(resource.clean_content)):
        embedding = embedding_service.embed(text)
        chunk = Chunk(
            idea_id=idea.id,
            resource_id=resource.id,
            text=text,
            token_count=rough_token_count(text),
            embedding_json=dumps(embedding),
            position=position,
        )
        db.add(chunk)
        chunks.append(chunk)
    db.flush()
    return resource, chunks


async def initialize_memory(db: Session, idea: Idea, initial_input: str | None = None) -> None:
    started = time.perf_counter()
    try:
        _reset_existing_memory(db, idea)
        if initial_input:
            create_resource_and_chunks(db, idea, initial_input)
        chunks = db.query(Chunk).filter(Chunk.idea_id == idea.id).all()
        if not chunks:
            seed_text = f"{idea.title}. {idea.description} {idea.problem}"
            create_resource_and_chunks(db, idea, seed_text, "Initial idea brief")
            chunks = db.query(Chunk).filter(Chunk.idea_id == idea.id).all()

        idea.memory_state = "AGENT_1_RUNNING"
        db.flush()
        sources = {chunk.id: chunk.text for chunk in chunks}
        intent = _idea_intent(idea)
        agent1 = await run_agent1(intent, sources)
        _validate_agent1(agent1)
        _log_agent(db, idea.id, "AGENT_1", {"sources": list(sources)}, agent1.model_dump(), started)
        idea.agent_1_validated = True
        idea.memory_state = "AGENT_1_VALIDATED"
        db.flush()

        idea.memory_state = "AGENT_2_RUNNING"
        await _run_agent2(db, idea, agent1, chunks)
        idea.agent_2_validated = True
        idea.memory_initialized = True
        idea.memory_state = "MEMORY_READY"
        idea.initialized_at = datetime.utcnow()
        idea.last_memory_error = None
        db.add(TimelineEntry(idea_id=idea.id, entry_type="memory", content="Initialized memory graph and textual memory."))
        db.commit()
    except Exception as exc:
        db.rollback()
        idea.memory_state = "MEMORY_FAILED"
        idea.last_memory_error = str(exc)
        db.add(idea)
        db.commit()
        raise


def _reset_existing_memory(db: Session, idea: Idea) -> None:
    for edge in db.query(GraphEdge).filter(GraphEdge.idea_id == idea.id).all():
        db.delete(edge)
    for node in db.query(GraphNode).filter(GraphNode.idea_id == idea.id).all():
        db.delete(node)
    existing_memory = db.query(IdeaMemory).filter(IdeaMemory.idea_id == idea.id).first()
    if existing_memory:
        db.delete(existing_memory)
        idea.memory = None
    idea.agent_1_validated = False
    idea.agent_2_validated = False
    idea.memory_initialized = False
    idea.memory_state = "EMPTY"
    idea.last_memory_error = None
    idea.initialized_at = None
    db.flush()


async def _run_agent2(db: Session, idea: Idea, agent1: Agent1Output, chunks: list[Chunk]) -> None:
    started = time.perf_counter()
    concept_embeddings = {concept: embedding_service.embed(concept) for concept in agent1.umbrella_concepts}
    assignments = _assign_chunks_to_concepts(agent1, chunks, concept_embeddings)
    text_memory = await run_agent2_text_memory(
        _idea_intent(idea),
        {concept: [chunk.text for chunk in assigned] for concept, assigned in assignments.items()},
    )
    summary_by_label = {item.label.lower(): item.summary for item in text_memory.node_summaries}
    nodes: list[GraphNode] = []
    for concept, assigned in assignments.items():
        vectors = [loads(chunk.embedding_json, []) for chunk in assigned]
        centroid = mean_embedding(vectors) if vectors else concept_embeddings[concept]
        node = GraphNode(
            idea_id=idea.id,
            label=concept,
            summary=summary_by_label.get(concept.lower(), f"{concept} is part of the initial memory."),
            centroid_embedding_json=dumps(centroid),
            member_count=len(assigned),
            source_chunk_ids_json=dumps([chunk.id for chunk in assigned]),
            created_by="AGENT_2",
        )
        db.add(node)
        nodes.append(node)
    db.flush()
    create_similarity_edges(db, idea.id, nodes)
    label_to_node = {node.label.lower(): node for node in nodes}
    for hint in agent1.bridge_hints:
        source = label_to_node.get(hint.concept_a.lower())
        target = label_to_node.get(hint.concept_b.lower())
        if source and target:
            upsert_bridge_edge(db, idea.id, source.id, target.id, 0.75, hint.reason)
    concept_map = {
        node.label: {
            "summary": node.summary,
            "source_ids": loads(node.source_chunk_ids_json, []),
            "connected_concepts": [],
        }
        for node in nodes
    }
    db.add(IdeaMemory(idea_id=idea.id, textual_summary=text_memory.textual_summary, concept_map_json=dumps(concept_map)))
    _log_agent(db, idea.id, "AGENT_2", {"concepts": agent1.umbrella_concepts}, {"textual_summary": text_memory.textual_summary}, started)


def _idea_intent(idea: Idea) -> str:
    note_text = " ".join(note.markdown for note in idea.notes)
    return " ".join(part for part in [idea.title, idea.description, idea.problem, note_text] if part).strip()


def _assign_chunks_to_concepts(
    agent1: Agent1Output,
    chunks: list[Chunk],
    concept_embeddings: dict[str, list[float]],
) -> dict[str, list[Chunk]]:
    assignments: dict[str, list[Chunk]] = {concept: [] for concept in agent1.umbrella_concepts}
    assigned_ids: set[str] = set()
    for chunk in chunks:
        scores = {
            concept: _chunk_concept_score(chunk, concept, agent1, concept_embeddings)
            for concept in agent1.umbrella_concepts
        }
        best = max(scores, key=scores.get)
        assignments[best].append(chunk)
        assigned_ids.add(chunk.id)

    for concept in agent1.umbrella_concepts:
        if assignments[concept]:
            continue
        candidates = sorted(
            chunks,
            key=lambda chunk: _chunk_concept_score(chunk, concept, agent1, concept_embeddings),
            reverse=True,
        )
        replacement = next((chunk for chunk in candidates if chunk.id not in assigned_ids), None)
        if replacement:
            assignments[concept].append(replacement)
            assigned_ids.add(replacement.id)
            continue
        donor = max(assignments, key=lambda label: len(assignments[label]))
        if len(assignments[donor]) > 1:
            assignments[concept].append(assignments[donor].pop())

    return {concept: assigned for concept, assigned in assignments.items() if assigned}


def _chunk_concept_score(
    chunk: Chunk,
    concept: str,
    agent1: Agent1Output,
    concept_embeddings: dict[str, list[float]],
) -> float:
    chunk_embedding = loads(chunk.embedding_json, [])
    score = cosine_similarity(chunk_embedding, concept_embeddings[concept])
    text = chunk.text.lower()
    concept_tokens = [token for token in concept.lower().replace("-", " ").split() if len(token) > 3]
    if concept_tokens:
        overlap = sum(1 for token in concept_tokens if token in text) / len(concept_tokens)
        score += overlap * 0.45
    mapped = [item.lower() for item in agent1.resource_to_umbrella_map.get(chunk.id, [])]
    if concept.lower() in mapped:
        score += 0.65
    phrases = [phrase.lower() for phrase in agent1.keyphrase_map.get(chunk.id, [])]
    if any(any(token in phrase for token in concept_tokens) for phrase in phrases):
        score += 0.2
    return score


def assert_memory_ready(db: Session, idea: Idea) -> IdeaMemory:
    memory = db.query(IdeaMemory).filter(IdeaMemory.idea_id == idea.id).first()
    nodes = db.query(GraphNode).filter(GraphNode.idea_id == idea.id).all()
    if (
        not idea.agent_1_validated
        or not idea.agent_2_validated
        or not idea.memory_initialized
        or idea.memory_state != "MEMORY_READY"
        or not memory
        or not nodes
        or any(not loads(node.centroid_embedding_json, []) for node in nodes)
    ):
        raise HTTPException(
            status_code=409,
            detail={
                "error": "MEMORY_NOT_READY",
                "message": "Agent 3 requires validated Agent 1 schema and Agent 2 memory graph.",
            },
        )
    return memory


async def dump_update(db: Session, idea: Idea, input_value: str) -> DumpResponse:
    started = time.perf_counter()
    memory = assert_memory_ready(db, idea)
    resource, chunks = create_resource_and_chunks(db, idea, input_value)
    nodes = db.query(GraphNode).filter(GraphNode.idea_id == idea.id).all()
    delta_vectors = [loads(chunk.embedding_json, []) for chunk in chunks]
    delta_centroid = mean_embedding(delta_vectors)
    ranked = sorted(
        [(node, cosine_similarity(delta_centroid, loads(node.centroid_embedding_json, []))) for node in nodes],
        key=lambda item: item[1],
        reverse=True,
    )
    primary, max_score = ranked[0]
    secondary, second_score = ranked[1] if len(ranked) > 1 else (None, 0.0)
    if max_score >= 0.75:
        decision = "ASSIMILATE"
    elif second_score >= 0.55:
        decision = "BRIDGE"
    else:
        decision = "ACCOMMODATE"
    helper = await run_agent3_summary(decision, resource.clean_content, [node.label for node in nodes])
    actions: list[str] = []
    new_node_id = None
    secondary_id = secondary.id if secondary else None
    if decision == "ASSIMILATE":
        existing_ids = loads(primary.source_chunk_ids_json, [])
        primary.source_chunk_ids_json = dumps(existing_ids + [chunk.id for chunk in chunks])
        primary.centroid_embedding_json = dumps(running_mean(loads(primary.centroid_embedding_json, []), primary.member_count, delta_vectors))
        primary.member_count += len(chunks)
        if primary.member_count % 5 == 0:
            primary.summary = helper.summary
        actions.extend(["attached chunks to existing node", "updated centroid", "incremented member count"])
    elif decision == "ACCOMMODATE":
        node = GraphNode(
            idea_id=idea.id,
            label=helper.label or "new concept",
            summary=helper.summary,
            centroid_embedding_json=dumps(delta_centroid),
            member_count=len(chunks),
            source_chunk_ids_json=dumps([chunk.id for chunk in chunks]),
            created_by="AGENT_3",
        )
        db.add(node)
        db.flush()
        new_node_id = node.id
        create_similarity_edges(db, idea.id, [node] + nodes)
        memory.textual_summary = f"{memory.textual_summary}\n\nNew concept - {node.label}: {node.summary}"
        actions.extend(["created new graph node", "refreshed textual memory"])
    else:
        upsert_bridge_edge(db, idea.id, primary.id, secondary.id, max(max_score, second_score), helper.reason)
        existing_ids = loads(primary.source_chunk_ids_json, [])
        primary.source_chunk_ids_json = dumps(existing_ids + [chunk.id for chunk in chunks])
        primary.centroid_embedding_json = dumps(running_mean(loads(primary.centroid_embedding_json, []), primary.member_count, delta_vectors))
        primary.member_count += len(chunks)
        memory.textual_summary = f"{memory.textual_summary}\n\nBridge: {helper.reason}"
        actions.extend(["attached chunks to strongest node", "created or strengthened bridge edge", "refreshed textual memory"])
    db.add(TimelineEntry(idea_id=idea.id, entry_type="memory", content=f"{decision}: {helper.reason}"))
    _log_agent(db, idea.id, "AGENT_3", {"resource_id": resource.id}, {"decision": decision, "reason": helper.reason}, started)
    db.commit()
    nodes, edges = get_graph(db, idea.id)
    return DumpResponse(
        decision=decision,
        primaryNodeId=primary.id,
        secondaryNodeId=secondary_id if decision == "BRIDGE" else None,
        newNodeId=new_node_id,
        confidence=round(max_score, 4),
        actionsTaken=actions,
        reason=helper.reason,
        updatedGraph=graph_out(nodes, edges),
    )


async def query_memory(db: Session, idea: Idea, question: str):
    started = time.perf_counter()
    memory = assert_memory_ready(db, idea)
    nodes = db.query(GraphNode).filter(GraphNode.idea_id == idea.id).all()
    question_embedding = embedding_service.embed(question)
    ranked = sorted(
        [(node, cosine_similarity(question_embedding, loads(node.centroid_embedding_json, []))) for node in nodes],
        key=lambda item: item[1],
        reverse=True,
    )
    labels = [node.label for node, _ in ranked[:3]]
    output = await run_agent4_query(question, memory.textual_summary, labels)
    _log_agent(db, idea.id, "AGENT_4", {"mode": "query", "question": question}, output.model_dump(), started)
    db.commit()
    return output


async def generate_tasks(db: Session, idea: Idea):
    started = time.perf_counter()
    memory = assert_memory_ready(db, idea)
    nodes = db.query(GraphNode).filter(GraphNode.idea_id == idea.id).order_by(GraphNode.member_count.desc()).all()
    existing = [task.title for task in db.query(Task).filter(Task.idea_id == idea.id).all()]
    output = await run_agent4_generate(memory.textual_summary, [node.label for node in nodes], existing)
    for item in output.kanban_tasks:
        create_task(db, idea.id, TaskCreate(title=item.title, description=item.description, lane=item.column, points=item.points))
    if output.timeline_entry:
        db.add(TimelineEntry(idea_id=idea.id, entry_type="generation", content=output.timeline_entry))
    _log_agent(db, idea.id, "AGENT_4", {"mode": "generate"}, output.model_dump(), started)
    db.commit()
    return output


def _validate_agent1(output: Agent1Output) -> None:
    if not (1 <= len(output.umbrella_concepts) <= 8):
        raise ValueError("Agent 1 must produce 1-8 umbrella concepts.")


def _log_agent(db: Session, idea_id: str, agent_type: str, input_payload: dict, output_payload: dict, started: float) -> AgentRun:
    run = AgentRun(
        idea_id=idea_id,
        agent_type=agent_type,
        status="completed",
        input_json=dumps(input_payload),
        output_json=dumps(output_payload),
        latency_ms=max(0, int((time.perf_counter() - started) * 1000)),
    )
    db.add(run)
    db.flush()
    return run
