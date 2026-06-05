-- Migration 072: Add work column to classical_texts for MCP v3.2 per-work queries
-- This enables AC.S1.1 gate: SELECT count(*) FROM classical_texts WHERE work='BPHS'
-- The work column mirrors text_key but uses the MARSYS canonical short-code (uppercase).

ALTER TABLE classical_texts
  ADD COLUMN IF NOT EXISTS work text GENERATED ALWAYS AS (upper(text_key)) STORED;

-- Index for fast per-work queries (used by read_classical_text MCP tool)
CREATE INDEX IF NOT EXISTS idx_classical_texts_work ON classical_texts (work);

COMMENT ON COLUMN classical_texts.work IS
  'Uppercase canonical short-code for the classical work, generated from text_key. '
  'Examples: BPHS, BPHS_JAIMINI, KP_READER_VOL1, TAJAKA_NEELAKANTHI. '
  'Added by MCP Transformation v3.2 migration 072.';
