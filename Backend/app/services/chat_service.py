import time
import json
import re
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.agents.agent4_generate import run_agent4_query
from app.core.config import get_settings
from app.models import Artifact, ChatMessage, ChatSession, Chunk, GraphNode, Idea, IdeaMemory, ProjectMemory, Resource
from app.schemas.chat import ChatMessageOut, ChatSourceOut, ChatSessionOut, IdeaAgentCardOut, IdeaCardTaskOut
from app.schemas.task import TaskCreate
from app.services.embedding_service import embedding_service
from app.services.memory_service import assert_memory_ready
from app.services.project_memory_service import (
    append_project_memory_event,
    create_project_memory_for_card,
    get_project_memory,
    project_memory_out,
    recent_project_memory_events,
)
from app.services.similarity_service import cosine_similarity
from app.services.task_service import create_task
from app.services.serialization import task_out
from app.utils import dumps, iso, loads


def create_chat_session(db: Session, idea: Idea, title: str | None = None) -> ChatSession:
    session = ChatSession(idea_id=idea.id, title=title or f"{idea.title} agent")
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_or_create_session(db: Session, idea: Idea, session_id: str | None = None) -> ChatSession:
    if session_id:
        session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.idea_id == idea.id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found.")
        return session

    session = (
        db.query(ChatSession)
        .filter(ChatSession.idea_id == idea.id)
        .order_by(ChatSession.updated_at.desc())
        .first()
    )
    if session:
        return session
    return create_chat_session(db, idea)


def list_chat_sessions(db: Session, idea: Idea) -> list[ChatSession]:
    return db.query(ChatSession).filter(ChatSession.idea_id == idea.id).order_by(ChatSession.updated_at.desc()).all()


def list_chat_messages(db: Session, session: ChatSession) -> list[ChatMessage]:
    return db.query(ChatMessage).filter(ChatMessage.session_id == session.id).order_by(ChatMessage.created_at.asc()).all()


async def chat_with_idea_agent(
    db: Session,
    idea: Idea,
    session: ChatSession,
    content: str,
    project_memory_id: str | None = None,
) -> tuple[ChatMessage, ChatMessage]:
    started = time.perf_counter()
    memory = assert_memory_ready(db, idea)
    nodes = db.query(GraphNode).filter(GraphNode.idea_id == idea.id).all()
    project_memory = get_project_memory(db, idea, project_memory_id) if project_memory_id else None
    project_events = recent_project_memory_events(db, project_memory, 8) if project_memory else []
    sources = _rank_sources(db, idea, content)
    history = list_chat_messages(db, session)[-8:]
    prompt = _build_agent_question(content, memory, nodes, sources, history, project_memory, project_events)
    answer = await _answer_with_optional_web_search(prompt, memory, nodes, content)

    user_message = ChatMessage(session_id=session.id, role="user", content=content)
    assistant_message = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=_ensure_bullets(answer),
        source_json=dumps([source.model_dump() for source in sources[:6]]),
    )
    session.updated_at = datetime.utcnow()
    db.add(user_message)
    db.add(assistant_message)
    db.add(session)
    db.flush()
    if project_memory:
        append_project_memory_event(db, project_memory, "chat_user", content[:1200], {"session_id": session.id}, refresh=False)
        append_project_memory_event(
            db,
            project_memory,
            "chat_assistant",
            assistant_message.content[:1200],
            {"session_id": session.id, "source_count": len(sources[:6])},
            refresh=True,
        )
    _ = started
    db.commit()
    db.refresh(user_message)
    db.refresh(assistant_message)
    db.refresh(session)
    return user_message, assistant_message


async def generate_idea_cards(db: Session, idea: Idea, prompt: str) -> tuple[list[IdeaAgentCardOut], list[ChatSourceOut]]:
    memory = assert_memory_ready(db, idea)
    nodes = db.query(GraphNode).filter(GraphNode.idea_id == idea.id).all()
    sources = _rank_sources(db, idea, prompt)
    cards = _try_generate_cards_with_model(idea, memory, nodes, sources, prompt)
    if not cards:
        cards = _fallback_idea_cards(idea, memory, nodes, sources, prompt)
    return cards, sources[:8]


