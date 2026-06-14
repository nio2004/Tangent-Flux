from sqlalchemy.orm import Session

from app.models import GraphEdge, GraphNode
from app.services.similarity_service import cosine_similarity
from app.utils import loads


def get_graph(db: Session, idea_id: str) -> tuple[list[GraphNode], list[GraphEdge]]:
    nodes = db.query(GraphNode).filter(GraphNode.idea_id == idea_id).all()
    edges = db.query(GraphEdge).filter(GraphEdge.idea_id == idea_id).all()
    return nodes, edges


<<<<<<< HEAD
def create_similarity_edges(db: Session, idea_id: str, nodes: list[GraphNode], threshold: float = 0.55) -> list[GraphEdge]:
=======
def create_similarity_edges(db: Session, idea_id: str, nodes: list[GraphNode], threshold: float = 0.68) -> list[GraphEdge]:
>>>>>>> 6f1c767a5b6ce400673ed3b3987875468dd9fa04
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
<<<<<<< HEAD
            if score >= threshold:
=======
            shared = _shared_source_ids(source, target)
            lexical_overlap = _label_overlap(source.label, target.label)
            if score >= threshold or (score >= 0.55 and (shared or lexical_overlap >= 0.34)):
                reason_parts = [f"Centroid similarity {score:.2f}."]
                if shared:
                    reason_parts.append(f"Shared {len(shared)} evidence chunk(s).")
                if lexical_overlap:
                    reason_parts.append(f"Label overlap {lexical_overlap:.2f}.")
>>>>>>> 6f1c767a5b6ce400673ed3b3987875468dd9fa04
                edge = GraphEdge(
                    idea_id=idea_id,
                    source_node_id=source.id,
                    target_node_id=target.id,
                    edge_type="SIMILARITY",
                    weight=round(score, 4),
<<<<<<< HEAD
                    reason="Centroid similarity crossed graph edge threshold.",
=======
                    reason=" ".join(reason_parts),
>>>>>>> 6f1c767a5b6ce400673ed3b3987875468dd9fa04
                )
                db.add(edge)
                edges.append(edge)
    db.flush()
    return edges


<<<<<<< HEAD
=======
def _shared_source_ids(source: GraphNode, target: GraphNode) -> set[str]:
    return set(loads(source.source_chunk_ids_json, [])) & set(loads(target.source_chunk_ids_json, []))


def _label_overlap(source: str, target: str) -> float:
    source_terms = {term for term in source.lower().replace("-", " ").split() if len(term) > 3}
    target_terms = {term for term in target.lower().replace("-", " ").split() if len(term) > 3}
    if not source_terms or not target_terms:
        return 0.0
    return len(source_terms & target_terms) / len(source_terms | target_terms)


>>>>>>> 6f1c767a5b6ce400673ed3b3987875468dd9fa04
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

