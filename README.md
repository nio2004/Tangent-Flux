# Tangent-Flux

Tangent-Flux is an AI-native idea workspace for turning scattered research, links, images, notes, and rough project thoughts into structured memory, graph visualizations, and actionable tasks.

The project is split into:

- `Frontend/` - React + Vite UI for the idea board, studio controls, memory graph, resource stack, gallery, Kanban, and idea agent chat.
- `Backend/` - FastAPI + SQLite backend with the four-agent memory pipeline, parsers, embeddings, graph generation, persistent sessions, tasks, resources, artifacts, and timeline events.

## Core Idea

Tangent-Flux helps with cognition overload by letting users dump raw material into an idea workspace:

- Research links
- Raw idea notes
- Images and diagrams
- Logs and updates
- Tasks and evidence

The backend then converts that context into both textual memory and graph memory. The user can visualize local/global memory, inspect concept relationships, and talk to an idea-specific agent that knows the idea's resources, images, graph nodes, evidence, and previous chat messages.

## Agent Pipeline

The backend implements a four-agent memory system:

1. **Agent 1: Memory Schema Agent**
   - Cold-start only.
   - Extracts umbrella concepts, source summaries, keyphrases, content types, bridge hints, and resource-to-concept mapping.

2. **Agent 2: Memory Generation Agent**
   - Runs after Agent 1 validation.
   - Creates textual memory, graph nodes, graph edges, concept clusters, embeddings, and centroid state.

3. **Agent 3: Memory Updation Agent**
   - Runs after memory is ready.
   - Uses deterministic similarity thresholds:
     - `ASSIMILATE` for strongly related updates
     - `BRIDGE` for cross-concept overlap
     - `ACCOMMODATE` for new concepts

4. **Agent 4: Generation and Query Agent**
   - Answers questions and generates tasks using textual memory, graph memory, resources, chunks, images, and chat history.

## Tech Stack

Backend:

- FastAPI
- SQLite
- SQLAlchemy
- Pydantic
- OpenAI Agents SDK
- OpenAI embeddings and vision models
- Pytest

Frontend:

- React
- TypeScript
- Vite
- Lucide icons
- CSS modules/global styling

## Setup

### Backend

```powershell
cd D:\CodingStuff\CodexHackathon\Tangent-Flux\Backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Edit `Backend/.env` and add your OpenAI API key:

```env
OPENAI_API_KEY=
DATABASE_URL=sqlite:///./tangent_flux.db
OPENAI_AGENT_MODEL=gpt-5-nano
OPENAI_VISION_MODEL=gpt-4.1-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
FRONTEND_ORIGIN=http://localhost:5173
USE_OPENAI_AGENTS=true
```

Run the backend:

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

API docs:

```text
http://127.0.0.1:8001/docs
```

### Frontend

```powershell
cd D:\CodingStuff\CodexHackathon\Tangent-Flux\Frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

## Useful Commands

Run backend tests:

```powershell
cd D:\CodingStuff\CodexHackathon\Tangent-Flux\Backend
.\.venv\Scripts\Activate.ps1
python -m pytest app/tests
```

Build frontend:

```powershell
cd D:\CodingStuff\CodexHackathon\Tangent-Flux\Frontend
npm run build
```

Run frontend tests:

```powershell
cd D:\CodingStuff\CodexHackathon\Tangent-Flux\Frontend
npm test
```

## Key Backend APIs

Ideas and workspace:

- `GET /api/ideas`
- `POST /api/ideas`
- `GET /api/ideas/{idea_id}`
- `PATCH /api/ideas/{idea_id}`
- `GET /api/ideas/{idea_id}/workspace`

Memory:

- `POST /api/ideas/{idea_id}/initialize`
- `POST /api/ideas/{idea_id}/dump`
- `GET /api/ideas/{idea_id}/memory`
- `GET /api/ideas/{idea_id}/graph`
- `GET /api/ideas/{idea_id}/agent-runs`

Generation and chat:

- `POST /api/ideas/{idea_id}/query`
- `POST /api/ideas/{idea_id}/generate`
- `GET /api/ideas/{idea_id}/chat/sessions`
- `POST /api/ideas/{idea_id}/chat/sessions`
- `POST /api/ideas/{idea_id}/chat/sessions/{session_id}/messages`

Workspace:

- `GET /api/ideas/{idea_id}/resources`
- `POST /api/ideas/{idea_id}/resources`
- `POST /api/ideas/{idea_id}/uploads`
- `GET /api/ideas/{idea_id}/tasks`
- `POST /api/ideas/{idea_id}/tasks`
- `PATCH /api/tasks/{task_id}`
- `POST /api/tasks/{task_id}/move`
- `GET /api/ideas/{idea_id}/timeline`

Graph overview:

- `GET /api/graph`

## Notes

- `Backend/.env` is local-only and must not be committed.
- SQLite is used for the MVP.
- Agent 3 refuses to run until Agent 1 and Agent 2 have validated memory, textual memory exists, and graph nodes with centroids exist.
- Uploaded images are described through the vision model and stored in the architecture gallery.
- Links are parsed into resources/chunks and appear as linked evidence.
