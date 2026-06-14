from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.routes.ideas import _get_idea
from app.core.database import get_db
from app.schemas.chat import (
    ChatMessageCreate,
    ChatResponseOut,
    ChatSessionCreate,
    ChatSessionDetailOut,
    ChatSessionOut,
    IdeaCardGenerateRequest,
    IdeaCardGenerateResponse,
    IdeaCardDetailRequest,
    IdeaCardDetailResponse,
    IdeaCardSelectRequest,
    IdeaCardSelectResponse,
)
from app.schemas.project_memory import ProjectMemoryEventCreate, ProjectMemoryEventOut, ProjectMemoryPayload
from app.services.chat_service import (
    chat_with_idea_agent,
    create_chat_session,
    generate_idea_card_detail,
    generate_idea_cards,
    get_or_create_session,
    list_chat_messages,
    list_chat_sessions,
    message_out,
    select_idea_card,
    session_out,
    sessions_out,
)
from app.services.project_memory_service import (
    append_project_memory_event,
    get_active_project_memory,
    project_memory_event_out,
    project_memory_payload,
)

router = APIRouter(prefix="/ideas", tags=["chat"])


@router.get("/{idea_id}/chat/sessions", response_model=list[ChatSessionOut])
def sessions(idea_id: str, db: Session = Depends(get_db)):
    idea = _get_idea(db, idea_id)
    return sessions_out(db, list_chat_sessions(db, idea))


@router.post("/{idea_id}/chat/sessions", response_model=ChatSessionOut)
def create_session(idea_id: str, payload: ChatSessionCreate, db: Session = Depends(get_db)):
    idea = _get_idea(db, idea_id)
    return session_out(create_chat_session(db, idea, payload.title))


@router.get("/{idea_id}/chat/sessions/{session_id}", response_model=ChatSessionDetailOut)
def session_detail(idea_id: str, session_id: str, db: Session = Depends(get_db)):
    idea = _get_idea(db, idea_id)
    session = get_or_create_session(db, idea, session_id)
    messages = list_chat_messages(db, session)
    return ChatSessionDetailOut(session=session_out(session, len(messages)), messages=[message_out(message) for message in messages])


@router.post("/{idea_id}/chat", response_model=ChatResponseOut)
async def chat(idea_id: str, payload: ChatMessageCreate, session_id: str | None = None, db: Session = Depends(get_db)):
    idea = _get_idea(db, idea_id)
    session = get_or_create_session(db, idea, session_id)
    user_message, assistant_message = await chat_with_idea_agent(db, idea, session, payload.content, payload.projectMemoryId)
    message_count = len(list_chat_messages(db, session))
    return ChatResponseOut(
        session=session_out(session, message_count),
        userMessage=message_out(user_message),
        assistantMessage=message_out(assistant_message),
    )


@router.post("/{idea_id}/chat/idea-cards", response_model=IdeaCardGenerateResponse)
async def idea_cards(idea_id: str, payload: IdeaCardGenerateRequest, db: Session = Depends(get_db)):
    idea = _get_idea(db, idea_id)
    cards, grounding = await generate_idea_cards(db, idea, payload.prompt)
    return IdeaCardGenerateResponse(cards=cards, grounding=grounding)


@router.post("/{idea_id}/chat/idea-cards/detail", response_model=IdeaCardDetailResponse)
async def idea_card_detail(idea_id: str, payload: IdeaCardDetailRequest, db: Session = Depends(get_db)):
    idea = _get_idea(db, idea_id)
    card, grounding = await generate_idea_card_detail(db, idea, payload.prompt, payload.card)
    return IdeaCardDetailResponse(card=card, grounding=grounding)


@router.post("/{idea_id}/chat/idea-cards/select", response_model=IdeaCardSelectResponse)
def select_card(idea_id: str, payload: IdeaCardSelectRequest, db: Session = Depends(get_db)):
    idea = _get_idea(db, idea_id)
    tasks, project_memory = select_idea_card(db, idea, payload.card)
    return IdeaCardSelectResponse(card=payload.card, tasks=tasks, projectMemory=project_memory)


@router.get("/{idea_id}/project-memory", response_model=ProjectMemoryPayload)
def active_project_memory(idea_id: str, db: Session = Depends(get_db)):
    idea = _get_idea(db, idea_id)
    return project_memory_payload(db, idea)


@router.post("/{idea_id}/project-memory/events", response_model=ProjectMemoryEventOut)
def add_project_memory_event(idea_id: str, payload: ProjectMemoryEventCreate, db: Session = Depends(get_db)):
    idea = _get_idea(db, idea_id)
    project_memory = get_active_project_memory(db, idea)
    if not project_memory:
        raise HTTPException(status_code=404, detail="No active project memory.")
    event = append_project_memory_event(db, project_memory, payload.eventType, payload.content, payload.metadata)
    db.commit()
    db.refresh(event)
    return project_memory_event_out(event)
