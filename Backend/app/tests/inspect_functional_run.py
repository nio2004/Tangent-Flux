import json
import sqlite3

IDEA_ID = "032c5b8f-6aeb-4966-b6bf-4654303161a3"

conn = sqlite3.connect("tangent_flux.db")
conn.row_factory = sqlite3.Row

runs = conn.execute(
    """
    select agent_type, status, latency_ms, error_message, output_json, created_at
    from agent_runs
    where idea_id = ?
    order by created_at
    """,
    (IDEA_ID,),
).fetchall()

for row in runs:
    output = json.loads(row["output_json"] or "{}")
    print(
        json.dumps(
            {
                "agent": row["agent_type"],
                "status": row["status"],
                "latency_ms": row["latency_ms"],
                "error": row["error_message"],
                "output_keys": list(output.keys()),
                "decision": output.get("decision"),
                "reason": output.get("reason"),
                "created_at": row["created_at"],
            },
            indent=2,
        )
    )

counts = {
    "graph_nodes": conn.execute("select count(*) from graph_nodes where idea_id = ?", (IDEA_ID,)).fetchone()[0],
    "graph_edges": conn.execute("select count(*) from graph_edges where idea_id = ?", (IDEA_ID,)).fetchone()[0],
    "tasks": conn.execute("select count(*) from tasks where idea_id = ?", (IDEA_ID,)).fetchone()[0],
    "timeline_entries": conn.execute("select count(*) from timeline_entries where idea_id = ?", (IDEA_ID,)).fetchone()[0],
    "resources": conn.execute("select count(*) from resources where idea_id = ?", (IDEA_ID,)).fetchone()[0],
}
print(json.dumps({"counts": counts}, indent=2))
