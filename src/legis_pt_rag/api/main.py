"""FastAPI app exposing the RAG pipeline as HTTP endpoints."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from legis_pt_rag import __version__
from legis_pt_rag.api.routes import router
from legis_pt_rag.api.state import AppState
from legis_pt_rag.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    state = AppState.from_settings(get_settings())
    app.state.rag = state
    try:
        yield
    finally:
        state.close()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="legis-pt-rag",
        version=__version__,
        description="RAG over the Constituição da República Portuguesa.",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    app.include_router(router)
    return app


app = create_app()
