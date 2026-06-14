# Tangent-Flux Frontend Logic

This document explains the current frontend behavior and data expectations so a backend coding agent can add APIs, persistence, uploads, and real-time workspace data without having to reverse-engineer the React app.

## Product Shape

Tangent-Flux is a frontend-only React workspace right now. The first screen is a visual idea board. Each idea card opens into a focused research workspace with a banner-style overview, notes, resources, tasks, gallery artifacts, timeline entries, and studio controls.

The detail workspace is organized into three major visual sections:

- A framed insight surface with the scrollable Brainstorm/Idea Dump panel taking the main left column and Problem Statement plus Linked Evidence stacked on the right.
- A Task and Context Mesh section with the Kanban task workspace beside the Architecture Gallery.
- A Research Journal section rendered as a horizontal timeline with glowing log points and hover/focus detail reveal.

The frontend currently uses local sample data and React state only. There is no backend, persistence, auth, routing, or file storage yet.

## Stack

- React 19
- TypeScript
- Vite
- MUI `Dialog` for the quick-add modal
- `lucide-react` icons
- Vanilla CSS in `src/styles/global.css`
- Small local UI primitives:
  - `src/components/ui/button.tsx`
  - `src/components/ui/badge.tsx`

## Key Files

- `src/App.tsx`: root shell and state owner
- `src/types/idea.ts`: frontend domain types
- `src/data/ideas.ts`: local sample data
- `src/lib/kanban.ts`: pure task creation and lane movement helpers
- `src/lib/markdown.ts`: tiny markdown renderer for notes preview
- `src/components/dashboard/*`: board, filters, cards, top-level browsing
- `src/components/detail/*`: selected idea workspace
- `src/components/quick-add/QuickAddDialog.tsx`: idea capture modal

## Root State

`App.tsx` owns the main app state:

```ts
ideas: Idea[]
query: string
activeFilter: string
selectedIdea: Idea | null
detailOpen: boolean
quickAddOpen: boolean
morphRect: DOMRect | null
notes: string
cover: string | null
board: KanbanBoard
```

Important backend note: `notes`, `cover`, `board`, `resources`, `timeline`, and `gallery` are currently global demo state, not per-idea persisted state. A backend should model these per idea.

## Domain Types

Current primary frontend type:

```ts
interface Idea {
  id: string;
  title: string;
  status:
    | "Prototype"
    | "Incubating"
    | "Exploration"
    | "Pinned"
    | "Research"
    | "Buildable"
    | "Experimental"
    | "Capture"
    | "Archive";
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
```

Supporting types:

```ts
interface ResourcePreview {
  type: string;
  title: string;
  meta: string;
  description: string;
}

interface TimelineEntry {
  time: string;
  text: string;
}

interface GallerySlide {
  title: string;
  caption: string;
  art: string;
}

type KanbanLaneId = "todo" | "progress" | "completed";

interface KanbanTask {
  id: string;
  title: string;
  points: number;
}

type KanbanBoard = Record<KanbanLaneId, KanbanTask[]>;
```

## Main Frontend Flows

### Board Load

`App.tsx` initializes ideas from `src/data/ideas.ts`. The dashboard immediately renders:

- `Topbar`
- `FilterBar`
- `IdeaGrid`
- `IdeaCard` for each visible idea

There is no loading state yet because all data is local.

### Search And Filter

Search is live and local:

- `query` filters ideas by title, description, and tags.
- `activeFilter` matches `idea.tags` or `idea.status`.
- Search and filter are combined in a `useMemo` inside `App.tsx`.

Backend-ready behavior: if the dataset grows, this can become `GET /api/ideas?query=&filter=`.

### Open Idea Detail

When a user clicks an idea card:

1. `IdeaCard` passes the clicked card `DOMRect` to `App.openIdea`.
2. `App` stores `morphRect` and `selectedIdea`.
3. After a short timeout, `detailOpen` becomes `true`.
4. The detail workspace slides in.
5. Body scrolling is locked while detail is open.

