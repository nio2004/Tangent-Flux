import { request } from "./client.ts";
import type { ChatResponse, ChatSession, ChatSessionDetail, IdeaAgentCard, IdeaCardGenerateResponse, IdeaCardSelectResponse, ProjectMemoryPayload } from "../types/idea.ts";

export function fetchChatSessions(ideaId: string): Promise<ChatSession[]> {
  return request<ChatSession[]>(`/ideas/${ideaId}/chat/sessions`);
}

export function createChatSession(ideaId: string, title?: string): Promise<ChatSession> {
  return request<ChatSession>(`/ideas/${ideaId}/chat/sessions`, {
    method: "POST",
    body: JSON.stringify({ title }),
  });
}

export function fetchChatSession(ideaId: string, sessionId: string): Promise<ChatSessionDetail> {
  return request<ChatSessionDetail>(`/ideas/${ideaId}/chat/sessions/${sessionId}`);
}

export function sendIdeaAgentMessage(ideaId: string, content: string, sessionId?: string, projectMemoryId?: string): Promise<ChatResponse> {
  const suffix = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : "";
  return request<ChatResponse>(`/ideas/${ideaId}/chat${suffix}`, {
    method: "POST",
    body: JSON.stringify({ content, projectMemoryId }),
  });
}

export function fetchProjectMemory(ideaId: string): Promise<ProjectMemoryPayload> {
  return request<ProjectMemoryPayload>(`/ideas/${ideaId}/project-memory`);
}

export function generateIdeaCards(ideaId: string, prompt: string): Promise<IdeaCardGenerateResponse> {
  return request<IdeaCardGenerateResponse>(`/ideas/${ideaId}/chat/idea-cards`, {
    method: "POST",
    body: JSON.stringify({ prompt }),
  });
}

export function selectIdeaCard(ideaId: string, card: IdeaAgentCard): Promise<IdeaCardSelectResponse> {
  return request<IdeaCardSelectResponse>(`/ideas/${ideaId}/chat/idea-cards/select`, {
    method: "POST",
    body: JSON.stringify({ card }),
  });
}
