-- 1329_l0_writer_timeout_budgets.sql
--
-- Suvarna: raise asset_registry.writer_timeout_seconds for the L0/L2 writers whose budget is smaller than their real runtime.
-- Data-only: ONE column of seven asset_registry rows, no DDL, no new object. Transaction ownership belongs to
-- platform/scripts/migrate.ts (no BEGIN/COMMIT here). Same pattern as migrations 1218 and 1296.
--
-- THE DEFECT. Forced run 981a51ec failed bg_muhurta_lattice and bg_sky_calendar with
-- "TIMEOUT: writer exceeded its writer_timeout_seconds budget (600s)". The per-asset registry value overrides the job-level
-- WRITER_TIMEOUT_SECONDS=7200, so a 600 s registry value caps the writer no matter what the job allows.
--
-- SELECTION (read on production, read-only, 2026-10-08, all 75 assets of the Suvarna set). Every asset below 7200 plus every asset
-- whose longest completed duration in build_run_assets exceeds 70% of its budget:
--   asset                  OLD    NEW     why
--   bg_muhurta_lattice     600    7200    timed out at 597 s in run 981a51ec
--   bg_sky_calendar        600    7200    timed out at 599 s in run 981a51ec
--   bg_cohort              600    7200    named in the brief (600 s class, synthetic cohort rebuild)
--   bg_parihara_rules      600    7200    named in the brief
--   bg_vidhi_primitives    600    7200    named in the brief
--   bo_laksana             10800  14400   longest completed run 8102 s = 75% of 10800 (over the 70% line)
--   bg_ephemeris           10800  21600   825,084-row rebuild has no successful full build on record; run 981a51ec reached 1876 s+
--                                         before it was cancelled. A timeout here would block the whole DAG. Judgement, not a measurement.
-- NOTE: for bg_muhurta_lattice / bg_sky_calendar the history is only no-op runs (<= 80 s), so 7200 is a judgement, not a measured fit.
-- NOT TOUCHED: bg_kota_chakra_rings/bg_phaladeepika_latta/bg_vedha_malefic_scale (60), bg_kp_sublord_division (120),
-- bg_class_lifetime_counts/bg_vidhi_floors/bo_sudarshana (600): longest completed run 0-10 s. Every other asset
-- (bg_ephemeris is handled above) is at 7200 or 10800 with completed durations below 70% of it.
--
-- GUARD. Each row is read FOR UPDATE. A missing or inactive row RAISES (the budget must land on a live asset). A row already at or
-- above its NEW value is a NOTICE no-op: the migration only ever RAISES a budget, never lowers one, so replaying it is idempotent.
-- A row below its NEW value is updated and re-read; if the UPDATE did not take, RAISE (never trust a silent no-op, CLAUDE.md N.4).
--
-- NO TRIGGER EFFECT. nirmana_registry_receipt_invalidation fires only AFTER UPDATE OF depends_on, natural_key_partition, health_probe,
-- integrity_check_sql, target_floor, asset_kind, asset_type, scope, has_writer, is_active, target_table (definition read on production
-- with pg_get_triggerdef, 2026-10-08). writer_timeout_seconds is not among them, so no asset_freshness receipt is staled.
--
-- Seed: platform/scripts/seed/asset_registry_seed.ts carries the same values (its ON CONFLICT preserves live values).
-- Tests: platform/tests/unit/migrations/l0_writer_timeout_budgets_1329_static.test.ts.
--
-- Post-apply verification:
--   SELECT asset_id, writer_timeout_seconds FROM asset_registry WHERE asset_id IN ('bg_muhurta_lattice','bg_sky_calendar','bg_cohort',
--     'bg_parihara_rules','bg_vidhi_primitives','bo_laksana','bg_ephemeris') ORDER BY 2, 1;   -- expect 7200 x5, bo_laksana 14400, bg_ephemeris 21600
--
-- ROLLBACK (not executed by migrate.ts):
--   UPDATE asset_registry SET writer_timeout_seconds = 600 WHERE asset_id IN ('bg_muhurta_lattice','bg_sky_calendar','bg_cohort',
--     'bg_parihara_rules','bg_vidhi_primitives') AND writer_timeout_seconds = 7200;
--   UPDATE asset_registry SET writer_timeout_seconds = 10800 WHERE asset_id = 'bo_laksana' AND writer_timeout_seconds = 14400;
--   UPDATE asset_registry SET writer_timeout_seconds = 10800 WHERE asset_id = 'bg_ephemeris' AND writer_timeout_seconds = 21600;

SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '60s';

DO $m1329$
DECLARE
  r      record;
  cur    integer;
  active boolean;
BEGIN
  FOR r IN
    SELECT * FROM (VALUES
      ('bg_muhurta_lattice',  7200),
      ('bg_sky_calendar',     7200),
      ('bg_cohort',           7200),
      ('bg_parihara_rules',   7200),
      ('bg_vidhi_primitives', 7200),
      ('bo_laksana',          14400),
      ('bg_ephemeris',        21600)
    ) AS v(asset_id, new_v)
  LOOP
    SELECT writer_timeout_seconds, is_active INTO cur, active
      FROM asset_registry WHERE asset_id = r.asset_id FOR UPDATE;
    IF NOT FOUND THEN
      RAISE EXCEPTION '1329: % has no asset_registry row', r.asset_id;
    ELSIF active IS DISTINCT FROM true THEN
      RAISE EXCEPTION '1329: % is not active in asset_registry', r.asset_id;
    ELSIF cur >= r.new_v THEN
      RAISE NOTICE '1329: % writer_timeout_seconds already % (>= %); nothing to do', r.asset_id, cur, r.new_v;
    ELSE
      UPDATE asset_registry
         SET writer_timeout_seconds = r.new_v
       WHERE asset_id = r.asset_id
         AND (writer_timeout_seconds IS NULL OR writer_timeout_seconds < r.new_v);
      SELECT writer_timeout_seconds INTO cur FROM asset_registry WHERE asset_id = r.asset_id;
      IF cur IS DISTINCT FROM r.new_v THEN
        RAISE EXCEPTION '1329: % writer_timeout_seconds update did not take (expected %, found %)', r.asset_id, r.new_v, cur;
      END IF;
    END IF;
  END LOOP;
END
$m1329$;
