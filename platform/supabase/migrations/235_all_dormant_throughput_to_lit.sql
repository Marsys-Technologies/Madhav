-- 235_all_dormant_throughput_to_lit.sql
-- =============================================================================
-- Follow-up to migrations 229 + 233: promote ALL remaining L0/L1 asset
-- throughput records from 'dormant' to 'lit' for the native chart, and
-- INSERT records for bg_ontology + bg_reference which had no throughput row.
--
-- Actual row counts confirmed against prod (2026-06-16) — all assets have data:
--   bg_dasha_systems     18
--   bg_doshas            50
--   bg_ephemeris     825,084
--   bg_ontology          623   (no throughput record — INSERT)
--   bg_reference       1,512   (no throughput record — INSERT)
--   bg_rules           2,912
--   bg_texts          10,651
--   ga_dashas        536,471
--   ga_vargas         21,635
--
-- After this migration, zero L0/L1 assets with real data should carry the
-- "build-state stale" badge in the cockpit.
--
-- Idempotent: UPDATEs are guarded by state='dormant'; INSERTs use ON CONFLICT.
-- Scoped to canonical chart_id only.
-- =============================================================================

BEGIN;

-- 1. Promote dormant → lit for existing records with confirmed data.
UPDATE asset_throughput
SET
  state         = 'lit',
  last_built_at = COALESCE(last_built_at, NOW()),
  last_error    = NULL
WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
  AND asset_id IN (
    'bg_dasha_systems', 'bg_doshas', 'bg_ephemeris',
    'bg_rules', 'bg_texts',
    'ga_dashas', 'ga_vargas'
  )
  AND state = 'dormant';

-- 2. Insert lit records for assets with no throughput row at all.
INSERT INTO asset_throughput (chart_id, asset_id, state, last_built_at, last_error)
VALUES
  ('482012f1-710e-4a25-994a-93821f5871aa', 'bg_ontology',  'lit', NOW(), NULL),
  ('482012f1-710e-4a25-994a-93821f5871aa', 'bg_reference',  'lit', NOW(), NULL)
ON CONFLICT (chart_id, asset_id) WHERE chart_id IS NOT NULL DO UPDATE
  SET state = 'lit', last_error = NULL;

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--
-- BEGIN;
-- UPDATE asset_throughput SET state = 'dormant', last_built_at = NULL
-- WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
--   AND asset_id IN ('bg_dasha_systems','bg_doshas','bg_ephemeris','bg_rules','bg_texts','ga_dashas','ga_vargas');
-- DELETE FROM asset_throughput
-- WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
--   AND asset_id IN ('bg_ontology','bg_reference');
-- COMMIT;
-- =============================================================================
