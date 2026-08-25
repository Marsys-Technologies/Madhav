-- Migration 605: correct the bg_sky_calendar floor provenance.
--
-- The original 31,064 floor was measured on 2026-07-29 in a local process
-- where the required Swiss Ephemeris .se1 corpus was absent. pyswisseph
-- silently served its Moshier analytic fallback, while the registry text
-- incorrectly described the result as a production-equivalent build and
-- asserted that a later build could never contain fewer rows.
--
-- The authoritative production build is one file-backed Linux/x86_64 run from
-- 2026-08-02: 28,755 ingress + 1,674 station + 308 solar eclipse + 312 lunar
-- eclipse + 10 double-transit rows = 31,059. The writer now rejects a missing
-- file corpus, a Moshier fallback, an unpinned write runtime, and changed file
-- digests before scanning. This migration changes metadata only; it neither
-- rewrites nor fabricates sky-calendar rows.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

DO $$
DECLARE
  registry_row asset_registry%ROWTYPE;
  changed_rows INTEGER := 0;
  legacy_explanation CONSTANT TEXT :=
    'Live-verified 2026-07-29 against a real throwaway Postgres: 28,760 ingress + 1,674 station + 308 eclipse_solar + 312 eclipse_lunar + 10 double_transit = 31,064, over horizon 1900-01-01 -> 2036-07-29 (today+10y at verification time). A later build reads >= this count as the forward edge rolls forward (never less).';
  corrected_explanation CONSTANT TEXT :=
    '31,059 achieved rows in the authoritative 2026-08-02 production build using the pinned Swiss Ephemeris file corpus on Linux/x86_64: 28,755 ingress + 1,674 station + 308 eclipse_solar + 312 eclipse_lunar + 10 double_transit. This is an achieved baseline, not a forecast; explicit rolling-horizon rebuilds may increase it.';
BEGIN
  SELECT * INTO registry_row
  FROM asset_registry
  WHERE asset_id = 'bg_sky_calendar'
  FOR UPDATE;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'migration 605 requires bg_sky_calendar registry row';
  END IF;

  IF (
    registry_row.target_table = 'bg_sky_calendar'
    AND registry_row.count_sql = 'SELECT COUNT(*) FROM bg_sky_calendar'
    AND registry_row.size_sql = 'SELECT pg_total_relation_size(''bg_sky_calendar'')'
    AND registry_row.is_active IS TRUE
    AND registry_row.has_writer IS TRUE
    AND registry_row.catalog_status = 'CURRENT'
    AND registry_row.asset_kind = 'data'
    AND (
      (
        registry_row.target_floor = 31064
        AND registry_row.volume_explanation = legacy_explanation
      ) OR (
        registry_row.target_floor = 31059
        AND registry_row.volume_explanation = corrected_explanation
      )
    )
  ) IS NOT TRUE THEN
    RAISE EXCEPTION 'migration 605 refuses unknown bg_sky_calendar registry contract';
  END IF;

  UPDATE asset_registry
  SET target_floor = 31059,
      volume_explanation = corrected_explanation
  WHERE asset_id = 'bg_sky_calendar';
  GET DIAGNOSTICS changed_rows = ROW_COUNT;

  IF changed_rows <> 1 THEN
    RAISE EXCEPTION 'migration 605 expected to update one registry row, updated %',
      changed_rows;
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM asset_registry
    WHERE asset_id = 'bg_sky_calendar'
      AND target_table = 'bg_sky_calendar'
      AND count_sql = 'SELECT COUNT(*) FROM bg_sky_calendar'
      AND size_sql = 'SELECT pg_total_relation_size(''bg_sky_calendar'')'
      AND target_floor = 31059
      AND volume_explanation = corrected_explanation
      AND is_active IS TRUE
      AND has_writer IS TRUE
      AND catalog_status = 'CURRENT'
      AND asset_kind = 'data'
  ) THEN
    RAISE EXCEPTION 'migration 605 failed bg_sky_calendar registry postflight';
  END IF;
END $$;
