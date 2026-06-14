from app.agents.prompts import AGENT_2_INSTRUCTIONS
from app.agents.sdk import run_structured_agent
from app.schemas.agent import Agent2TextMemoryOutput, NodeSummary


async def run_agent2_text_memory(intent: str, concept_chunks: dict[str, list[str]]) -> Agent2TextMemoryOutput:
    prompt = f"Intent: {intent}\nConcept chunks:\n{concept_chunks}"
    output = await run_structured_agent("Memory Generation Agent", AGENT_2_INSTRUCTIONS, prompt, Agent2TextMemoryOutput)
    if output:
        return output
    node_summaries = [
        NodeSummary(label=label, summary=_summarize_chunks(label, chunks)) for label, chunks in concept_chunks.items()
    ]
    textual = " ".join(f"{item.label}: {item.summary}" for item in node_summaries)
    return Agent2TextMemoryOutput(textual_summary=textual, node_summaries=node_summaries)


def _summarize_chunks(label: str, chunks: list[str]) -> str:
    joined = " ".join(chunks)
    if not joined:
        return f"{label} is present in the initial idea memory."
    return joined[:260] + ("..." if len(joined) > 260 else "")

