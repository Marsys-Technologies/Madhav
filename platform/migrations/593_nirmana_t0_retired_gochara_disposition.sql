-- 593_nirmana_t0_retired_gochara_disposition.sql
--
-- NIRMĀṆA ELEVATION v6 — T0 catalogue reconciliation.
--
-- Applied file 563 retired ka_gochara_sweep after ka_gochara became the serving
-- authority, but the lifecycle fields introduced by applied migration 590 were
-- deliberately left NULL pending a ruling. T0 now has the evidence needed to
-- make that disposition explicit:
--   * ka_gochara_sweep is RETIRED and inactive;
--   * ka_gochara is CURRENT, active, and serves generation='3.0' from the same
--     kala_gochara_windows table;
--   * generation='v1' rows remain live historical capital and must not be
--     rebuilt by the retired writer.
--
-- This migration changes catalogue metadata only. It does not delete, rewrite,
-- protect, or rebuild any kala_gochara_windows rows.
--
-- IDEMPOTENT: an exact retry is a no-op; a conflicting pre-existing lifecycle
-- declaration fails before mutation.
-- REVERSIBLE: set superseded_by and data_disposition back to NULL for this one
-- asset only. The retained data is never changed by either direction.

BEGIN;

DO $$
DECLARE
  sweep_status text;
  sweep_active boolean;
  successor_status text;
  successor_active boolean;
  existing_successor text;
  existing_disposition text;
BEGIN
  SELECT catalog_status, is_active, superseded_by, data_disposition
    INTO sweep_status, sweep_active, existing_successor, existing_disposition
    FROM asset_registry
   WHERE asset_id = 'ka_gochara_sweep';

  IF NOT FOUND THEN
    RAISE EXCEPTION 'migration 593 requires asset_registry.ka_gochara_sweep';
  END IF;

  SELECT catalog_status, is_active
    INTO successor_status, successor_active
    FROM asset_registry
   WHERE asset_id = 'ka_gochara';

  IF NOT FOUND THEN
    RAISE EXCEPTION 'migration 593 requires successor asset_registry.ka_gochara';
  END IF;

  IF sweep_status <> 'RETIRED' OR sweep_active IS DISTINCT FROM false THEN
    RAISE EXCEPTION
      'migration 593 refuses non-retired sweep state: status=%, is_active=%',
      sweep_status, sweep_active;
  END IF;

  IF successor_status <> 'CURRENT' OR successor_active IS DISTINCT FROM true THEN
    RAISE EXCEPTION
      'migration 593 refuses non-current successor state: status=%, is_active=%',
      successor_status, successor_active;
  END IF;

  IF existing_successor IS NOT NULL
     AND existing_successor <> 'ka_gochara' THEN
    RAISE EXCEPTION
      'migration 593 refuses conflicting successor declaration: %',
      existing_successor;
  END IF;

  IF existing_disposition IS NOT NULL
     AND existing_disposition <> 'RETAINED_AS_CAPITAL' THEN
    RAISE EXCEPTION
      'migration 593 refuses conflicting data disposition: %',
      existing_disposition;
  END IF;
END $$;

UPDATE asset_registry
   SET superseded_by = 'ka_gochara',
       data_disposition = 'RETAINED_AS_CAPITAL'
 WHERE asset_id = 'ka_gochara_sweep'
   AND (superseded_by IS NULL OR data_disposition IS NULL);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
      FROM asset_registry
     WHERE asset_id = 'ka_gochara_sweep'
       AND catalog_status = 'RETIRED'
       AND is_active = false
       AND superseded_by = 'ka_gochara'
       AND data_disposition = 'RETAINED_AS_CAPITAL'
  ) THEN
    RAISE EXCEPTION 'migration 593 failed to record the retired sweep disposition';
  END IF;
END $$;

COMMIT;
