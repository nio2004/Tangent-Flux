from app.core.config import get_settings
from app.services.similarity_service import deterministic_embedding
import os


class EmbeddingService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._client = None

    def embed(self, text: str) -> list[float]:
        if not self.settings.openai_api_key:
            return deterministic_embedding(text)
        try:
            from openai import OpenAI

            if self._client is None:
                os.environ.setdefault("OPENAI_API_KEY", self.settings.openai_api_key)
                self._client = OpenAI(api_key=self.settings.openai_api_key)
            result = self._client.embeddings.create(model=self.settings.openai_embedding_model, input=text[:8000])
            return list(result.data[0].embedding)
        except Exception:
            return deterministic_embedding(text)

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(text) for text in texts]


embedding_service = EmbeddingService()
