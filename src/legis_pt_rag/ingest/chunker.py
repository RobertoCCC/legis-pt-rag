"""Split parsed Articles into embedding-friendly Chunks.

The Constituição has both very short articles (one sentence) and very long ones
(article 165.º has dozens of numbered paragraphs). We pack paragraphs greedily
into chunks of roughly ``target_words`` words, but never split a single numbered
paragraph in half — citations stay coherent that way.
"""

from __future__ import annotations

from collections.abc import Iterable

from legis_pt_rag.models import Article, Chunk

DEFAULT_TARGET_WORDS = 250


def chunk_article(article: Article, *, target_words: int = DEFAULT_TARGET_WORDS) -> list[Chunk]:
    paragraphs = [p.strip() for p in article.text.split("\n") if p.strip()]
    if not paragraphs:
        return []

    groups: list[list[str]] = [[]]
    word_count = 0
    for para in paragraphs:
        words = len(para.split())
        if word_count + words > target_words and groups[-1]:
            groups.append([])
            word_count = 0
        groups[-1].append(para)
        word_count += words

    chunks: list[Chunk] = []
    for idx, group in enumerate(groups):
        body = "\n".join(group)
        text = _format_chunk_text(article, body)
        chunks.append(
            Chunk(
                article_number=article.number,
                article_title=article.title,
                chunk_index=idx,
                text=text,
                diploma=article.diploma,
                book=article.book,
                title_section=article.title_section,
                chapter=article.chapter,
                section=article.section,
                source_url=article.source_url,
            )
        )
    return chunks


def chunk_articles(
    articles: Iterable[Article], *, target_words: int = DEFAULT_TARGET_WORDS
) -> list[Chunk]:
    out: list[Chunk] = []
    for article in articles:
        out.extend(chunk_article(article, target_words=target_words))
    return out


def _format_chunk_text(article: Article, body: str) -> str:
    """Prepend a heading so embeddings carry the article's context."""
    parts: list[str] = []
    location_bits = [
        b for b in (article.book, article.title_section, article.chapter, article.section) if b
    ]
    if location_bits:
        parts.append(" · ".join(location_bits))
    heading = f"{article.diploma} — Art. {article.number}.º"
    if article.title:
        heading += f" ({article.title})"
    parts.append(heading)
    parts.append(body)
    return "\n".join(parts)
