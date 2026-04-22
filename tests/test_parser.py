from legis_pt_rag.ingest.parser import parse_crp


def test_parses_all_articles(crp_html: str) -> None:
    arts = parse_crp(crp_html, source_url="https://example.test/crp")
    assert len(arts) >= 290, "CRP should contain ~296 articles"
    assert arts[0].number == "1"
    assert arts[0].title == "República Portuguesa"
    assert "República soberana" in arts[0].text
    assert arts[-1].number == "296"


def test_article_13_has_correct_title_and_body(crp_html: str) -> None:
    arts = parse_crp(crp_html, source_url="https://example.test/crp")
    art13 = next(a for a in arts if a.number == "13")
    assert art13.title == "Princípio da igualdade"
    assert "dignidade social" in art13.text


def test_hierarchy_context_propagates(crp_html: str) -> None:
    arts = parse_crp(crp_html, source_url="https://example.test/crp")
    art13 = next(a for a in arts if a.number == "13")
    assert art13.book is not None
    assert "PARTE" in art13.book.upper()


def test_handles_inline_title_format(crp_html: str) -> None:
    """Articles like 'Artigo 92.º Conselho Económico e Social' use inline title."""
    arts = parse_crp(crp_html, source_url="https://example.test/crp")
    art92 = next(a for a in arts if a.number == "92")
    assert "Conselho Económico" in art92.title
