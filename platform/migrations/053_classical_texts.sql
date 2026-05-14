-- Migration 053: classical_texts table
-- M8 Classical Cross-Reference — Tier 1/2/3/Nadi corpus metadata
-- Note: Plan specified 046 but 046-052 are used by aiops; using 053.
-- 2026-05-14 M8-A-S1

CREATE TABLE IF NOT EXISTS classical_texts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  text_key TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  author TEXT,
  tradition TEXT NOT NULL,
  school TEXT NOT NULL,
  tier INTEGER NOT NULL CHECK (tier IN (1, 2, 3)),
  language_original TEXT NOT NULL,
  translation_author TEXT,
  source_url TEXT,
  procurement_date DATE,
  chunk_count INTEGER DEFAULT 0,
  attribution_baseline_confidence NUMERIC(4, 3) DEFAULT 0.5,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE classical_texts IS 'M8: One row per classical Jyotish text. text_key is the canonical ingestion identifier (e.g. bphs, phaladeepika).';
COMMENT ON COLUMN classical_texts.tradition IS 'parashari | jaimini | tajika | kp | nadi | bnn';
COMMENT ON COLUMN classical_texts.tier IS '1=mandatory, 2=high priority, 3=standard priority';