The morph animation is purely visual. Backend work only needs to provide the selected idea and its related workspace data.

The detail header uses `CoverDropzone` as a banner/background layer. The visible idea metadata comes from the selected `Idea`; status is no longer repeated as a title badge because tags are already rendered below the description.

### Quick Add

`QuickAddDialog` collects:

- title, required
- source/link
- quick note
- comma-separated tags

It creates a frontend `Idea` object locally and prepends it to `ideas`.

Backend-ready behavior:

- `POST /api/ideas`
- Return the created idea with canonical `id`, timestamps, counters, and derived `code`.
- If a source or note is provided, create initial resource/note records server-side.

### Notes

`MarkdownNotes` supports edit and preview mode. It stores one markdown string in root state.

Backend-ready behavior:

- Notes should become per-idea.
- Persist markdown, not rendered HTML.
- The frontend can continue rendering markdown client-side, or the backend can expose sanitized rendered HTML if desired.

Suggested endpoint:

```http
GET /api/ideas/:ideaId/notes
PUT /api/ideas/:ideaId/notes/:noteId
POST /api/ideas/:ideaId/notes
```

### Cover Upload

`CoverDropzone` reads an uploaded image with `FileReader.readAsDataURL` and stores the base64 data URL in local state.

Backend-ready behavior:

- Replace base64 local state with an upload flow.
- Store returned asset URL on the idea or a related media record.

Suggested endpoint:

```http
POST /api/ideas/:ideaId/cover
Content-Type: multipart/form-data

Response: { "coverUrl": "https://..." }
```

### Resources

`ResourceCarousel` displays static `ResourcePreview[]` from `src/data/ideas.ts`.

In the current layout, resources appear as the bottom card in the right rail of the first detail section, paired with the Problem Statement above it. This keeps the evidence close to the brainstorm notes without competing with the task/gallery section.

Backend-ready behavior:

- Resources should be linked to an idea.
- They should support type, title, source URL, metadata, confidence/review state, and timestamps.

Suggested endpoint:

```http
GET /api/ideas/:ideaId/resources
POST /api/ideas/:ideaId/resources
PATCH /api/resources/:resourceId
DELETE /api/resources/:resourceId
```

### Kanban Tasks

`KanbanWorkspace` displays a `KanbanBoard` with three lanes:

- `todo`
- `progress`
- `completed`

Tasks can be moved between lanes. `StudioControlsOverlay` can add a new task to `todo`.

The preview board renders each lane as a stacked-card preview. The first task in each lane array is the visible top card. When a task is dragged or moved into a lane, `moveTask` prepends it to the target lane so the most recently moved task appears on top and older tasks sit behind it.

Pure helper behavior lives in `src/lib/kanban.ts`:

- `createTask(title, points)`
- `moveTask(board, taskId, targetLane)`

Backend-ready behavior:

- Tasks should be per idea.
- Movement should persist lane/order, with newest moved items placed first unless the backend later adds manual reordering.
- Consider adding `sortOrder` because the frontend currently derives stack order from array position.

Suggested endpoint:

```http
GET /api/ideas/:ideaId/tasks
POST /api/ideas/:ideaId/tasks
PATCH /api/tasks/:taskId
POST /api/tasks/:taskId/move
```

Suggested move body:

```json
{
  "lane": "progress",
  "sortOrder": 2000
}
```

### Timeline

`TimelineWindow` shows a static list of timestamped entries as a horizontal research timeline. It opens on the latest five entries, supports left/right navigation, and renders each entry as a compact glowing log point. The entry text is revealed on hover or keyboard focus to keep the timeline scannable.

Backend-ready behavior:

- Timeline should be generated from explicit journal entries and important system events.
- It can include idea creation, note edits, resource attachments, task movement, review approval, and uploads.

Suggested endpoint:

