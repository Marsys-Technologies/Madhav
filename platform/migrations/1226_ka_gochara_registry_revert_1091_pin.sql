-- Migration 1226: revert migration 1091's registry re-pin of asset_id='ka_gochara' —
--                 the row must describe what its REGISTERED WRITER writes.
-- Pravāha A5.4 (steward M20261001T231926-f994, 2026-10-01; analysis M20261001T223507 / A5.4-cockpit-count).
-- Created: 2026-10-02. Author: pravaha stream A.
--
-- Numbering: 1226 is the lowest free number above main's highest (1225) by the E-009-discipline scan of
-- every origin/* head and both migration directories at authoring time (claimed: 1210-1220, 1222, 1223
-- [closed PR #2873], 1225, 1300; 1224 is held by Suvarna).
--
-- WHY THIS EXISTS
-- ===============
-- 1091 (WP10 step 5, applied 2026-09-24) re-pinned ka_gochara to the '4.0' production surface:
--   target_table = kala_gochara_windows, count_sql = windows WHERE generation='4.0',
--   clear_tables = {windows, contacts, coverage}, integrity_check_sql = the '4.0' contract (a)-(k).
-- It called the resulting cockpit 0 "expected and benign between steps 5 and 6", on the assumption that
-- the '4.0' build followed at once. It did not: the registered writer (writers/ka_gochara.py) still
-- writes kala_gochara_windows_v2 at generation '2.0' (TABLE / GENERATION_V2), the '4.0' rows come from the
-- cutover scripts, and the '4.1' candidate (A2.5) and '5.0' (A5.3) are separate assets. Read-only
-- production facts, 2026-10-02:
--   * count_sql counts 0 windows at '4.0' for BOTH charts, while the writer wrote 87 (482012f1) and
--     76 (1c826d5a) rows at '2.0' (asset_throughput says 'stale' / 'lit'). CLAUDE.md N.4: count_sql must
--     count what the writer writes — the cockpit stats route reads count_sql, not asset_throughput.
--   * integrity_check_sql evaluates TRUE on 482012f1 with 0 windows and 0 contacts in its scope — a signal
--     that cannot read false about the rows the writer actually wrote (N.8).
--   * EXPLICIT_CLEAR_OPS['ka_gochara'] cleared only '4.0' rows, so a Clear never touched the writer's own
--     windows_v2 rows nor its kala_gochara_v2_build_state fingerprints (after which the writer's
--     delta-aware skip would refuse to rebuild).
--
-- WHAT THIS DOES — asset_id = 'ka_gochara' ONLY, four columns, taken from kala_gochara_cutover_step05_snapshot
-- (the pre-1091 row 1091 snapped; it is in production, and the values below were extracted from it and
-- checked byte-for-byte by md5 before being embedded):
--   target_table        kala_gochara_windows            -> kala_gochara_windows_v2
--   count_sql           ... windows ... generation='4.0' -> the pre-1091 text (windows_v2, generation '2.0')
--   integrity_check_sql the 1091 '4.0' contract          -> the pre-1091 (670) contract, D-CND-03
--   clear_tables        {windows,contacts,coverage}      -> NULL (the pre-1091 value; 1091's own comment
--                       says the column is DISPLAY-ONLY — the Clear runtime reads EXPLICIT_CLEAR_OPS,
--                       reverted in the same PR)
-- NOT touched: depends_on (1091 widened it to the '4.0' kernel inputs; ordering-only, harmless, and a
-- different question), target_floor, the century row, ka_gochara_sweep, any other asset.
--
-- THE 1091 PIN IS RE-APPLIED TOGETHER WITH THE WRITER SWITCH AT D-FLIP (native-only), not before.
--
-- GUARDS (a routine migration must be safe to replay and loud on surprise)
-- =======================================================================
--   * Idempotent: if the row already holds the restored values the migration is a NOTICE and a no-op.
--   * Raises on an unexpected prior state: the row must hold exactly 1091's target_table / count_sql /
--     clear_tables and an integrity contract carrying 1091's marker, else RAISE EXCEPTION (it never
--     overwrites a value somebody else changed).
--   * Where kala_gochara_cutover_step05_snapshot exists (production), the migration RAISES unless the
--     snapshot's count_sql and integrity_check_sql md5s equal the values it is about to write and the
--     snapshot's clear_tables is NULL — "restore from the snapshot" is verified, not trusted. (A fresh or
--     disposable database has no snapshot and skips this check.)
--   * Exactly one row must be updated; the post-state is re-read and compared.
--
-- SIDE EFFECT (same as 1091): the nirmana_registry_receipt_invalidation trigger fires on target_table /
-- integrity_check_sql (migration 596) and marks this asset's asset_freshness rows stale ('registry config
-- changed'); only a successful sidecar execution restores fresh. No data row is touched.
--
-- SEED: asset_registry_seed.ts owns target_table on conflict (target_table = EXCLUDED.target_table), so the
-- seed row changes in the same PR; otherwise the next runSeed() would silently re-apply 1091's pin.
--
-- RUNNER AUTHORITY: the routine runner connects as amjis_app, which owns asset_registry (it issued 1218's
-- UPDATE of the same table). No BEGIN/COMMIT here: platform/scripts/migrate.ts owns the transaction.
-- NOT applied by this change.

DO $mig_1226$
DECLARE
  v_target      CONSTANT text := 'kala_gochara_windows_v2';
  v_count_sql   CONSTANT text := $ka_count_670$SELECT COUNT(*) FROM kala_gochara_windows_v2 WHERE chart_id=$1 AND generation='2.0'$ka_count_670$;
  v_integrity   CONSTANT text := $ka_integrity_670$
-- ka_gochara integrity contract (D-CND-03: chart-partitioned, attribution-preserving).
--
-- SCOPE — read this before changing anything. The `asset_registry` row for `ka_gochara` names
-- `kala_gochara_windows` as its target_table and counts generation '3.0' there — the WRITER does
-- neither. `pipeline/orchestrator/writers/ka_gochara.py` writes exclusively to
-- `kala_gochara_windows_v2` at generation '2.0', and the protected-table name does not appear
-- anywhere in that module (a statically-guarded absence). This contract is written for the asset
-- AS THE WRITER BEHAVES, so every conjunct that asserts content is scoped to
-- `kala_gochara_windows_v2` at generation '2.0'. The registry mismatch is a real defect and is
-- recorded in ka_gochara.volume.md — it is not encoded here as if it were true.
--
-- `kala_gochara_windows_v2` DOES carry a natural-key UNIQUE
-- (chart_id, event_class, window_start, peak_date, coalesce(milestone_id,''),
--  coalesce(resolution,''), generation) — measured on the live DB, contrary to the W3 brief's
-- "surrogate id only" listing — so a plain natural-key distinctness conjunct would be redundant
-- (D-CND-03 rule 4). The accretion detector this asset actually needs is (a)+(b) below: the
-- writer's replacement key is (chart_id, event_class, generation), which the UNIQUE cannot see.
SELECT
  -- (a) §N.3 attribution: every served row of this writer's generation must be covered by this
  -- writer's own bookkeeping for the same (chart, event_class, generation), with a real
  -- fingerprint behind it. A row whose class was later removed from the resonance map survives
  -- the natural key but has no build-state parent, and shows up here.
  NOT EXISTS (
    SELECT 1 FROM kala_gochara_windows_v2 w
    WHERE w.generation = '2.0'
      AND NOT EXISTS (
        SELECT 1 FROM kala_gochara_v2_build_state b
        WHERE b.chart_id = w.chart_id AND b.event_class = w.event_class
          AND b.generation = '2.0' AND b.class_fingerprint IS NOT NULL
      )
  )
  -- (b) §N.4 cockpit truth / §N.8 earned signal: the build-state counter is not taken on trust —
  -- it must equal the rows actually present for that (chart, event_class, generation), and a
  -- class recorded as an honest skip must have written nothing. This is the exact defect class
  -- already observed on this asset's `asset_throughput` row (a stale counter presented as a
  -- build fact) — here it is made permanently checkable at the grain the writer owns.
  AND NOT EXISTS (
    SELECT 1 FROM kala_gochara_v2_build_state b
    WHERE b.generation = '2.0'
      AND ((SELECT count(*) FROM kala_gochara_windows_v2 w
            WHERE w.chart_id = b.chart_id AND w.event_class = b.event_class
              AND w.generation = '2.0') <> b.rows_written
        OR (b.skipped_reason IS NOT NULL AND b.rows_written <> 0))
  )
  -- (c) §N.5: a window may only exist for an event class this chart's resonance map declares.
  -- The targets are the upstream authority — a window for an undeclared class is ungrounded.
  AND NOT EXISTS (
    SELECT 1 FROM kala_gochara_windows_v2 w
    WHERE w.generation = '2.0'
      AND NOT EXISTS (
        SELECT 1 FROM gochara_resonance_map g
        WHERE g.chart_id = w.chart_id AND g.event_class = w.event_class
      )
  )
  -- (d) window well-formedness for the generation this writer owns: the peak instant lies inside
  -- the window it is the peak OF. Deliberately scoped to generation '2.0' rather than applied
  -- table-wide, because 16 rows elsewhere in this family (15 in the v1 archive, 1 at generation
  -- '3.0', both other assets' output) violate containment today — a whole-family conjunct would
  -- make THIS asset's health signal red for another writer's defect, which is exactly the
  -- mis-attribution the registry already commits. The detector for those rows is handed to their
  -- owning assets in ka_gochara.volume.md.
  AND NOT EXISTS (
    SELECT 1 FROM kala_gochara_windows_v2 w
    WHERE w.generation = '2.0'
      AND (w.window_end < w.window_start
        OR w.peak_date < w.window_start
        OR w.peak_date > w.window_end)
  )
  -- (e) D-TIME horizon disclosure: every served row must lie inside the progressive horizon its
  -- own build-state discloses. A row outside it is an undisclosed claim about a span this build
  -- never scanned — and it is what a stale near-horizon cache looks like from the outside.
  AND NOT EXISTS (
    SELECT 1 FROM kala_gochara_windows_v2 w
    JOIN kala_gochara_v2_build_state b
      ON b.chart_id = w.chart_id AND b.event_class = w.event_class AND b.generation = w.generation
    WHERE w.generation = '2.0'
      AND (w.window_start < b.horizon_start_date OR w.window_end > b.horizon_end_date)
  )
  -- (f) THE UNTOUCHABLE-DATA RAIL, asserted rather than assumed: this writer's generation must
  -- never appear in the protected `kala_gochara_windows` relation. The absence is enforced today
  -- by construction (the writer cannot name that table), and this conjunct is what would notice
  -- if that ever stopped being true.
  AND NOT EXISTS (
    SELECT 1 FROM kala_gochara_windows p WHERE p.generation = '2.0'
  )
  -- (g) §N.3 generation hygiene: this writer's replacement key is (chart, event_class,
  -- generation) and it never stamps an era slice, so an era-stamped row inside generation '2.0'
  -- came from a different writer sharing the table — the cross-generation contamination the
  -- shared `kala_gochara_windows_v2` relation makes possible.
  AND NOT EXISTS (
    SELECT 1 FROM kala_gochara_windows_v2 w
    WHERE w.generation = '2.0' AND w.era_slice_key IS NOT NULL
  )
  -- (h) HARD-FLOOR CORPUS PRESENCE (§N.4, and the writer's own module docstring point 3, which
  -- names the v1 corpus as this writer's frozen validation benchmark). For every chart this
  -- writer has materialized, the irreplaceable v1 corpus for that same chart must still be
  -- present in `kala_gochara_windows`, and must remain strictly larger than this writer's
  -- ±3-year near-horizon layer for that chart — v1 is a birth→+100y daily sweep, so a v1 group
  -- that has shrunk to the size of the near-horizon layer has lost rows that cannot be
  -- regenerated (the retired writer's registration was removed). This conjunct is the reason
  -- the contract can NEVER be satisfied by the corpus being emptied: emptying it makes the
  -- contract FALSE, per chart.
  AND NOT EXISTS (
    SELECT 1 FROM (SELECT DISTINCT chart_id FROM kala_gochara_windows_v2 WHERE generation = '2.0') c
    WHERE (SELECT count(*) FROM kala_gochara_windows p
           WHERE p.chart_id = c.chart_id AND p.generation = 'v1')
          <= (SELECT count(*) FROM kala_gochara_windows_v2 w
              WHERE w.chart_id = c.chart_id AND w.generation = '2.0')
  )
  AS integrity_passed
$ka_integrity_670$;
  -- what 1091 left behind (the state this migration expects to find)
  v_prior_target     CONSTANT text   := 'kala_gochara_windows';
  v_prior_count_sql  CONSTANT text   := 'SELECT COUNT(*) FROM kala_gochara_windows WHERE chart_id=$1 AND generation=''4.0''';
  v_prior_clear      CONSTANT text[] := ARRAY['kala_gochara_windows', 'kala_gochara_contacts', 'kala_gochara_coverage'];
  v_prior_marker     CONSTANT text   := 'ka_gochara integrity contract (WP10 re-pin, plan §6.3)';
  v_cur         record;
  v_snap        record;
  v_n           integer;
BEGIN
  SELECT target_table, count_sql, integrity_check_sql, clear_tables
    INTO v_cur
    FROM asset_registry
   WHERE asset_id = 'ka_gochara'
   FOR UPDATE;
  IF NOT FOUND THEN
    RAISE EXCEPTION '1226: asset_registry has no ka_gochara row — nothing to revert (refusing to guess)';
  END IF;

  -- idempotent replay
  IF v_cur.target_table = v_target
     AND v_cur.count_sql = v_count_sql
     AND v_cur.integrity_check_sql = v_integrity
     AND v_cur.clear_tables IS NULL THEN
    RAISE NOTICE '1226: ka_gochara already holds the restored writer-surface registry values — no-op';
    RETURN;
  END IF;

  -- unexpected prior state: only 1091's exact result may be reverted
  IF v_cur.target_table IS DISTINCT FROM v_prior_target
     OR v_cur.count_sql IS DISTINCT FROM v_prior_count_sql
     OR v_cur.clear_tables IS DISTINCT FROM v_prior_clear
     OR v_cur.integrity_check_sql IS NULL
     OR position(v_prior_marker IN v_cur.integrity_check_sql) = 0 THEN
    RAISE EXCEPTION '1226: unexpected prior state for ka_gochara (target_table=%, count_sql=%, clear_tables=%) — only the exact state 1091 left may be reverted; refusing to overwrite',
                    v_cur.target_table, v_cur.count_sql, v_cur.clear_tables;
  END IF;

  -- "restore from the snapshot" is verified where the snapshot exists (production)
  IF to_regclass('public.kala_gochara_cutover_step05_snapshot') IS NOT NULL THEN
    EXECUTE 'SELECT md5(count_sql) AS count_md5, md5(integrity_check_sql) AS integrity_md5,
                    (clear_tables IS NULL) AS clear_is_null
               FROM public.kala_gochara_cutover_step05_snapshot WHERE asset_id = ''ka_gochara'''
       INTO v_snap;
    IF v_snap IS NULL THEN
      RAISE EXCEPTION '1226: kala_gochara_cutover_step05_snapshot exists but has no ka_gochara row';
    END IF;
    IF v_snap.count_md5 IS DISTINCT FROM md5(v_count_sql)
       OR v_snap.integrity_md5 IS DISTINCT FROM md5(v_integrity)
       OR v_snap.clear_is_null IS DISTINCT FROM true THEN
      RAISE EXCEPTION '1226: the snapshot does not equal the values this migration would write (count_sql md5 %, integrity md5 %, clear_tables NULL %) — refusing to restore',
                      v_snap.count_md5, v_snap.integrity_md5, v_snap.clear_is_null;
    END IF;
  END IF;

  UPDATE asset_registry
     SET target_table        = v_target,
         count_sql           = v_count_sql,
         integrity_check_sql = v_integrity,
         clear_tables        = NULL
   WHERE asset_id = 'ka_gochara';
  GET DIAGNOSTICS v_n = ROW_COUNT;
  IF v_n <> 1 THEN
    RAISE EXCEPTION '1226: expected to update exactly one ka_gochara row, updated %', v_n;
  END IF;

  -- post-state, re-read
  PERFORM 1 FROM asset_registry
   WHERE asset_id = 'ka_gochara'
     AND target_table = v_target AND count_sql = v_count_sql
     AND integrity_check_sql = v_integrity AND clear_tables IS NULL;
  IF NOT FOUND THEN
    RAISE EXCEPTION '1226: post-update read of ka_gochara does not equal the intended values';
  END IF;
END
$mig_1226$;
