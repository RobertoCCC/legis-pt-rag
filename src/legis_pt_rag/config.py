from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = Field(
        default="postgresql://localhost:5432/legis_pt_rag",
        description="Postgres connection string (with pgvector extension installed).",
    )
    gemini_api_key: str = Field(
        default="",
        description="Google AI Studio API key for Gemini (free tier).",
    )
    embedding_model: str = Field(default="gemini-embedding-001")
    generation_model: str = Field(default="gemini-2.5-flash")
    embedding_dim: int = Field(default=768)
    top_k: int = Field(default=6, description="Number of chunks to retrieve per query.")

    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000"],
        description="Allowed CORS origins for the web frontend.",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
