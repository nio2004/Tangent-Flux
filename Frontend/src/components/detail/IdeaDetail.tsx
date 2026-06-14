import { ChevronLeft, ChevronRight, GitBranch, Image, PanelLeftClose, PanelLeftOpen, Sparkles, X } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useState } from "react";
import type {
  GallerySlide,
  GraphEdge,
  GraphNode,
  Idea,
  IdeaMemory,
  KanbanBoard,
  KanbanLaneId,
  KanbanTask,
  ResourcePreview,
  TimelineEntry,
} from "../../types/idea.ts";
import { Badge } from "../ui/badge.tsx";
import { Button } from "../ui/button.tsx";
import { CoverDropzone } from "./CoverDropzone.tsx";
import { KanbanWorkspace } from "./KanbanWorkspace.tsx";
import { MarkdownNotes } from "./MarkdownNotes.tsx";
import { ResourceCarousel } from "./ResourceCarousel.tsx";
import { StudioControlsOverlay } from "./StudioControlsOverlay.tsx";
import { TimelineWindow } from "./TimelineWindow.tsx";

interface IdeaDetailProps {
  idea: Idea;
  open: boolean;
  notes: string;
  cover: string | null;
  board: KanbanBoard;
  resources: ResourcePreview[];
  timeline: TimelineEntry[];
  gallery: GallerySlide[];
  memory: IdeaMemory | null;
  graph: { nodes: GraphNode[]; edges: GraphEdge[] };
  loading: boolean;
  error: string | null;
  onClose: () => void;
  onNotesSave: (notes: string) => void;
  onCoverChange: (cover: string) => void;
  onMoveTask: (taskId: string, lane: KanbanLaneId) => void;
  onAddTask: (task: KanbanTask) => Promise<void> | void;
  onWorkspaceChange: () => Promise<void>;
  onInitializeMemory: () => Promise<void>;
}

function GalleryPanel({ slides }: { slides: GallerySlide[] }) {
  const [index, setIndex] = useState(0);
  useEffect(() => setIndex(0), [slides]);
  const fallback: GallerySlide = {
    title: "No diagrams yet",
    caption: "Upload an image from Studio Controls to ingest it with vision.",
    art: "mesh",
  };
  const safeIndex = slides.length ? Math.min(index, slides.length - 1) : 0;
  const slide = slides[safeIndex] ?? fallback;
  const total = Math.max(slides.length, 1);
  const position = `${String(safeIndex + 1).padStart(2, "0")} / ${String(total).padStart(2, "0")}`;

  function move(direction: number) {
    setIndex((current) => (current + direction + total) % total);
  }

  return (
    <section className="workspace-panel gallery-stage" id="gallery">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Architecture Gallery</p>
          <h3>{slide.title}</h3>
        </div>
        <div className="gallery-toggle" aria-label="Architecture image selector">
          <Button variant="ghost" size="icon" onClick={() => move(-1)} aria-label="Previous architecture view">
            <ChevronLeft size={18} aria-hidden="true" />
          </Button>
          <span>{position}</span>
          <Button variant="ghost" size="icon" onClick={() => move(1)} aria-label="Next architecture view">
            <ChevronRight size={18} aria-hidden="true" />
          </Button>
        </div>
      </div>
      <AnimatePresence mode="wait">
        <motion.div
          className={`gallery-art gallery-${slide.art}`}
          key={slide.title}
          initial={{ opacity: 0, y: 16, scale: 0.98 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -12, scale: 0.98 }}
          transition={{ duration: 0.24, ease: [0.22, 1, 0.36, 1] }}
        >
          {slide.assetUrl ? (
            <img src={slide.assetUrl} alt={slide.title} />
          ) : (
            <>
              <Image size={28} aria-hidden="true" />
              <span>{slide.title}</span>
            </>
          )}
        </motion.div>
      </AnimatePresence>
      <p className="gallery-caption">{slide.caption}</p>
    </section>
  );
}

