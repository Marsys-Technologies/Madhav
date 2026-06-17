-- =============================================================================
-- 294_catalog_status_current.sql
-- Fix catalog_status for built assets that defaulted to 'DRAFT'.
--
-- Root cause: several registry migrations omitted catalog_status from their
-- INSERT column list; the column default is 'DRAFT'::text, so those assets
-- are invisible in the Nirmāṇa cockpit (which filters on catalog_status).
--
-- Assets updated to CURRENT — all have live data in production:
--   ga_nakshatra  : 1,802 rows in chart_facts (built 2026-06-17)
--   bg_prashna_rules : 36 rows across 5 prashna reference tables (Gate-2)
--   bg_transit_engine: 9 rows (Gate-2)
--   bg_transit_rules : 41 rows (Gate-2)
--
-- Gate-3 deferred (tables exist but 0 rows — legitimately DRAFT):
--   ga_yoga   : yoga_families / ga_yoga_firings empty → flag for Gate-3
--   ga_prashna: prashna_charts empty → flag for Gate-3
--
-- Rollback (down): SET catalog_status = NULL / DEFAULT ('DRAFT') for same assets.
-- Applied surgically — never via deploy.yml.
-- =============================================================================

BEGIN;

UPDATE asset_registry SET catalog_status = 'CURRENT'
WHERE asset_id IN (
    'ga_nakshatra',
    'bg_prashna_rules',
    'bg_transit_engine',
    'bg_transit_rules'
);

COMMIT;
