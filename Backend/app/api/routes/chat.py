from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.routes.ideas import _get_idea
from app.core.database import get_db
from app.schemas.chat import ChatMessageCreate, ChatResponseOut, ChatSessionCreate, ChatSessionDetailOut, ChatSessionOut
from app.services.chat_service import (
    chat_with_idea_agent,
    create_chat_session,
    get_or_create_session,
    list_chat_messages,
    list_chat_sessions,
    message_out,
    session_out,
    sessions_out,
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
    user_message, assistant_message = await chat_with_idea_agent(db, idea, session, payload.content)
    message_count = len(list_chat_messages(db, session))
    return ChatResponseOut(
        session=session_out(session, message_count),
        userMessage=message_out(user_message),
        assistantMessage=message_out(assistant_message),
    )
