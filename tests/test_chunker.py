from legis_pt_rag.ingest.chunker import chunk_article, chunk_articles
from legis_pt_rag.ingest.parser import parse_crp
from legis_pt_rag.models import Article


def _article(text: str, *, number: str = "1", title: str = "Test") -> Article:
    return Article(
        number=number,
        title=title,
        text=text,
        source_url="https://example.test",
        diploma="Constituição da República Portuguesa",
        book="PARTE I",
    )


def test_short_article_yields_one_chunk() -> None:
    art = _article("Texto curto.")
    chunks = chunk_article(art)
    assert len(chunks) == 1
    assert "Texto curto." in chunks[0].text
    assert "Art. 1.º" in chunks[0].text


def test_long_article_splits_at_paragraph_boundaries() -> None:
    paragraphs = [f"{i}. {'palavra ' * 60}" for i in range(1, 6)]
    art = _article("\n".join(paragraphs))
    chunks = chunk_article(art, target_words=100)
    assert len(chunks) >= 2
    for chunk in chunks:
        assert "Art. 1.º" in chunk.text


def test_chunk_text_carries_hierarchy(crp_html: str) -> None:
    arts = parse_crp(crp_html, source_url="https://example.test/crp")
    chunks = chunk_articles(arts)
    art13_chunk = next(c for c in chunks if c.article_number == "13")
    assert "PARTE" in art13_chunk.text
    assert "Princípio da igualdade" in art13_chunk.text
