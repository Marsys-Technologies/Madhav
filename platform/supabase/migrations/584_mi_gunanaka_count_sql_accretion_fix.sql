-- Migration 584: mi_gunanaka count_sql — count the accretion table too (F-188)
-- Created: 2026-08-22
--
-- ROOT CAUSE. asset_registry.count_sql for mi_gunanaka has always been the
-- single-table form:
--   SELECT count(*) FROM mimamsa_multipliers WHERE chart_id = $1
-- mi_gunanaka.py::run() also writes to mimamsa_calibration_snapshot via
-- _publish_snapshot() (INSERT ... ON CONFLICT (snapshot_id) DO NOTHING, keyed
-- on a snapshot_id that embeds int(time.time())). That table is a deliberate,
-- RATIFIED exception to CLAUDE.md §N.3's per-chart delete-then-insert
-- standard — it is an append-only historical record for the L5 calibration
-- loop (two-key publication; key-1 = mi_gunanaka, key-2 = native
-- Ācārya-Pratinidhi sign-off), and it accretes a new row on every rebuild by
-- design. See mi_gunanaka.py::_publish_snapshot's docstring and
-- 00_ARCHITECTURE/briefs/parisesa/F188_ACCRETION_EXCEPTION_v1_0.md for the
-- full doctrine note.
--
-- The single-table count_sql therefore silently undercounts: it reports only
-- the stable mimamsa_multipliers row count and never surfaces the accreted
-- mimamsa_calibration_snapshot rows a chart has accumulated across rebuilds.
-- Confirmed live on prod chart 482012f1 (2026-08-22): 9 mimamsa_multipliers
-- rows + 4 mimamsa_calibration_snapshot rows = 13 true owned rows; the
-- pre-fix count_sql reports 9. Per CLAUDE.md §N.4 ("Cockpit truth: each asset
-- needs a correct chart-scoped count_sql"), the defect was the SILENCE about
-- the second table, not the accretion behaviour itself (which is correct and
-- ratified) — say so explicitly, this migration does not touch either data
-- table, only the registry's own count formula.
--
-- WHY A MIGRATION IS REQUIRED. asset_registry is seeded once by
-- scripts/seed/asset_registry_seed.ts; a corrected seed only fixes fresh
-- environments. The already-deployed asset_registry row for mi_gunanaka must
-- be corrected in place. The seed file's mi_gunanaka entry is corrected in
-- the same PR (source-of-truth for fresh seeds) — this migration carries the
-- identical value to the already-seeded row so production is right
-- immediately.
--
-- Pattern precedent: 309_ga_structural_count_sql_scope_fix.sql,
-- 314_bo_samskara_count_sql_scope_fix.sql, 315_ga_prashna_count_sql_fix.sql,
-- 448_bo_laksana_count_sql_scope_fix.sql — all a single scoped UPDATE on
-- asset_registry.count_sql, no data-table mutation. $1 is repeated per
-- subquery, the established multi-table convention (see ga_condition's
-- count_sql in asset_registry_seed.ts).
--
-- SCOPE. One row, one column, keyed by asset_id — no blanket UPDATE. The
-- verification block below aborts the migration rather than reporting
-- success on a partial apply (CLAUDE.md §N.8). Idempotent: re-running writes
-- the same literal string.

BEGIN;

UPDATE asset_registry
   SET count_sql = $sql$SELECT (SELECT COUNT(*) FROM mimamsa_multipliers WHERE chart_id = $1) + (SELECT COUNT(*) FROM mimamsa_calibration_snapshot WHERE chart_id = $1) AS count$sql$
 WHERE asset_id = 'mi_gunanaka';

-- ── Verification — a real detector, per CLAUDE.md §N.8 ──────────────────────

DO $f188_verify$
DECLARE
  v_row_count   int;
  v_count_sql   text;
BEGIN
  SELECT count(*), max(count_sql) INTO v_row_count, v_count_sql
    FROM asset_registry
   WHERE asset_id = 'mi_gunanaka';

  IF v_row_count <> 1 THEN
    RAISE EXCEPTION 'F-188: expected exactly 1 asset_registry row for mi_gunanaka, found %', v_row_count;
  END IF;

  IF v_count_sql NOT LIKE '%mimamsa_multipliers%' OR v_count_sql NOT LIKE '%mimamsa_calibration_snapshot%' THEN
    RAISE EXCEPTION 'F-188: mi_gunanaka count_sql does not reference both tables after UPDATE (got: %)', v_count_sql;
  END IF;

  RAISE NOTICE 'F-188: mi_gunanaka.count_sql now counts both mimamsa_multipliers and mimamsa_calibration_snapshot';
END $f188_verify$;

COMMIT;

-- DOWN:
-- BEGIN;
-- UPDATE asset_registry
--    SET count_sql = 'SELECT count(*) FROM mimamsa_multipliers WHERE chart_id = $1'
--  WHERE asset_id = 'mi_gunanaka';
-- COMMIT;

-- §N.4: surgical, verified. NEVER edit this file after it has been applied.
