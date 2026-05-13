"""Vercel serverless entry point — wraps the FastAPI app from src/legis_pt_rag."""

from __future__ import annotations

import sys
from pathlib import Path

# Vercel ships the project root as the function's CWD but doesn't add `src/` to
# sys.path. We do it ourselves so `from legis_pt_rag...` resolves at import time.
_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from legis_pt_rag.api.main import app  # noqa: E402

__all__ = ["app"]
