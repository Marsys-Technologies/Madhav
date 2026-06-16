-- 234_activate_romanize_service_engines.sql
-- =============================================================================
-- Fixes two issues for bg_panchanga and bg_ephemeris_engine:
--
-- 1. is_active=false: both service engines were deactivated (likely by a seed
--    re-apply pre-flight that marked NULL-target_table assets as inactive,
--    same root cause as the ga_ assets fixed in migration 228). Being inactive
--    excludes them from the stats route query (WHERE is_active=true), so they
--    do not appear in the cockpit. Restore to is_active=true.
--
-- 2. sanskrit_name in Devanagari script: the seed seeded these two assets with
--    Devanagari text ('पञ्चाङ्ग गणना' / 'दृक् एफिमेरिस') while every other
--    asset in the registry uses romanized IAST. Native decision 2026-06-16:
--    romanize to match the other 39 assets.
--
-- Correct values per brief §P3:
--   bg_panchanga.sanskrit_name        → 'Pañcāṅga Gaṇanā'
--   bg_ephemeris_engine.sanskrit_name → 'Druk Ephemeris'
--   (english_name unchanged: 'Panchanga Engine' / 'Ephemeris Engine')
--
-- Idempotent (UPDATE by asset_id; re-running sets same values).
-- =============================================================================

BEGIN;

UPDATE asset_registry
SET
  is_active     = true,
  sanskrit_name = 'Pañcāṅga Gaṇanā'
WHERE asset_id = 'bg_panchanga';

UPDATE asset_registry
SET
  is_active     = true,
  sanskrit_name = 'Druk Ephemeris'
WHERE asset_id = 'bg_ephemeris_engine';

COMMIT;

-- =============================================================================
-- DOWN (manual rollback — restores Devanagari names + deactivates):
--
-- BEGIN;
-- UPDATE asset_registry SET is_active=false, sanskrit_name='पञ्चाङ्ग गणना' WHERE asset_id='bg_panchanga';
-- UPDATE asset_registry SET is_active=false, sanskrit_name='दृक् एफिमेरिस' WHERE asset_id='bg_ephemeris_engine';
-- COMMIT;
-- =============================================================================
