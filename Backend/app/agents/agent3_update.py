from app.agents.prompts import AGENT_3_INSTRUCTIONS
from app.agents.sdk import run_structured_agent
from app.schemas.agent import Agent3SummaryOutput


async def run_agent3_summary(decision: str, content: str, node_labels: list[str]) -> Agent3SummaryOutput:
    prompt = f"Decision: {decision}\nNode labels: {node_labels}\nNew content: {content}"
    output = await run_structured_agent("Memory Updation Agent", AGENT_3_INSTRUCTIONS, prompt, Agent3SummaryOutput)
    if output:
        return output
    label = _label_from_content(content) if decision == "ACCOMMODATE" else None
    return Agent3SummaryOutput(
        label=label,
        summary=content[:240] + ("..." if len(content) > 240 else ""),
        reason=f"Deterministic similarity routing selected {decision}.",
    )


def _label_from_content(content: str) -> str:
    words = [word.lower().strip(".,:;!?") for word in content.split() if len(word) > 4]
    return " ".join(words[:3]) or "new concept"

