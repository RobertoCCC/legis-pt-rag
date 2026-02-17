"""Download consolidated legislation HTML from public Portuguese sources."""

from __future__ import annotations

from pathlib import Path

import httpx

USER_AGENT = "legis-pt-rag/0.1 (+https://github.com/RobertoCCC/legis-pt-rag)"

CRP_URL = "https://www.parlamento.pt/Legislacao/Paginas/ConstituicaoRepublicaPortuguesa.aspx"


def fetch_url(url: str, cache_path: Path | None = None) -> str:
    """Fetch a URL, caching the response on disk so reruns are free."""
    if cache_path is not None and cache_path.exists():
        return cache_path.read_text(encoding="utf-8")

    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        resp = client.get(url, headers={"User-Agent": USER_AGENT})
        resp.raise_for_status()
        html = resp.text

    if cache_path is not None:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(html, encoding="utf-8")

    return html


def fetch_crp(cache_dir: Path | None = None) -> str:
    cache_path = cache_dir / "crp.html" if cache_dir else None
    return fetch_url(CRP_URL, cache_path)
