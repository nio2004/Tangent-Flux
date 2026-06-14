import hashlib
import math


def deterministic_embedding(text: str, dimensions: int = 64) -> list[float]:
    vector = [0.0] * dimensions
    words = [word.strip(".,:;!?()[]{}<>\"'").lower() for word in text.split()]
    for word in words:
        if not word:
            continue
        digest = hashlib.sha256(word.encode("utf-8")).digest()
        index = int.from_bytes(digest[:2], "big") % dimensions
        sign = 1.0 if digest[2] % 2 == 0 else -1.0
        vector[index] += sign
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    limit = min(len(a), len(b))
    dot = sum(a[index] * b[index] for index in range(limit))
    norm_a = math.sqrt(sum(value * value for value in a[:limit]))
    norm_b = math.sqrt(sum(value * value for value in b[:limit]))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def mean_embedding(vectors: list[list[float]]) -> list[float]:
    if not vectors:
        return []
    dimensions = len(vectors[0])
    return [sum(vector[index] for vector in vectors) / len(vectors) for index in range(dimensions)]


def running_mean(old: list[float], old_count: int, new_vectors: list[list[float]]) -> list[float]:
    if not old:
        return mean_embedding(new_vectors)
    if not new_vectors:
        return old
    new_mean = mean_embedding(new_vectors)
    total = old_count + len(new_vectors)
    return [
        ((old[index] * old_count) + (new_mean[index] * len(new_vectors))) / total
        for index in range(min(len(old), len(new_mean)))
    ]

