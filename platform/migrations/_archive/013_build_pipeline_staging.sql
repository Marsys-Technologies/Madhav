-- 013_build_pipeline_staging.sql
-- Phase 14B: staging tables + build manifest registry
BEGIN;

-- Staging mirrors of live RAG tables. Pipeline writes here first;
-- a transactional swap promotes staging to live atomically.
CREATE TABLE IF NOT EXISTS rag_chunks_staging (LIKE rag_chunks INCLUDING ALL);
CREATE TABLE IF NOT EXISTS rag_embeddings_staging (LIKE rag_embeddings INCLUDING ALL);

-- Build manifest registry. Every pipeline run lands one row here.
-- The latest_build_id row points at the manifest currently live in rag_chunks.
CREATE TABLE IF NOT EXISTS build_manifests (
  build_id TEXT PRIMARY KEY,
  triggered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  triggered_by TEXT NOT NULL,                 -- 'manual:<email>' | 'scheduler' | 'github-push'
  registry_fingerprint TEXT NOT NULL,         -- sha256 of VALIDATED_ASSET_REGISTRY at fetch time
  pipeline_image_uri TEXT NOT NULL,           -- artifact registry image tag
  embedding_model TEXT NOT NULL,              -- 'text-multilingual-embedding-002'
  embedding_dim INTEGER NOT NULL,             -- 768
  chunk_count INTEGER NOT NULL,
  embedding_count INTEGER NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('staging', 'live', 'rolled_back', 'failed')),
  manifest_uri TEXT NOT NULL,                 -- gs://madhav-marsys-build-artifacts/build-<id>/manifest.json
  promoted_at TIMESTAMPTZ,
  notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_build_manifests_status ON build_manifests(status);
CREATE INDEX IF NOT EXISTS idx_build_manifests_triggered_at ON build_manifests(triggered_at DESC);

COMMIT;
