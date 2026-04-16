"""HTTP routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pgvector.psycopg import register_vector
from pydantic import BaseModel, Field

from legis_pt_rag.api.state import AppState
from legis_pt_rag.models import Answer
from legis_pt_rag.rag.pipeline import RagPipeline

router = APIRouter()


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500)


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/v1/ask", response_model=Answer)
def ask(req: AskRequest, request: Request) -> Answer:
    state: AppState = request.app.state.rag
    try:
        with state.pool.connection() as conn:
            register_vector(conn)
            pipeline = RagPipeline(conn, state.embedder, state.generator, top_k=state.top_k)
            return pipeline.answer(req.question)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
