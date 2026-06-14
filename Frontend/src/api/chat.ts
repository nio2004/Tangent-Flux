import { request } from "./client.ts";
import type { ChatResponse, ChatSession, ChatSessionDetail } from "../types/idea.ts";

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

export function sendIdeaAgentMessage(ideaId: string, content: string, sessionId?: string): Promise<ChatResponse> {
  const suffix = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : "";
  return request<ChatResponse>(`/ideas/${ideaId}/chat${suffix}`, {
    method: "POST",
    body: JSON.stringify({ content }),
  });
}
