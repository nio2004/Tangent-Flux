from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import GraphEdge, GraphNode, Idea
from app.utils import loads

router = APIRouter(tags=["graph-overview"])


@router.get("/graph")
def graph_overview(db: Session = Depends(get_db)):
    ideas = db.query(Idea).order_by(Idea.updated_at.desc()).all()
    nodes = []
    edges = []
    idea_signals = {}

    for idea in ideas:
        idea_node_id = f"idea:{idea.id}"
        tags = loads(idea.tags_json, [])
        concept_labels = []
        nodes.append(
            {
                "id": idea_node_id,
                "label": idea.title,
                "kind": "idea",
                "summary": idea.description,
                "ideaId": idea.id,
                "status": idea.status,
                "tags": tags,
            }
        )
        graph_nodes = db.query(GraphNode).filter(GraphNode.idea_id == idea.id).all()
        for graph_node in graph_nodes:
            concept_labels.append(graph_node.label.lower())
            node_id = f"concept:{graph_node.id}"
            nodes.append(
                {
                    "id": node_id,
                    "label": graph_node.label,
                    "kind": "concept",
                    "summary": graph_node.summary,
                    "ideaId": idea.id,
                    "memberCount": graph_node.member_count,
                }
            )
            edges.append(
                {
                    "id": f"owns:{idea.id}:{graph_node.id}",
                    "source": idea_node_id,
                    "target": node_id,
                    "edgeType": "OWNS_CONCEPT",
                    "weight": 1,
                    "reason": "Concept belongs to this idea memory.",
                }
            )

        graph_edges = db.query(GraphEdge).filter(GraphEdge.idea_id == idea.id).all()
        for graph_edge in graph_edges:
            edges.append(
                {
                    "id": f"memory:{graph_edge.id}",
                    "source": f"concept:{graph_edge.source_node_id}",
                    "target": f"concept:{graph_edge.target_node_id}",
                    "edgeType": graph_edge.edge_type,
                    "weight": graph_edge.weight,
                    "reason": graph_edge.reason,
                }
            )
        idea_signals[idea.id] = {
            "node_id": idea_node_id,
            "tags": {tag.lower() for tag in tags},
            "concepts": set(concept_labels),
        }

    for index, source in enumerate(ideas):
        for target in ideas[index + 1 :]:
            source_signals = idea_signals[source.id]
            target_signals = idea_signals[target.id]
            shared_tags = source_signals["tags"] & target_signals["tags"]
            shared_concepts = source_signals["concepts"] & target_signals["concepts"]
            if not shared_tags and not shared_concepts:
                continue
            reasons = []
            if shared_tags:
                reasons.append(f"Shared tags: {', '.join(sorted(shared_tags))}.")
            if shared_concepts:
                reasons.append(f"Shared memory concepts: {', '.join(sorted(shared_concepts))}.")
            weight = min(1.0, 0.25 * len(shared_tags) + 0.35 * len(shared_concepts))
            edges.append(
                {
                    "id": f"idea-related:{source.id}:{target.id}",
                    "source": source_signals["node_id"],
                    "target": target_signals["node_id"],
                    "edgeType": "IDEA_RELATED",
                    "weight": round(weight, 4),
                    "reason": " ".join(reasons),
                }
            )

    return {"nodes": nodes, "edges": edges}
