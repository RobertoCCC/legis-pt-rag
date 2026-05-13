"""Vercel serverless entry point — wraps the FastAPI app from src/legis_pt_rag.

Vercel's FastAPI preset auto-detects `main.py` at the project root and exposes
the `app` it finds there. We keep the real package under `src/` for a clean
src-layout, and patch `sys.path` here so the import resolves.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from legis_pt_rag.api.main import app  # noqa: E402

__all__ = ["app"]
