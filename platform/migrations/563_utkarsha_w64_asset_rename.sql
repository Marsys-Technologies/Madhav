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
  --     referrers to be removed before their referent).
  IF EXISTS (
    SELECT 1 FROM information_schema.tables
     WHERE table_schema = 'public' AND table_name = 'asset_coefficients'
  ) THEN
    DELETE FROM asset_coefficients WHERE asset_id = 'ka_gochara';
  END IF;

  -- 1. Delete the zero-row self-test service (ka_gochara global scope).
  --    The renamed ka_gochara_v2_materialize takes the ka_gochara asset_id.
  --    FK referrers were cleaned in steps 0a/0b above.
  DELETE FROM asset_registry WHERE asset_id = 'ka_gochara' AND scope = 'global';

  -- 2. Rename ka_gochara_v2_materialize → ka_gochara (per_chart scope, real materializer).
  --    Only if it hasn't already been renamed.
  IF EXISTS (SELECT 1 FROM asset_registry WHERE asset_id = 'ka_gochara_v2_materialize') THEN
    UPDATE asset_registry
    SET asset_id = 'ka_gochara',
        english_name = 'Gochara V3 Per-Chart Materializer',
        english_description = 'Primary per-chart gochara window materializer (GOCHARA-UTKARSA). Writes kala_gochara_windows_v2 (staging surface). Renamed from ka_gochara_v2_materialize at W6.4 cutover (UTK-R2).'
    WHERE asset_id = 'ka_gochara_v2_materialize';
  END IF;

  -- 3. Mark ka_gochara_sweep as RETIRED (data + protection remain; catalog status change only).
  UPDATE asset_registry
  SET catalog_status = 'RETIRED',
      is_active = false
  WHERE asset_id = 'ka_gochara_sweep';

END $$;
