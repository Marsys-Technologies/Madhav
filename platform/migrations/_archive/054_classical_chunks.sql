-- Migration 054: classical_chunks table
-- M8 Classical Cross-Reference — chunked text with pgvector embeddings
-- Note: Plan specified 047 but 046-052 are used by aiops; using 054.
-- 2026-05-14 M8-A-S1

CREATE TABLE IF NOT EXISTS classical_chunks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  text_id UUID NOT NULL REFERENCES classical_texts(id) ON DELETE CASCADE,
  chunk_index INTEGER NOT NULL,
  chapter TEXT,
  verse_range TEXT,
  content TEXT NOT NULL,
  embedding VECTOR(768),
  language TEXT NOT NULL DEFAULT 'en',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (text_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS classical_chunks_text_id_idx ON classical_chunks(text_id);
CREATE INDEX IF NOT EXISTS classical_chunks_embedding_idx ON classical_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

COMMENT ON TABLE classical_chunks IS 'M8: Chunked classical text passages. embedding is Vertex AI text-embedding-004 (768-dim). ivfflat index for cosine similarity search.';
COMMENT ON COLUMN classical_chunks.verse_range IS 'e.g. ''1.1-1.5'' for chapter 1 verses 1-5';