async def generate_idea_card_detail(
    db: Session,
    idea: Idea,
    prompt: str,
    card: IdeaAgentCardOut,
) -> tuple[IdeaAgentCardOut, list[ChatSourceOut]]:
    memory = assert_memory_ready(db, idea)
    nodes = db.query(GraphNode).filter(GraphNode.idea_id == idea.id).all()
    sources = _rank_sources(db, idea, f"{prompt} {card.title} {card.summary}")
    detailed = _try_generate_card_detail_with_model(idea, memory, nodes, sources, prompt, card)
    if not detailed:
        detailed = _fallback_card_detail(idea, memory, nodes, sources, prompt, card)
    return detailed, sources[:8]


def select_idea_card(db: Session, idea: Idea, card: IdeaAgentCardOut):
    assert_memory_ready(db, idea)
    created = []
    for item in card.firstTasks[:8]:
        task = create_task(
            db,
            idea.id,
            TaskCreate(title=item.title, description=item.description, lane="todo", points=item.points),
        )
        created.append(task)
    project_memory = create_project_memory_for_card(db, idea, card, created)
    db.commit()
    for task in created:
        db.refresh(task)
    db.refresh(project_memory)
    return [task_out(task) for task in created], project_memory_out(project_memory)


def session_out(session: ChatSession, message_count: int | None = None) -> ChatSessionOut:
    count = message_count if message_count is not None else len(session.messages)
    return ChatSessionOut(
        id=session.id,
        ideaId=session.idea_id,
        title=session.title,
        createdAt=iso(session.created_at) or "",
        updatedAt=iso(session.updated_at) or "",
        messageCount=count,
    )


def sessions_out(db: Session, sessions: list[ChatSession]) -> list[ChatSessionOut]:
    counts = dict(
        db.query(ChatMessage.session_id, func.count(ChatMessage.id))
        .filter(ChatMessage.session_id.in_([session.id for session in sessions]))
        .group_by(ChatMessage.session_id)
        .all()
    ) if sessions else {}
    return [session_out(session, int(counts.get(session.id, 0))) for session in sessions]


def message_out(message: ChatMessage) -> ChatMessageOut:
    sources = [ChatSourceOut(**source) for source in loads(message.source_json, [])]
    return ChatMessageOut(
        id=message.id,
        role=message.role,
        content=message.content,
        sources=sources,
        createdAt=iso(message.created_at) or "",
    )


def _rank_sources(db: Session, idea: Idea, question: str) -> list[ChatSourceOut]:
    question_embedding = embedding_service.embed(question)
    chunk_rows = (
        db.query(Chunk, Resource)
        .join(Resource, Chunk.resource_id == Resource.id)
        .filter(Chunk.idea_id == idea.id)
        .all()
    )
    ranked_chunks = sorted(
        [
            (
                cosine_similarity(question_embedding, loads(chunk.embedding_json, [])),
                chunk,
                resource,
            )
            for chunk, resource in chunk_rows
        ],
        key=lambda item: item[0],
        reverse=True,
    )
    sources: list[ChatSourceOut] = []
    seen: set[str] = set()
    graph_nodes = db.query(GraphNode).filter(GraphNode.idea_id == idea.id).all()
    for node in graph_nodes[:6]:
        sources.append(
            ChatSourceOut(
                kind="graph",
                id=node.id,
                title=node.label,
                excerpt=node.summary[:420],
            )
        )

    for _score, chunk, resource in ranked_chunks[:8]:
        if chunk.id in seen:
            continue
        seen.add(chunk.id)
        sources.append(
            ChatSourceOut(
                kind=resource.type,
                id=chunk.id,
                title=resource.title,
                excerpt=chunk.text[:420],
            )
        )

    artifacts = db.query(Artifact).filter(Artifact.idea_id == idea.id).order_by(Artifact.created_at.desc()).limit(4).all()
    for artifact in artifacts:
        if artifact.caption:
            sources.append(
                ChatSourceOut(
                    kind="image",
                    id=artifact.id,
                    title=artifact.title,
                    excerpt=artifact.caption[:420],
                )
            )
    return sources


