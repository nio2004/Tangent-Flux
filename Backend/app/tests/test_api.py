from fastapi.testclient import TestClient
import base64

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.api.routes import uploads
from app.services import chat_service, parser_service
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


def test_idea_dump_note_persists(client: TestClient):
    idea = client.post(
        "/api/ideas",
        json={
            "title": "Persistent Dump Test",
            "description": "Testing note persistence.",
            "problem": "Idea dump edits should survive a workspace reload.",
            "tags": ["Test"],
        },
    ).json()

    saved = client.put(
        f"/api/ideas/{idea['id']}/notes",
        json={"markdown": "## Saved dump\n\nThis should come back from SQLite."},
    )
    assert saved.status_code == 200
    assert saved.json()["markdown"] == "## Saved dump\n\nThis should come back from SQLite."

    workspace = client.get(f"/api/ideas/{idea['id']}/workspace")
    assert workspace.status_code == 200
    notes = workspace.json()["notes"]
    assert len(notes) == 1
    assert notes[0]["markdown"] == "## Saved dump\n\nThis should come back from SQLite."


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
        json={
            "input": "This linked evidence describes Tangent-Flux studio controls, persistent resources, timeline logs, and task creation workflows.",
            "title": "Example evidence",
        },
    )
    assert resource.status_code == 200
    assert resource.json()["title"] == "Example evidence"

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


def test_failed_resource_is_not_persisted(client: TestClient):
    idea = client.post(
        "/api/ideas",
        json={
            "title": "Failed Resource Test",
            "description": "Testing that failed linked attachments stay out of the resource stack.",
            "problem": "Failed resource parses should be visible as errors only.",
            "tags": ["Test"],
        },
    ).json()
    idea_id = idea["id"]

    resource = client.post(
        f"/api/ideas/{idea_id}/resources",
        json={"input": "too short", "title": "Broken link"},
    )
    assert resource.status_code == 422
    assert "Raw text must be at least 20 characters" in resource.json()["detail"]

    resources = client.get(f"/api/ideas/{idea_id}/resources")
    assert resources.status_code == 200
    assert resources.json() == []


def test_bare_domain_resource_is_treated_as_url(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    class FakeResponse:
        text = "<html><title>ChatGPT</title><body>" + ("useful source material " * 20) + "</body></html>"

        def raise_for_status(self) -> None:
            return None

    captured_urls: list[str] = []

    def fake_get(url: str, **_kwargs):
        captured_urls.append(url)
        return FakeResponse()

    monkeypatch.setattr(parser_service.requests, "get", fake_get)
    idea = client.post(
        "/api/ideas",
        json={
            "title": "Bare Domain Test",
            "description": "Testing bare domains in linked attachments.",
            "problem": "Users should not need to type a URL scheme.",
            "tags": ["Test"],
        },
    ).json()

    resource = client.post(
        f"/api/ideas/{idea['id']}/resources",
        json={"input": "chatgpt.com", "title": "ChatGPT"},
    )
    assert resource.status_code == 200
    assert captured_urls == ["https://chatgpt.com"]
    assert resource.json()["sourceUrl"] == "https://chatgpt.com"


def test_short_webpage_resource_returns_actionable_error(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    class FakeResponse:
        text = "<html><title>Short Page</title><body>Short page.</body></html>"

        def raise_for_status(self) -> None:
            return None

    monkeypatch.setattr(parser_service.requests, "get", lambda *_args, **_kwargs: FakeResponse())
    idea = client.post(
        "/api/ideas",
        json={
            "title": "Short Page Test",
            "description": "Testing short webpage errors.",
            "problem": "Users need useful parser failure messages.",
            "tags": ["Test"],
        },
    ).json()

    resource = client.post(
        f"/api/ideas/{idea['id']}/resources",
        json={"input": "chatgpt.com", "title": "ChatGPT"},
    )
    assert resource.status_code == 422
    assert "did not expose enough readable text" in resource.json()["detail"]


def test_webpage_resource_uses_visible_text_fallback(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    class FakeResponse:
        text = """
        <html>
          <head><title>Great Articles</title><script>window.noisy = true;</script></head>
          <body>
            <h1>150 Great Articles and Essays</h1>
            <p>The best classic and new articles, nonfiction and essays from around the net.</p>
            <ul>
              <li>Attitude by Margaret Atwood</li>
              <li>This is Water by David Foster Wallace</li>
              <li>On Keeping a Notebook by Joan Didion</li>
            </ul>
            <p>""" + ("interesting readable article list content " * 12) + """</p>
          </body>
        </html>
        """

        def raise_for_status(self) -> None:
            return None

    monkeypatch.setattr(parser_service.requests, "get", lambda *_args, **_kwargs: FakeResponse())
    idea = client.post(
        "/api/ideas",
        json={
            "title": "Visible Text Fallback Test",
            "description": "Testing visible HTML text extraction.",
            "problem": "Index pages should become resources when they contain readable text.",
            "tags": ["Test"],
        },
    ).json()

    resource = client.post(
        f"/api/ideas/{idea['id']}/resources",
        json={"input": "https://tetw.org/Greats", "title": "Greats"},
    )
    assert resource.status_code == 200
    assert resource.json()["title"] == "Greats"
    assert resource.json()["meta"] == "webpage / parsed"
    assert "150 Great Articles" in resource.json()["description"]


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


def test_idea_agent_chat_persists_session(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    async def fake_query(question: str, memory: str, nodes: list[str]):
        from app.schemas.agent import Agent4QueryOutput

        return Agent4QueryOutput(
            answer=f"Grounded answer using {', '.join(nodes[:2])}: GRPO and the uploaded diagram can be compared.",
            source_nodes=nodes[:2],
        )

    monkeypatch.setattr(chat_service, "run_agent4_query", fake_query)
    idea = client.post(
        "/api/ideas",
        json={
            "title": "Agent Chat Test",
            "description": "Testing idea-specific chat.",
            "problem": "Compare research papers and uploaded diagrams.",
            "tags": ["AI", "Memory"],
        },
    ).json()
    idea_id = idea["id"]

    initialized = client.post(
        f"/api/ideas/{idea_id}/initialize",
        json={"input": "GRPO improves RL fine tuning. SFT gives supervised warm starts. Attention diagrams explain token relationships."},
    )
    assert initialized.status_code == 200

    response = client.post(
        f"/api/ideas/{idea_id}/chat",
        json={"content": "Is there a relationship between GRPO and the attention diagram?"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["session"]["id"]
    assert payload["assistantMessage"]["role"] == "assistant"
    assert "GRPO" in payload["assistantMessage"]["content"]
    assert payload["assistantMessage"]["content"].startswith("- ")
    assert payload["assistantMessage"]["sources"]

    session_id = payload["session"]["id"]
    detail = client.get(f"/api/ideas/{idea_id}/chat/sessions/{session_id}")
    assert detail.status_code == 200
    assert len(detail.json()["messages"]) == 2
