from sqlalchemy.orm import Session

from app.models import GraphEdge, GraphNode
from app.services.similarity_service import cosine_similarity
from app.utils import loads


def get_graph(db: Session, idea_id: str) -> tuple[list[GraphNode], list[GraphEdge]]:
    nodes = db.query(GraphNode).filter(GraphNode.idea_id == idea_id).all()
    edges = db.query(GraphEdge).filter(GraphEdge.idea_id == idea_id).all()
    return nodes, edges


def create_similarity_edges(db: Session, idea_id: str, nodes: list[GraphNode], threshold: float = 0.55) -> list[GraphEdge]:
    edges: list[GraphEdge] = []
    existing = {
        tuple(sorted([edge.source_node_id, edge.target_node_id]))
        for edge in db.query(GraphEdge).filter(GraphEdge.idea_id == idea_id).all()
    }
    for index, source in enumerate(nodes):
        for target in nodes[index + 1 :]:
            key = tuple(sorted([source.id, target.id]))
            if key in existing:
                continue
            score = cosine_similarity(loads(source.centroid_embedding_json, []), loads(target.centroid_embedding_json, []))
            if score >= threshold:
                edge = GraphEdge(
                    idea_id=idea_id,
                    source_node_id=source.id,
                    target_node_id=target.id,
                    edge_type="SIMILARITY",
                    weight=round(score, 4),
                    reason="Centroid similarity crossed graph edge threshold.",
                )
                db.add(edge)
                edges.append(edge)
    db.flush()
    return edges


def upsert_bridge_edge(db: Session, idea_id: str, source_id: str, target_id: str, weight: float, reason: str) -> GraphEdge:
    source_id, target_id = sorted([source_id, target_id])
    edge = (
        db.query(GraphEdge)
        .filter(GraphEdge.idea_id == idea_id)
        .filter(GraphEdge.source_node_id == source_id)
        .filter(GraphEdge.target_node_id == target_id)
        .first()
    )
    if edge:
        edge.edge_type = "BRIDGE"
        edge.weight = max(edge.weight, round(weight, 4))
        edge.reason = reason
    else:
        edge = GraphEdge(
            idea_id=idea_id,
            source_node_id=source_id,
            target_node_id=target_id,
            edge_type="BRIDGE",
            weight=round(weight, 4),
            reason=reason,
        )
        db.add(edge)
    db.flush()
    return edge