def _build_agent_question(
    question: str,
    memory: IdeaMemory,
    nodes: list[GraphNode],
    sources: list[ChatSourceOut],
    history: list[ChatMessage],
    project_memory: ProjectMemory | None = None,
    project_events: list | None = None,
) -> str:
    project_context = ""
    if project_memory:
        event_context = "\n".join(f"{event.event_type}: {event.content[:500]}" for event in (project_events or []))
        project_context = (
            f"Active selected-project memory, use this first:\n{project_memory.textual_summary}\n\n"
            f"Recent selected-project events:\n{event_context or 'No recent project events.'}\n\n"
        )
    node_context = "\n".join(f"- {node.label}: {node.summary}" for node in nodes[:12])
    source_context = "\n".join(f"- [{source.kind}] {source.title}: {source.excerpt}" for source in sources[:8])
    history_context = "\n".join(f"{message.role}: {message.content[:500]}" for message in history)
    return (
        "You are the idea-specific Tangent-Flux memory agent. Answer using only the grounded context below. "
        "You can compare links, image descriptions, graph nodes, and textual memory. "
        "If the evidence is insufficient, say what is missing and suggest what to upload or ask next. "
        "Format every answer as bullet points. Never return one long paragraph. "
        "If the user asks to show visualization, visualize, graph, diagram, or relationship, include a 'Visualization references' bullet "
        "that names the relevant graph nodes, image descriptions, links, and evidence titles.\n\n"
        f"{project_context}"
        f"Textual memory:\n{memory.textual_summary}\n\n"
        f"Graph nodes:\n{node_context or 'No graph nodes.'}\n\n"
        f"Relevant evidence, chunks, and image descriptions:\n{source_context or 'No ranked sources.'}\n\n"
        f"Recent chat:\n{history_context or 'No prior messages.'}\n\n"
        f"User question:\n{question}"
    )


def _try_generate_cards_with_model(
    idea: Idea,
    memory: IdeaMemory,
    nodes: list[GraphNode],
    sources: list[ChatSourceOut],
    prompt: str,
) -> list[IdeaAgentCardOut]:
    settings = get_settings()
    if not settings.openai_api_key:
        return []
    node_context = "\n".join(f"- {node.label}: {node.summary}" for node in nodes[:12])
    source_context = "\n".join(f"- [{source.kind}] {source.title}: {source.excerpt}" for source in sources[:10])
    request = (
        "Generate 3-5 compact buildable idea cards for this Tangent-Flux idea. "
        "This is the fast first pass only. Filter for strongest fit to the user's request, local memory, and current web context. "
        "Use web search for latest information when useful. Return only JSON matching this shape: "
        '{"cards":[{"id":"short-slug","title":"...","mainTopic":"...","summary":"...",'
        '"score":0.82}]}. '
        "The summary must be 1-2 sentences. Do not include whyNow, fitReason, evidence, risks, or tasks yet. "
        "Do not include markdown outside JSON.\n\n"
        f"Idea: {idea.title}\nProblem: {idea.problem}\nDescription: {idea.description}\n"
        f"Textual memory:\n{memory.textual_summary}\n\nGraph nodes:\n{node_context}\n\n"
        f"Ranked local evidence:\n{source_context}\n\nUser request:\n{prompt}"
    )
    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)
        tools = [{"type": "web_search_preview"}] if settings.openai_enable_web_search else None
        response = client.responses.create(
            model=settings.openai_idea_generation_model,
            tools=tools,
            input=request,
        )
        text = getattr(response, "output_text", None) or ""
        payload = _extract_json_object(text)
        return _cards_from_payload(payload)
    except Exception:
        return []


