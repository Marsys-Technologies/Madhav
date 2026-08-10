-- 563_utkarsha_w64_asset_rename.sql
-- GOCHARA-UTKARSA W6.4 (UTK-R2): Retire ka_gochara self-test, rename ka_gochara_v2_materialize → ka_gochara,
-- mark ka_gochara_sweep as RETIRED.
--
-- Idempotent: safe to run multiple times.

DO $$
BEGIN
  -- 1. Delete the zero-row self-test service (ka_gochara global scope).
  --    The renamed ka_gochara_v2_materialize takes the ka_gochara asset_id.
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
