import { type ReactNode, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import Lenis from "lenis";
import { ArrowDown, BrainCircuit, Network, Upload, Wand2 } from "lucide-react";
import { FilterBar } from "./components/dashboard/FilterBar.tsx";
import { GraphOverview } from "./components/dashboard/GraphOverview.tsx";
import { IdeaGrid } from "./components/dashboard/IdeaGrid.tsx";
import { GlobeSignal } from "./components/dashboard/GlobeSignal.tsx";
import { IdeaDetail } from "./components/detail/IdeaDetail.tsx";
import { Topbar } from "./components/layout/Topbar.tsx";
import { QuickAddDialog } from "./components/quick-add/QuickAddDialog.tsx";
import tangentFluxLogo from "./assets/tangent-flux-logo.svg";
import { gallery as sampleGallery, ideas as initialIdeas, initialKanban, resources as sampleResources, starterNotes, timeline as sampleTimeline } from "./data/ideas.ts";
import { createIdea as createIdeaApi, fetchGraphOverview, fetchIdeas, fetchWorkspace, initializeMemory } from "./api/ideas.ts";
import { addTask as addTaskApi, moveTask as moveTaskApi, saveCoverImage, saveIdeaNotes } from "./api/workspace.ts";
import { moveTask } from "./lib/kanban.ts";
import type {
  GallerySlide,
  GraphEdge,
  GraphNode,
  Idea,
  IdeaMemory,
  KanbanLaneId,
  KanbanTask,
  OverviewGraph,
  ResourcePreview,
  TimelineEntry,
} from "./types/idea.ts";

gsap.registerPlugin(ScrollTrigger);

function App() {
  const [introVisible, setIntroVisible] = useState(true);
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
  const [resources, setResources] = useState<ResourcePreview[]>(sampleResources);
  const [timeline, setTimeline] = useState<TimelineEntry[]>(sampleTimeline);
  const [gallery, setGallery] = useState<GallerySlide[]>(sampleGallery);
  const [localMemory, setLocalMemory] = useState<IdeaMemory | null>(null);
  const [localGraph, setLocalGraph] = useState<{ nodes: GraphNode[]; edges: GraphEdge[] }>({ nodes: [], edges: [] });
  const [workspaceLoading, setWorkspaceLoading] = useState(false);
  const [workspaceError, setWorkspaceError] = useState<string | null>(null);
  const [overviewGraph, setOverviewGraph] = useState<OverviewGraph | null>(null);
  const [graphLoading, setGraphLoading] = useState(false);
  const [graphError, setGraphError] = useState<string | null>(null);

  useEffect(() => {
    const introTimer = window.setTimeout(() => setIntroVisible(false), 2600);

    return () => window.clearTimeout(introTimer);
  }, []);

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
      setGallery(workspace.artifacts.length ? workspace.artifacts : sampleGallery);
      setLocalMemory(workspace.memory);
      setLocalGraph(workspace.graph);
      setIdeas((currentIdeas) => currentIdeas.map((item) => (item.id === workspace.idea.id ? workspace.idea : item)));
    } catch (error) {
      setWorkspaceError(error instanceof Error ? error.message : "Workspace failed to load.");
      setResources(sampleResources);
      setTimeline(sampleTimeline);
      setGallery(sampleGallery);
    } finally {
      setWorkspaceLoading(false);
    }
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
      setBoard((current) => ({ ...current, todo: [created, ...current.todo] }));
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

  async function handleNotesSave(markdown: string) {
    if (!selectedIdea) {
      setNotes(markdown);
      return;
    }
    setWorkspaceError(null);
    setNotes(markdown);
    try {
      await saveIdeaNotes(selectedIdea.id, markdown);
      await refreshSelectedWorkspace();
    } catch (error) {
      setWorkspaceError(error instanceof Error ? error.message : "Idea dump could not be saved.");
    }
  }

  async function handleCoverChange(nextCover: string) {
    setCover(nextCover);
    if (!selectedIdea) {
      return;
    }

    setWorkspaceError(null);
    try {
      const saved = await saveCoverImage(selectedIdea.id, nextCover);
      setCover(saved.coverUrl);
      setIdeas((currentIdeas) =>
        currentIdeas.map((idea) => (idea.id === selectedIdea.id ? { ...idea, coverUrl: saved.coverUrl } : idea)),
      );
    } catch (error) {
      setWorkspaceError(error instanceof Error ? error.message : "Cover image could not be saved.");
    }
  }

  return (
    <SmoothScrollProvider>
      <div className="app-shell">
        {introVisible && <IntroLoader />}

        {!detailOpen && (
          <Topbar
            query={query}
            onQueryChange={setQuery}
            onQuickAdd={() => setQuickAddOpen(true)}
            activeView={activeView}
            onViewChange={setActiveView}
          />
        )}

        <LandingHero
          onQuickAdd={() => setQuickAddOpen(true)}
          onExploreGraph={() => {
            setActiveView("graph");
            document.getElementById("board")?.scrollIntoView({ behavior: "smooth" });
          }}
        />

        <main className="dashboard" id="board">
          <div className="dashboard-heading">
            <div>
              <p className="eyebrow">Live cognitive workspace</p>
              <h1>From scattered signal to buildable direction.</h1>
            </div>
            <p>
              Dump the tabs, notes, papers, diagrams, and 2am fragments. Tangent-Flux maps how they connect, where
              they conflict, and what they collectively point toward.
            </p>
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
            onNotesSave={handleNotesSave}
            onCoverChange={handleCoverChange}
            onMoveTask={handleMoveTask}
            onAddTask={handleAddTask}
            onWorkspaceChange={refreshSelectedWorkspace}
            onInitializeMemory={handleInitializeMemory}
          />
        )}

        <QuickAddDialog open={quickAddOpen} onClose={() => setQuickAddOpen(false)} onCreate={createIdea} />
      </div>
    </SmoothScrollProvider>
  );
}

