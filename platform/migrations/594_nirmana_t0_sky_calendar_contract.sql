-- 594_nirmana_t0_sky_calendar_contract.sql
--
-- NIRMĀṆA ELEVATION v6 — T0 output-contract reconciliation.
--
-- Applied migration 561 renamed the physical table from bg_sky_events to
-- bg_sky_calendar and corrected count_sql, but target_table, size_sql, the
-- seed catalogue, and the writer INSERT target retained the old name. The
-- result is a live registry contract that points target_table at a missing
-- relation and a writer that cannot write the canonical table.
--
-- The source changes accompanying this forward migration update the writer and
-- seed. This migration repairs the live catalogue metadata only; it does not
-- rename, delete, rebuild, or mutate any sky-calendar rows.
--
-- IDEMPOTENT: exact canonical values are re-asserted.
-- REVERSIBLE: restore the three registry strings to bg_sky_events only if the
-- physical table and writer are also deliberately renamed back.

BEGIN;

DO $$
BEGIN
  IF to_regclass('public.bg_sky_calendar') IS NULL THEN
    RAISE EXCEPTION 'migration 594 requires public.bg_sky_calendar';
  END IF;

  IF NOT EXISTS (
    SELECT 1
      FROM asset_registry
     WHERE asset_id = 'bg_sky_calendar'
       AND catalog_status = 'CURRENT'
       AND is_active = true
       AND has_writer = true
  ) THEN
    RAISE EXCEPTION 'migration 594 requires the active bg_sky_calendar registry asset';
  END IF;
END $$;

UPDATE asset_registry
   SET target_table = 'bg_sky_calendar',
       count_sql = 'SELECT COUNT(*) FROM bg_sky_calendar',
       size_sql = 'SELECT pg_total_relation_size(''bg_sky_calendar'')'
 WHERE asset_id = 'bg_sky_calendar';

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
      FROM asset_registry
     WHERE asset_id = 'bg_sky_calendar'
       AND target_table = 'bg_sky_calendar'
       AND count_sql = 'SELECT COUNT(*) FROM bg_sky_calendar'
       AND size_sql = 'SELECT pg_total_relation_size(''bg_sky_calendar'')'
       AND to_regclass(target_table) = 'bg_sky_calendar'::regclass
  ) THEN
    RAISE EXCEPTION 'migration 594 failed to repair the sky-calendar registry contract';
  END IF;
END $$;

COMMIT;
