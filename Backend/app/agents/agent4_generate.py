from app.agents.prompts import AGENT_4_INSTRUCTIONS
from app.agents.sdk import run_structured_agent
from app.schemas.agent import Agent4GenerateOutput, Agent4QueryOutput, GeneratedTask


async def run_agent4_query(question: str, memory: str, nodes: list[str]) -> Agent4QueryOutput:
    prompt = f"Question: {question}\nTextual memory: {memory}\nNodes: {nodes}"
    output = await run_structured_agent("Query Agent", AGENT_4_INSTRUCTIONS, prompt, Agent4QueryOutput)
    if output:
        return output
    node_text = ", ".join(nodes[:3]) or "the current memory"
    return Agent4QueryOutput(answer=f"Based on {node_text}: {memory[:500]}", source_nodes=nodes[:3])


async def run_agent4_generate(memory: str, nodes: list[str], existing_tasks: list[str]) -> Agent4GenerateOutput:
    prompt = f"Memory: {memory}\nNodes: {nodes}\nExisting tasks: {existing_tasks}"
    output = await run_structured_agent("Generation Agent", AGENT_4_INSTRUCTIONS, prompt, Agent4GenerateOutput)
    if output:
        return output
    generated = []
    for label in nodes[:3]:
        title = f"Prototype {label} workflow"
        if title not in existing_tasks:
            generated.append(GeneratedTask(title=title, description=f"Turn the {label} cluster into a testable build step."))
    return Agent4GenerateOutput(
        kanban_tasks=generated or [GeneratedTask(title="Define next build experiment", description="Convert the strongest memory cluster into an executable task.")],
        timeline_entry="Generated next build tasks from idea memory.",
        bridge_suggestion=None,
    )

