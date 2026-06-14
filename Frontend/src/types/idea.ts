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
  coverUrl?: string | null;
  memoryState?: string;
  initialSource?: string;
  quickNote?: string;
}

export interface ResourcePreview {
  id?: string;
  type: string;
  title: string;
  meta: string;
  description: string;
  sourceUrl?: string | null;
  status?: string;
}

export interface TimelineEntry {
  id?: string;
  time: string;
  text: string;
  type?: string;
}

export interface GallerySlide {
  id?: string;
  title: string;
  caption: string;
  art: string;
  assetUrl?: string | null;
}

export type KanbanLaneId = "todo" | "progress" | "completed";

export interface KanbanTask {
  id: string;
  title: string;
  points: number;
  lane?: KanbanLaneId;
  sortOrder?: number;
  description?: string;
}

export type KanbanBoard = Record<KanbanLaneId, KanbanTask[]>;

export interface IdeaMemory {
  textualSummary: string;
  conceptMap: Record<string, unknown>;
}

export interface GraphNode {
  id: string;
  label: string;
  summary: string;
  memberCount: number;
  createdBy: string;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  edgeType: string;
  weight: number;
  reason: string;
}

export interface OverviewGraphNode {
  id: string;
  label: string;
  kind: "idea" | "concept";
  summary: string;
  ideaId: string;
  status?: string;
  tags?: string[];
  memberCount?: number;
}

export interface OverviewGraphEdge {
  id: string;
  source: string;
  target: string;
  edgeType: string;
  weight: number;
  reason: string;
}

export interface OverviewGraph {
  nodes: OverviewGraphNode[];
  edges: OverviewGraphEdge[];
}

export interface WorkspacePayload {
  idea: Idea;
  notes: { id: string; title: string; markdown: string }[];
  resources: ResourcePreview[];
  tasks: KanbanBoard;
  timeline: TimelineEntry[];
  artifacts: GallerySlide[];
  coverUrl: string | null;
  memory: IdeaMemory | null;
  graph: { nodes: GraphNode[]; edges: GraphEdge[] };
  agentRuns: unknown[];
}

export interface ChatSource {
  kind: string;
  id: string;
  title: string;
  excerpt: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | string;
  content: string;
  sources: ChatSource[];
  createdAt: string;
}

export interface ChatSession {
  id: string;
  ideaId: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  messageCount: number;
}

export interface ChatSessionDetail {
  session: ChatSession;
  messages: ChatMessage[];
}

export interface ChatResponse {
  session: ChatSession;
  userMessage: ChatMessage;
  assistantMessage: ChatMessage;
}

export interface ProjectMemoryEvent {
  id: string;
  projectMemoryId: string;
  ideaId: string;
  eventType: string;
  content: string;
  metadata: Record<string, unknown>;
  createdAt: string;
}

export interface ProjectMemory {
  id: string;
  ideaId: string;
  cardId: string;
  title: string;
  mainTopic: string;
  selectedCard: IdeaAgentCard | null;
  textualSummary: string;
  status: string;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
  lastRefreshedAt: string;
}

export interface ProjectMemoryPayload {
  projectMemory: ProjectMemory | null;
  recentEvents: ProjectMemoryEvent[];
}

export interface IdeaCardTask {
  title: string;
  description: string;
  points: number;
}

export interface IdeaAgentCard {
  id: string;
  title: string;
  mainTopic: string;
  summary: string;
  whyNow: string;
  fitReason: string;
  evidence: string[];
  risks: string[];
  firstTasks: IdeaCardTask[];
  score: number;
}

export interface IdeaCardGenerateResponse {
  cards: IdeaAgentCard[];
  grounding: ChatSource[];
}

export interface IdeaCardDetailResponse {
  card: IdeaAgentCard;
  grounding: ChatSource[];
}

export interface IdeaCardSelectResponse {
  card: IdeaAgentCard;
  tasks: KanbanTask[];
  projectMemory: ProjectMemory;
}
