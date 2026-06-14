import type { GallerySlide, Idea, KanbanBoard, ResourcePreview, TimelineEntry } from "../types/idea.ts";

export const ideas: Idea[] = [
  {
    id: "context-weaver",
    title: "Context Weaver",
    status: "Prototype",
    description: "A visual pipeline that turns scattered links, notes, and prompts into reusable build context.",
    tags: ["AI", "Research", "Architecture"],
    progress: 72,
    resources: 8,
    notes: 12,
    updated: "12 min ago",
    activity: "hot",
    code: "CTX",
    importance: 5,
    texture: "linear-gradient(135deg, rgba(22,140,255,.9), rgba(255,209,47,.42)), radial-gradient(circle at 70% 20%, rgba(255,255,255,.28), transparent 26%)",
    problem: "Research context gets trapped in chat threads and tabs, which makes follow-up implementation slower than it should be.",
  },
  {
    id: "artifact-review-loop",
    title: "Artifact Review Loop",
    status: "Research",
    description: "A review surface for sources, assumptions, changed files, and approval moments before work ships.",
    tags: ["Review", "AI", "Pinned"],
    progress: 48,
    resources: 5,
    notes: 9,
    updated: "38 min ago",
    activity: "active",
    code: "REV",
    importance: 4,
    texture: "linear-gradient(145deg, rgba(255,45,63,.86), rgba(22,140,255,.46)), repeating-linear-gradient(45deg, rgba(255,255,255,.14) 0 1px, transparent 1px 13px)",
    problem: "AI-generated work needs compact evidence trails so reviewers can trust what changed and why.",
  },
  {
    id: "visual-dependency-map",
    title: "Visual Dependency Map",
    status: "Exploration",
    description: "A diagram board for surfacing how modules, prompts, tasks, and docs connect across a project.",
    tags: ["Architecture", "Graph"],
    progress: 33,
    resources: 7,
    notes: 6,
    updated: "Today",
    activity: "quiet",
    code: "VDM",
    importance: 3,
    texture: "radial-gradient(circle at 30% 30%, rgba(216,226,239,.72), transparent 24%), linear-gradient(135deg, rgba(8,9,13,.9), rgba(22,140,255,.56))",
    problem: "Project architecture is often understood only by the person who last touched it.",
  },
  {
    id: "prompt-card-lab",
    title: "Prompt Card Lab",
    status: "Buildable",
    description: "Composable prompt cards with source notes, test summaries, and reuse ratings for repeatable work.",
    tags: ["AI", "Tasks"],
    progress: 61,
    resources: 4,
    notes: 7,
    updated: "Yesterday",
    activity: "active",
    code: "LAB",
    importance: 4,
    texture: "linear-gradient(135deg, rgba(255,209,47,.88), rgba(255,45,63,.48)), radial-gradient(circle at 18% 72%, rgba(216,226,239,.35), transparent 28%)",
    problem: "Good prompts are hard to compare, improve, and reuse when they live as raw text snippets.",
  },
  {
    id: "source-trust-console",
    title: "Source Trust Console",
    status: "Experimental",
    description: "A compact evidence view that grades source freshness, contradiction risk, and open assumptions.",
    tags: ["Research", "Evidence"],
    progress: 27,
    resources: 10,
    notes: 4,
    updated: "2 days ago",
    activity: "quiet",
    code: "SRC",
    importance: 2,
    texture: "linear-gradient(135deg, rgba(216,226,239,.72), rgba(255,209,47,.35)), radial-gradient(circle at 72% 76%, rgba(56,255,156,.3), transparent 20%)",
    problem: "Freshness and uncertainty are easy to lose when references are copied between tools.",
  },
  {
    id: "build-task-compass",
    title: "Build Task Compass",
    status: "Incubating",
    description: "A tiny planning layer that turns research branches into build tasks with acceptance cues.",
    tags: ["Tasks", "Architecture", "Pinned"],
    progress: 54,
    resources: 3,
    notes: 11,
    updated: "3 days ago",
    activity: "new",
    code: "BTS",
    importance: 4,
    texture: "linear-gradient(145deg, rgba(22,140,255,.68), rgba(8,9,13,.92)), repeating-radial-gradient(circle at 22% 40%, rgba(255,255,255,.14) 0 1px, transparent 1px 10px)",
    problem: "It is too easy for interesting research to stay inspirational instead of becoming testable work.",
  },
];

export const resources: ResourcePreview[] = [
  {
    type: "Source",
    title: "Interaction notes",
    meta: "4 excerpts, confidence high",
    description: "Annotated findings from user sessions and interface review.",
  },
  {
    type: "Prompt",
    title: "Workspace synthesis prompt",
    meta: "ready for review",
    description: "A reusable prompt card with assumptions, constraints, and expected output shape.",
  },
  {
    type: "Artifact",
    title: "Test summary card",
    meta: "2 changes pending",
    description: "Build evidence with open questions and next-step recommendations.",
  },
];

export const timeline: TimelineEntry[] = [
  { time: "09:20", text: "Captured a source freshness risk around copied research snippets." },
  { time: "10:05", text: "Mapped dashboard-to-detail transition as the signature product motion." },
  { time: "11:40", text: "Added approval-pending state to make AI work reviewable." },
  { time: "13:10", text: "Split notes, tasks, and resources into separate workspace panels." },
  { time: "15:32", text: "Flagged mobile density as the primary usability constraint." },
];

export const gallery: GallerySlide[] = [
  {
    title: "Context mesh",
    caption: "Soft artifact surface showing source cards converging into a build brief.",
    art: "mesh",
  },
  {
    title: "Review checkpoint",
    caption: "Approval state with changed files, assumptions, and test evidence.",
    art: "review",
  },
  {
    title: "Task compass",
    caption: "Kanban lanes connected to research notes and linked evidence.",
    art: "task",
  },
];

export const initialKanban: KanbanBoard = {
  todo: [
    { id: "map-evidence", title: "Map evidence states", points: 3 },
    { id: "draft-mobile", title: "Draft mobile workspace", points: 2 },
  ],
  progress: [{ id: "prototype-transition", title: "Prototype morph transition", points: 5 }],
  completed: [{ id: "collect-context", title: "Collect frontend context", points: 1 }],
};

export const starterNotes = [
  "# Research brief",
  "- **Sources:** attached and ready for review",
  "- **Assumptions:** local-first sample data for v1",
  "- Keep `tests` visible in every build summary",
  "> Approval pending before implementation handoff.",
].join("\n");
