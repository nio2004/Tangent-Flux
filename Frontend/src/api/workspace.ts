import { API_BASE, request } from "./client.ts";
import type { GallerySlide, KanbanLaneId, KanbanTask, ResourcePreview, TimelineEntry } from "../types/idea.ts";

export function addResource(ideaId: string, input: string, title?: string): Promise<ResourcePreview> {
  return request<ResourcePreview>(`/ideas/${ideaId}/resources`, {
    method: "POST",
    body: JSON.stringify({ input, title }),
  });
}

<<<<<<< HEAD
=======
export function saveIdeaNotes(ideaId: string, markdown: string): Promise<{ id: string; title: string; markdown: string }> {
  return request<{ id: string; title: string; markdown: string }>(`/ideas/${ideaId}/notes`, {
    method: "PUT",
    body: JSON.stringify({ markdown }),
  });
}

export function saveCoverImage(ideaId: string, coverUrl: string | null): Promise<{ coverUrl: string | null }> {
  return request<{ coverUrl: string | null }>(`/ideas/${ideaId}/cover`, {
    method: "PUT",
    body: JSON.stringify({ coverUrl }),
  });
}

>>>>>>> 6f1c767a5b6ce400673ed3b3987875468dd9fa04
export function addTask(ideaId: string, title: string, points = 2): Promise<KanbanTask> {
  return request<KanbanTask>(`/ideas/${ideaId}/tasks`, {
    method: "POST",
    body: JSON.stringify({ title, points, lane: "todo" }),
  });
}

export function moveTask(taskId: string, lane: KanbanLaneId, sortOrder = 1000): Promise<KanbanTask> {
  return request<KanbanTask>(`/tasks/${taskId}/move`, {
    method: "POST",
    body: JSON.stringify({ lane, sortOrder }),
  });
}

export function addTimelineEntry(ideaId: string, text: string, type = "journal"): Promise<TimelineEntry> {
  return request<TimelineEntry>(`/ideas/${ideaId}/timeline`, {
    method: "POST",
    body: JSON.stringify({ text, type }),
  });
}

export function addArtifact(ideaId: string, title: string, caption: string, art = "mesh"): Promise<GallerySlide> {
  return request<GallerySlide>(`/ideas/${ideaId}/artifacts`, {
    method: "POST",
    body: JSON.stringify({ title, caption, art }),
  });
}

export async function uploadImageArtifact(ideaId: string, file: File): Promise<GallerySlide> {
  const body = new FormData();
  body.append("file", file);
  let response: Response;
  try {
    response = await fetch(`${API_BASE}/ideas/${ideaId}/artifacts/image`, {
      method: "POST",
      body,
    });
  } catch {
    throw new Error(`Backend is not reachable at ${API_BASE}. Start FastAPI on port 8001, then upload again.`);
  }
  if (!response.ok) {
    let message = `${response.status} ${response.statusText}`;
    try {
      const payload = await response.json();
      message = typeof payload.detail === "string" ? payload.detail : JSON.stringify(payload.detail ?? payload);
    } catch {
      // Keep HTTP status message.
    }
    throw new Error(message);
  }
  return response.json() as Promise<GallerySlide>;
}