function LocalMemoryPanel({
  memory,
  graph,
  memoryState,
  loading,
  onInitializeMemory,
}: {
  memory: IdeaMemory | null;
  graph: { nodes: GraphNode[]; edges: GraphEdge[] };
  memoryState?: string;
  loading: boolean;
  onInitializeMemory: () => Promise<void>;
}) {
  const nodes = graph.nodes;
  const edges = graph.edges;
  const hasMemory = Boolean(memory?.textualSummary || nodes.length);

  return (
    <section className="workspace-panel local-memory-panel" id="memory">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Local Memory</p>
          <h3>Agent-made concept graph</h3>
        </div>
        <Button variant="ghost" onClick={onInitializeMemory} disabled={loading}>
          <GitBranch size={16} aria-hidden="true" />
          <span>{hasMemory ? "Rebuild" : "Initialize"}</span>
        </Button>
      </div>

      {hasMemory ? (
        <div className="local-memory-layout">
          <div className="memory-summary">
            <p>{memory?.textualSummary || "Memory summary is not written yet."}</p>
            <div className="memory-stats">
              <span>{memoryState ?? "EMPTY"}</span>
              <span>{nodes.length} nodes</span>
              <span>{edges.length} edges</span>
            </div>
          </div>
          <div className="local-graph" aria-label="Local idea graph visualization">
            {edges.map((edge: GraphEdge) => {
              const sourceIndex = nodes.findIndex((node) => node.id === edge.source);
              const targetIndex = nodes.findIndex((node) => node.id === edge.target);
              if (sourceIndex < 0 || targetIndex < 0) {
                return null;
              }
              const sourceAngle = (sourceIndex / Math.max(nodes.length, 1)) * Math.PI * 2;
              const targetAngle = (targetIndex / Math.max(nodes.length, 1)) * Math.PI * 2;
              const sourceX = 50 + Math.cos(sourceAngle) * 32;
              const sourceY = 50 + Math.sin(sourceAngle) * 30;
              const targetX = 50 + Math.cos(targetAngle) * 32;
              const targetY = 50 + Math.sin(targetAngle) * 30;
              const dx = targetX - sourceX;
              const dy = targetY - sourceY;

              return (
                <span
                  key={edge.id}
                  className={edge.edgeType === "BRIDGE" ? "local-edge is-bridge" : "local-edge"}
                  title={`${edge.edgeType} ${edge.weight.toFixed(2)}`}
                  style={{
                    left: `${sourceX}%`,
                    top: `${sourceY}%`,
                    width: `${Math.hypot(dx, dy)}%`,
                    transform: `rotate(${Math.atan2(dy, dx) * (180 / Math.PI)}deg)`,
                  }}
                />
              );
            })}
            {nodes.map((node: GraphNode, index: number) => {
              const angle = (index / Math.max(nodes.length, 1)) * Math.PI * 2;
              const left = nodes.length === 1 ? 50 : 50 + Math.cos(angle) * 32;
              const top = nodes.length === 1 ? 50 : 50 + Math.sin(angle) * 30;
              return (
                <div key={node.id} className="local-node" title={node.summary} style={{ left: `${left}%`, top: `${top}%` }}>
                  <strong>{node.label}</strong>
                  <span>{node.memberCount} chunks</span>
                </div>
              );
            })}
          </div>
        </div>
      ) : (
        <div className="memory-empty">
          <GitBranch size={22} aria-hidden="true" />
          <p>Add linked evidence or diagrams, then initialize memory to see the local graph.</p>
        </div>
      )}
    </section>
  );
}

