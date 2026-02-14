from __future__ import annotations

from pydantic import BaseModel, Field


class Article(BaseModel):
    """One article from a consolidated piece of legislation."""

    number: str = Field(..., description="Article number, e.g. '238' or '10-A'.")
    title: str = Field(default="", description="Article title / epigrafe.")
    text: str = Field(..., description="Full article body, plain text.")
    book: str | None = Field(default=None, description="LIVRO context, if any.")
    title_section: str | None = Field(default=None, description="TÍTULO context, if any.")
    chapter: str | None = Field(default=None, description="CAPÍTULO context, if any.")
    section: str | None = Field(default=None, description="SECÇÃO context, if any.")
    source_url: str = Field(..., description="URL the article was scraped from.")
    diploma: str = Field(..., description="Diploma name, e.g. 'Código do Trabalho'.")

    @property
    def citation(self) -> str:
        return f"Art. {self.number}.º — {self.diploma}"


class Chunk(BaseModel):
    """A chunk of an article suitable for embedding and retrieval."""

    article_number: str
    article_title: str
    chunk_index: int
    text: str
    diploma: str
    book: str | None = None
    title_section: str | None = None
    chapter: str | None = None
    section: str | None = None
    source_url: str

    @property
    def heading(self) -> str:
        return f"Art. {self.article_number}.º — {self.article_title}".strip(" —")


class RetrievedChunk(BaseModel):
    chunk: Chunk
    distance: float


class Citation(BaseModel):
    article_number: str
    article_title: str
    diploma: str
    source_url: str


class Answer(BaseModel):
    question: str
    answer: str
    citations: list[Citation]
    model: str
