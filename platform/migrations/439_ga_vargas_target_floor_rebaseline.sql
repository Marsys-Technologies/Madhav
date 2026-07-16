-- Migration 439: ga_vargas target_floor re-baseline (D-1.6 Lane S-6, D15b-F5)
-- Created: 2026-07-16
--
-- CLAUDE.md §N.4 "Floors aspirational, not gates": target_floor should equal the
-- achieved count after a build, never a fabricated/stale number. ga_vargas'
-- target_floor was 20877 (a stale prior-build snapshot); a live probe of
-- chart_divisionals for chart 482012f1-710e-4a25-994a-93821f5871aa (Abhisek) on
-- 2026-07-16 shows 22092 actual rows. Re-baselining the floor to the live achieved
-- count so the cockpit stops reporting a false under-target for this asset.
--
-- Idempotent: unconditional UPDATE keyed on asset_id — safe to re-run.

BEGIN;

UPDATE asset_registry
SET target_floor = 22092
WHERE asset_id = 'ga_vargas';

COMMIT;
