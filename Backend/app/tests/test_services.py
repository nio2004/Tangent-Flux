from app.agents.agent3_update import _label_from_content
from app.agents.agent1_schema import _map_source_to_concepts, fallback_agent1, schema_validation_issues
from app.models import Chunk
from app.services.memory_service import _assign_chunks_to_concepts, _text_label_overlap
from app.services.chunk_service import chunk_text
from app.services.parser_service import detect_source_type, parse_raw_text
from app.services.similarity_service import cosine_similarity, deterministic_embedding, running_mean
from app.utils import dumps


def test_parser_dispatch():
    assert detect_source_type("https://arxiv.org/abs/2501.00001") == "arxiv"
    assert detect_source_type("https://www.reddit.com/r/MachineLearning/comments/test") == "reddit"
    assert detect_source_type("https://example.com/post") == "webpage"
    assert detect_source_type("raw idea dump about graph memory") == "raw_text"


def test_raw_text_parser_and_chunker():
    parsed = parse_raw_text("This is a long enough raw idea dump about memory graphs and project direction.")
    assert parsed.source_type == "raw_text"
    assert parsed.clean_content.startswith("This is")
    assert chunk_text(parsed.clean_content)


def test_similarity_helpers():
    a = deterministic_embedding("grpo fine tuning resource constraints")
    b = deterministic_embedding("grpo training memory constraints")
    c = deterministic_embedding("cooking recipes and garden soil")
    assert cosine_similarity(a, b) > cosine_similarity(a, c)
    updated = running_mean(a, 1, [b])
    assert len(updated) == len(a)


def test_agent1_fallback_extracts_grounded_concepts_not_keywords():
    intent = (
        "I want a summary system that thinks like a human brain using accommodation "
        "and assimilation, with graphs of similar context for agents dealing with long context windows."
    )
    sources = {
        "paper": (
            "Coding Agents are Effective Long-Context Processors. The paper frames long-context processing "
            "as file system navigation and shows coding agents can use tools for iterative retrieval."
        ),
        "note": (
            "Don't trust large context windows. Context rot means attention drops outside the smart zone, "
            "so memory should keep compact summaries and evidence outside the live prompt."
        ),
    }

    output = fallback_agent1(sources, intent)

    assert "accommodation assimilation memory" in output.umbrella_concepts
    assert "similar-context graph" in output.umbrella_concepts
    assert "long-context memory" in output.umbrella_concepts
    assert not {"arxiv", "question", "context", "agent"} & set(output.umbrella_concepts)
    assert all(len(phrase.split()) > 1 for phrases in output.keyphrase_map.values() for phrase in phrases)


def test_agent1_fallback_only_maps_concepts_supported_by_source():
    sources = {
        "reasoning": "Scientific reasoning benchmarks need stronger evaluation loops and proof checking.",
        "fine_tune": "Fine-tune small language models with curated traces and preference data.",
    }
    output = fallback_agent1(sources, "Explore scientific reasoning core fine-tune LLMs.")

    assert not schema_validation_issues(output, sources, "Explore scientific reasoning core fine-tune LLMs.")
    assert _map_source_to_concepts(
        sources["reasoning"],
        ["scientific reasoning core fine-tune", "reasoning core fine-tune llms"],
    ) == []


def test_concept_assignment_does_not_create_empty_nodes():
    sources = {
        "c1": "Human memory uses accommodation and assimilation to update schemas from new evidence.",
        "c2": "Large context windows suffer context rot, so compact memory summaries preserve useful working context.",
        "c3": "Graph memory links related concepts and evidence so agents can recover user intent later.",
    }
    agent1 = fallback_agent1(sources, "Build human-like graph memory for long context agents.")
    concepts = [
        "accommodation assimilation memory",
        "context window limits",
        "similar-context graph",
    ]
    agent1.umbrella_concepts = concepts
    agent1.resource_to_umbrella_map = {
        "c1": ["accommodation assimilation memory"],
        "c2": ["context window limits"],
        "c3": ["similar-context graph"],
    }
    chunks = [
        Chunk(id=source_id, text=text, embedding_json=dumps(deterministic_embedding(text)))
        for source_id, text in sources.items()
    ]
    concept_embeddings = {concept: deterministic_embedding(concept) for concept in concepts}

    assignments = _assign_chunks_to_concepts(agent1, chunks, concept_embeddings)

    assert set(assignments) == set(concepts)
    assert all(assignments[concept] for concept in concepts)
    assert {chunk.id for chunk in assignments["accommodation assimilation memory"]} == {"c1"}
    assert {chunk.id for chunk in assignments["context window limits"]} == {"c2"}
    assert {chunk.id for chunk in assignments["similar-context graph"]} == {"c3"}


def test_agent3_new_concept_label_and_overlap_gate():
    content = (
        "Vector databases can store episodic memory with hybrid retrieval, metadata filters, "
        "and reranking so agents can recover relevant user context."
    )

    assert _label_from_content(content) == "vector databases can store"
    assert _text_label_overlap(content, "context window limits") < 0.25
    assert _text_label_overlap(content, "hybrid retrieval memory") >= 0.25

