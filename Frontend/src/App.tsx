import { useEffect, useMemo, useState } from "react";
import { FilterBar } from "./components/dashboard/FilterBar.tsx";
import { IdeaGrid } from "./components/dashboard/IdeaGrid.tsx";
import { IdeaDetail } from "./components/detail/IdeaDetail.tsx";
import { Topbar } from "./components/layout/Topbar.tsx";
import { QuickAddDialog } from "./components/quick-add/QuickAddDialog.tsx";
import { ideas as initialIdeas, initialKanban, starterNotes } from "./data/ideas.ts";
import { moveTask } from "./lib/kanban.ts";
import type { Idea, KanbanLaneId, KanbanTask } from "./types/idea.ts";

function App() {
  const [ideas, setIdeas] = useState(initialIdeas);
  const [query, setQuery] = useState("");
  const [activeFilter, setActiveFilter] = useState("All Signals");
  const [selectedIdea, setSelectedIdea] = useState<Idea | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [quickAddOpen, setQuickAddOpen] = useState(false);
  const [morphRect, setMorphRect] = useState<DOMRect | null>(null);
  const [notes, setNotes] = useState(starterNotes);
  const [cover, setCover] = useState<string | null>(null);
  const [board, setBoard] = useState(initialKanban);

  const filteredIdeas = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();

    return ideas.filter((idea) => {
      const matchesQuery =
        !normalizedQuery ||
        [idea.title, idea.description, ...idea.tags].some((value) =>
          value.toLowerCase().includes(normalizedQuery),
        );
      const matchesFilter =
        activeFilter === "All Signals" ||
        idea.tags.some((tag) => tag.toLowerCase() === activeFilter.toLowerCase()) ||
        idea.status.toLowerCase() === activeFilter.toLowerCase();

      return matchesQuery && matchesFilter;
    });
  }, [activeFilter, ideas, query]);

  useEffect(() => {
    document.body.classList.toggle("body-locked", detailOpen);

    return () => document.body.classList.remove("body-locked");
  }, [detailOpen]);

  function openIdea(idea: Idea, rect: DOMRect) {
    setMorphRect(rect);
    setSelectedIdea(idea);
    window.setTimeout(() => setDetailOpen(true), 180);
    window.setTimeout(() => setMorphRect(null), 620);
  }

  function closeDetail() {
    setDetailOpen(false);
    window.setTimeout(() => setSelectedIdea(null), 260);
  }

  function createIdea(idea: Idea) {
    setIdeas((currentIdeas) => [idea, ...currentIdeas]);
    setActiveFilter("All Signals");
    setQuery("");
  }

  return (
    <div className="app-shell">
      <Topbar query={query} onQueryChange={setQuery} onQuickAdd={() => setQuickAddOpen(true)} />

      <main className="dashboard" id="board">
        <div className="dashboard-heading">
          <div>
            <p className="eyebrow">Live workspace</p>
            <h1>Your research workspace</h1>
          </div>
          <p>Sources, changes, tasks, and next steps stay visible while ideas move toward buildable work.</p>
        </div>
        <FilterBar activeFilter={activeFilter} onFilterChange={setActiveFilter} />
        <IdeaGrid ideas={filteredIdeas} onOpenIdea={openIdea} onQuickAdd={() => setQuickAddOpen(true)} />
      </main>

      {morphRect && (
        <div
          className="morph-layer"
          aria-hidden="true"
          style={{
            "--morph-left": `${morphRect.left}px`,
            "--morph-top": `${morphRect.top}px`,
            "--morph-width": `${morphRect.width}px`,
            "--morph-height": `${morphRect.height}px`,
          } as React.CSSProperties}
        >
          <div className="morph-card" />
        </div>
      )}

      {selectedIdea && (
        <IdeaDetail
          idea={selectedIdea}
          open={detailOpen}
          notes={notes}
          cover={cover}
          board={board}
          onClose={closeDetail}
          onNotesSave={setNotes}
          onCoverChange={setCover}
          onMoveTask={(taskId: string, lane: KanbanLaneId) => setBoard((current) => moveTask(current, taskId, lane))}
          onAddTask={(task: KanbanTask) =>
            setBoard((current) => ({
              ...current,
              todo: [task, ...current.todo],
            }))
          }
        />
      )}

      <QuickAddDialog open={quickAddOpen} onClose={() => setQuickAddOpen(false)} onCreate={createIdea} />
    </div>
  );
}

export default App;
