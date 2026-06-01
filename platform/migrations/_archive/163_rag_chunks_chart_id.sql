-- 163_rag_chunks_chart_id.sql
-- RAG-CHUNKS-CHART-ID-KEYING (BRIEF: RAG_CHUNKS_CHART_ID_KEYING v1.0)
--
-- Adds chart_id, ayanamsha_id, source_type to rag_chunks (and its staging twin)
-- so that rag_embedder.embed_chart_document() — which already writes these
-- columns — no longer errors against the live schema.
--
-- chart_id is NULLABLE: NULL = global/chart-independent corpus row.
-- Classical corpus lives in classical_chunks (separate table); those rows
-- are NOT migrated here.
--
-- Down migration is included as a comment block at the bottom.

-- ── rag_chunks ─────────────────────────────────────────────────────────────────

ALTER TABLE rag_chunks
  ADD COLUMN IF NOT EXISTS chart_id     UUID REFERENCES charts(chart_id),
  ADD COLUMN IF NOT EXISTS ayanamsha_id TEXT,
  ADD COLUMN IF NOT EXISTS source_type  TEXT;

-- Per-chart retrieval + idempotent re-embed support
CREATE INDEX IF NOT EXISTS idx_rag_chunks_chart
    ON rag_chunks(chart_id);

CREATE INDEX IF NOT EXISTS idx_rag_chunks_chart_aya
    ON rag_chunks(chart_id, ayanamsha_id, source_type);

-- Backfill existing per-chart corpus rows to the native chart.
-- doc_types that are chart-specific: msr_signal, ucn_section, cdlm_cell,
-- l1_fact, domain_report, cgm_node, l4_remedial, l5_timeline, rm_element.
-- Rows that are genuinely chart-independent remain NULL.
UPDATE rag_chunks
   SET chart_id = '362f9f17-95a5-490b-a5a7-027d3e0efda0'
 WHERE chart_id IS NULL
   AND doc_type IN (
       'msr_signal', 'ucn_section', 'cdlm_cell', 'l1_fact',
       'domain_report', 'cgm_node', 'l4_remedial', 'l5_timeline', 'rm_element',
       'forensic_render'
   );

-- ── rag_chunks_staging ────────────────────────────────────────────────────────
-- Staging was created with LIKE rag_chunks INCLUDING ALL (migration 013) and does
-- not inherit subsequent ALTER TABLE changes, so columns must be added explicitly.

ALTER TABLE rag_chunks_staging
  ADD COLUMN IF NOT EXISTS chart_id     UUID,
  ADD COLUMN IF NOT EXISTS ayanamsha_id TEXT,
  ADD COLUMN IF NOT EXISTS source_type  TEXT;

-- ── Down migration ─────────────────────────────────────────────────────────────
-- To reverse this migration:
--
--   DROP INDEX IF EXISTS idx_rag_chunks_chart_aya;
--   DROP INDEX IF EXISTS idx_rag_chunks_chart;
--   ALTER TABLE rag_chunks
--     DROP COLUMN IF EXISTS source_type,
--     DROP COLUMN IF EXISTS ayanamsha_id,
--     DROP COLUMN IF EXISTS chart_id;
--   ALTER TABLE rag_chunks_staging
--     DROP COLUMN IF EXISTS source_type,
--     DROP COLUMN IF EXISTS ayanamsha_id,
--     DROP COLUMN IF EXISTS chart_id;
