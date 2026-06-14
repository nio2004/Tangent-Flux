import { ChevronLeft, ChevronRight, Image, PanelLeftClose, PanelLeftOpen, Sparkles, X } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import { useState } from "react";
import { gallery, resources, timeline } from "../../data/ideas.ts";
import type { GallerySlide, Idea, KanbanBoard, KanbanLaneId, KanbanTask } from "../../types/idea.ts";
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
  onClose: () => void;
  onNotesSave: (notes: string) => void;
  onCoverChange: (cover: string) => void;
  onMoveTask: (taskId: string, lane: KanbanLaneId) => void;
  onAddTask: (task: KanbanTask) => void;
}

function GalleryPanel({ slides }: { slides: GallerySlide[] }) {
  const [index, setIndex] = useState(0);
  const slide = slides[index];
  const position = `${String(index + 1).padStart(2, "0")} / ${String(slides.length).padStart(2, "0")}`;

  function move(direction: number) {
    setIndex((current) => (current + direction + slides.length) % slides.length);
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
          <Image size={28} aria-hidden="true" />
          <span>{slide.title}</span>
        </motion.div>
      </AnimatePresence>
      <p className="gallery-caption">{slide.caption}</p>
    </section>
  );
}

export function IdeaDetail({
  idea,
  open,
  notes,
  cover,
  board,
  onClose,
  onNotesSave,
  onCoverChange,
  onMoveTask,
  onAddTask,
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
            </div>

            <nav className="detail-nav" aria-label="Idea workspace sections">
              {["Overview", "Notes", "Tasks", "Resources", "Gallery", "Timeline"].map((item) => (
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

      <StudioControlsOverlay open={studioOpen} onClose={() => setStudioOpen(false)} onAddTask={onAddTask} />
    </>
  );
}
