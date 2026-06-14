from fastapi.testclient import TestClient
import base64

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.api.routes import uploads
from app.services.seed_service import seed_if_empty

PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
)


@pytest.fixture()
def client():
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    seed_db = TestingSessionLocal()
    try:
        seed_if_empty(seed_db)
    finally:
        seed_db.close()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    try:
        yield test_client
    finally:
        app.dependency_overrides.clear()
        test_client.close()


def test_ideas_and_workspace_hydrate(client: TestClient):
    response = client.get("/api/ideas")
    assert response.status_code == 200
    ideas = response.json()
    assert ideas

    workspace = client.get(f"/api/ideas/{ideas[0]['id']}/workspace")
    assert workspace.status_code == 200
    payload = workspace.json()
    assert {"idea", "notes", "resources", "tasks", "timeline", "artifacts", "graph", "agentRuns"} <= set(payload)


def test_agent3_guard_and_memory_flow(client: TestClient):
    idea = client.post(
        "/api/ideas",
        json={
            "title": "Guard Flow Test",
            "description": "Testing GRPO fine tuning, evaluation metrics, and resource constraints.",
            "problem": "Turn scattered RL research into build direction.",
            "tags": ["AI", "Research"],
        },
    ).json()

    blocked = client.post(
        f"/api/ideas/{idea['id']}/dump",
        json={"input": "GRPO update about memory efficient fine tuning and evaluation."},
    )
    assert blocked.status_code == 409
    assert blocked.json()["detail"]["error"] == "MEMORY_NOT_READY"

    initialized = client.post(
        f"/api/ideas/{idea['id']}/initialize",
        json={
            "input": "GRPO fine tuning can reduce memory pressure. Evaluation metrics compare reward quality. Small GPUs create resource constraints."
        },
    )
    assert initialized.status_code == 200
    assert initialized.json()["graph"]["nodes"]

    updated = client.post(
        f"/api/ideas/{idea['id']}/dump",
        json={"input": "Unsloth GRPO training loop is more memory efficient and belongs in the build plan."},
    )
    assert updated.status_code == 200
    assert updated.json()["decision"] in {"ASSIMILATE", "ACCOMMODATE", "BRIDGE"}


def test_workspace_mutations_for_studio_controls(client: TestClient):
    idea = client.post(
        "/api/ideas",
        json={
            "title": "Studio Controls Test",
            "description": "Testing workspace mutations from the frontend studio controls.",
            "problem": "Make links, diagrams, logs, and tasks persist.",
            "tags": ["Test"],
        },
    ).json()
    idea_id = idea["id"]

    resource = client.post(
        f"/api/ideas/{idea_id}/resources",
        json={"input": "https://example.com/tangent-flux", "title": "Example link"},
    )
    assert resource.status_code == 200
    assert resource.json()["title"] == "Example link"

    artifact = client.post(
        f"/api/ideas/{idea_id}/artifacts",
        json={"title": "Architecture sketch", "caption": "A first diagram.", "art": "mesh"},
    )
    assert artifact.status_code == 200
    assert artifact.json()["title"] == "Architecture sketch"

    timeline = client.post(
        f"/api/ideas/{idea_id}/timeline",
        json={"text": "Logged a useful update.", "type": "journal"},
    )
    assert timeline.status_code == 200
    assert timeline.json()["text"] == "Logged a useful update."

    task = client.post(
        f"/api/ideas/{idea_id}/tasks",
        json={"title": "Persist a studio task", "lane": "todo", "points": 2},
    )
    assert task.status_code == 200
    assert task.json()["title"] == "Persist a studio task"

    workspace = client.get(f"/api/ideas/{idea_id}/workspace")
    assert workspace.status_code == 200
    payload = workspace.json()
    assert payload["resources"]
    assert payload["artifacts"]
    assert payload["timeline"]
    assert payload["tasks"]["todo"]


def test_image_upload_and_graph_overview(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        uploads,
        "ingest_image",
        lambda _content, _content_type, filename: f"Vision summary for {filename}: architecture diagram with labeled flow.",
    )
    idea = client.post(
        "/api/ideas",
        json={
            "title": "Image Upload Test",
            "description": "Testing image ingestion.",
            "problem": "Images should become gallery artifacts.",
            "tags": ["Vision"],
        },
    ).json()
    idea_id = idea["id"]

    upload = client.post(
        f"/api/ideas/{idea_id}/artifacts/image",
        files={"file": ("diagram.png", PNG_1X1, "image/png")},
    )
    assert upload.status_code == 200
    assert upload.json()["title"] == "diagram.png"
    assert "Vision summary" in upload.json()["caption"]
    assert upload.json()["assetUrl"].startswith("data:image/png;base64,")

    workspace = client.get(f"/api/ideas/{idea_id}/workspace").json()
    assert workspace["artifacts"]
    assert workspace["artifacts"][0]["caption"].startswith("Vision summary")
    assert workspace["resources"] == []

    graph = client.get("/api/graph")
    assert graph.status_code == 200
    assert graph.json()["nodes"]
