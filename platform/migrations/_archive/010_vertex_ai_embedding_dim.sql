-- 010_vertex_ai_embedding_dim.sql
-- AM-JIS: Update rag_embeddings.embedding dimension from 1024 (Voyage-3-large)
-- to 768 (Vertex AI text-multilingual-embedding-002).
-- Applied after B.3 migration (Voyage → Vertex AI, 2026-04-28).
--
-- IMPORTANT: This migration TRUNCATES existing embeddings. After applying,
-- re-run python-sidecar/rag/embed.py to re-index all chunks with Vertex AI.

BEGIN;

-- Step 1: Drop dependent HNSW index (cannot ALTER column type with index present)
DROP INDEX IF EXISTS idx_rag_embeddings_hnsw;

-- Step 2: Clear stale Voyage-3-large embeddings (dimension mismatch would reject inserts)
TRUNCATE rag_embeddings;

-- Step 3: Alter embedding column to Vertex AI dimension (768)
ALTER TABLE rag_embeddings ALTER COLUMN embedding TYPE vector(768);

-- Step 4: Recreate HNSW index for Vertex AI text-multilingual-embedding-002 (768 dims)
CREATE INDEX IF NOT EXISTS idx_rag_embeddings_hnsw
    ON rag_embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

COMMIT;
