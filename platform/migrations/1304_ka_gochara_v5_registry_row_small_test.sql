-- 1304_ka_gochara_v5_registry_row_small_test.sql
--
-- Pravāha (C41-P2, 2026-10-03): UPDATE ONLY the asset_registry row ka_gochara_v5, preparing it for
-- the steward-dispatched SMALL TEST build (dispatch_v5_small_test_job.py, C37/C41-P1). The row stays
-- is_active = false — the A2.5 transient-flip pattern is the only activation.
--
-- ⚠ ORDERING: POST-WINDOW. This migration must be applied ONLY AFTER the Gochara 5 protected window
-- is complete. It is an ordinary ROUTINE migration (NOT in PROTECTED_PUBLIC_SCHEMA_MIGRATIONS,
-- platform/scripts/migrate.ts).
--
-- WHAT (values per Stream A's ST-SMALLTEST-A1 reply, EVENTS M20261003T181323-f9c7 §1, steward OK
-- M20261003T181341-51ab):
--   has_substeps            = true    — the completeness probe (asset_runner.py:1267-1290) and
--                                       substep handling key off it;
--   writer_timeout_seconds  = 28800   — the watchdog deadline (runner.py execute_dag) is per ASSET
--                                       DISPATCH, bounding the whole substep plan of one run. 28800 s
--                                       (8 h) is ONE value for the small test AND the measuring build
--                                       over the whole 1998-2085 horizon (steward TIMEOUT-RULING
--                                       2026-10-05), so no second registry migration is needed: a
--                                       healthy run must never be ended by the cap. The cost is only
--                                       slower detection of a genuinely hung writer, and every run is
--                                       supervised. (A fired cap is a teardown case; the Cloud Run
--                                       job task timeout, 86400 s, sits above it.) The sealed FULL
--                                       build's value is set later, from the measured timings;
--   depends_on              = ['ga_positions','ga_dashas'] — what the writer truly reads: natal
--                                       graha longitudes via chart_context.py (ga_positions) and
--                                       Vimshottari rows via dasha_read.py (ga_dashas). NOT
--                                       bg_transit_rules (VEDHA_SOURCE is None), NOT
--                                       bg_transit_av_gates (P5 held), NOT bg_sky_calendar (v3 only);
--   count_sql / target_table / size_sql — the v5 truth counter. v5 does NOT write
--                                       kala_gochara_windows; the 5.0 outputs live in the ka_gochara_*
--                                       tables, so the 1243 placeholder counter is wrong for v5.
--                                       The chart-scoped counter is the evaluation windows, kept in
--                                       the ONE constant v_count_sql below (Stream B confirms the
--                                       target against the stats route before the window);
--   target_floor            = 0       — floors are aspirational;
--   estimated_seconds       = NULL    — honest until timed.
-- CHECKED, NOT WRITTEN (before AND after the write): scope = 'per_chart', is_active = false, has_writer = true, asset_kind = 'data', asset_type = 'data',
--   health_probe NULL, integrity_check_sql NULL, rebuild_on_probe_fail = false. integrity_check_sql is NEVER assigned here: NULL is skipped on the run path
--   (asset_runner.py) and is the honest no-declared-integrity of an unverifiable small-test row (steward CHAIN-3101-RULING-FINAL). health_probe must be
--   NULL, not an empty string: the dispatch reads '' as None but the teardown compares literally with None, so a '' row could be dispatched and then be
--   un-teardownable (Astra review of PR 3101, blocker 2); 1243 inserted NULL, so a '' is someone's later edit and is refused by name, not normalised.
--   The dispatch and teardown scripts validate the same fields (their EXPECTED_REGISTRY_ROW), literally.
--
-- PRIOR-STATE GUARD (Astra review of PR 3101, blocker 1): the row is locked first (SELECT ... FOR UPDATE, under the lock_timeout below) and its
--   current values are validated. Accepted: EXACTLY the 1243 shape (has_substeps false, timeout 600, depends_on empty, the kala_gochara_windows
--   target_table / count_sql / size_sql) or EXACTLY the 1304 shape (a re-run). Anything else — an operator's edit, a different scope, a probe — refuses
--   by field name and changes nothing. Every column this migration assigns is one the guard validated.
--
-- HOW IT APPLIES: a plain UPDATE migration, NOT in PROTECTED_DATA_PLANE_MIGRATIONS or PROTECTED_PUBLIC_SCHEMA_MIGRATIONS (platform/scripts/migrate.ts), so
-- the ROUTINE deploy-time runner applies it on the first deploy after it merges. The gate is therefore the MERGE TIMING (post-window, above), not a
-- protected window. READBACK after the apply (read-only): platform/scripts/v5_small_test_registry_row_readback.sql (PR 3097) shows the row and its
-- expected values.
--
-- WHAT IT DOES NOT TOUCH: is_active (stays false), every other column, every other asset_registry row. No INSERT, no DELETE, no grant, no DDL, no chart data.
--
-- ONE KNOWN SIDE EFFECT (migration 596, platform/supabase/migrations/596_nirmana_provenance_receipts.sql): the trigger
--   nirmana_registry_receipt_invalidation fires AFTER UPDATE OF depends_on / target_floor / target_table (among others) when the row changes, and its
--   function marks THIS asset's asset_freshness rows ('stale', reason registry_changed; WHERE asset_id = NEW.asset_id) so only a governed build
--   restores 'fresh'. On the first apply any existing ka_gochara_v5 freshness row goes stale; no other asset's row and no data row is touched. A
--   re-run changes no value, so the trigger's OLD IS DISTINCT FROM NEW guard does not fire. (An earlier header said "no other table": wrong.)
--
-- POST-CHECKS (raise, rolling the migration back — style of migration 1243):
--   1. the UPDATE changed EXACTLY ONE row;
--   2. the landed row holds every value above AND the checked fields (scope, is_active IS FALSE, health_probe IS NULL, ...);
--   3. a supplementary check of visible tuple versions (xmin = this transaction's id): NO OTHER
--      asset_registry row version was written by this transaction. (Not proof that nothing else was
--      touched — it cannot see deletes, subtransaction writes or other tables; the narrow write
--      scope is established by the single UPDATE above.)
--
-- LOCK TIMEOUT (pattern: migrations 1218/1255/1302/1303). `SET LOCAL lock_timeout = '5s'`: a blocked
-- migrate job must fail fast, not hang a shared deploy.
--
-- E6 GUARDS (done in the same change): registry_depends_on_migrations.json gains this migration
-- (regenerate_draft_level_map.py --write-migration-pin), registry_input_draft.json's v5 row carries
-- the same two edges, and the DRAFT outputs are re-rendered at the recorded stamp (registry
-- revision 25, frozen_at 2026-10-03T18:00:00+00:00). v5 is inactive, so the level map and the
-- active-127 do not move.
--
-- ROLLBACK NOTE: restore by a new reviewed migration against the then-current state, never by
-- blind reversal.

SET LOCAL lock_timeout = '5s';

DO $mig$
DECLARE
  -- Stream B confirms the count_sql target against the stats route; it lives in this ONE constant.
  v_count_sql CONSTANT text := 'SELECT COUNT(*) FROM ka_gochara_eval_window WHERE chart_id=$1 AND generation=''5.0''';
  v_size_sql  CONSTANT text := 'SELECT pg_total_relation_size(''ka_gochara_eval_window'')';
  -- the 1243 inert-row values this migration replaces (migration 1243's own text, kala_gochara_windows placeholders)
  v_old_count_sql CONSTANT text := 'SELECT COUNT(*) FROM kala_gochara_windows WHERE chart_id=$1 AND generation=''5.0''';
  v_old_size_sql  CONSTANT text := 'SELECT pg_total_relation_size(''kala_gochara_windows'')';
  v_asset CONSTANT text := 'ka_gochara_v5';
  r asset_registry%ROWTYPE;
  v_bad_common text[];
  v_bad_1243 text[];
  v_bad_1304 text[];
  v_changed int;
  v_ok int;
  v_touched_other int;
BEGIN
  -- PRIOR-STATE GUARD (see the header): lock the row, then accept ONLY the 1243 shape or the exact 1304 shape.
  SELECT * INTO r FROM asset_registry WHERE asset_id = v_asset FOR UPDATE;
  IF NOT FOUND THEN
    RAISE EXCEPTION '1304: expected to update exactly one asset_registry row (ka_gochara_v5), found none';
  END IF;

  -- fields this migration never assigns and both shapes share (a probe or integrity statement, a rebuild flag, other routing or scope: refused)
  v_bad_common := array_remove(ARRAY[
    CASE WHEN r.scope IS DISTINCT FROM 'per_chart' THEN 'scope' END,
    CASE WHEN r.is_active IS DISTINCT FROM false THEN 'is_active' END,
    CASE WHEN r.has_writer IS DISTINCT FROM true THEN 'has_writer' END,
    CASE WHEN r.asset_kind IS DISTINCT FROM 'data' THEN 'asset_kind' END,
    CASE WHEN r.asset_type IS DISTINCT FROM 'data' THEN 'asset_type' END,
    CASE WHEN r.health_probe IS NOT NULL THEN 'health_probe' END,
    CASE WHEN r.integrity_check_sql IS NOT NULL THEN 'integrity_check_sql' END,
    CASE WHEN r.rebuild_on_probe_fail IS DISTINCT FROM false THEN 'rebuild_on_probe_fail' END,
    -- assigned below, and the same in both shapes
    CASE WHEN r.target_floor IS DISTINCT FROM 0 THEN 'target_floor' END,
    CASE WHEN r.estimated_seconds IS NOT NULL THEN 'estimated_seconds' END
  ]::text[], NULL::text);
  v_bad_1243 := array_remove(ARRAY[
    CASE WHEN r.has_substeps IS DISTINCT FROM false THEN 'has_substeps' END,
    CASE WHEN r.writer_timeout_seconds IS DISTINCT FROM 600 THEN 'writer_timeout_seconds' END,
    CASE WHEN r.depends_on IS DISTINCT FROM ARRAY[]::text[] THEN 'depends_on' END,
    CASE WHEN r.count_sql IS DISTINCT FROM v_old_count_sql THEN 'count_sql' END,
    CASE WHEN r.target_table IS DISTINCT FROM 'kala_gochara_windows' THEN 'target_table' END,
    CASE WHEN r.size_sql IS DISTINCT FROM v_old_size_sql THEN 'size_sql' END
  ]::text[], NULL::text);
  v_bad_1304 := array_remove(ARRAY[
    CASE WHEN r.has_substeps IS DISTINCT FROM true THEN 'has_substeps' END,
    CASE WHEN r.writer_timeout_seconds IS DISTINCT FROM 28800 THEN 'writer_timeout_seconds' END,
    CASE WHEN r.depends_on IS DISTINCT FROM ARRAY['ga_positions','ga_dashas']::text[] THEN 'depends_on' END,
    CASE WHEN r.count_sql IS DISTINCT FROM v_count_sql THEN 'count_sql' END,
    CASE WHEN r.target_table IS DISTINCT FROM 'ka_gochara_eval_window' THEN 'target_table' END,
    CASE WHEN r.size_sql IS DISTINCT FROM v_size_sql THEN 'size_sql' END
  ]::text[], NULL::text);
  IF cardinality(v_bad_common) > 0 OR (cardinality(v_bad_1243) > 0 AND cardinality(v_bad_1304) > 0) THEN
    RAISE EXCEPTION '1304: refusing to overwrite the ka_gochara_v5 row: it is neither the migration-1243 shape nor the migration-1304 shape; nothing was changed. Fields differing from the shared shape: [%]; from the 1243 shape: [%]; from the 1304 shape: [%]',
      array_to_string(v_bad_common, ', '), array_to_string(v_bad_1243, ', '), array_to_string(v_bad_1304, ', ');
  END IF;

  UPDATE asset_registry
     SET has_substeps = true,
         writer_timeout_seconds = 28800,
         depends_on = ARRAY['ga_positions','ga_dashas']::text[],
         count_sql = v_count_sql,
         target_table = 'ka_gochara_eval_window',
         size_sql = v_size_sql,
         target_floor = 0,
         estimated_seconds = NULL
   WHERE asset_id = 'ka_gochara_v5';

  GET DIAGNOSTICS v_changed = ROW_COUNT;
  IF v_changed <> 1 THEN
    RAISE EXCEPTION '1304: expected to update exactly one asset_registry row (ka_gochara_v5), updated %', v_changed;
  END IF;

  SELECT count(*) INTO v_ok
    FROM asset_registry
   WHERE asset_id = 'ka_gochara_v5'
     AND scope = 'per_chart'
     AND is_active IS FALSE
     AND has_writer IS TRUE
     AND has_substeps IS TRUE
     AND writer_timeout_seconds = 28800
     AND depends_on = ARRAY['ga_positions','ga_dashas']::text[]
     AND count_sql = v_count_sql
     AND target_table = 'ka_gochara_eval_window'
     AND size_sql = v_size_sql
     AND target_floor = 0
     AND estimated_seconds IS NULL
     -- ROUTING FIELDS (Codex round 4 D2; steward DB4): checked, never written. asset_runner.py reads these to decide HOW the asset runs
     -- ("Asset metadata" block): an integrity check or probe PLUS rebuild_on_probe_fail = true takes the probe-green shortcut, where a passing
     -- probe marks the asset built WITHOUT running the writer. The dispatch and the teardown refuse a row that differs, so the migration
     -- refuses to land one (health_probe and integrity_check_sql must be NULL literally: the teardown compares with None).
     AND asset_kind = 'data'
     AND asset_type = 'data'
     AND health_probe IS NULL
     AND integrity_check_sql IS NULL
     AND rebuild_on_probe_fail IS FALSE;
  IF v_ok <> 1 THEN
    RAISE EXCEPTION '1304: the ka_gochara_v5 row did not land in the expected small-test shape (is_active=false, has_substeps=true, timeout 28800, depends_on [ga_positions,ga_dashas], the ka_gochara_eval_window counter, plain data routing: asset_kind/asset_type data, no health_probe, no integrity_check_sql, rebuild_on_probe_fail false)';
  END IF;

  -- Supplementary check of visible tuple versions (see the header): no OTHER asset_registry row
  -- version written by this transaction.
  SELECT count(*) INTO v_touched_other
    FROM asset_registry
   WHERE xmin = pg_current_xact_id()::xid
     AND asset_id <> 'ka_gochara_v5';
  IF v_touched_other <> 0 THEN
    RAISE EXCEPTION '1304: % other asset_registry row version(s) were written by this transaction — the migration must touch ONLY ka_gochara_v5', v_touched_other;
  END IF;
END $mig$;
