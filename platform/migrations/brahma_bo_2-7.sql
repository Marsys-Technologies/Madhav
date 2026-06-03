-- Migration: brahma_bo_2-7.sql
-- Asset:      bodha.embeddings (BO-2-7)
-- Layer:      L2 Bodha — Chart Intelligence
-- Table:      bodha_signal_embeddings
-- Purpose:    One 768-dim pgvector embedding per MSR signal row in msr_signals.
--             Feeds corpus.search vector-search path; cosine similarity via HNSW.
-- Model:      text-multilingual-embedding-002 (Vertex AI, same as rag_embeddings)
-- Depends on: msr_signals (from migration 009_msr_signals.sql)
--             pgvector extension (enabled in baseline)
--
-- ROLLBACK:
--   DROP INDEX IF EXISTS idx_bodha_signal_embeddings_hnsw;
--   DROP TABLE IF EXISTS bodha_signal_embeddings;

BEGIN;

-- ── Ensure pgvector extension ─────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS vector;

-- ── bodha_signal_embeddings ───────────────────────────────────────────────────
--
-- Primary key:  signal_id (TEXT) — maps 1:1 to msr_signals.signal_id
-- embedding:    vector(768) — Vertex AI text-multilingual-embedding-002 output
-- model_name:   records which embedding model was used (for future re-embedding)
-- source_citation: copied from msr_signals.source_citation at embed time
--                  (nullable — msr_signals may not have this column on older schemas)
-- embedded_at:  timestamp of last upsert (set by bo_2-7.py)
--
CREATE TABLE IF NOT EXISTS bodha_signal_embeddings (
    signal_id       TEXT        PRIMARY KEY,
    embedding       vector(768) NOT NULL,
    model_name      TEXT        NOT NULL DEFAULT 'text-multilingual-embedding-002',
    source_citation TEXT,
    embedded_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── HNSW index (cosine) ───────────────────────────────────────────────────────
--
-- m=16, ef_construction=64 — same parameters as idx_rag_embeddings_hnsw in
-- rag/embed.py; tuned for MARSYS corpus size (~600 signals, expandable to ~5k).
--
CREATE INDEX IF NOT EXISTS idx_bodha_signal_embeddings_hnsw
    ON bodha_signal_embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- ── Scalar support indices ────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_bodha_signal_embeddings_model
    ON bodha_signal_embeddings (model_name);

CREATE INDEX IF NOT EXISTS idx_bodha_signal_embeddings_embedded_at
    ON bodha_signal_embeddings (embedded_at DESC);

COMMIT;
