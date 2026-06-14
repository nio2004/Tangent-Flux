import re
from collections import Counter

from app.agents.prompts import AGENT_3_INSTRUCTIONS
from app.agents.sdk import run_structured_agent
from app.schemas.agent import Agent3SummaryOutput

STOPWORDS = {
    "about",
    "after",
    "also",
    "and",
    "are",
    "because",
    "between",
    "from",
    "have",
    "into",
    "that",
    "the",
    "this",
    "with",
    "would",
    "your",
}


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
    phrases = Counter()
    for sentence in re.split(r"(?<=[.!?])\s+|\n+", content.lower()):
        tokens = [
            token
            for token in re.findall(r"[a-z][a-z0-9\-]{2,}", sentence)
            if token not in STOPWORDS and not token.isdigit()
        ]
        for size in (4, 3, 2):
            for index in range(0, len(tokens) - size + 1):
                phrase = " ".join(tokens[index : index + size])
                if not _is_generic_phrase(phrase):
                    phrases[phrase] += 1 + (0.25 * size)
    if phrases:
        return phrases.most_common(1)[0][0]
    words = [word.lower().strip(".,:;!?") for word in content.split() if len(word) > 4 and word.lower() not in STOPWORDS]
    return " ".join(words[:3]) or "new concept"


def _is_generic_phrase(phrase: str) -> bool:
    generic = {"content", "article", "source", "thing", "stuff", "notes", "update"}
    words = set(phrase.split())
    return bool(words & generic) or len(words) < 2

