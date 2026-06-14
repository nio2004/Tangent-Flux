import { request } from "./client.ts";
import type { Idea, OverviewGraph, WorkspacePayload } from "../types/idea.ts";

export interface CreateIdeaInput {
  title: string;
  description?: string;
  problem?: string;
  tags?: string[];
  source?: string;
  quick_note?: string;
}

export function fetchIdeas(): Promise<Idea[]> {
  return request<Idea[]>("/ideas");
}

export function createIdea(input: CreateIdeaInput): Promise<Idea> {
  return request<Idea>("/ideas", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function fetchWorkspace(ideaId: string): Promise<WorkspacePayload> {
  return request<WorkspacePayload>(`/ideas/${ideaId}/workspace`);
}

export function fetchGraphOverview(): Promise<OverviewGraph> {
  return request<OverviewGraph>("/graph");
}

export function initializeMemory(ideaId: string, input?: string): Promise<{ memory: unknown; graph: WorkspacePayload["graph"] }> {
  return request<{ memory: unknown; graph: WorkspacePayload["graph"] }>(`/ideas/${ideaId}/initialize`, {
    method: "POST",
    body: JSON.stringify({ input }),
  });
}
<<<<<<< HEAD
=======

export function saveIdeaNote(ideaId: string, markdown: string): Promise<{ id: string; title: string; markdown: string }> {
  return request<{ id: string; title: string; markdown: string }>(`/ideas/${ideaId}/notes`, {
    method: "PUT",
    body: JSON.stringify({ markdown }),
  });
}
>>>>>>> 6f1c767a5b6ce400673ed3b3987875468dd9fa04
