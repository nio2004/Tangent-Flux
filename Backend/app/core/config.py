from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./tangent_flux.db"
    openai_api_key: str | None = None
    openai_agent_model: str = "gpt-5-nano"
    openai_idea_generation_model: str = "gpt-5.5"
    openai_vision_model: str = "gpt-4.1-mini"
    openai_web_search_model: str = "gpt-4.1-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    frontend_origin: str = "http://localhost:5173"
    use_openai_agents: bool = True
    openai_enable_web_search: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
