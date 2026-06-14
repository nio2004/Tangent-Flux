import re


def rough_token_count(text: str) -> int:
    return max(1, len(text.split()))


def chunk_text(text: str, target_words: int = 120, max_words: int = 220) -> list[str]:
    paragraphs = [part.strip() for part in re.split(r"\n{2,}|(?<=[.!?])\s+", text) if part.strip()]
    chunks: list[str] = []
    current: list[str] = []
    count = 0
    for paragraph in paragraphs:
        words = paragraph.split()
        if count + len(words) > max_words and current:
            chunks.append(" ".join(current))
            current = []
            count = 0
        current.append(paragraph)
        count += len(words)
        if count >= target_words:
            chunks.append(" ".join(current))
            current = []
            count = 0
    if current:
        chunks.append(" ".join(current))
    return chunks or [text]