```http
GET /api/ideas/:ideaId/timeline
POST /api/ideas/:ideaId/timeline
```

### Gallery

The gallery is static demo data. It represents architecture diagrams, prompt cards, product previews, or generated artifacts.

The current Architecture Gallery uses arrow controls instead of text toggles. Long artifact titles are constrained and wrapped inside the gallery card so large headings do not overflow into neighboring layout columns.

Backend-ready behavior:

- Treat gallery items as idea artifacts.
- Store title, caption, type, asset URL, preview URL, and review state.

Suggested endpoint:

```http
GET /api/ideas/:ideaId/artifacts
POST /api/ideas/:ideaId/artifacts
PATCH /api/artifacts/:artifactId
DELETE /api/artifacts/:artifactId
```

## Recommended Backend Data Model

Minimum useful entities:

- `User`
- `Workspace`
- `Idea`
- `IdeaNote`
- `IdeaResource`
- `IdeaTask`
- `IdeaTimelineEntry`
- `IdeaArtifact`
- `IdeaAsset`

Recommended `Idea` backend fields:

```ts
interface BackendIdea {
  id: string;
  workspaceId: string;
  title: string;
  status: Idea["status"];
  description: string;
  problem: string;
  tags: string[];
  progress: number;
  activity: Idea["activity"];
  code: string;
  importance: number;
  texture?: string;
  coverUrl?: string;
  resourceCount: number;
  noteCount: number;
  taskCount: number;
  createdAt: string;
  updatedAt: string;
}
```

Important mapping note:

- Frontend `resources` and `notes` are numeric counters on `Idea`.
- Actual records should live in separate tables/collections.
- API responses can include counters to keep cards fast.

## Suggested API Shape

For a first backend pass, keep the API simple:

```http
GET    /api/ideas
POST   /api/ideas
GET    /api/ideas/:ideaId
PATCH  /api/ideas/:ideaId
DELETE /api/ideas/:ideaId

GET    /api/ideas/:ideaId/workspace
```

`GET /api/ideas/:ideaId/workspace` can hydrate the detail view in one request:

```json
{
  "idea": {},
  "notes": [],
  "resources": [],
  "tasks": {
    "todo": [],
    "progress": [],
    "completed": []
  },
  "timeline": [],
  "artifacts": [],
  "coverUrl": null
}
```

This is the most frontend-friendly first integration because opening the detail workspace needs all related surfaces.

## Frontend Integration Points To Replace

When adding the backend, replace these local sources:

- `initialIdeas` in `src/App.tsx`
- `resources`, `timeline`, `gallery`, `initialKanban`, and `starterNotes` from `src/data/ideas.ts`
- local `setIdeas` create flow in `createIdea`
- local `setNotes`
- local `setCover`
- local `setBoard`

Recommended frontend service boundary:

```text
src/api/
  client.ts
  ideas.ts
  workspace.ts
  uploads.ts
```

Keep backend calls out of presentational components. `App.tsx` or future route/container components should own data fetching and mutation orchestration.

## Loading And Error States Needed Later

The current UI has no async states. A backend integration should add:

- initial board loading state
- board fetch error state with retry
- quick-add submit loading and validation error
- detail workspace loading state after card click
- notes save pending/error state
- cover upload progress/error state
- task move optimistic update with rollback
- resource/artifact empty states

## Auth And Multi-Workspace Assumptions

The frontend visually implies a workspace product, but there is no auth or workspace selector yet.

For backend planning:

- every idea should belong to a workspace
- every workspace should belong to one or more users
- API calls should be scoped by authenticated user and workspace
- frontend can later add workspace switching in `Topbar`

## Current Verification

The pure helper logic has tests:

- `tests/kanban.test.ts`
- `tests/markdown.test.ts`

Current test command used successfully:

```powershell
node --test tests/*.test.ts
```

The production build previously passed after dependency installation. The latest `vite.config.ts` sets `base: "./"` so the built app can use relative assets.
