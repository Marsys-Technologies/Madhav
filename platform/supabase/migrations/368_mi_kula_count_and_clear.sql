-- Migration 368: mi_kula — fix count_sql to cover both emitted tables
--
-- Root cause: mi_kula's registered count_sql was:
--   SELECT count(*) FROM mimamsa_signal_families
-- which omitted mimamsa_negative_controls entirely. The Cockpit stat therefore
-- showed only the families count (12) and the clear mechanism derived from
-- count_sql had no knowledge of the negative_controls table (4 rows), leaving
-- it as dark data that survived every layer clear.
--
-- Fix:
--   count_sql — summed count across both global catalog tables (no chart_id,
--               these tables are not chart-scoped).
--   clear     — handled in code via EXPLICIT_CLEAR_OPS in assetClearSpec.ts
--               (migration 368 comment; code change is the authoritative fix
--               for the DELETE side since deriveDeleteSqlFromCountSql() cannot
--               produce an unscoped DELETE from the summed count_sql form).
--
-- Idempotent: pure UPDATE of count_sql.

UPDATE asset_registry
SET count_sql = $$SELECT
  (SELECT count(*) FROM mimamsa_signal_families) +
  (SELECT count(*) FROM mimamsa_negative_controls) AS count$$
WHERE asset_id = 'mi_kula';
