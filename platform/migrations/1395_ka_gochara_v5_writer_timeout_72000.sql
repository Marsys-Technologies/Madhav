-- 1395_ka_gochara_v5_writer_timeout_72000.sql
--
-- J-3c cap (owner surrogate SR-J3-CAP-LIVE): raise asset_registry.writer_timeout_seconds for ka_gochara_v5 from 28,800 s (8 h) to 72,000 s (20 h).
-- Data-only: ONE column of ONE asset_registry row, no DDL, no new object. Transaction ownership belongs to platform/scripts/migrate.ts
-- (no BEGIN/COMMIT here). Same pattern as migrations 1218, 1296 and 1329.
--
-- WHY. The measuring build (run shape all_classes_full of ka_gochara_v5, MEASURING_BUILD_CONTRACT_v1_0.md) is projected at 34,593 s, which is
-- over the 28,800 s watchdog that migration 1304 set. The orchestrator watchdog (runner.py execute_dag, JL-023) reads this registry value per
-- asset dispatch as wall-clock for the whole asset, and the registry value wins over the job's WRITER_TIMEOUT_SECONDS. 72,000 s leaves
-- about 2x headroom over the projection. The pipeline Cloud Run job (brahma-build-pipeline-job) deploys with --task-timeout=86400, which is
-- above 72,000, so no platform change is needed (checked by the cockpit; deploy.yml is untouched).
--
-- GUARD (never a silent no-op). The row is read FOR UPDATE under the lock_timeout below. The migration changes the row ONLY when it is exactly the
-- shape migration 1304 left: the row exists AND writer_timeout_seconds = 28800. A missing row, a NULL, 72000 already, or any other value
-- RAISES by name and changes nothing. After the UPDATE:
--   * ROW_COUNT must be exactly 1;
--   * the row re-read must show 72000;
--   * the whole row minus writer_timeout_seconds must be identical to what was read before (is_active, has_writer, has_substeps, depends_on and
--     every other column, including any column added later);
--   * no OTHER asset_registry row version may have been written by this transaction (xmin check, the 1304 pattern).
--
-- NO TRIGGER EFFECT. nirmana_registry_receipt_invalidation fires only AFTER UPDATE OF depends_on, natural_key_partition, health_probe,
-- integrity_check_sql, target_floor, asset_kind, asset_type, scope, has_writer, is_active, target_table (see migration 1329's note); writer_timeout_seconds
-- is not among them, so no asset_freshness row goes stale.
--
-- NOT PROTECTED. A plain UPDATE: no public-schema DDL, so it is in neither PROTECTED_PUBLIC_SCHEMA_MIGRATIONS nor PROTECTED_DATA_PLANE_MIGRATIONS and not in
-- kala_protected_migrations.txt (the Kala window selects public-schema DDL only). The routine deploy-time runner applies it.
--
-- AFTER 1395: migration 1304 would refuse a replay on this row (its guard accepts only the 1243 or the 1304 shape, timeout 600 or 28800). That is
-- intended: the ledger applies each migration once, and a replay must never walk the cap back down.
--
-- Seed: platform/scripts/seed/asset_registry_seed.ts carries writer_timeout_seconds: 72000 for ka_gochara_v5 (its ON CONFLICT preserves live values).
--
-- Post-apply verification (read-only):
--   SELECT asset_id, writer_timeout_seconds, is_active, has_writer, has_substeps, depends_on FROM asset_registry WHERE asset_id = 'ka_gochara_v5';
--     -- expect 72000 | f | t | t | {ga_positions,ga_dashas}
--   Fingerprint of the row (the same 28-column md5 platform/scripts/gochara-window-readbacks.sh uses for the 1243 pin), computed in the guarded local
--   fixture by replaying the real 1243, 1304 and 1395 over the baseline registry DDL (the 1243 step reproduces the pinned 49995b52b7c416c8e0ef8f43b1158b57):
--     after 1243 49995b52b7c416c8e0ef8f43b1158b57 | after 1304 89814fffd6e1aec8d5de63d5007e87d3 | after 1395 8339e7adcbc90d0c62f50c4e62815b33
--   SELECT md5(row(asset_id, layer, sort_order, sanskrit_name, english_name, english_description, storage_type, target_table, count_sql, size_sql,
--     target_floor, expected_volume_formula, expected_volume_inputs, volume_explanation, depends_on, scope, is_active, estimated_seconds, asset_type, layer_name,
--     layer_index, provides_apis, health_probe, catalog_status, asset_kind, has_writer, has_substeps, writer_timeout_seconds)::text)
--     FROM asset_registry WHERE asset_id = 'ka_gochara_v5';   -- expect 8339e7adcbc90d0c62f50c4e62815b33
--
-- ROLLBACK (not executed by migrate.ts):
--   UPDATE asset_registry SET writer_timeout_seconds = 28800 WHERE asset_id = 'ka_gochara_v5' AND writer_timeout_seconds = 72000;

SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '60s';

DO $m1395$
DECLARE
  v_before  jsonb;
  v_after   jsonb;
  v_cur     integer;
  v_changed integer;
  v_other   integer;
BEGIN
  SELECT to_jsonb(r) INTO v_before
    FROM asset_registry r
   WHERE r.asset_id = 'ka_gochara_v5'
     FOR UPDATE;
  IF v_before IS NULL THEN
    RAISE EXCEPTION '1395: ka_gochara_v5 has no asset_registry row; nothing was changed';
  END IF;

  v_cur := (v_before ->> 'writer_timeout_seconds')::integer;
  IF v_cur IS DISTINCT FROM 28800 THEN
    RAISE EXCEPTION '1395: refusing to change ka_gochara_v5: writer_timeout_seconds is % (expected exactly 28800, the migration-1304 value); nothing was changed', coalesce(v_cur::text, 'NULL');
  END IF;

  UPDATE asset_registry
     SET writer_timeout_seconds = 72000
   WHERE asset_id = 'ka_gochara_v5'
     AND writer_timeout_seconds = 28800;

  GET DIAGNOSTICS v_changed = ROW_COUNT;
  IF v_changed <> 1 THEN
    RAISE EXCEPTION '1395: expected to update exactly one asset_registry row (ka_gochara_v5), updated %', v_changed;
  END IF;

  SELECT to_jsonb(r) INTO v_after FROM asset_registry r WHERE r.asset_id = 'ka_gochara_v5';
  IF (v_after ->> 'writer_timeout_seconds') IS DISTINCT FROM '72000' THEN
    RAISE EXCEPTION '1395: ka_gochara_v5 writer_timeout_seconds update did not take (expected 72000, found %)', coalesce(v_after ->> 'writer_timeout_seconds', 'NULL');
  END IF;
  IF (v_after - 'writer_timeout_seconds') IS DISTINCT FROM (v_before - 'writer_timeout_seconds') THEN
    RAISE EXCEPTION '1395: a column other than writer_timeout_seconds changed on ka_gochara_v5; the migration must touch ONLY that column';
  END IF;

  -- Supplementary check of visible tuple versions: no OTHER asset_registry row version was written by this transaction.
  SELECT count(*) INTO v_other
    FROM asset_registry
   WHERE xmin = pg_current_xact_id()::xid
     AND asset_id <> 'ka_gochara_v5';
  IF v_other <> 0 THEN
    RAISE EXCEPTION '1395: % other asset_registry row version(s) were written by this transaction; the migration must touch ONLY ka_gochara_v5', v_other;
  END IF;
END
$m1395$;
