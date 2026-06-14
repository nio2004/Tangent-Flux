import re
from collections import Counter

from app.agents.prompts import AGENT_1_INSTRUCTIONS
from app.agents.sdk import run_structured_agent
from app.schemas.agent import Agent1Output, BridgeHint

STOPWORDS = {
    "abstract",
    "about",
    "after",
    "also",
    "and",
    "are",
    "back",
    "because",
    "between",
    "below",
    "browser",
    "click",
    "code",
    "color",
    "create",
    "dealing",
    "download",
    "figure",
    "few",
    "first",
    "for",
    "from",
    "have",
    "html",
    "ideas",
    "initial",
    "into",
    "issue",
    "paper",
    "pdf",
    "preprint",
    "report",
    "scheme",
    "section",
    "captured",
    "source",
    "submit",
    "table",
    "that",
    "the",
    "this",
    "want",
    "with",
    "working",
    "would",
    "your",
}

GENERIC_CONCEPTS = {
    "agent",
    "agents",
    "archive",
    "arxiv",
    "coding",
    "context",
    "file",
    "github",
    "html",
    "llm",
    "model",
    "paper",
    "question",
    "captured",
    "source",
    "text",
    "user",
    "window",
}

METADATA_WORDS = {
    "abstract",
    "archive",
    "arxiv",
    "browser",
    "download",
    "github",
    "html",
    "issue",
    "pdf",
    "preprint",
    "report",
    "submit",
}


async def run_agent1(intent: str, sources: dict[str, str]) -> Agent1Output:
    prompt = f"Intent: {intent}\nSources:\n{sources}"
    output = await run_structured_agent("Memory Schema Agent", AGENT_1_INSTRUCTIONS, prompt, Agent1Output)
    if output and _is_high_quality_output(output):
        return output
    return fallback_agent1(sources, intent)


def fallback_agent1(sources: dict[str, str], intent: str = "") -> Agent1Output:
    weighted_text = " ".join([intent, intent, intent, *sources.values()]).lower()
    ranked_phrases = [*_rank_phrases(intent, boost=3.0), *_rank_phrases(weighted_text)]
    concepts = _concepts_from_terms(ranked_phrases)
    if len(concepts) < 2:
        concepts = ["idea direction", "source evidence"]
    summaries = {source_id: _summary(text) for source_id, text in sources.items()}
    keyphrases = {source_id: _keyphrases(text) for source_id, text in sources.items()}
    resource_map = {source_id: _map_source_to_concepts(text, concepts) for source_id, text in sources.items()}
    bridge_hints = []
    if len(concepts) >= 2:
        bridge_hints.append(
            BridgeHint(
                concept_a=concepts[0],
                concept_b=concepts[1],
                reason="These grounded concepts co-occur across the idea/source material and can inform the same memory graph.",
            )
        )
    return Agent1Output(
        umbrella_concepts=concepts[:6],
        per_source_summary=summaries,
        keyphrase_map=keyphrases,
        content_type_map={source_id: "concept" for source_id in sources},
        bridge_hints=bridge_hints,
        resource_to_umbrella_map=resource_map,
    )


def _is_high_quality_output(output: Agent1Output) -> bool:
    concepts = [_normalize_phrase(concept) for concept in output.umbrella_concepts]
    if len(set(concepts)) < len(concepts):
        return False
    vague = sum(1 for concept in concepts if _is_vague_concept(concept))
    return vague <= max(1, len(concepts) // 3)


def _summary(text: str) -> str:
    sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", _clean_text(text))
        if len(sentence.split()) >= 6 and not _looks_like_page_chrome(sentence)
    ]
    return (sentences[0] if sentences else _clean_text(text)[:180])[:240]


def _keyphrases(text: str) -> list[str]:
    return _rank_phrases(text)[:6]


def _concepts_from_terms(terms: list[str]) -> list[str]:
    concepts = []
    for term in terms:
        normalized = _normalize_phrase(term)
        if normalized and normalized not in concepts and not _is_vague_concept(normalized):
            concepts.append(normalized)
    return concepts[:6]


