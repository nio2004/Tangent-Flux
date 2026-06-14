import time
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.agents.agent4_generate import run_agent4_query
from app.core.config import get_settings
from app.models import Artifact, ChatMessage, ChatSession, Chunk, GraphNode, Idea, IdeaMemory, Resource
from app.schemas.chat import ChatMessageOut, ChatSourceOut, ChatSessionOut
from app.services.embedding_service import embedding_service
from app.services.memory_service import assert_memory_ready
from app.services.similarity_service import cosine_similarity
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


async def chat_with_idea_agent(db: Session, idea: Idea, session: ChatSession, content: str) -> tuple[ChatMessage, ChatMessage]:
    started = time.perf_counter()
    memory = assert_memory_ready(db, idea)
    nodes = db.query(GraphNode).filter(GraphNode.idea_id == idea.id).all()
    sources = _rank_sources(db, idea, content)
    history = list_chat_messages(db, session)[-8:]
    prompt = _build_agent_question(content, memory, nodes, sources, history)
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
    _ = started
    db.commit()
    db.refresh(user_message)
    db.refresh(assistant_message)
    db.refresh(session)
    return user_message, assistant_message


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
) -> str:
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
        f"Textual memory:\n{memory.textual_summary}\n\n"
        f"Graph nodes:\n{node_context or 'No graph nodes.'}\n\n"
        f"Relevant evidence, chunks, and image descriptions:\n{source_context or 'No ranked sources.'}\n\n"
        f"Recent chat:\n{history_context or 'No prior messages.'}\n\n"
        f"User question:\n{question}"
    )


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