export function IdeaDetail({
  idea,
  open,
  notes,
  cover,
  board,
  resources,
  timeline,
  gallery,
  memory,
  graph,
  loading,
  error,
  onClose,
  onNotesSave,
  onCoverChange,
  onMoveTask,
  onAddTask,
  onWorkspaceChange,
  onInitializeMemory,
}: IdeaDetailProps) {
  const [kanbanExpanded, setKanbanExpanded] = useState(false);
  const [studioOpen, setStudioOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    <>
      <motion.section
        className={open ? "detail-view is-open" : "detail-view"}
        aria-hidden={!open}
        initial={false}
        animate={open ? { opacity: 1 } : { opacity: 0 }}
        transition={{ duration: 0.22 }}
      >
        <motion.div
          className={sidebarCollapsed ? "detail-shell sidebar-collapsed" : "detail-shell"}
          initial={false}
          animate={open ? { y: 0, scale: 1 } : { y: 20, scale: 0.985 }}
          transition={{ type: "spring", stiffness: 230, damping: 28 }}
        >
          <aside className="detail-side">
            <div className="detail-side-top">
              <Button variant="ghost" size="icon" onClick={onClose} aria-label="Close idea workspace">
                <X size={18} aria-hidden="true" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setSidebarCollapsed((current) => !current)}
                aria-label={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
              >
                {sidebarCollapsed ? <PanelLeftOpen size={18} aria-hidden="true" /> : <PanelLeftClose size={18} aria-hidden="true" />}
              </Button>
            </div>

            <div className="momentum-card">
              <p className="eyebrow">Momentum</p>
              <strong>{idea.progress}%</strong>
              <span>{idea.resources} sources / {idea.notes} notes</span>
              {idea.memoryState && <span>{idea.memoryState}</span>}
            </div>

            <nav className="detail-nav" aria-label="Idea workspace sections">
              {["Overview", "Notes", "Memory", "Tasks", "Resources", "Gallery", "Timeline"].map((item) => (
                <a href={`#${item.toLowerCase()}`} key={item}>
                  <ChevronLeft size={14} aria-hidden="true" />
                  {item}
                </a>
              ))}
            </nav>

            <Button variant="hot" onClick={() => setStudioOpen(true)}>
              <Sparkles size={17} aria-hidden="true" />
              <span>Studio Controls</span>
            </Button>
          </aside>

          <main className="detail-main">
            {(loading || error) && (
              <section className="workspace-panel workspace-status">
                <p className="eyebrow">{loading ? "Syncing" : "Backend issue"}</p>
                <p>{loading ? "Loading workspace data..." : error}</p>
              </section>
            )}
            <section className={cover ? "detail-hero has-cover" : "detail-hero"} id="overview">
              <CoverDropzone cover={cover} onCoverChange={onCoverChange} />
              <div className="detail-hero-copy">
                <p className="eyebrow">Focused workspace</p>
                <p className="detail-kicker">
                  {idea.activity} / {idea.code}
                </p>
                <div className="detail-title-row">
                  <h1>{idea.title}</h1>
                </div>
                <p>{idea.description}</p>
                <div className="tag-row">
                  {idea.tags.map((tag) => (
                    <Badge tone="muted" key={tag}>
                      {tag}
                    </Badge>
                  ))}
                </div>
              </div>
            </section>

            <div className="detail-sections">
              <section className="detail-section insight-layout" aria-label="Brainstorm, problem, and evidence">
                <MarkdownNotes value={notes} onSave={onNotesSave} />

                <div className="insight-rail">
                  <section className="workspace-panel problem-card">
                    <p className="eyebrow">Problem Statement</p>
                    <h3>Why this idea matters</h3>
                    <p>{idea.problem}</p>
                    <div className="review-strip">
                      <span>Sources attached</span>
                      <span>Assumptions visible</span>
                      <span>Approval pending</span>
                    </div>
                  </section>

                  <ResourceCarousel resources={resources} />
                </div>
              </section>

              <LocalMemoryPanel
                memory={memory}
                graph={graph}
                memoryState={idea.memoryState}
                loading={loading}
                onInitializeMemory={onInitializeMemory}
              />

              <section className="detail-section task-context-layout" aria-label="Task and context mesh">
                <KanbanWorkspace
                  board={board}
                  expanded={kanbanExpanded}
                  onExpandedChange={setKanbanExpanded}
                  onMoveTask={onMoveTask}
                />
                <GalleryPanel slides={gallery} />
              </section>

              <TimelineWindow entries={timeline} />
            </div>
          </main>
        </motion.div>
      </motion.section>

      <StudioControlsOverlay
        open={studioOpen}
        ideaId={idea.id}
        onClose={() => setStudioOpen(false)}
        onAddTask={onAddTask}
        onWorkspaceChange={onWorkspaceChange}
      />
    </>
  );
}
