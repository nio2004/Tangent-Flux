from app.services.chunk_service import chunk_text
from app.services.parser_service import detect_source_type, parse_raw_text
from app.services.similarity_service import cosine_similarity, deterministic_embedding, running_mean


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

