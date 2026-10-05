-- 1296_bodha_writer_timeouts_s_l2_rebuild.sql
--
-- Suvarna S-L2 FAST PATH (production rebuild window): raise asset_registry.writer_timeout_seconds for seven bodha writers.
-- Data-only: exact-value-guarded UPDATEs of ONE column (writer_timeout_seconds) of seven asset_registry rows, no DDL, no new
-- object (no temp table either), so it runs fine as amjis_app, the routine migration runner and the owner of asset_registry.
-- Transaction ownership belongs to platform/scripts/migrate.ts (no BEGIN/COMMIT here).
--
-- THE DEFECT. The in-process per-writer watchdog marks an asset `error` when it exceeds asset_registry.writer_timeout_seconds
-- (runner.py _timeout_for / the deadline check) and cascade-blocks its dependents. bo_arudha exceeded its 600 s in the first run of
-- the S-L2 rebuild in production (TIMEOUT marking error at 600 s while the writer was still working).
--
-- WHY THESE NEW VALUES. bo_laksana will now write about 25,360 signals per ayanamsha (2.5x the earlier 10,084), so the downstream
-- writers grow accordingly; and the 600 s writers that timed out depend on ga_structural (slow pre-open bind). The budgets are therefore
-- 7200 s for the five 600 s writers and 10800 s for bo_grounding and bo_laksana_rerank (the same ceiling the other bodha assets read).
--
--   asset                    OLD (read on production 2026-10-05 14:41Z)   NEW
--   bo_arudha                600                                          7200
--   bo_nakshatra_semantic    600                                          7200
--   bo_special_lagna         600                                          7200
--   bo_vargottama_dhana      600                                          7200
--   bo_yantra_mechanism      600                                          7200
--   bo_grounding             1800 (migration 1218)                        10800
--   bo_laksana_rerank        1800 (migration 1218)                        10800
--
-- NOT TOUCHED: bo_sudarshana (600; it completed in about 30 s) and every other asset_registry row (the other bodha assets read 10800).
--
-- GUARD AND WHAT HAPPENS WHEN IT DOES NOT MATCH. Each row is updated ONLY WHERE writer_timeout_seconds equals its expected OLD value.
-- A row already at its NEW value is a no-op (NOTICE); a row holding any other value (a deliberate edit meanwhile) is LEFT ALONE with a
-- NOTICE naming the value found, and a missing row is a NOTICE; none of these fail the deploy (a timeout budget is not data). Replaying
-- the file is therefore a no-op (idempotent). The ONE case that RAISES: a row whose guard matched (it held the OLD value) still does
-- not hold the NEW value after its UPDATE, i.e. the UPDATE silently did not take effect (never trust a silent no-op, CLAUDE.md N.4 /
-- Trap 103). Each target row is read FOR UPDATE first so the guard and the UPDATE see the same value.
--
-- NO TRIGGER EFFECT. nirmana_registry_receipt_invalidation fires only AFTER UPDATE OF depends_on, natural_key_partition, health_probe,
-- integrity_check_sql, target_floor, asset_kind, asset_type, scope, has_writer, is_active, target_table (definition read on production
-- with pg_get_triggerdef). writer_timeout_seconds is not among them and this migration sets only writer_timeout_seconds, so no
-- asset_freshness row of any asset is marked stale. Same reasoning, and the same frozen-manifest safety (writer_timeout_seconds is not in
-- registryContractFingerprintInput), as migration 1218.
--
-- THE SEED. platform/scripts/seed/asset_registry_seed.ts now carries the same seven values so a fresh database matches (its INSERT
-- writes the column; its ON CONFLICT clause preserves the live value, so the seed never overwrites production). On a fresh database
-- that seed has already written the NEW value, the guard finds it and this migration is a NOTICE no-op.
--
-- Tests: platform/tests/unit/migrations/bodha_writer_timeouts_1296_static.test.ts (static) and
-- platform/python-sidecar/tests/test_migration_1296_bodha_writer_timeouts.py (executes this file on a disposable PostgreSQL).
--
-- Post-apply verification (CLAUDE.md N.4; read as suvarna_reader, not trusted from the deploy log): expect 7200 x5, 10800 x2, bo_sudarshana 600.
--   SELECT asset_id, writer_timeout_seconds FROM asset_registry WHERE asset_id IN ('bo_arudha','bo_nakshatra_semantic',
--     'bo_special_lagna','bo_vargottama_dhana','bo_yantra_mechanism','bo_grounding','bo_laksana_rerank','bo_sudarshana') ORDER BY 2, 1;
--
-- ROLLBACK (not executed by migrate.ts):
--   UPDATE asset_registry SET writer_timeout_seconds = 600 WHERE asset_id IN ('bo_arudha','bo_nakshatra_semantic','bo_special_lagna',
--     'bo_vargottama_dhana','bo_yantra_mechanism') AND writer_timeout_seconds = 7200;
--   UPDATE asset_registry SET writer_timeout_seconds = 1800 WHERE asset_id IN ('bo_grounding','bo_laksana_rerank') AND writer_timeout_seconds = 10800;

SET LOCAL lock_timeout = '5s';

DO $m1296$
DECLARE
  r   record;
  cur integer;
BEGIN
  FOR r IN
    SELECT * FROM (VALUES
      ('bo_arudha',             600,  7200),
      ('bo_nakshatra_semantic', 600,  7200),
      ('bo_special_lagna',      600,  7200),
      ('bo_vargottama_dhana',   600,  7200),
      ('bo_yantra_mechanism',   600,  7200),
      ('bo_grounding',          1800, 10800),
      ('bo_laksana_rerank',     1800, 10800)
    ) AS v(asset_id, old_v, new_v)
  LOOP
    SELECT writer_timeout_seconds INTO cur FROM asset_registry WHERE asset_id = r.asset_id FOR UPDATE;
    IF NOT FOUND THEN
      RAISE NOTICE '1296: % has no asset_registry row; nothing to do', r.asset_id;
    ELSIF cur = r.new_v THEN
      RAISE NOTICE '1296: % writer_timeout_seconds already % ; nothing to do', r.asset_id, r.new_v;
    ELSIF cur IS DISTINCT FROM r.old_v THEN
      RAISE NOTICE '1296: % writer_timeout_seconds is % , not the expected % ; left untouched', r.asset_id, cur, r.old_v;
    ELSE
      UPDATE asset_registry
         SET writer_timeout_seconds = r.new_v
       WHERE asset_id = r.asset_id
         AND writer_timeout_seconds = r.old_v;
      SELECT writer_timeout_seconds INTO cur FROM asset_registry WHERE asset_id = r.asset_id;
      IF cur IS DISTINCT FROM r.new_v THEN
        RAISE EXCEPTION '1296: % writer_timeout_seconds update did not take (expected %, found %)', r.asset_id, r.new_v, cur;
      END IF;
    END IF;
  END LOOP;
END
$m1296$;
