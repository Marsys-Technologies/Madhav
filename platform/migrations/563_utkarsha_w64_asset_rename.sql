-- 563_utkarsha_w64_asset_rename.sql
-- GOCHARA-UTKARSA W6.4 (UTK-R2): Retire ka_gochara self-test, rename ka_gochara_v2_materialize → ka_gochara,
-- mark ka_gochara_sweep as RETIRED.
--
-- PARIṢKĀRA MR-05 fix (2026-08-10): original migration could not apply because
-- asset_throughput held a FK-referencing row (asset_id='ka_gochara', chart_id IS NULL,
-- the global-scope self-test row) that blocked the asset_registry DELETE with
-- error 23503 (foreign key violation). FK referrer cleanup is now added BEFORE
-- the asset_registry DELETE, making the migration appliable. The cleanup is
-- scoped exactly to the global-scope self-test rows that the original W6.4
-- work seeded: (asset_id='ka_gochara' AND chart_id IS NULL). Per-chart rows
-- (chart_id IS NOT NULL) are intentionally not touched — they belong to the
-- renamed materializer and should survive.
--
-- Also cleaned: asset_coefficients, if any rows exist for 'ka_gochara'.
-- Both deletes are safe to re-run (no-op when already clean).
--
-- PARIṢKĀRA fix #2 (2026-08-10, found by EXECUTING this migration against a
-- production-shaped throwaway DB, not by prose review — the class of defect
-- a review already missed once on this same file): step 2's rename was a
-- bare `UPDATE asset_registry SET asset_id = 'ka_gochara' WHERE asset_id =
-- 'ka_gochara_v2_materialize'`. asset_registry.asset_id is referenced by
-- non-deferrable FKs from asset_throughput.asset_id and
-- asset_coefficients.{upstream,downstream}_asset_id (confirmed the complete
-- set live via pg_constraint — only these two tables FK-reference
-- asset_registry(asset_id)). Production currently holds 2 live
-- asset_throughput rows for 'ka_gochara_v2_materialize' (charts 482012f1 and
-- 1c826d5a), so the bare UPDATE fails with FK 23503 the instant it runs — a
-- real failure this migration would have hit in production too. Fixed by
-- repointing every FK-referencing child row to the new asset_id BEFORE
-- dropping the old asset_registry row, instead of renaming the PK value in
-- place (see step 2 below).
--
-- Idempotent: safe to run multiple times.

DO $$
BEGIN
  -- 0a. PARIṢKĀRA MR-05: clean FK referrers in asset_throughput for the
  --     global-scope 'ka_gochara' self-test row BEFORE deleting asset_registry.
  --     This is the row that caused FK-23503 on the original migration. Scoped
  --     tightly: only chart_id IS NULL (global-scope self-test), only asset_id
  --     'ka_gochara'. Per-chart rows survive for the renamed materializer.
  DELETE FROM asset_throughput
   WHERE asset_id = 'ka_gochara' AND chart_id IS NULL;

  -- 0b. PARIṢKĀRA MR-05: clean any asset_coefficients rows for 'ka_gochara'
  --     (safe no-op if none exist; FK constraint on asset_registry requires
  --     referrers to be removed before their referent). asset_coefficients has
  --     no plain asset_id column -- it FK-references asset_registry via
  --     upstream_asset_id/downstream_asset_id (verified live 2026-08-10, the
  --     bug this fixes: the prior version of this block used `asset_id`,
  --     which doesn't exist on this table, and failed the live deploy).
  IF EXISTS (
    SELECT 1 FROM information_schema.tables
     WHERE table_schema = 'public' AND table_name = 'asset_coefficients'
  ) THEN
    DELETE FROM asset_coefficients
     WHERE upstream_asset_id = 'ka_gochara' OR downstream_asset_id = 'ka_gochara';
  END IF;

  -- 1. Delete the zero-row self-test service (ka_gochara global scope).
  --    The renamed ka_gochara_v2_materialize takes the ka_gochara asset_id.
  --    FK referrers were cleaned in steps 0a/0b above.
  DELETE FROM asset_registry WHERE asset_id = 'ka_gochara' AND scope = 'global';

  -- 2. Rename ka_gochara_v2_materialize → ka_gochara (per_chart scope, real materializer).
  --    Only if it hasn't already been renamed. Can't rename the PK value in place
  --    while FK-referencing rows exist (asset_throughput.asset_id,
  --    asset_coefficients.{upstream,downstream}_asset_id — both non-deferrable).
  --    Pattern: insert the new row (copy of the old, fields overridden), repoint
  --    every referencing child to the new asset_id, then drop the old row —
  --    each step individually FK-safe, unlike a bare UPDATE of the PK column.
  IF EXISTS (SELECT 1 FROM asset_registry WHERE asset_id = 'ka_gochara_v2_materialize') THEN

    -- 2a. Insert 'ka_gochara' as a copy of 'ka_gochara_v2_materialize' with the
    --     renamed identity fields, only if not already inserted (idempotency).
    IF NOT EXISTS (SELECT 1 FROM asset_registry WHERE asset_id = 'ka_gochara') THEN
      INSERT INTO asset_registry (
        asset_id, layer, sort_order, sanskrit_name, english_name, english_description,
        storage_type, target_table, count_sql, size_sql, target_floor,
        expected_volume_formula, expected_volume_inputs, volume_explanation, depends_on,
        scope, is_active, estimated_seconds, clear_tables, asset_type,
        layer_name, layer_index, provides_apis, health_probe, catalog_status,
        rebuild_on_probe_fail, integrity_check_sql, has_substeps, asset_kind,
        service_health, last_invoked_at, last_selftest_at, selftest_detail,
        has_writer, writer_timeout_seconds
      )
      SELECT
        'ka_gochara', layer, sort_order, sanskrit_name,
        'Gochara V3 Per-Chart Materializer',
        'Primary per-chart gochara window materializer (GOCHARA-UTKARSA). Writes kala_gochara_windows_v2 (staging surface). Renamed from ka_gochara_v2_materialize at W6.4 cutover (UTK-R2).',
        storage_type, target_table, count_sql, size_sql, target_floor,
        expected_volume_formula, expected_volume_inputs, volume_explanation, depends_on,
        scope, is_active, estimated_seconds, clear_tables, asset_type,
        layer_name, layer_index, provides_apis, health_probe, catalog_status,
        rebuild_on_probe_fail, integrity_check_sql, has_substeps, asset_kind,
        service_health, last_invoked_at, last_selftest_at, selftest_detail,
        has_writer, writer_timeout_seconds
      FROM asset_registry
      WHERE asset_id = 'ka_gochara_v2_materialize';
    END IF;

    -- 2b. Repoint every FK-referencing child row from the old asset_id to the new one.
    UPDATE asset_throughput
       SET asset_id = 'ka_gochara'
     WHERE asset_id = 'ka_gochara_v2_materialize';

    UPDATE asset_coefficients
       SET upstream_asset_id = 'ka_gochara'
     WHERE upstream_asset_id = 'ka_gochara_v2_materialize';

    UPDATE asset_coefficients
       SET downstream_asset_id = 'ka_gochara'
     WHERE downstream_asset_id = 'ka_gochara_v2_materialize';

    -- 2c. Now safe to drop the old row — no more referrers.
    DELETE FROM asset_registry WHERE asset_id = 'ka_gochara_v2_materialize';
  END IF;

  -- 3. Mark ka_gochara_sweep as RETIRED (data + protection remain; catalog status change only).
  UPDATE asset_registry
  SET catalog_status = 'RETIRED',
      is_active = false
  WHERE asset_id = 'ka_gochara_sweep';

END $$;
