-- 1072_kala_b1_registry_truth_and_sweep_protection.sql
--
-- KĀLA (L3) PRE-ELEVATION, Phase 1.1 / B1 — the registry half of "make the programme
-- safe". Sibling of migration 1071, which installs the database guard; this file
-- re-establishes the route-level protection rows underneath it.
--
-- ── PART 1: ka_gochara.target_table — WITHDRAWN (2026-09-29) ──────────────────
--
-- This migration was authored 2026-09-22 with a Part 1 that flipped
-- `asset_registry.ka_gochara.target_table` from `kala_gochara_windows` to
-- `kala_gochara_windows_v2`, matching the then-current Kāla B1 writer identity
-- (`writers/ka_gochara.py` TABLE = "kala_gochara_windows_v2", generation='2.0').
--
-- Part 1 is WITHDRAWN before first apply (this file has never been applied to
-- production — verified pending in `migrate.ts --dry-run` output). Two days after
-- authoring, migration 1091 (WP10 step 5, created and applied 2026-09-24 under
-- PRODUCTION_TRANCHE_1, native-authorised) re-pinned the ka_gochara registry row
-- to the '4.0' cutover surface: count_sql reads
-- `kala_gochara_windows ... generation='4.0'` and integrity conjunct (j) requires
-- `target_table = count_sql relation`. Production therefore holds
-- target_table='kala_gochara_windows' paired with the '4.0' count_sql. Applying
-- the old Part 1 now would flip target_table to `kala_gochara_windows_v2` and
-- break conjunct (j) in production; the seed literal (the one column the seed
-- owns on conflict) is corrected to the 1091 row in the same change, so any later
-- runSeed() converges to the same identity instead of undoing it.
--
-- The '4.0' windows for ka_gochara are written by the WP10 cutover scripts —
-- `scripts/kala_gochara_cutover/step06_candidate_build.py` (contacts/coverage
-- ledger) and `step06b_windows_projection.py` (kala_gochara_windows projection,
-- GENERATION_DEFAULT='4.0') — not by the writer module `ka_gochara.py`, whose
-- native-ruled '2.0'/_v2 identity is unchanged and is a DIFFERENT question
-- (writer-module output vs registry/catalog row for the asset; the registry row
-- is what conjunct (j), the cockpit Clear path and the seed govern). The standing
-- detector is `platform/scripts/__tests__/gochara_seed_target_table_parity.test.ts`,
-- which now binds the seed row to the 1091 identity and to conjunct (j).
--
-- ── PART 2: build_protected_assets rows for the retired sweep ───────────────────
--
-- Migration 588 emptied this table (0 rows, every chart, measured 2026-09-22). Both
-- cockpit Clear routes read it to withhold a protected asset from the preview and from
-- the DELETE loop, so with it empty that layer withholds nothing.
--
-- Rows are re-established for `ka_gochara_sweep` ONLY, and deliberately not for
-- `ka_gochara`: a `ka_gochara` row is what left the century materializer in a permanent
-- BUILD-PROTECTED error (Defect D-02) and caused 588. `ka_gochara_sweep` is RETIRED and
-- is never built, so withholding it costs no build and blocks only deletion.
--
-- The INSERT is DATA-DRIVEN — `SELECT DISTINCT chart_id ... WHERE generation='v1'` —
-- rather than a hardcoded pair of canonical UUIDs as in 540/566. That is the point:
-- production holds 2,667 v1 rows for chart cb73cd3d… ("Kiran Shenoy"), which neither 540
-- nor 566 ever listed, so a hand-seeded registry was fail-OPEN for it. Migration 1071's
-- trigger does not consult this table at all and is fail-CLOSED for every chart; these
-- rows are the route-level layer above it, and are honestly acknowledged as a snapshot
-- of the charts holding v1 rows AT APPLY TIME, not a standing invariant.
--
-- Part 2 remains correct against the post-1091 registry state: it touches only
-- `build_protected_assets`, and its v1 corpus premise is itself pinned by 1091's
-- integrity conjunct (h) (for every chart with '4.0' rows the v1 corpus must still
-- be present and strictly larger) — so the corpus these rows protect cannot have
-- silently gone away.
--
-- `protected_generations` is set to '{v1}' (the column's own default, stated explicitly
-- rather than relied upon). Neither Clear route reads that column — both SELECT
-- `asset_id` only — so route-level withholding is asset-level while the column's claim is
-- generation-level. That gap is NOT closed here and is recorded honestly (CLAUDE.md §N.8:
-- a signal must measure the claim it asserts). For `ka_gochara_sweep` the two coincide,
-- because every row it ever wrote is generation='v1'; migration 1071's trigger is the
-- generation-precise detector. See `PHASE1_1_B1_CLOSURE.md` for the open item.
--
-- ── SAFETY ──────────────────────────────────────────────────────────────────────
-- Touches no row of any `kala_*` data table and no schema. Does not alter migration 540
-- (its triggers are already gone) and does not reopen migration 566, the origin of the
-- century BUILD-PROTECTED guard. Does not un-retire `ka_gochara_sweep`. Does not touch
-- the ka_gochara registry row at all (Part 1 withdrawn — 1091's re-pin stands).
--
-- L3 Kāla reserved migration range 1070-1119 (DP-SD-021); 1072 verified free in BOTH
-- `platform/migrations/` and `platform/supabase/migrations/`, which
-- `platform/scripts/migrate.ts:832-835` reads as one numeric sequence.
--
-- IDEMPOTENT: the INSERT is ON CONFLICT DO NOTHING, so a second run is a no-op.
-- Proven by applying this file twice against a disposable Postgres (see
-- PHASE1_1_B1_CLOSURE.md).

BEGIN;

SET LOCAL lock_timeout = '2s';

-- ── PART 2 ──────────────────────────────────────────────────────────────────────

INSERT INTO build_protected_assets (asset_id, chart_id, reason, protected_generations)
SELECT DISTINCT
       'ka_gochara_sweep',
       w.chart_id,
       'Kala B1 (2026-09-22, pre-elevation Phase 1.1): the retired ka_gochara_sweep '
       'generation=v1 corpus. MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md S4 — '
       '"ka_gochara_sweep remains retired, snapshot-protected and never rebuildable". '
       'Its @register was removed at retirement, so the build system cannot regenerate '
       'these rows (migration 588 STANDING CAUTION). Re-established after migration 588 '
       'emptied this table; chart set derived from the rows themselves rather than '
       'hardcoded, because migrations 540/566 listed only the two canonical charts and '
       'were fail-open for every other chart holding v1 rows.',
       '{v1}'::text[]
  FROM kala_gochara_windows w
 WHERE w.generation = 'v1'
ON CONFLICT (asset_id, chart_id) DO NOTHING;

-- ── Fail closed if Part 2 did not take effect ─────────────────────────────────
-- A silent no-op must not pass as applied (CLAUDE.md §N.8). The checks below can
-- genuinely read false: revert the INSERT above and this block raises.

DO $$
DECLARE
  v1_charts    bigint;
  guarded      bigint;
BEGIN
  IF NOT EXISTS (SELECT 1 FROM asset_registry WHERE asset_id = 'ka_gochara') THEN
    RAISE EXCEPTION
      'migration 1072: asset_registry has no ka_gochara row; the registry this '
      'migration documents has nothing to protect above';
  END IF;

  -- Every chart that actually holds v1 rows must now carry a protection row. Stated as
  -- a comparison against the live data rather than a fixed count, so the check cannot
  -- quietly pass on a stale expectation.
  SELECT COUNT(DISTINCT chart_id) INTO v1_charts
    FROM kala_gochara_windows WHERE generation = 'v1';

  SELECT COUNT(*) INTO guarded
    FROM build_protected_assets
   WHERE asset_id = 'ka_gochara_sweep'
     AND chart_id IN (SELECT DISTINCT chart_id FROM kala_gochara_windows
                       WHERE generation = 'v1');

  IF guarded <> v1_charts THEN
    RAISE EXCEPTION
      'migration 1072 did not take effect: % chart(s) hold generation=v1 rows but only '
      '% carry a ka_gochara_sweep protection row', v1_charts, guarded;
  END IF;

  IF v1_charts = 0 THEN
    RAISE NOTICE 'migration 1072: no generation=''v1'' rows present, so zero protection '
                 'rows were needed — reported as an honest zero, not as a pass';
  END IF;

  -- The sweep must not have been resurrected by anything in this change.
  IF EXISTS (SELECT 1 FROM asset_registry
              WHERE asset_id = 'ka_gochara_sweep' AND is_active IS DISTINCT FROM FALSE) THEN
    RAISE EXCEPTION
      'migration 1072: ka_gochara_sweep is no longer is_active=false — the Clear-route '
      'filter this migration''s sibling change depends on would be defeated';
  END IF;
END $$;

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   DELETE FROM build_protected_assets WHERE asset_id = 'ka_gochara_sweep';
--   COMMIT;
-- No kala_* data row and no asset_registry row is touched by this migration or
-- its DOWN (Part 1 was withdrawn before first apply — the ka_gochara registry
-- row is governed by migration 1091 and the seed literal, not by this file).
-- =============================================================================
