"""End-to-end RAG: embed query, retrieve top-k, generate grounded answer."""

from __future__ import annotations

from collections.abc import Iterable

import psycopg

from legis_pt_rag.models import Answer, Citation, RetrievedChunk
from legis_pt_rag.rag.embeddings import Embedder
from legis_pt_rag.rag.llm import Generator
from legis_pt_rag.rag.store import search


class RagPipeline:
    def __init__(
        self,
        conn: psycopg.Connection,
        embedder: Embedder,
        generator: Generator,
        *,
        top_k: int = 6,
    ) -> None:
        self._conn = conn
        self._embedder = embedder
        self._generator = generator
        self._top_k = top_k

    def answer(self, question: str) -> Answer:
        query_emb = self._embedder.embed_query(question)
        retrieved = search(self._conn, query_emb, top_k=self._top_k)
        context = _format_context(retrieved)
        text = self._generator.generate(question, context)
        return Answer(
            question=question,
            answer=text,
            citations=_unique_citations(retrieved),
            model=self._generator.model,
        )


def _format_context(retrieved: Iterable[RetrievedChunk]) -> str:
    blocks = []
    for r in retrieved:
        c = r.chunk
        blocks.append(f"[Art. {c.article_number}.º] {c.text}")
    return "\n\n---\n\n".join(blocks)


def _unique_citations(retrieved: Iterable[RetrievedChunk]) -> list[Citation]:
    seen: set[tuple[str, str]] = set()
    out: list[Citation] = []
    for r in retrieved:
        c = r.chunk
        key = (c.diploma, c.article_number)
        if key in seen:
            continue
        seen.add(key)
        out.append(
            Citation(
                article_number=c.article_number,
                article_title=c.article_title,
                diploma=c.diploma,
                source_url=c.source_url,
            )
        )
    return out
