-- Phase 4 §6.6 follow-up: Bhava-Chalit (Sripati cusp) house position on ephemeris_daily.
-- Single-native mode: bhava_chalit_house is anchored to native birth chart's
-- Sripati cusps computed once at bootstrap_ephemeris start. M7 multi-native
-- extension will require either per-native column duplication or query-time
-- on-the-fly computation against per-native cusps.
--
-- The column complements (does NOT replace) whole_sign_house from §4.B.
-- Whole-Sign and Bhava-Chalit are peer surfaces; senior acharyas consult
-- both, especially for sandhi (sign-boundary) planets.
BEGIN;

ALTER TABLE ephemeris_daily
  ADD COLUMN IF NOT EXISTS bhava_chalit_house SMALLINT;  -- 1..12

ALTER TABLE ephemeris_daily_staging
  ADD COLUMN IF NOT EXISTS bhava_chalit_house SMALLINT;

CREATE INDEX IF NOT EXISTS idx_ephemeris_bhava_chalit
  ON ephemeris_daily(planet, bhava_chalit_house, date);

COMMIT;
