-- 218_chart_divisionals_unique_idx_fix.sql
-- =============================================================================
-- Fix the chart_divisionals data-integrity bug that capped the ga_vargas asset
-- at ~1,850 rows when the writer computes ~78k.
--
-- ROOT CAUSE (diagnosed 2026-06-11): the unique index
--   chart_divisionals_unique_idx (chart_id, graha, ayanamsha_id, varga)
-- is too coarse. The ga_vargas writer (GA6) emits ~25 distinct fact_category /
-- fact_key rows per (chart, graha, ayanamsha, varga) — varga_position,
-- varga_dignity, varga_house_lord, varga_vimsopaka_contribution, varga_rollup,
-- … — but they all collide on that 4-column index. The writer's INSERT uses
-- `ON CONFLICT DO NOTHING`, so only ONE row per (chart, graha, ayanamsha, varga)
-- survived (the first inserted, varga_position) and the other ~24 categories
-- were silently dropped. This also explains why every later build's vargas
-- stayed attributed to the first build_id that wrote them — every subsequent
-- INSERT no-oped against the surviving rows.
--
-- The materialized view `mv_chart_vargas_summary` already assumes the CORRECT
-- granularity: it GROUPs BY (chart_id, ayanamsha_id, graha, varga) and pivots
-- `max(CASE WHEN fact_key = 'dignity' …)`, `'deity'`, `'house'`, etc. — i.e. it
-- expects many rows per planet-varga, one per fact_key. The coarse index
-- contradicted that design, so those pivoted columns were all NULL.
--
-- FIX: widen the unique index to include fact_category + fact_key so every
-- category row coexists, matching the MV's pivot. NULLS NOT DISTINCT (PG15+)
-- keeps re-runs idempotent for any NULL-bearing key column. build_id is
-- deliberately excluded: the data plane holds one canonical build per chart
-- (stale builds are cleaned), so a row is unique per fact regardless of build.
--
-- After this migration the orphan rows are deleted and the ga_vargas writer is
-- re-run for the canonical build (operational step, outside this DDL).
--
-- Idempotent (DROP IF EXISTS + CREATE). Reversible (DOWN restores coarse index).
-- =============================================================================

BEGIN;

DROP INDEX IF EXISTS chart_divisionals_unique_idx;

CREATE UNIQUE INDEX chart_divisionals_unique_idx
  ON chart_divisionals (chart_id, graha, ayanamsha_id, varga, fact_category, fact_key)
  NULLS NOT DISTINCT;

COMMIT;

-- =============================================================================
-- DOWN (manual rollback — restores the pre-218 coarse unique index):
--
-- BEGIN;
-- DROP INDEX IF EXISTS chart_divisionals_unique_idx;
-- CREATE UNIQUE INDEX chart_divisionals_unique_idx
--   ON chart_divisionals (chart_id, graha, ayanamsha_id, varga);
-- COMMIT;
-- NOTE: the coarse index will again collapse the writer's per-category rows;
-- only restore it if also reverting the ga_vargas writer to its pre-fix output.
-- =============================================================================
