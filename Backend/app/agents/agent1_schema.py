import re
from collections import Counter

from app.agents.prompts import AGENT_1_INSTRUCTIONS
from app.agents.sdk import run_structured_agent
from app.schemas.agent import Agent1Output, BridgeHint

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


async def run_agent1(intent: str, sources: dict[str, str]) -> Agent1Output:
    prompt = f"Intent: {intent}\nSources:\n{sources}"
    output = await run_structured_agent("Memory Schema Agent", AGENT_1_INSTRUCTIONS, prompt, Agent1Output)
    if output:
        return output
    return fallback_agent1(sources)


def fallback_agent1(sources: dict[str, str]) -> Agent1Output:
    all_text = " ".join(sources.values()).lower()
    words = [
        word
        for word in re.findall(r"[a-zA-Z][a-zA-Z\-]{2,}", all_text)
        if word not in STOPWORDS and len(word) > 3
    ]
    counts = Counter(words)
    top = [word for word, _ in counts.most_common(8)]
    concepts = _concepts_from_terms(top)
    if len(concepts) < 2:
        concepts = ["idea direction", "build context"]
    summaries = {source_id: _summary(text) for source_id, text in sources.items()}
    keyphrases = {source_id: _keyphrases(text) for source_id, text in sources.items()}
    resource_map = {source_id: concepts[: min(2, len(concepts))] for source_id in sources}
    bridge_hints = []
    if len(concepts) >= 2:
        bridge_hints.append(BridgeHint(concept_a=concepts[0], concept_b=concepts[1], reason="Top concepts co-occur in the initial dump."))
    return Agent1Output(
        umbrella_concepts=concepts[:6],
        per_source_summary=summaries,
        keyphrase_map=keyphrases,
        content_type_map={source_id: "concept" for source_id in sources},
        bridge_hints=bridge_hints,
        resource_to_umbrella_map=resource_map,
    )


def _summary(text: str) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return (sentences[0] if sentences else text[:180])[:240]


def _keyphrases(text: str) -> list[str]:
    words = [word.lower() for word in re.findall(r"[a-zA-Z][a-zA-Z\-]{3,}", text) if word.lower() not in STOPWORDS]
    return [word for word, _ in Counter(words).most_common(6)]


def _concepts_from_terms(terms: list[str]) -> list[str]:
    concepts = []
    for term in terms:
        if term not in concepts:
            concepts.append(term)
    return concepts[:6]

