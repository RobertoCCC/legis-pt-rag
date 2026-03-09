"""Embedding client using Google's free Gemini embedding API."""

from __future__ import annotations

import time
from collections.abc import Iterable
from typing import TYPE_CHECKING

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

if TYPE_CHECKING:
    from google.genai import Client

QUERY_TASK = "RETRIEVAL_QUERY"
DOCUMENT_TASK = "RETRIEVAL_DOCUMENT"


class Embedder:
    """Thin wrapper around `google-genai` embed_content.

    The free tier of ``gemini-embedding-001`` counts every item in the
    ``contents`` list as one request against the 100 RPM quota, so we send one
    text per call and pace ourselves with a small sleep between calls.

    ``output_dim`` truncates Gemini's 3072-d embeddings via Matryoshka
    representation learning — preserves quality while staying under pgvector's
    HNSW 2000-dim ceiling.
    """

    def __init__(
        self,
        client: Client,
        *,
        model: str = "gemini-embedding-001",
        output_dim: int = 768,
        min_interval_seconds: float = 0.65,
    ) -> None:
        self._client = client
        self._model = model
        self._output_dim = output_dim
        self._min_interval = min_interval_seconds
        self._last_call_ts: float = 0.0

    def embed_documents(self, texts: Iterable[str]) -> list[list[float]]:
        return [self.embed_document(text) for text in texts]

    def embed_document(self, text: str) -> list[float]:
        self._throttle()
        return self._call_api(text, DOCUMENT_TASK)

    def embed_query(self, text: str) -> list[float]:
        self._throttle()
        return self._call_api(text, QUERY_TASK)

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_call_ts
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_call_ts = time.monotonic()

    @retry(
        stop=stop_after_attempt(6),
        wait=wait_exponential(multiplier=2, min=4, max=60),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    def _call_api(self, text: str, task: str) -> list[float]:
        from google.genai import types

        config = types.EmbedContentConfig(
            task_type=task,
            output_dimensionality=self._output_dim,
        )
        resp = self._client.models.embed_content(
            model=self._model,
            contents=text,
            config=config,
        )
        embeddings = resp.embeddings or []
        if not embeddings:
            raise RuntimeError("Gemini returned no embeddings.")
        return list(embeddings[0].values or [])
