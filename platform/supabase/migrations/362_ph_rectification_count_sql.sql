-- Migration 362: Fix ph_rectification count_sql to sum both tables
--
-- ph_rectification writes TWO tables:
--   phala_rectification      (185 rows, 37 offsets × 5 ayanamshas)
--   phala_rectification_best (1 row, staged best candidate)
--
-- The DELETE completeness is fixed in code (EXPLICIT_CLEAR_OPS in
-- platform/src/lib/cockpit/assetClearSpec.ts). This migration fixes the
-- PREVIEW side so the per-asset count reconciles with what the clear actually
-- deletes — same pattern as migration 358 for the L2/L5 multi-table writers.
--
-- Idempotent: pure UPDATE of count_sql.

UPDATE asset_registry
SET count_sql = 'SELECT (SELECT count(*) FROM phala_rectification WHERE chart_id = $1) + (SELECT count(*) FROM phala_rectification_best WHERE chart_id = $1) AS count'
WHERE asset_id = 'ph_rectification';
