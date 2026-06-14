import { ChevronLeft, Image, Sparkles, X } from "lucide-react";
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

  return (
    <section className="workspace-panel gallery-stage" id="gallery">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Architecture Gallery</p>
          <h3>{slide.title}</h3>
        </div>
        <div className="resource-controls">
          {slides.map((item, itemIndex) => (
            <button
              key={item.title}
              type="button"
              className={itemIndex === index ? "is-active" : ""}
              onClick={() => setIndex(itemIndex)}
              aria-label={`Show ${item.title}`}
            />
          ))}
        </div>
      </div>
      <div className={`gallery-art gallery-${slide.art}`}>
        <Image size={28} aria-hidden="true" />
        <span>{slide.title}</span>
      </div>
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

  return (
    <>
      <section className={open ? "detail-view is-open" : "detail-view"} aria-hidden={!open}>
        <div className="detail-shell">
          <aside className="detail-side">
            <Button variant="ghost" size="icon" onClick={onClose} aria-label="Close idea workspace">
              <X size={18} aria-hidden="true" />
            </Button>

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
            <section className="detail-hero" id="overview">
              <div className="detail-hero-copy">
                <p className="eyebrow">Focused workspace</p>
                <div className="detail-title-row">
                  <h1>{idea.title}</h1>
                  <Badge tone="accent">{idea.status}</Badge>
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
              <CoverDropzone cover={cover} onCoverChange={onCoverChange} />
            </section>

            <div className="studio-grid">
              <section className="workspace-panel problem-card">
                <p className="eyebrow">Problem Statement</p>
                <h3>What this needs to solve</h3>
                <p>{idea.problem}</p>
                <div className="review-strip">
                  <span>Sources attached</span>
                  <span>Assumptions visible</span>
                  <span>Approval pending</span>
                </div>
              </section>

              <MarkdownNotes value={notes} onSave={onNotesSave} />
              <ResourceCarousel resources={resources} />
              <KanbanWorkspace
                board={board}
                expanded={kanbanExpanded}
                onExpandedChange={setKanbanExpanded}
                onMoveTask={onMoveTask}
              />
              <GalleryPanel slides={gallery} />
              <TimelineWindow entries={timeline} />
            </div>
          </main>
        </div>
      </section>

      <StudioControlsOverlay open={studioOpen} onClose={() => setStudioOpen(false)} onAddTask={onAddTask} />
    </>
  );
}