def _extract_json_object(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.S)
        if not match:
            return {}
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return {}


def _cards_from_payload(payload: dict) -> list[IdeaAgentCardOut]:
    cards = payload.get("cards", []) if isinstance(payload, dict) else []
    result = []
    for index, item in enumerate(cards[:5]):
        try:
            result.append(
                IdeaAgentCardOut(
                    id=str(item.get("id") or f"idea-card-{index + 1}"),
                    title=str(item.get("title") or "Build direction"),
                    mainTopic=str(item.get("mainTopic") or item.get("main_topic") or "Opportunity"),
                    summary=str(item.get("summary") or ""),
                    whyNow=str(item.get("whyNow") or item.get("why_now") or ""),
                    fitReason=str(item.get("fitReason") or item.get("fit_reason") or ""),
                    evidence=[str(value) for value in item.get("evidence", [])[:6]],
                    risks=[str(value) for value in item.get("risks", [])[:5]],
                    firstTasks=[
                        IdeaCardTaskOut(
                            title=str(task.get("title") or "Define next step"),
                            description=str(task.get("description") or ""),
                            points=max(1, min(8, int(task.get("points") or 1))),
                        )
                        for task in item.get("firstTasks", item.get("first_tasks", []))[:6]
                        if isinstance(task, dict)
                    ],
                    score=max(0.0, min(1.0, float(item.get("score") or 0.0))),
                )
            )
        except (TypeError, ValueError):
            continue
    return result


def _try_generate_card_detail_with_model(
    idea: Idea,
    memory: IdeaMemory,
    nodes: list[GraphNode],
    sources: list[ChatSourceOut],
    prompt: str,
    card: IdeaAgentCardOut,
) -> IdeaAgentCardOut | None:
    settings = get_settings()
    if not settings.openai_api_key:
        return None
    node_context = "\n".join(f"- {node.label}: {node.summary}" for node in nodes[:12])
    source_context = "\n".join(f"- [{source.kind}] {source.title}: {source.excerpt}" for source in sources[:10])
    request = (
        "Generate the deep-dive detail for exactly one selected Tangent-Flux idea card. "
        "Keep the original title, mainTopic, summary, id, and score unless a small correction is required. "
        "Return only JSON matching this shape: "
        '{"card":{"id":"...","title":"...","mainTopic":"...","summary":"...",'
        '"whyNow":"...","fitReason":"...","evidence":["..."],"risks":["..."],'
        '"firstTasks":[{"title":"...","description":"...","points":2}],"score":0.82}}. '
        "Evidence should name grounded memory, graph, web, or source facts. "
        "Risks should be actionable. firstTasks must be concrete Kanban TODOs. "
        "Do not include markdown outside JSON.\n\n"
        f"Idea: {idea.title}\nProblem: {idea.problem}\nDescription: {idea.description}\n"
        f"Textual memory:\n{memory.textual_summary}\n\nGraph nodes:\n{node_context}\n\n"
        f"Ranked local evidence:\n{source_context}\n\nOriginal user request:\n{prompt}\n\n"
        f"Selected compact card JSON:\n{card.model_dump_json()}"
    )
    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)
        tools = [{"type": "web_search_preview"}] if settings.openai_enable_web_search else None
        response = client.responses.create(
            model=settings.openai_idea_generation_model,
            tools=tools,
            input=request,
        )
        text = getattr(response, "output_text", None) or ""
        payload = _extract_json_object(text)
        card_payload = payload.get("card", payload) if isinstance(payload, dict) else {}
        cards = _cards_from_payload({"cards": [card_payload]})
        return cards[0] if cards else None
    except Exception:
        return None