function SmoothScrollProvider({ children }: { children: ReactNode }) {
  useEffect(() => {
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    if (reduceMotion) {
      return;
    }

    const lenis = new Lenis({
      duration: 1.18,
      easing: (time: number) => Math.min(1, 1.001 - Math.pow(2, -10 * time)),
      smoothWheel: true,
      syncTouch: false,
      wheelMultiplier: 0.82,
      prevent: (node: Element) => Boolean(node.closest("[data-lenis-prevent]")),
    });

    const raf = (time: number) => {
      lenis.raf(time * 1000);
    };

    lenis.on("scroll", ScrollTrigger.update);
    gsap.ticker.add(raf);
    gsap.ticker.lagSmoothing(0);

    return () => {
      gsap.ticker.remove(raf);
      lenis.destroy();
    };
  }, []);

  return children;
}

function IntroLoader() {
  return (
    <div className="intro-loader" aria-label="Loading Tangent-Flux">
      <div className="intro-card">
        <img className="intro-logo" src={tangentFluxLogo} alt="" />
        <div className="intro-copy">
          <strong>Tangent-Flux</strong>
        </div>
      </div>
    </div>
  );
}

interface LandingHeroProps {
  onQuickAdd: () => void;
  onExploreGraph: () => void;
}

function LandingHero({ onQuickAdd, onExploreGraph }: LandingHeroProps) {
  const sectionRef = useRef<HTMLElement | null>(null);

  useLayoutEffect(() => {
    const section = sectionRef.current;

    if (!section) {
      return;
    }

    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    if (reduceMotion) {
      return;
    }

    const context = gsap.context(() => {
      const timeline = gsap.timeline({
        defaults: { ease: "none" },
        scrollTrigger: {
          trigger: section,
          start: "top top",
          end: "+=260%",
          pin: true,
          scrub: 1,
          anticipatePin: 1,
          invalidateOnRefresh: true,
        },
      });

      timeline
        .to(".landing-copy", { yPercent: -34, opacity: 0, duration: 0.3 }, 0)
        .to(".graph-backdrop-sigil", { scale: 3, opacity: 0.58, duration: 0.4, transformOrigin: "50% 50%" }, 0.2)
        .to(".thought-stream", { opacity: 0.9, y: -18, stagger: 0.04, duration: 0.28 }, 0.32)
        .fromTo(".pitch-panel", { x: 110, y: 36, opacity: 0 }, { x: 0, y: 0, opacity: 1, duration: 0.3 }, 0.5)
        .fromTo(".landing-proof-row", { y: 28, opacity: 0 }, { y: 0, opacity: 1, duration: 0.24 }, 0.58)
        .fromTo(".landing-icon-row span", { scale: 0.56, opacity: 0 }, { scale: 1, opacity: 1, stagger: 0.035, duration: 0.22 }, 0.62)
        .fromTo(".landing-actions-pinned", { y: 30, opacity: 0 }, { y: 0, opacity: 1, duration: 0.22 }, 0.72)
        .fromTo(".landing-workspace-bridge", { y: 24, opacity: 0 }, { y: 0, opacity: 1, duration: 0.18 }, 0.82)
        .to({}, { duration: 0.18 }, 0.82);
    }, section);

    return () => context.revert();
  }, []);

  return (
    <section ref={sectionRef} className="landing-hero" id="top" aria-labelledby="landing-title">
      <div className="landing-pin">
        <GraphBackdrop />

        <div className="landing-copy">
          <div className="hero-brand-block" aria-label="Tangent-Flux">
            <img src={tangentFluxLogo} alt="" />
            <span>Tangent-Flux</span>
          </div>
          <h1 id="landing-title">
            <span>Your</span>
            <span>ideas</span>
            <span>finally</span>
            <span>thinking</span>
            <span>together!</span>
            <span className="blinking-cursor" aria-hidden="true"></span>
          </h1>
        </div>

        <div className="pitch-panel" aria-label="Tangent-Flux pitch">
          <p>You've bookmarked 400 things this year. How many did you build?</p>
          <strong>That's the gap Tangent-Flux closes.</strong>
          <span>
            Tangent-Flux maps raw notes, papers, tweets, and rough architectures into a living graph that reasons
            with you.
          </span>
        </div>

        <div className="landing-proof-row" aria-label="Product capabilities">
          <span>Raw ideas</span>
          <span>Research papers</span>
          <span>Web pages</span>
          <span>Architecture notes</span>
          <span>Hidden bridges</span>
        </div>

        <div className="landing-icon-row" aria-hidden="true">
          <span>
            <Upload size={20} />
          </span>
          <span>
            <BrainCircuit size={22} />
          </span>
          <span>
            <Network size={22} />
          </span>
          <span>
            <Wand2 size={20} />
          </span>
        </div>

        <div className="landing-actions landing-actions-pinned">
          <button className="landing-primary" type="button" onClick={onQuickAdd}>
            <Wand2 size={18} aria-hidden="true" />
            Start with a raw idea
          </button>
          <button className="landing-secondary" type="button" onClick={onExploreGraph}>
            <BrainCircuit size={18} aria-hidden="true" />
            Watch the graph think
          </button>
        </div>

        <div className="landing-workspace-bridge">
          <span>collect</span>
          <span>dump</span>
          <span>generate</span>
          <strong>Stop just consuming. Start building.</strong>
        </div>

        <a className="scroll-cue" href="#board" aria-label="Scroll to workspace">
          <ArrowDown size={18} aria-hidden="true" />
        </a>
      </div>
    </section>
  );
}

