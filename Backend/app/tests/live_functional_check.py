import json
import time
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8001"


def summarize(payload):
    if isinstance(payload, dict):
        summary = {}
        for key in ["id", "title", "memoryState", "decision", "confidence", "answer", "sourceNodes"]:
            if key in payload:
                summary[key] = payload[key]
        if "graph" in payload and isinstance(payload["graph"], dict):
            summary["graph_nodes"] = len(payload["graph"].get("nodes", []))
            summary["graph_edges"] = len(payload["graph"].get("edges", []))
        if "nodes" in payload:
            summary["nodes"] = len(payload.get("nodes", []))
            summary["edges"] = len(payload.get("edges", []))
        if "kanban_tasks" in payload:
            summary["tasks_generated"] = len(payload.get("kanban_tasks", []))
        return summary or list(payload.keys())[:8]
    if isinstance(payload, list):
        return {"count": len(payload)}
    return str(payload)[:200]


def call(results, name, method, path, body=None, expect=None):
    start = time.perf_counter()
    data = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        BASE + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            raw = response.read().decode("utf-8")
            payload = json.loads(raw) if raw else None
            status = response.status
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = raw
        status = exc.code

    latency = int((time.perf_counter() - start) * 1000)
    ok = status == expect if expect else 200 <= status < 300
    results.append(
        {
            "name": name,
            "method": method,
            "path": path,
            "status": status,
            "expected": expect,
            "ok": ok,
            "latency_ms": latency,
            "summary": summarize(payload),
        }
    )
    if not ok:
        raise RuntimeError(json.dumps({"failed": name, "status": status, "payload": payload}, indent=2)[:3000])
    return payload


def main():
    results = []
    state = {}

    call(results, "health", "GET", "/health")
    call(results, "list ideas", "GET", "/api/ideas")
    created = call(
        results,
        "create idea",
        "POST",
        "/api/ideas",
        {
            "title": "Functional Test Memory",
            "description": "Testing Tangent-Flux memory around GRPO fine tuning, CLIP, evaluation, and resource constraints.",
            "problem": "Convert scattered AI research into buildable project tasks.",
            "tags": ["AI", "Research", "Test"],
        },
    )
    idea_id = created["id"]
    state["idea_id"] = idea_id

    call(results, "workspace before init", "GET", f"/api/ideas/{idea_id}/workspace")
    call(
        results,
        "agent3 guard before init",
        "POST",
        f"/api/ideas/{idea_id}/dump",
        {"input": "GRPO update should be blocked before memory exists."},
        expect=409,
    )

    init = call(
        results,
        "initialize memory",
        "POST",
        f"/api/ideas/{idea_id}/initialize",
        {
            "input": (
                "GRPO fine tuning can reduce memory pressure on small GPUs. "
                "Evaluation metrics should compare reward quality and task success. "
                "CLIP bridges image and text representations for multimodal retrieval and contrastive learning."
            )
        },
    )
    state["init_nodes"] = len(init["graph"]["nodes"])
    state["init_edges"] = len(init["graph"]["edges"])

    call(results, "graph after init", "GET", f"/api/ideas/{idea_id}/graph")
    call(results, "memory after init", "GET", f"/api/ideas/{idea_id}/memory")

    related = call(
        results,
        "dump related update",
        "POST",
        f"/api/ideas/{idea_id}/dump",
        {
            "input": (
                "Unsloth GRPO training loop appears more memory efficient than vanilla transformer "
                "fine tuning and should be added to the constrained GPU build plan."
            )
        },
    )
    state["related_decision"] = related.get("decision")

    novel = call(
        results,
        "dump novel update",
        "POST",
        f"/api/ideas/{idea_id}/dump",
        {
            "input": (
                "I found a paper about diffusion-based UI layout generation and visual design critique, "
                "which may be a separate artifact generation direction."
            )
        },
    )
    state["novel_decision"] = novel.get("decision")

    bridge = call(
        results,
        "dump bridge update",
        "POST",
        f"/api/ideas/{idea_id}/dump",
        {
            "input": (
                "A CLIP-style reward model could connect multimodal image-text embeddings with RL fine tuning "
                "by scoring generated outputs against textual goals."
            )
        },
    )
    state["bridge_decision"] = bridge.get("decision")

    query = call(
        results,
        "query memory",
        "POST",
        f"/api/ideas/{idea_id}/query",
        {"question": "What do I have related to GRPO fine tuning and resource constraints?"},
    )
    state["query_sources"] = query.get("sourceNodes")

    generated = call(results, "generate tasks", "POST", f"/api/ideas/{idea_id}/generate")
    state["generated_tasks"] = len(generated.get("kanban_tasks", []))

    tasks = call(results, "tasks board", "GET", f"/api/ideas/{idea_id}/tasks")
    state["todo_count"] = len(tasks.get("todo", []))

    logs = call(results, "agent logs", "GET", f"/api/ideas/{idea_id}/agent-runs")
    state["agent_log_count"] = len(logs)

    workspace = call(results, "workspace final", "GET", f"/api/ideas/{idea_id}/workspace")
    state["final_memory_state"] = workspace["idea"]["memoryState"]
    state["final_nodes"] = len(workspace["graph"]["nodes"])
    state["final_edges"] = len(workspace["graph"]["edges"])

    report = {"base_url": BASE, "state": state, "results": results}
    with open("functional-test-report.json", "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
