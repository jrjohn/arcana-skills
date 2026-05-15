-- Image OCR schema for claude-session-archive v1.15+
-- Idempotent — safe to re-run.
--
-- Cross-machine dedup at the cache layer (SHA256 of raw image bytes is global).
-- Per-message OCR rows in image_ocr enable UNION ALL search.

CREATE TABLE IF NOT EXISTS image_ocr_cache (
    sha256       TEXT PRIMARY KEY,
    media_type   TEXT NOT NULL,
    width        INT,
    height       INT,
    byte_size    INT,
    ocr_text     TEXT NOT NULL,
    engine       TEXT NOT NULL,
    ocr_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    ocr_host     TEXT
);

CREATE TABLE IF NOT EXISTS image_ocr (
    id           BIGSERIAL PRIMARY KEY,
    session_id   TEXT NOT NULL,
    project      TEXT NOT NULL,
    parent_seq   INTEGER NOT NULL,
    image_index  INTEGER NOT NULL,
    sha256       TEXT NOT NULL REFERENCES image_ocr_cache(sha256),
    ts           TIMESTAMPTZ,
    content      TEXT NOT NULL,
    content_tsv  tsvector GENERATED ALWAYS AS (to_tsvector('simple'::regconfig, COALESCE(content, ''::text))) STORED,
    embedding    vector(1024),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (session_id, parent_seq, image_index)
);

CREATE INDEX IF NOT EXISTS image_ocr_tsv_idx     ON image_ocr USING gin (content_tsv);
CREATE INDEX IF NOT EXISTS image_ocr_emb_idx     ON image_ocr USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS image_ocr_parent_idx  ON image_ocr (session_id, parent_seq);
CREATE INDEX IF NOT EXISTS image_ocr_ts_idx      ON image_ocr (ts);
CREATE INDEX IF NOT EXISTS image_ocr_project_idx ON image_ocr (project, ts);
CREATE INDEX IF NOT EXISTS image_ocr_sha_idx     ON image_ocr (sha256);
