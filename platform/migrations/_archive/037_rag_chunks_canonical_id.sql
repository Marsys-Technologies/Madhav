-- 037_rag_chunks_canonical_id.sql
-- W2-BUGS UQE-1 (Bug B2W-1): remedial_codex_query SELECTs rag_chunks.canonical_id
-- but the column does not exist. Add the column and backfill for l4_remedial rows
-- so the tool returns proper source_canonical_id instead of falling through to the
-- 'REMEDIAL_CODEX_v2_0' default for every row.

ALTER TABLE rag_chunks ADD COLUMN IF NOT EXISTS canonical_id TEXT;

UPDATE rag_chunks SET canonical_id = 'REMEDIAL_CODEX_v2_0'
  WHERE doc_type = 'l4_remedial' AND canonical_id IS NULL;
