-- Phase 4B: Derived Vedic-interpretable columns on ephemeris_daily.
-- Single-native mode: whole_sign_house is anchored to native lagna = Aries.
-- Backfill via platform/python-sidecar/pipeline/enrich_ephemeris_daily.py
-- after migration applies.
--
-- The base columns (longitude/latitude/sign/...) are unchanged. These
-- six columns are nullable initially and populated by the enrichment
-- pass or by bootstrap on a fresh build.
BEGIN;

ALTER TABLE ephemeris_daily
  ADD COLUMN IF NOT EXISTS is_combust BOOLEAN,
  ADD COLUMN IF NOT EXISTS combust_orb_deg NUMERIC(7,4),
  ADD COLUMN IF NOT EXISTS dignity_d1 TEXT,         -- 'exalted'|'debilitated'|'own_sign'|'mooltrikona'|'neutral'
  ADD COLUMN IF NOT EXISTS vargottama_today BOOLEAN,
  ADD COLUMN IF NOT EXISTS sign_ingress_today BOOLEAN,
  ADD COLUMN IF NOT EXISTS graha_yuddha_with TEXT,  -- nullable planet name when within 1° of another
  ADD COLUMN IF NOT EXISTS whole_sign_house SMALLINT;  -- 1..12, anchored to native lagna = Aries

ALTER TABLE ephemeris_daily_staging
  ADD COLUMN IF NOT EXISTS is_combust BOOLEAN,
  ADD COLUMN IF NOT EXISTS combust_orb_deg NUMERIC(7,4),
  ADD COLUMN IF NOT EXISTS dignity_d1 TEXT,
  ADD COLUMN IF NOT EXISTS vargottama_today BOOLEAN,
  ADD COLUMN IF NOT EXISTS sign_ingress_today BOOLEAN,
  ADD COLUMN IF NOT EXISTS graha_yuddha_with TEXT,
  ADD COLUMN IF NOT EXISTS whole_sign_house SMALLINT;

-- Targeted indexes for common synthesis-layer filters.
CREATE INDEX IF NOT EXISTS idx_ephemeris_combust ON ephemeris_daily(planet, date) WHERE is_combust = TRUE;
CREATE INDEX IF NOT EXISTS idx_ephemeris_dignity ON ephemeris_daily(planet, dignity_d1) WHERE dignity_d1 IN ('exalted','debilitated');
CREATE INDEX IF NOT EXISTS idx_ephemeris_ingress ON ephemeris_daily(planet, date) WHERE sign_ingress_today = TRUE;
CREATE INDEX IF NOT EXISTS idx_ephemeris_house ON ephemeris_daily(planet, whole_sign_house, date);

COMMIT;
