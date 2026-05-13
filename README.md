# legis-pt-rag

RAG (Retrieval-Augmented Generation) over consolidated Portuguese legislation.
Starts with the **Constitution of the Portuguese Republic** (296 articles, source: parlamento.pt),
and is designed to grow to other statutes (Labour Code, Civil Code, etc.).

100% free stack: **Neon** (Postgres + pgvector) · **Google Gemini** (embeddings + generation) · **FastAPI** · **Vercel** (deploy).

🌐 **Live API:** https://legis-pt-rag-8p6s.vercel.app

```bash
curl -X POST https://legis-pt-rag-8p6s.vercel.app/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "O que diz a Constituição sobre liberdade de expressão?"}'
```

> ⚠️ This project is educational. Generated answers **do not constitute legal advice**. Always consult a lawyer for real matters.

## How it works

```
┌──────────┐   ┌─────────────┐   ┌─────────────────┐   ┌──────────────────┐
│ question │ → │  embed      │ → │ pgvector top-K  │ → │ Gemini grounded  │
│ (PT)     │   │ (Gemini)    │   │ (cosine)        │   │ generation + cite│
└──────────┘   └─────────────┘   └─────────────────┘   └──────────────────┘
```

1. **Ingestion**: fetches the CRP, splits into articles (preserving the PARTE/TÍTULO/CAPÍTULO/SECÇÃO hierarchy), then chunks by numbered paragraph.
2. **Embeddings**: each chunk is embedded with `gemini-embedding-001` truncated to 768 dims (Matryoshka).
3. **Storage**: chunks + embeddings live in Postgres with an HNSW index (pgvector).
4. **Answering**: the question is embedded, top-K is retrieved by cosine distance, and Gemini generates a grounded answer with article citations.

Note: questions and answers stay in **European Portuguese** — that's the source language of the corpus and the target audience.

## Local setup

Requires **Python 3.12+** and [uv](https://docs.astral.sh/uv/).

```bash
uv sync --all-extras --dev
cp .env.example .env
# fill in DATABASE_URL (Neon) and GEMINI_API_KEY
```

### Credentials

- **Neon**: create an account at [neon.tech](https://neon.tech) (free tier never expires). Copy the connection string into `DATABASE_URL`.
- **Gemini**: get an API key at [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey). Free tier: 1500 req/day.

### Ingest

```bash
uv run legis-pt init       # create pgvector schema
uv run legis-pt ingest     # fetch + parse + chunk + embed + upsert (~5 min)
```

### Ask via CLI

```bash
uv run legis-pt ask "Quais são os direitos fundamentais?"
```

### Serve the API

```bash
uv run uvicorn legis_pt_rag.api.main:app --reload
```

`POST /v1/ask` with body `{"question": "..."}` returns an `Answer` with text + citations.

## Tests

```bash
uv run pytest -v          # 7 tests (parser + chunker)
uv run ruff check .       # lint
uv run ruff format .      # format
uv run mypy src           # type-check
```

## Layout

```
src/legis_pt_rag/
├── ingest/         # fetcher + parser (HTML → Article) + chunker
├── rag/            # embeddings, store (pgvector), llm (Gemini), pipeline
├── db/schema.sql   # CREATE TABLE chunks + HNSW index
├── api/            # FastAPI app + routes
├── cli.py          # typer commands (init, ingest, ask)
├── config.py       # pydantic-settings (.env)
└── models.py       # pydantic models
```

## Roadmap

- [x] Full CRP (296 articles)
- [ ] Labour Code (Código do Trabalho)
- [ ] Civil Code (Código Civil)
- [ ] Version history (track constitutional revisions)
- [ ] Next.js chat frontend

## License

MIT — see [LICENSE](LICENSE).
