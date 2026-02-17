"""Parse the consolidated Constituição da República Portuguesa HTML into Articles."""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass

from bs4 import BeautifulSoup, Tag

from legis_pt_rag.models import Article

_ARTICLE_NUM_RE = re.compile(
    r"^\s*Artigo\s+(\d+)\s*\.?\s*º?\s*(?:-\s*([A-Z]))?(?:\s+(.+?))?\s*$",
    re.IGNORECASE,
)
_PARTE_RE = re.compile(r"^\s*PARTE\s+([IVXLCDM]+)\b", re.IGNORECASE)
_TITULO_RE = re.compile(r"^\s*T[ÍI]TULO\s+([IVXLCDM]+)\b", re.IGNORECASE)
_CAPITULO_RE = re.compile(r"^\s*CAP[ÍI]TULO\s+([IVXLCDM]+)\b", re.IGNORECASE)
_SECCAO_RE = re.compile(r"^\s*SEC[ÇC][ÃA]O\s+([IVXLCDM]+)\b", re.IGNORECASE)


@dataclass
class _Context:
    part: str | None = None
    title_section: str | None = None
    chapter: str | None = None
    section: str | None = None


def parse_crp(html: str, *, source_url: str) -> list[Article]:
    """Parse parlamento.pt CRP page into a list of Article models.

    The page lays out each article as a sequence of paragraphs::

        <p>Artigo 13.º</p>
        <p>Princípio da igualdade</p>
        <p>1. Todos os cidadãos têm a mesma dignidade social ...</p>
        <p>2. Ninguém pode ser ...</p>

    Hierarchy markers (PARTE, TÍTULO, CAPÍTULO, SECÇÃO) appear as their own
    paragraphs, often followed by a heading paragraph.
    """
    soup = BeautifulSoup(html, "html.parser")
    paragraphs = _content_paragraphs(soup)
    return list(_iter_articles(paragraphs, source_url=source_url))


def _content_paragraphs(soup: BeautifulSoup) -> list[Tag]:
    """Return paragraphs that contain real article text (skip nav/sidebars)."""
    keep: list[Tag] = []
    seen_first_article = False
    for p in soup.find_all("p"):
        text = p.get_text(" ", strip=True)
        if not text:
            continue
        if not seen_first_article and not _ARTICLE_NUM_RE.match(text):
            if "Artigo 1.º" in text:
                seen_first_article = True
            else:
                continue
        seen_first_article = True
        keep.append(p)
    return keep


def _iter_articles(paragraphs: list[Tag], *, source_url: str) -> Iterator[Article]:
    context = _Context()
    i = 0
    while i < len(paragraphs):
        text = paragraphs[i].get_text(" ", strip=True)
        m = _ARTICLE_NUM_RE.match(text)
        if not m:
            _maybe_update_context(context, text)
            i += 1
            continue

        number = _format_number(m.group(1), m.group(2))
        inline_title = (m.group(3) or "").strip()
        title = inline_title
        body_lines: list[str] = []

        if not inline_title and i + 1 < len(paragraphs):
            i += 1
            title = paragraphs[i].get_text(" ", strip=True)

        i += 1
        while i < len(paragraphs):
            next_text = paragraphs[i].get_text(" ", strip=True)
            if _ARTICLE_NUM_RE.match(next_text):
                break
            if _is_hierarchy(next_text):
                _maybe_update_context(context, next_text)
                i += 1
                continue
            body_lines.append(next_text)
            i += 1

        body = "\n".join(line for line in body_lines if line)
        if not body:
            continue
        yield Article(
            number=number,
            title=title,
            text=body,
            book=context.part,
            title_section=context.title_section,
            chapter=context.chapter,
            section=context.section,
            source_url=source_url,
            diploma="Constituição da República Portuguesa",
        )


def _format_number(num: str, suffix: str | None) -> str:
    return f"{num}-{suffix}" if suffix else num


def _is_hierarchy(text: str) -> bool:
    return bool(
        _PARTE_RE.match(text)
        or _TITULO_RE.match(text)
        or _CAPITULO_RE.match(text)
        or _SECCAO_RE.match(text)
    )


def _maybe_update_context(ctx: _Context, text: str) -> None:
    if _PARTE_RE.match(text):
        ctx.part = text
        ctx.title_section = None
        ctx.chapter = None
        ctx.section = None
    elif _TITULO_RE.match(text):
        ctx.title_section = text
        ctx.chapter = None
        ctx.section = None
    elif _CAPITULO_RE.match(text):
        ctx.chapter = text
        ctx.section = None
    elif _SECCAO_RE.match(text):
        ctx.section = text
