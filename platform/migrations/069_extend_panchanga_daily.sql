-- Phase 4C enrichment: add 5 JSONB enrichment columns to panchanga_daily.
-- Migration 060 created the table with the 5 core limbs (tithi/vara/nakshatra/yoga/karana).
-- This migration adds computed enrichment data populated by bootstrap_panchanga.py --rebuild.
-- All columns are nullable — existing rows are unaffected until rebuild runs (~73K rows,
-- ~60 min against prod Cloud SQL). Until rebuild runs, new fields return null gracefully;
-- the 5-limb path is unchanged. Idempotent: ADD COLUMN IF NOT EXISTS; safe to run twice.
BEGIN;

ALTER TABLE panchanga_daily
  ADD COLUMN IF NOT EXISTS special_yogas  JSONB,
  ADD COLUMN IF NOT EXISTS choghadiya     JSONB,
  ADD COLUMN IF NOT EXISTS hora           JSONB,
  ADD COLUMN IF NOT EXISTS inauspicious   JSONB,
  ADD COLUMN IF NOT EXISTS auspicious     JSONB;

-- special_yogas: [{name, rating, start_ts, end_ts}]
-- GIN index for existence/key checks: e.g. WHERE special_yogas @> '[{"name":"Guru Pushya"}]'
CREATE INDEX IF NOT EXISTS idx_panchanga_special_yogas
  ON panchanga_daily USING GIN (special_yogas)
  WHERE special_yogas IS NOT NULL;

-- inauspicious: {rahu:{start,end}, yama:{start,end}, gulika:{start,end}, dur_muhurta:[...]}
-- GIN index for key-presence queries: e.g. WHERE inauspicious ? 'rahu'
CREATE INDEX IF NOT EXISTS idx_panchanga_inauspicious
  ON panchanga_daily USING GIN (inauspicious)
  WHERE inauspicious IS NOT NULL;

COMMIT;
