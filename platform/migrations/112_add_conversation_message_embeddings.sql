-- R9-S2: Semantic conversation search embeddings.
-- Dimension 768 matches Vertex AI text-multilingual-embedding-002 (EMBED_DIM in embedText.ts).
-- Brief AC-1 originally specified vector(1536); adjusted to 768 to match the existing embedder.
CREATE TABLE IF NOT EXISTS conversation_message_embeddings (
  message_id UUID PRIMARY KEY REFERENCES conversation_messages(id) ON DELETE CASCADE,
  embedding  vector(768),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_cme_embedding
  ON conversation_message_embeddings
  USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
