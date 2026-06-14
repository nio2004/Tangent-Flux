from typing import Literal

from pydantic import BaseModel, Field, model_validator


ContentType = Literal["concept", "evidence", "method", "tool", "goal"]
MemoryDecision = Literal["ASSIMILATE", "ACCOMMODATE", "BRIDGE"]


class BridgeHint(BaseModel):
    concept_a: str
    concept_b: str
    reason: str


class Agent1Output(BaseModel):
    umbrella_concepts: list[str] = Field(min_length=1, max_length=8)
    per_source_summary: dict[str, str]
    keyphrase_map: dict[str, list[str]]
    content_type_map: dict[str, ContentType]
    bridge_hints: list[BridgeHint] = []
    resource_to_umbrella_map: dict[str, list[str]]

    @model_validator(mode="after")
    def validate_references(self) -> "Agent1Output":
        normalized = {concept.lower() for concept in self.umbrella_concepts}
        for hint in self.bridge_hints:
            if hint.concept_a.lower() not in normalized or hint.concept_b.lower() not in normalized:
                raise ValueError("Bridge hints must reference known umbrella concepts")
        for source_id in self.per_source_summary:
            if source_id not in self.keyphrase_map:
                raise ValueError(f"Missing keyphrase map for {source_id}")
        return self


class NodeSummary(BaseModel):
    label: str
    summary: str


class Agent2TextMemoryOutput(BaseModel):
    textual_summary: str
    node_summaries: list[NodeSummary]


class Agent3SummaryOutput(BaseModel):
    label: str | None = None
    summary: str
    reason: str


class GeneratedTask(BaseModel):
    title: str
    description: str = ""
    column: Literal["todo", "progress", "completed"] = "todo"
    points: int = 1


class Agent4GenerateOutput(BaseModel):
    kanban_tasks: list[GeneratedTask]
    timeline_entry: str | None = None
    bridge_suggestion: str | None = None


class Agent4QueryOutput(BaseModel):
    answer: str
    source_nodes: list[str] = []

