"""Shared app state: DB connection pool + Gemini-backed RAG pipeline."""

from __future__ import annotations

from dataclasses import dataclass

from psycopg_pool import ConnectionPool

from legis_pt_rag.config import Settings
from legis_pt_rag.rag.embeddings import Embedder
from legis_pt_rag.rag.llm import Generator


@dataclass
class AppState:
    pool: ConnectionPool
    embedder: Embedder
    generator: Generator
    top_k: int

    @classmethod
    def from_settings(cls, settings: Settings) -> AppState:
        from google import genai

        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY env var is required.")
        client = genai.Client(api_key=settings.gemini_api_key)
        pool = ConnectionPool(settings.database_url, min_size=1, max_size=4, open=True)
        return cls(
            pool=pool,
            embedder=Embedder(
                client, model=settings.embedding_model, output_dim=settings.embedding_dim
            ),
            generator=Generator(client, model=settings.generation_model),
            top_k=settings.top_k,
        )

    def close(self) -> None:
        self.pool.close()
