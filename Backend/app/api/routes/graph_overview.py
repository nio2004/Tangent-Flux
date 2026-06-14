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

    for idea in ideas:
        idea_node_id = f"idea:{idea.id}"
        tags = loads(idea.tags_json, [])
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

    return {"nodes": nodes, "edges": edges}
