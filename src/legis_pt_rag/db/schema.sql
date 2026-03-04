CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS chunks (
    id              BIGSERIAL PRIMARY KEY,
    diploma         TEXT        NOT NULL,
    article_number  TEXT        NOT NULL,
    article_title   TEXT        NOT NULL DEFAULT '',
    chunk_index     INTEGER     NOT NULL,
    book            TEXT,
    title_section   TEXT,
    chapter         TEXT,
    section         TEXT,
    source_url      TEXT        NOT NULL,
    content         TEXT        NOT NULL,
    embedding       vector(768) NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (diploma, article_number, chunk_index)
);

CREATE INDEX IF NOT EXISTS chunks_embedding_idx
    ON chunks USING hnsw (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS chunks_diploma_idx ON chunks (diploma);
