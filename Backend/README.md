# Tangent-Flux Backend

FastAPI backend for the Tangent-Flux idea workspace and four-agent memory pipeline.

## Setup

```powershell
cd Backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

The API starts with SQLite and seeds frontend-compatible demo ideas when the database is empty.

## Core Endpoints

- `GET /api/ideas`
- `POST /api/ideas`
- `GET /api/ideas/{idea_id}`
- `PATCH /api/ideas/{idea_id}`
- `GET /api/ideas/{idea_id}/workspace`
- `POST /api/ideas/{idea_id}/initialize`
- `POST /api/ideas/{idea_id}/dump`
- `GET /api/ideas/{idea_id}/graph`
- `GET /api/ideas/{idea_id}/memory`
- `GET /api/ideas/{idea_id}/agent-runs`
- `POST /api/ideas/{idea_id}/query`
- `POST /api/ideas/{idea_id}/generate`
- `GET /api/ideas/{idea_id}/resources`
- `POST /api/ideas/{idea_id}/resources`
- `GET /api/ideas/{idea_id}/tasks`
- `POST /api/ideas/{idea_id}/tasks`
- `PATCH /api/tasks/{task_id}`
- `POST /api/tasks/{task_id}/move`
- `GET /api/ideas/{idea_id}/timeline`
- `POST /api/ideas/{idea_id}/timeline`

## Agent Readiness

Agent 3 is guarded by backend state. `/dump` returns `409 MEMORY_NOT_READY` unless Agent 1 and Agent 2 are validated and graph + textual memory exist.

