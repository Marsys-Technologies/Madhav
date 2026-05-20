-- Migration 069 — extend_panchanga_daily (5 JSONB enrichment columns)
-- PSHIP-S3H (2026-05-20): Extends panchanga_daily with special_yogas, inauspicious,
-- auspicious, choghadiya, hora JSONB columns for Option H hybrid architecture.
-- Populated by bootstrap_panchanga.py --rebuild after this migration is applied.
-- Brief specifies "061" but 061–068 are already taken; 069 is the next available slot.

ALTER TABLE panchanga_daily
  ADD COLUMN IF NOT EXISTS special_yogas JSONB,
  ADD COLUMN IF NOT EXISTS inauspicious  JSONB,
  ADD COLUMN IF NOT EXISTS auspicious    JSONB,
  ADD COLUMN IF NOT EXISTS choghadiya    JSONB,
  ADD COLUMN IF NOT EXISTS hora          JSONB;

-- GIN index for special_yogas to enable @> / jsonb_path_query operator searches.
-- E.g.: SELECT date FROM panchanga_daily WHERE special_yogas @> '[{"yoga":"Sarvartha Siddhi"}]';
CREATE INDEX IF NOT EXISTS idx_panchanga_daily_special_yogas
  ON panchanga_daily USING GIN(special_yogas);

-- Separate GIN index for inauspicious to allow rahu_kalam / yamagandam queries.
CREATE INDEX IF NOT EXISTS idx_panchanga_daily_inauspicious
  ON panchanga_daily USING GIN(inauspicious);
