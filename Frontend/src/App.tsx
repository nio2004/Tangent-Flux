import { useEffect, useMemo, useState } from "react";
import { FilterBar } from "./components/dashboard/FilterBar.tsx";
import { GraphOverview } from "./components/dashboard/GraphOverview.tsx";
import { IdeaGrid } from "./components/dashboard/IdeaGrid.tsx";
import { IdeaDetail } from "./components/detail/IdeaDetail.tsx";
import { Topbar } from "./components/layout/Topbar.tsx";
import { QuickAddDialog } from "./components/quick-add/QuickAddDialog.tsx";
import { ideas as initialIdeas, initialKanban, starterNotes } from "./data/ideas.ts";
import { createIdea as createIdeaApi, fetchGraphOverview, fetchIdeas, fetchWorkspace, initializeMemory } from "./api/ideas.ts";
import { addTask as addTaskApi, moveTask as moveTaskApi } from "./api/workspace.ts";
import { moveTask } from "./lib/kanban.ts";
import type { GallerySlide, GraphEdge, GraphNode, Idea, IdeaMemory, KanbanLaneId, KanbanTask, OverviewGraph, ResourcePreview, TimelineEntry } from "./types/idea.ts";

function App() {
  const [ideas, setIdeas] = useState(initialIdeas);
  const [query, setQuery] = useState("");
  const [activeFilter, setActiveFilter] = useState("All Signals");
  const [activeView, setActiveView] = useState<"board" | "graph">("board");
  const [selectedIdea, setSelectedIdea] = useState<Idea | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [quickAddOpen, setQuickAddOpen] = useState(false);
  const [morphRect, setMorphRect] = useState<DOMRect | null>(null);
  const [notes, setNotes] = useState(starterNotes);
  const [cover, setCover] = useState<string | null>(null);
  const [board, setBoard] = useState(initialKanban);
  const [resources, setResources] = useState<ResourcePreview[]>([]);
  const [timeline, setTimeline] = useState<TimelineEntry[]>([]);
  const [gallery, setGallery] = useState<GallerySlide[]>([]);
  const [localMemory, setLocalMemory] = useState<IdeaMemory | null>(null);
  const [localGraph, setLocalGraph] = useState<{ nodes: GraphNode[]; edges: GraphEdge[] }>({ nodes: [], edges: [] });
  const [workspaceLoading, setWorkspaceLoading] = useState(false);
  const [workspaceError, setWorkspaceError] = useState<string | null>(null);
  const [overviewGraph, setOverviewGraph] = useState<OverviewGraph | null>(null);
  const [graphLoading, setGraphLoading] = useState(false);
  const [graphError, setGraphError] = useState<string | null>(null);

  useEffect(() => {
    fetchIdeas()
      .then(setIdeas)
      .catch((error) => {
        console.warn("Backend idea load failed; using local sample data.", error);
      });
  }, []);

  useEffect(() => {
    if (activeView === "graph") {
      loadGraphOverview();
    }
  }, [activeView]);

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
    loadWorkspace(idea.id);
    window.setTimeout(() => setDetailOpen(true), 180);
    window.setTimeout(() => setMorphRect(null), 620);
  }

  function closeDetail() {
    setDetailOpen(false);
    window.setTimeout(() => setSelectedIdea(null), 260);
  }

  async function loadWorkspace(ideaId: string) {
    setWorkspaceLoading(true);
    setWorkspaceError(null);
    try {
      const workspace = await fetchWorkspace(ideaId);
      setSelectedIdea(workspace.idea);
      setNotes(workspace.notes[0]?.markdown ?? starterNotes);
      setCover(workspace.coverUrl);
      setBoard(workspace.tasks);
      setResources(workspace.resources);
      setTimeline(workspace.timeline);
      setGallery(workspace.artifacts);
      setLocalMemory(workspace.memory);
      setLocalGraph(workspace.graph);
      setIdeas((currentIdeas) => currentIdeas.map((idea) => (idea.id === workspace.idea.id ? workspace.idea : idea)));
    } catch (error) {
      setWorkspaceError(error instanceof Error ? error.message : "Workspace failed to load.");
    } finally {
      setWorkspaceLoading(false);
    }
  }

  async function createIdea(idea: Idea) {
    try {
      const created = await createIdeaApi({
        title: idea.title,
        description: idea.description,
        problem: idea.problem,
        tags: idea.tags,
        source: idea.initialSource,
        quick_note: idea.quickNote,
      });
      setIdeas((currentIdeas) => [created, ...currentIdeas]);
    } catch {
      setIdeas((currentIdeas) => [idea, ...currentIdeas]);
    }
    setActiveFilter("All Signals");
    setQuery("");
  }

  async function refreshSelectedWorkspace() {
    if (selectedIdea) {
      await loadWorkspace(selectedIdea.id);
    }
  }

  async function loadGraphOverview() {
    setGraphLoading(true);
    setGraphError(null);
    try {
      setOverviewGraph(await fetchGraphOverview());
    } catch (error) {
      setGraphError(error instanceof Error ? error.message : "Graph failed to load.");
    } finally {
      setGraphLoading(false);
    }
  }

  async function handleAddTask(task: KanbanTask) {
    if (!selectedIdea) {
      return;
    }
    try {
      const created = await addTaskApi(selectedIdea.id, task.title, task.points);
      setBoard((current) => ({
        ...current,
        todo: [created, ...current.todo],
      }));
      await refreshSelectedWorkspace();
    } catch (error) {
      setWorkspaceError(error instanceof Error ? error.message : "Task could not be saved.");
    }
  }

  async function handleMoveTask(taskId: string, lane: KanbanLaneId) {
    setBoard((current) => moveTask(current, taskId, lane));
    try {
      await moveTaskApi(taskId, lane);
      await refreshSelectedWorkspace();
    } catch (error) {
      setWorkspaceError(error instanceof Error ? error.message : "Task move could not be saved.");
    }
  }

  async function handleInitializeMemory() {
    if (!selectedIdea) {
      return;
    }
    setWorkspaceLoading(true);
    setWorkspaceError(null);
    try {
      await initializeMemory(selectedIdea.id);
      await loadWorkspace(selectedIdea.id);
      if (activeView === "graph") {
        await loadGraphOverview();
      }
    } catch (error) {
      setWorkspaceError(error instanceof Error ? error.message : "Memory initialization failed.");
    } finally {
      setWorkspaceLoading(false);
    }
  }

  return (
    <div className="app-shell">
      <Topbar
        query={query}
        onQueryChange={setQuery}
        onQuickAdd={() => setQuickAddOpen(true)}
        activeView={activeView}
        onViewChange={setActiveView}
      />

      <main className="dashboard" id="board">
        <div className="dashboard-heading">
          <div>
            <p className="eyebrow">Live workspace</p>
            <h1>Your research workspace</h1>
          </div>
          <p>Sources, changes, tasks, and next steps stay visible while ideas move toward buildable work.</p>
        </div>
        {activeView === "board" ? (
          <>
            <FilterBar activeFilter={activeFilter} onFilterChange={setActiveFilter} />
            <IdeaGrid ideas={filteredIdeas} onOpenIdea={openIdea} onQuickAdd={() => setQuickAddOpen(true)} />
          </>
        ) : (
          <GraphOverview graph={overviewGraph} loading={graphLoading} error={graphError} onRefresh={loadGraphOverview} />
        )}
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
          resources={resources}
          timeline={timeline}
          gallery={gallery}
          memory={localMemory}
          graph={localGraph}
          loading={workspaceLoading}
          error={workspaceError}
          onClose={closeDetail}
          onNotesSave={setNotes}
          onCoverChange={setCover}
          onMoveTask={handleMoveTask}
          onAddTask={handleAddTask}
          onWorkspaceChange={refreshSelectedWorkspace}
          onInitializeMemory={handleInitializeMemory}
        />
      )}

      <QuickAddDialog open={quickAddOpen} onClose={() => setQuickAddOpen(false)} onCreate={createIdea} />
    </div>
  );
}

export default App;
