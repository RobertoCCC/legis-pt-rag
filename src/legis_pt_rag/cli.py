"""CLI entrypoints for ingestion and one-off queries."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import typer

from legis_pt_rag.config import get_settings
from legis_pt_rag.ingest.chunker import chunk_articles
from legis_pt_rag.ingest.fetcher import CRP_URL, fetch_crp
from legis_pt_rag.ingest.parser import parse_crp
from legis_pt_rag.rag.embeddings import Embedder
from legis_pt_rag.rag.llm import Generator
from legis_pt_rag.rag.pipeline import RagPipeline
from legis_pt_rag.rag.store import get_connection, init_schema, upsert_chunks

if TYPE_CHECKING:
    from google.genai import Client

app = typer.Typer(help="legis-pt-rag — RAG over Portuguese consolidated legislation.")

_DEFAULT_CACHE_DIR = Path("data/cache")


def _genai_client() -> Client:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise typer.BadParameter(
            "GEMINI_API_KEY is not set. Get a free key at https://aistudio.google.com/app/apikey."
        )
    from google import genai

    return genai.Client(api_key=settings.gemini_api_key)


@app.command()
def init() -> None:
    """Create the pgvector schema in the configured database."""
    settings = get_settings()
    with get_connection(settings.database_url) as conn:
        init_schema(conn)
    typer.echo("Schema applied.")


@app.command()
def ingest(
    cache_dir: Path = typer.Option(_DEFAULT_CACHE_DIR, help="Where to cache the fetched HTML."),
) -> None:
    """Fetch the CRP, chunk it, embed via Gemini, and upsert into Postgres."""
    settings = get_settings()
    typer.echo(f"Fetching CRP from {CRP_URL} …")
    html = fetch_crp(cache_dir=cache_dir)

    typer.echo("Parsing articles …")
    articles = parse_crp(html, source_url=CRP_URL)
    typer.echo(f"  {len(articles)} articles")

    typer.echo("Chunking …")
    chunks = chunk_articles(articles)
    typer.echo(f"  {len(chunks)} chunks")

    typer.echo(f"Embedding via Gemini (≈{len(chunks) * 0.7:.0f}s) …")
    client = _genai_client()
    embedder = Embedder(client, model=settings.embedding_model, output_dim=settings.embedding_dim)
    embeddings: list[list[float]] = []
    with typer.progressbar(chunks, label="Embedding") as bar:
        for chunk in bar:
            embeddings.append(embedder.embed_document(chunk.text))

    typer.echo("Writing to Postgres …")
    with get_connection(settings.database_url) as conn:
        init_schema(conn)
        written = upsert_chunks(conn, chunks, embeddings)
    typer.echo(f"  upserted {written} chunks ✔")


@app.command()
def ask(question: str) -> None:
    """Ask the RAG pipeline a question from the CLI."""
    settings = get_settings()
    client = _genai_client()
    embedder = Embedder(client, model=settings.embedding_model, output_dim=settings.embedding_dim)
    generator = Generator(client, model=settings.generation_model)
    with get_connection(settings.database_url) as conn:
        pipeline = RagPipeline(conn, embedder, generator, top_k=settings.top_k)
        answer = pipeline.answer(question)
    typer.echo(answer.answer)
    typer.echo("\nFontes:")
    for c in answer.citations:
        typer.echo(f"  - Art. {c.article_number}.º — {c.diploma}")


if __name__ == "__main__":
    app()
