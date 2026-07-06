-- Migration 415: chart_dashas — partial index for ga_condition's per-graha
-- mahadasha lookup (BA-P3 FIX: ga_condition statement-timeout root cause).
--
-- Root cause (BA Phase-3 Abhinandan diagnostic rebuild, 2026-07-06):
-- ga_condition_writer._load_dasha_periods runs, per graha,
--   SELECT ... FROM chart_dashas
--   WHERE chart_id = $1 AND lord_graha = $2 AND level_n = 1
--   ORDER BY start_iso LIMIT 3
-- The only supporting index, cd_lord_lookup_idx (chart_id, ayanamsha_id,
-- lord_graha, system_id), does not cover level_n, so the planner does a
-- Bitmap Index Scan on (chart_id, lord_graha) that fetches ~20,591 heap rows
-- (every level/ayanamsha for that graha) only to filter down to the ~27
-- level_n=1 rows — est. cost ~59,724 (verified via EXPLAIN). On this chart's
-- 603K-row chart_dashas footprint, under a hot/contended table, that scan
-- crossed the 30s statement_timeout for the FIRST graha (Sun), and the
-- writer's swallow-without-rollback then poisoned the whole substep
-- transaction (fixed separately in ga_condition_writer.py), cascading to a
-- failed L1 that blocked the entire L2-L5 DAG.
--
-- Fix: a partial index on exactly the queried shape — (chart_id, lord_graha,
-- start_iso) WHERE level_n = 1. Indexes ONLY mahadasha (level_n=1) rows (a
-- small fraction of chart_dashas), so it is compact and the build is quick;
-- turns the ~20,591-row heap scan into a direct ~27-row index seek that also
-- satisfies the ORDER BY start_iso.
--
-- Lock note (same as migrations 359/414): the migrate.ts runner wraps each
-- file in BEGIN/COMMIT, which is incompatible with CREATE INDEX CONCURRENTLY,
-- so this is a plain index build under a brief SHARE lock. The partial
-- predicate keeps the indexed set small, so the lock window is short.

BEGIN;

CREATE INDEX IF NOT EXISTS chart_dashas_condition_lookup_idx
  ON chart_dashas (chart_id, lord_graha, start_iso)
  WHERE level_n = 1;

COMMIT;

-- DOWN:
-- DROP INDEX IF EXISTS chart_dashas_condition_lookup_idx;
