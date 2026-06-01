-- Migration 055: classical_attributions table
-- M8 Classical Cross-Reference — MSR signal × chunk attribution records
-- Note: Plan specified 048 but 046-052 are used by aiops; using 055.
-- 2026-05-14 M8-A-S1

CREATE TABLE IF NOT EXISTS classical_attributions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  msr_signal_id TEXT NOT NULL,
  chunk_id UUID NOT NULL REFERENCES classical_chunks(id) ON DELETE CASCADE,
  attribution_type TEXT NOT NULL CHECK (
    attribution_type IN ('confirms', 'contradicts', 'partial', 'extends', 'silent')
  ),
  confidence NUMERIC(4, 3) NOT NULL,
  confidence_tier TEXT GENERATED ALWAYS AS (
    CASE
      WHEN confidence >= 0.75 THEN 'HIGH'
      WHEN confidence >= 0.50 THEN 'MEDIUM'
      ELSE 'LOW'
    END
  ) STORED,
  derivation_notes TEXT,
  translation_cross_checked BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS classical_attributions_signal_idx ON classical_attributions(msr_signal_id);
CREATE INDEX IF NOT EXISTS classical_attributions_chunk_idx ON classical_attributions(chunk_id);
CREATE INDEX IF NOT EXISTS classical_attributions_type_idx ON classical_attributions(attribution_type);

COMMENT ON TABLE classical_attributions IS 'M8: LLM-judged attribution of each MSR signal to classical text passages. confidence_tier generated from confidence score.';
COMMENT ON COLUMN classical_attributions.attribution_type IS 'confirms|contradicts|partial|extends|silent';
COMMENT ON COLUMN classical_attributions.confidence_tier IS 'Generated: HIGH (>=0.75) | MEDIUM (0.50-0.75) | LOW (<0.50)';
