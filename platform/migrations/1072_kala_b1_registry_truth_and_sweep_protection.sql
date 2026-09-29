-- 1072_kala_b1_registry_truth_and_sweep_protection.sql
--
-- KĀLA (L3) PRE-ELEVATION, Phase 1.1 / B1 — the registry half of "make the programme
-- safe". Sibling of migration 1071, which installs the database guard; this file makes
-- the registry tell the truth about which relation each gochara asset owns, and
-- re-establishes the route-level protection rows underneath it.
--
-- ── PART 1: ka_gochara.target_table ─────────────────────────────────────────────
--
-- `asset_registry.ka_gochara.target_table` reads `kala_gochara_windows` — the PROTECTED
-- corpus. The writer has not produced that relation since its rewrite under a native
-- ruling: `writers/ka_gochara.py:120` declares `TABLE = "kala_gochara_windows_v2"`, its
-- DELETE is scoped to (chart_id × event_class × generation='2.0') at :336 and its INSERT
-- carries generation='2.0' at :362, and the module docstring states the ruling verbatim —
-- "this writer's only DELETE/SELECT/INSERT target is kala_gochara_windows_v2 -- there is
-- no code path, error branch, or override that ever names kala_gochara_windows".
-- W0 census #4 (MADHAV_DATA_PLANE_L3_W0_FIELD_CONTRACT_REGISTER_v1_0.md) settles the same
-- identity: ka_gochara → kala_gochara_windows_v2 (generation 2) + kala_gochara_v2_build_state.
--
-- This was already KNOWN and deliberately HELD — CURRENT_STATE_AND_DISPOSITION §4.1
-- records `ka_gochara` as "after resonance; seed target mismatch held". The hold was not
-- doubt about the correct value; it was that `target_table` is the one column of its trio
-- the SEED owns on conflict (`target_table = EXCLUDED.target_table` in
-- `platform/scripts/seed/asset_registry_seed.ts`'s DO UPDATE, against
-- `count_sql = asset_registry.count_sql` and `depends_on = asset_registry.depends_on`),
-- so a DB-only correction would be silently reverted by the next `runSeed()`.
--
-- The hold is therefore released by fixing BOTH halves in ONE change: this migration and
-- the seed literal, in the same commit, with
-- `platform/scripts/__tests__/gochara_seed_target_table_parity.test.ts` as the standing
-- detector that reads the writer's own TABLE constant and refuses to let them diverge
-- again. Collision check at authoring time: no open PR touches
-- `asset_registry_seed.ts` (verified across all 16 open PRs, 2026-09-22).
--
-- Not a live deletion vector by itself, and this migration does not pretend otherwise:
-- the cockpit Clear path resolves `count_sql` BEFORE `target_table`
-- (`clear/execute/route.ts:167` vs :175), and `ka_gochara`'s live count_sql already
-- names `_v2`. This is registry truth — the row a future clear-spec, digest, freshness
-- or census reader consumes — not the hole B1 closes. The hole is the retired sweep, and
-- that is migration 1071 plus the `is_active` filter on both Clear routes.
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
-- century BUILD-PROTECTED guard. Does not un-retire `ka_gochara_sweep`.
--
-- Expected benign side effect, disclosed rather than discovered later: `asset_registry`
-- carries trigger `nirmana_registry_receipt_invalidation`, so the Part-1 UPDATE marks
-- `asset_freshness` for `ka_gochara` stale with reason `registry_changed`. That is the
-- intended meaning of a registry change, not damage.
--
-- L3 Kāla reserved migration range 1070-1119 (DP-SD-021); 1072 verified free in BOTH
-- `platform/migrations/` and `platform/supabase/migrations/`, which
-- `platform/scripts/migrate.ts:832-835` reads as one numeric sequence.
--
-- IDEMPOTENT: the UPDATE is a no-op on a second run (its WHERE no longer matches) and the
-- INSERT is ON CONFLICT DO NOTHING. Proven by applying this file twice against a
-- disposable Postgres (see PHASE1_1_B1_CLOSURE.md).

BEGIN;

SET LOCAL lock_timeout = '2s';

-- ── PART 1 ──────────────────────────────────────────────────────────────────────

UPDATE asset_registry
   SET target_table = 'kala_gochara_windows_v2'
 WHERE asset_id     = 'ka_gochara'
   AND target_table = 'kala_gochara_windows';

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

-- ── Fail closed if either part did not take effect ──────────────────────────────
-- A silent no-op must not pass as applied (CLAUDE.md §N.8). Both checks can genuinely
-- read false: revert either statement above and this block raises.

DO $$
DECLARE
  bad_target   text;
  v1_charts    bigint;
  guarded      bigint;
BEGIN
  SELECT target_table INTO bad_target
    FROM asset_registry WHERE asset_id = 'ka_gochara';

  IF bad_target IS NULL THEN
    RAISE EXCEPTION
      'migration 1072: asset_registry has no ka_gochara row; refusing to report a '
      'correction that had nothing to correct';
  END IF;

  IF bad_target <> 'kala_gochara_windows_v2' THEN
    RAISE EXCEPTION
      'migration 1072 did not take effect: ka_gochara.target_table is %, expected '
      'kala_gochara_windows_v2', bad_target;
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
--   UPDATE asset_registry SET target_table = 'kala_gochara_windows'
--    WHERE asset_id = 'ka_gochara';          -- restores the INCORRECT value; see PART 1
--   DELETE FROM build_protected_assets WHERE asset_id = 'ka_gochara_sweep';
--   COMMIT;
-- No kala_* data row is touched by this migration or its DOWN.
-- =============================================================================
