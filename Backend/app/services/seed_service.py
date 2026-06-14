from sqlalchemy.orm import Session

from app.models import Artifact, Idea, IdeaNote, Task, TimelineEntry
from app.utils import dumps


SEED_IDEAS = [
    {
        "id": "context-weaver",
        "title": "Context Weaver",
        "status": "Prototype",
        "description": "A visual pipeline that turns scattered links, notes, and prompts into reusable build context.",
        "tags": ["AI", "Research", "Architecture"],
        "progress": 72,
        "activity": "hot",
        "code": "CTX",
        "importance": 5,
        "texture": "linear-gradient(135deg, rgba(22,140,255,.9), rgba(255,209,47,.42)), radial-gradient(circle at 70% 20%, rgba(255,255,255,.28), transparent 26%)",
        "problem": "Research context gets trapped in chat threads and tabs, which makes follow-up implementation slower than it should be.",
    },
    {
        "id": "research-memory-engine",
        "title": "Research Memory Engine",
        "status": "Research",
        "description": "A per-idea memory graph that decides whether new research should be assimilated, accommodated, or bridged.",
        "tags": ["AI", "Graph", "Research"],
        "progress": 35,
        "activity": "active",
        "code": "RME",
        "importance": 5,
        "texture": "linear-gradient(145deg, rgba(127,119,221,.86), rgba(29,158,117,.46)), repeating-linear-gradient(45deg, rgba(255,255,255,.14) 0 1px, transparent 1px 13px)",
        "problem": "Interesting links and research notes pile up without becoming buildable direction.",
    },
    {
        "id": "build-task-compass",
        "title": "Build Task Compass",
        "status": "Incubating",
        "description": "A tiny planning layer that turns research branches into build tasks with acceptance cues.",
        "tags": ["Tasks", "Architecture", "Pinned"],
        "progress": 54,
        "activity": "new",
        "code": "BTS",
        "importance": 4,
        "texture": "linear-gradient(145deg, rgba(22,140,255,.68), rgba(8,9,13,.92)), repeating-radial-gradient(circle at 22% 40%, rgba(255,255,255,.14) 0 1px, transparent 1px 10px)",
        "problem": "It is too easy for interesting research to stay inspirational instead of becoming testable work.",
    },
]


def seed_if_empty(db: Session) -> None:
    if db.query(Idea).count() > 0:
        return
    for item in SEED_IDEAS:
        idea = Idea(
            id=item["id"],
            title=item["title"],
            status=item["status"],
            description=item["description"],
            problem=item["problem"],
            tags_json=dumps(item["tags"]),
            progress=item["progress"],
            activity=item["activity"],
            code=item["code"],
            importance=item["importance"],
            texture=item["texture"],
        )
        db.add(idea)
        db.add(IdeaNote(idea_id=idea.id, markdown=starter_notes(item["title"])))
        db.add(Task(idea_id=idea.id, id=f"{idea.id}-task-1", title="Map evidence states", points=3, lane="todo", sort_order=1000))
        db.add(Task(idea_id=idea.id, id=f"{idea.id}-task-2", title="Prototype memory workflow", points=5, lane="progress", sort_order=1000))
        db.add(TimelineEntry(idea_id=idea.id, content="Created initial workspace from frontend seed data.", entry_type="system"))
        db.add(Artifact(idea_id=idea.id, title="Context mesh", caption="Source cards converging into a build brief.", art="mesh"))
    db.commit()


def starter_notes(title: str) -> str:
    return "\n".join(
        [
            f"# {title} research brief",
            "- **Sources:** attached and ready for review",
            "- **Assumptions:** local-first sample data for v1",
            "- Keep agent decisions visible in the workspace",
        ]
    )