function BrandMark({ size = "default" }: { size?: "default" | "large" }) {
  return (
    <span className={`brand-mark brand-mark-${size}`} aria-hidden="true">
      <GlobeSignal />
    </span>
  );
}

function GraphSigil({ compact = false }: { compact?: boolean }) {
  const nodes = [
    ["core", "50%", "50%"],
    ["n1", "22%", "27%"],
    ["n2", "76%", "27%"],
    ["n3", "82%", "63%"],
    ["n4", "67%", "83%"],
    ["n5", "30%", "83%"],
    ["n6", "18%", "63%"],
    ["n7", "50%", "13%"],
    ["n8", "93%", "43%"],
    ["n9", "7%", "43%"],
  ];

  return (
    <div className={compact ? "graph-sigil graph-sigil-compact" : "graph-sigil"} aria-hidden="true">
      <span className="graph-halo graph-halo-outer" />
      <span className="graph-halo graph-halo-inner" />
      <span className="graph-line line-a" />
      <span className="graph-line line-b" />
      <span className="graph-line line-c" />
      <span className="graph-line line-d" />
      <span className="graph-line line-e" />
      <span className="graph-line line-f" />
      {nodes.map(([name, left, top]) => (
        <span className={`graph-dot graph-dot-${name}`} key={name} style={{ left, top }} />
      ))}
    </div>
  );
}

function GraphBackdrop() {
  return (
    <div className="graph-backdrop" aria-hidden="true">
      <div className="graph-backdrop-sigil">
        <GraphSigil />
      </div>
      <div className="thought-stream stream-one">
        <span>arxiv</span>
        <span>vision</span>
        <span>bert</span>
        <span>clip</span>
      </div>
      <div className="thought-stream stream-two">
        <span>tweets</span>
        <span>rough architecture</span>
        <span>novelty check</span>
      </div>
    </div>
  );
}

export default App;