def _rank_phrases(text: str, boost: float = 1.0) -> list[str]:
    return _rank_phrase_counts(text, boost).most_common_phrases


class _RankedPhrases(Counter[str]):
    @property
    def most_common_phrases(self) -> list[str]:
        return [phrase for phrase, _ in self.most_common(24)]


def _rank_phrase_counts(text: str, boost: float = 1.0) -> _RankedPhrases:
    counts: Counter[str] = Counter()
    for sentence in re.split(r"(?<=[.!?])\s+|\n+", _clean_text(text).lower()):
        if _looks_like_page_chrome(sentence):
            continue
        tokens = [
            token
            for token in re.findall(r"[a-z][a-z0-9\-]{2,}", sentence)
            if token not in STOPWORDS and not token.isdigit()
        ]
        tokens = [_canonical_token(token) for token in tokens]
        for size in (4, 3, 2):
            for index in range(0, len(tokens) - size + 1):
                phrase = _normalize_phrase(" ".join(tokens[index : index + size]))
                if phrase and not _is_vague_concept(phrase):
                    counts[phrase] += _phrase_score(phrase) * boost
    ranked = _RankedPhrases()
    ranked.update(counts)
    return ranked


def _phrase_score(phrase: str) -> float:
    tokens = phrase.split()
    score = 1.0 + (0.35 * len(tokens))
    if any("-" in token for token in tokens):
        score += 0.4
    if any(token in {"memory", "reasoning", "retrieval", "graph", "long-context", "context", "assimilation", "accommodation"} for token in tokens):
        score += 0.8
    return score


def _map_source_to_concepts(text: str, concepts: list[str]) -> list[str]:
    normalized = _clean_text(text).lower()
    matches = [concept for concept in concepts if any(token in normalized for token in concept.split())]
    return matches[:3] or concepts[:1]


def _normalize_phrase(value: str) -> str:
    phrase = value.lower().replace("accomodation", "accommodation")
    phrase = re.sub(r"[^a-zA-Z0-9\-\s]", " ", phrase)
    phrase = re.sub(r"\s+", " ", phrase).strip()
    words = [word for word in phrase.split() if word not in STOPWORDS]
    return _canonical_phrase(" ".join(words[:5]))


def _canonical_phrase(phrase: str) -> str:
    words = set(phrase.split())
    if {"accommodation", "assimilation"} <= words:
        return "accommodation assimilation memory"
    if "summary" in words and "system" in words:
        return "summary memory system"
    if "brain" in words and ("human" in words or "memory" in words or "concept" in words):
        return "human-like memory"
    if "similar" in words and "context" in words and ("graph" in words or "agent" in words):
        return "similar-context graph"
    if "long-context" in words and "processing" in words:
        return "long-context processing"
    if "long-context" in words and ("processors" in words or "processor" in words):
        return "coding agents for long-context"
    if "coding" in words and ("agents" in words or "agent" in words):
        return "coding agents for long-context"
    if "file" in words and "system" in words:
        return "file-system navigation"
    if "context" in words and "window" in words:
        return "context window limits"
    if "retrieval" in words and ("context" in words or "search" in words):
        return "retrieval strategies"
    if "long" in words and "context" in words:
        return "long-context memory"
    return phrase


def _canonical_token(token: str) -> str:
    replacements = {
        "graphs": "graph",
        "windows": "window",
        "summaries": "summary",
    }
    return replacements.get(token, token)


def _is_vague_concept(concept: str) -> bool:
    words = concept.split()
    if not words:
        return True
    if len(words) == 1 and words[0] in GENERIC_CONCEPTS:
        return True
    if any(word in METADATA_WORDS for word in words):
        return True
    return False


def _clean_text(text: str) -> str:
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"//.*?(?=\s|$)", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _looks_like_page_chrome(text: str) -> bool:
    lowered = text.lower()
    chrome_terms = [
        "back to arxiv",
        "data-theme",
        "document.documentelement",
        "localstorage",
        "readingmode",
        "restore the saved color scheme",
        "submit without github",
        "toc display",
        "why html",
    ]
    return any(term in lowered for term in chrome_terms)

