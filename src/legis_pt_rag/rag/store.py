"""Postgres + pgvector store for embedded legislation chunks."""

from __future__ import annotations

import importlib.resources as resources
from collections.abc import Iterable, Sequence

import psycopg
from pgvector.psycopg import register_vector

from legis_pt_rag.models import Chunk, RetrievedChunk


def get_connection(database_url: str) -> psycopg.Connection:
    conn = psycopg.connect(database_url)
    conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
    register_vector(conn)
    return conn


def init_schema(conn: psycopg.Connection) -> None:
    schema_sql = resources.files("legis_pt_rag.db").joinpath("schema.sql").read_text()
    with conn.cursor() as cur:
        cur.execute(schema_sql)
    conn.commit()


def upsert_chunks(
    conn: psycopg.Connection,
    chunks: Iterable[Chunk],
    embeddings: Sequence[Sequence[float]],
) -> int:
    chunks_list = list(chunks)
    if len(chunks_list) != len(embeddings):
        msg = f"chunks/embeddings length mismatch: {len(chunks_list)} vs {len(embeddings)}"
        raise ValueError(msg)

    rows = [
        (
            c.diploma,
            c.article_number,
            c.article_title,
            c.chunk_index,
            c.book,
            c.title_section,
            c.chapter,
            c.section,
            c.source_url,
            c.text,
            list(emb),
        )
        for c, emb in zip(chunks_list, embeddings, strict=True)
    ]

    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO chunks (
                diploma, article_number, article_title, chunk_index,
                book, title_section, chapter, section,
                source_url, content, embedding
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (diploma, article_number, chunk_index) DO UPDATE
            SET article_title = EXCLUDED.article_title,
                book = EXCLUDED.book,
                title_section = EXCLUDED.title_section,
                chapter = EXCLUDED.chapter,
                section = EXCLUDED.section,
                source_url = EXCLUDED.source_url,
                content = EXCLUDED.content,
                embedding = EXCLUDED.embedding,
                created_at = now()
            """,
            rows,
        )
    conn.commit()
    return len(rows)


def search(
    conn: psycopg.Connection,
    query_embedding: Sequence[float],
    *,
    top_k: int = 6,
    diploma: str | None = None,
) -> list[RetrievedChunk]:
    sql = """
        SELECT diploma, article_number, article_title, chunk_index,
               book, title_section, chapter, section,
               source_url, content,
               embedding <=> %s::vector AS distance
        FROM chunks
    """
    params: list[object] = [list(query_embedding)]
    if diploma:
        sql += " WHERE diploma = %s"
        params.append(diploma)
    sql += " ORDER BY distance ASC LIMIT %s"
    params.append(top_k)

    out: list[RetrievedChunk] = []
    with conn.cursor() as cur:
        cur.execute(sql, params)
        for row in cur.fetchall():
            chunk = Chunk(
                diploma=row[0],
                article_number=row[1],
                article_title=row[2],
                chunk_index=row[3],
                book=row[4],
                title_section=row[5],
                chapter=row[6],
                section=row[7],
                source_url=row[8],
                text=row[9],
            )
            out.append(RetrievedChunk(chunk=chunk, distance=float(row[10])))
    return out
