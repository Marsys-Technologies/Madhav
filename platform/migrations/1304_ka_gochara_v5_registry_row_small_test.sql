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
--   writer_timeout_seconds  = 7200    — the watchdog deadline (runner.py:704-705) is per ASSET
--                                       DISPATCH, bounding the whole substep plan of one run; 7200
--                                       is deliberately generous so the first timing measurement is
--                                       readable, not cut off. The FULL build's value is set later
--                                       from measured timings, by its own migration;
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
--
-- WHAT IT DOES NOT TOUCH: is_active (stays false), every other column, every other asset_registry
-- row, every other table. No INSERT, no DELETE, no grant, no DDL, no chart data.
--
-- POST-CHECKS (raise, rolling the migration back — style of migration 1243):
--   1. the UPDATE changed EXACTLY ONE row;
--   2. the landed row holds every value above AND is_active IS FALSE;
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
  v_changed int;
  v_ok int;
  v_touched_other int;
BEGIN
  UPDATE asset_registry
     SET has_substeps = true,
         writer_timeout_seconds = 7200,
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
     AND is_active IS FALSE
     AND has_writer IS TRUE
     AND has_substeps IS TRUE
     AND writer_timeout_seconds = 7200
     AND depends_on = ARRAY['ga_positions','ga_dashas']::text[]
     AND count_sql = v_count_sql
     AND target_table = 'ka_gochara_eval_window'
     AND size_sql = v_size_sql
     AND target_floor = 0
     AND estimated_seconds IS NULL;
  IF v_ok <> 1 THEN
    RAISE EXCEPTION '1304: the ka_gochara_v5 row did not land in the expected small-test shape (is_active=false, has_substeps=true, timeout 7200, depends_on [ga_positions,ga_dashas], the ka_gochara_eval_window counter)';
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