def _fallback_card_detail(
    idea: Idea,
    memory: IdeaMemory,
    nodes: list[GraphNode],
    sources: list[ChatSourceOut],
    prompt: str,
    card: IdeaAgentCardOut,
) -> IdeaAgentCardOut:
    evidence = [source.title for source in sources[:5] if source.title]
    topic = card.mainTopic or (nodes[0].label if nodes else idea.title)
    return IdeaAgentCardOut(
        id=card.id,
        title=card.title,
        mainTopic=topic,
        summary=card.summary or memory.textual_summary[:220],
        whyNow="This direction is supported by current local memory and should be validated against fresh evidence before deeper commitment.",
        fitReason=f"Matches the request '{prompt[:120]}' through the '{topic}' memory cluster and the selected idea's problem framing.",
        evidence=evidence or [idea.title],
        risks=["Needs current-market validation", "Scope may need pruning after first prototype", "Evidence quality should be checked before roadmap commitment"],
        firstTasks=[
            IdeaCardTaskOut(title=f"Validate {topic} assumptions", description="Check recent sources and list acceptance criteria.", points=2),
            IdeaCardTaskOut(title=f"Prototype {topic} workflow", description="Build the smallest artifact that proves this direction.", points=3),
            IdeaCardTaskOut(title="Review evidence and decide next branch", description="Compare results against memory graph evidence.", points=1),
        ],
        score=card.score or 0.72,
    )


def _fallback_idea_cards(
    idea: Idea,
    memory: IdeaMemory,
    nodes: list[GraphNode],
    sources: list[ChatSourceOut],
    prompt: str,
) -> list[IdeaAgentCardOut]:
    primary_nodes = nodes[:4] or [GraphNode(label=idea.title, summary=idea.description, idea_id=idea.id)]
    cards = []
    for index, node in enumerate(primary_nodes[:4]):
        evidence = [source.title for source in sources[index : index + 3] if source.title]
        title = f"{node.label.title()} build path"
        cards.append(
            IdeaAgentCardOut(
                id=f"local-{index + 1}",
                title=title,
                mainTopic=node.label,
                summary=node.summary or memory.textual_summary[:220],
                whyNow="",
                fitReason="",
                evidence=[],
                risks=[],
                firstTasks=[],
                score=max(0.55, 0.9 - index * 0.08),
            )
        )
    return cards


async def _answer_with_optional_web_search(prompt: str, memory: IdeaMemory, nodes: list[GraphNode], question: str) -> str:
    settings = get_settings()
    if settings.openai_enable_web_search and settings.openai_api_key and _looks_like_web_search_request(question):
        web_answer = _try_web_search_answer(settings.openai_api_key, settings.openai_web_search_model, prompt)
        if web_answer:
            return web_answer
    output = await run_agent4_query(prompt, memory.textual_summary, [node.label for node in nodes])
    return output.answer


def _looks_like_web_search_request(question: str) -> bool:
    text = question.lower()
    return any(
        marker in text
        for marker in [
            "web",
            "search",
            "latest",
            "current",
            "recent",
            "paper",
            "arxiv",
            "find data",
            "online",
        ]
    )


def _try_web_search_answer(api_key: str, model: str, prompt: str) -> str | None:
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model=model,
            tools=[{"type": "web_search_preview"}],
            input=(
                "Use web search only to supplement the local Tangent-Flux memory. "
                "Prefer local memory when it conflicts with search results. "
                "Return bullet points only.\n\n"
                f"{prompt}"
            ),
        )
        text = getattr(response, "output_text", None)
        return text.strip() if text else None
    except Exception:
        return None


def _ensure_bullets(answer: str) -> str:
    lines = [line.strip() for line in answer.splitlines() if line.strip()]
    if not lines:
        return "- I could not find enough grounded memory to answer that yet."
    if any(line.startswith(("-", "*", "•")) for line in lines):
        return "\n".join(f"- {line.lstrip('-*• ').strip()}" for line in lines)
    sentences = []
    for chunk in " ".join(lines).split(". "):
        cleaned = chunk.strip().rstrip(".")
        if cleaned:
            sentences.append(cleaned)
    return "\n".join(f"- {sentence}." for sentence in sentences[:8])
