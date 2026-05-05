# legis-pt-rag

RAG (Retrieval-Augmented Generation) sobre legislação portuguesa consolidada.
Começa pela **Constituição da República Portuguesa** (296 artigos, fonte: parlamento.pt),
e é desenhado para crescer para outros diplomas (Código do Trabalho, Código Civil, etc.).

Stack 100% gratuita: **Neon** (Postgres + pgvector) · **Google Gemini** (embeddings + geração) · **FastAPI** · **Render** (deploy).

> ⚠️ Este projeto é educativo. As respostas geradas **não constituem aconselhamento jurídico**. Consulte sempre um advogado para questões reais.

## Como funciona

```
┌──────────┐   ┌─────────────┐   ┌─────────────────┐   ┌──────────────────┐
│ pergunta │ → │  embed      │ → │ pgvector top-K  │ → │ Gemini grounded  │
│ (PT)     │   │ (Gemini)    │   │ (cosine)        │   │ generation + cite│
└──────────┘   └─────────────┘   └─────────────────┘   └──────────────────┘
```

1. **Ingestão**: faz fetch da CRP, parte em artigos (com hierarquia PARTE/TÍTULO/CAPÍTULO/SECÇÃO), faz chunking por parágrafo numerado.
2. **Embeddings**: cada chunk é embebido com `gemini-embedding-001` truncado a 768 dims (Matryoshka).
3. **Armazenamento**: chunks + embeddings em Postgres com índice HNSW (pgvector).
4. **Resposta**: a pergunta é embebida, faz-se top-K por cosine distance, e o Gemini gera uma resposta fundamentada com citações aos artigos.

## Setup local

Requer **Python 3.12+** e [uv](https://docs.astral.sh/uv/).

```bash
uv sync --all-extras --dev
cp .env.example .env
# preencher DATABASE_URL (Neon) e GEMINI_API_KEY
```

### Credenciais

- **Neon**: cria uma conta em [neon.tech](https://neon.tech) (tier gratuito não expira). Copia a connection string para `DATABASE_URL`.
- **Gemini**: obtém uma API key em [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey). Tier gratuito: 1500 req/dia.

### Ingestão

```bash
uv run legis-pt init       # cria schema pgvector
uv run legis-pt ingest     # fetch + parse + chunk + embed + upsert (~5 min)
```

### Perguntar via CLI

```bash
uv run legis-pt ask "Quais são os direitos fundamentais?"
```

### Servir a API

```bash
uv run uvicorn legis_pt_rag.api.main:app --reload
```

`POST /v1/ask` com body `{"question": "..."}` devolve `Answer` com texto + citações.

## Testes

```bash
uv run pytest -v          # 7 testes (parser + chunker)
uv run ruff check .       # lint
uv run ruff format .      # format
uv run mypy src           # type-check
```

## Estrutura

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

- [x] CRP completa (296 artigos)
- [ ] Código do Trabalho
- [ ] Código Civil
- [ ] Histórico de versões (acompanhar revisões constitucionais)
- [ ] Frontend Next.js com chat

## Licença

MIT — ver [LICENSE](LICENSE).
