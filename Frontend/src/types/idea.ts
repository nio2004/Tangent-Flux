export type IdeaStatus =
  | "Prototype"
  | "Incubating"
  | "Exploration"
  | "Pinned"
  | "Research"
  | "Buildable"
  | "Experimental"
  | "Capture"
  | "Archive";

export interface Idea {
  id: string;
  title: string;
  status: IdeaStatus;
  description: string;
  tags: string[];
  progress: number;
  resources: number;
  notes: number;
  updated: string;
  activity: "hot" | "active" | "quiet" | "new";
  code: string;
  importance: number;
  texture: string;
  problem: string;
}

export interface ResourcePreview {
  type: string;
  title: string;
  meta: string;
  description: string;
}

export interface TimelineEntry {
  time: string;
  text: string;
}

export interface GallerySlide {
  title: string;
  caption: string;
  art: string;
}

export type KanbanLaneId = "todo" | "progress" | "completed";

export interface KanbanTask {
  id: string;
  title: string;
  points: number;
}

export type KanbanBoard = Record<KanbanLaneId, KanbanTask[]>;
