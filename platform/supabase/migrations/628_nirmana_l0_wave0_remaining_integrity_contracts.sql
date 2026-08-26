-- Migration 628: close the remaining reviewed L0 wave-0 integrity contracts.
--
-- Sky Calendar and Muhurta Lattice are rolling corpora, so their registry
-- checks pin structural invariants, complete producer-family coverage, and
-- freshness while the separately reviewed output-digest specification binds
-- the exact accepted rows. Vidhi Primitives is static and therefore also pins
-- the exact canonical 60-row semantic digest.
--
-- This changes registry metadata only. A governed rebuild and accepted output
-- receipt remain necessary before any data can be called converged.
-- Transaction ownership belongs to platform/scripts/migrate.ts.

DO $$
DECLARE
  registry_row asset_registry%ROWTYPE;
  changed_rows integer := 0;
  sky_partition constant text :=
    'event_type,primary_body,secondary_body_key,event_jd';
  vidhi_partition constant text := 'primitive_id';
  muhurta_partition constant text :=
    'factor_family,factor_key,start_utc';
  sky_spec constant jsonb := $spec${"components":[{"key_columns":["event_type","primary_body","secondary_body_key","event_jd"],"name":"bg_sky_calendar","relation":"bg_sky_calendar","value_columns":["event_type","primary_body","secondary_body","secondary_body_key","event_jd","event_datetime_utc","sign","nakshatra","longitude_deg","speed_dps","detail","ayanamsha_key","sampling_method","source_citation"]}],"version":"nirmana-output-digest-spec-v1"}$spec$::jsonb;
  vidhi_spec constant jsonb := $spec${"components":[{"key_columns":["primitive_id"],"name":"vidhi_primitives","relation":"vidhi_primitives","value_columns":["primitive_id","version","definition","category","live_tool","tool_args","fallback_face","known_gap","mandatory_tags","cr27_prevents"]}],"version":"nirmana-output-digest-spec-v1"}$spec$::jsonb;
  muhurta_spec constant jsonb := $spec${"components":[{"key_columns":["factor_family","factor_key","start_utc"],"name":"bg_muhurta_lattice","relation":"bg_muhurta_lattice","value_columns":["factor_family","factor_key","start_utc","end_utc","detail","reference_lat","reference_lon","reference_tz_offset_minutes","reference_location_key","ayanamsha_key","sampling_method","source_citation","corpus_status"]}],"version":"nirmana-output-digest-spec-v1"}$spec$::jsonb;
  sky_check constant text := $check$
SELECT
  (SELECT count(*) >= 31059 FROM bg_sky_calendar)
  AND (SELECT array_agg(DISTINCT event_type ORDER BY event_type) =
      ARRAY['double_transit','eclipse_lunar','eclipse_solar','ingress','station']::text[]
    FROM bg_sky_calendar)
  AND (SELECT count(*) FILTER (WHERE event_type = 'ingress') >= 28755
       AND count(*) FILTER (WHERE event_type = 'station') >= 1674
       AND count(*) FILTER (WHERE event_type = 'eclipse_solar') >= 308
       AND count(*) FILTER (WHERE event_type = 'eclipse_lunar') >= 312
       AND count(*) FILTER (WHERE event_type = 'double_transit') >= 10
    FROM bg_sky_calendar)
  AND NOT EXISTS (
    SELECT 1 FROM bg_sky_calendar
    GROUP BY event_type,primary_body,secondary_body_key,event_jd
    HAVING count(*) <> 1)
  AND NOT EXISTS (
    SELECT 1 FROM bg_sky_calendar
    WHERE primary_body = '' OR secondary_body_key = ''
      OR event_datetime_utc IS NULL OR event_jd IS NULL
      OR ayanamsha_key <> 'lahiri'
      OR sampling_method <> 'sky_calendar_ingress_station_eclipse_doubletransit_v1'
      OR source_citation <>
        'pyswisseph DE441 (Swiss Ephemeris) via pipeline.transit_search + sol_eclipse_when_glob/lun_eclipse_when; Lahiri ayanamsha')
  AND (SELECT min(event_datetime_utc) < TIMESTAMP '1900-02-01'
       AND max(event_datetime_utc) >= CURRENT_DATE + INTERVAL '9 years'
    FROM bg_sky_calendar)
$check$;
  vidhi_check constant text := $check$
SELECT
  (SELECT count(*) = 60 FROM vidhi_primitives)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(
      primitive_id,version,definition,category,live_tool,tool_args,
      fallback_face,known_gap,mandatory_tags,cr27_prevents
    )::text,E'\n' ORDER BY primitive_id COLLATE "C"),''),'UTF8')),'hex') =
    '41463a2be208bc33c645cc943a242a2cd5b4906e8babd3dc68fe5ef566738cce'
   FROM vidhi_primitives)
$check$;
  muhurta_check constant text := $check$
SELECT
  (SELECT count(*) >= 91477 FROM bg_muhurta_lattice)
  AND (SELECT array_agg(DISTINCT factor_family ORDER BY factor_family) =
      ARRAY['agnivasa','combination_yoga','ghati_muhurta','kalam']::text[]
    FROM bg_muhurta_lattice)
  AND (SELECT count(*) FILTER (WHERE factor_family = 'agnivasa') >= 1826
       AND count(*) FILTER (WHERE factor_family = 'combination_yoga') >= 1481
       AND count(*) FILTER (WHERE factor_family = 'kalam') >= 33390
       AND count(*) FILTER (WHERE factor_family = 'ghati_muhurta') >= 54780
    FROM bg_muhurta_lattice)
  AND NOT EXISTS (
    SELECT 1 FROM bg_muhurta_lattice
    GROUP BY factor_family,factor_key,start_utc
    HAVING count(*) <> 1)
  AND NOT EXISTS (
    SELECT 1 FROM bg_muhurta_lattice
    WHERE factor_key = '' OR end_utc <= start_utc
      OR reference_lat <> 20.27 OR reference_lon <> 85.84
      OR reference_tz_offset_minutes <> 330
      OR reference_location_key <> 'bhubaneswar'
      OR ayanamsha_key <> 'lahiri'
      OR sampling_method <> 'muhurta_lattice_agnivasa_yoga_kalam_ghati_v1'
      OR source_citation = ''
      OR corpus_status NOT IN ('computed_cited','computed_uncited_convention'))
  AND (SELECT max(end_utc) >= CURRENT_DATE + INTERVAL '4 years'
    FROM bg_muhurta_lattice)
$check$;
BEGIN
  -- An exact active digest specification is part of each live contract. A
  -- missing, retired, or substituted specification must fail before mutation.
  IF (SELECT count(*) FROM asset_output_digest_specs
      WHERE retired_at IS NULL
        AND ((asset_id = 'bg_sky_calendar'
          AND spec_sha256 = 'd806c806b7d22231c1266ec8f0f11d84325daaeff03418d418dc460a4074c75c'
          AND spec = sky_spec)
        OR (asset_id = 'bg_vidhi_primitives'
          AND spec_sha256 = '179ab2c22fad87f5f3c21475e3ddc5151eaf5fd88ea1c05cea0a6d73b845804f'
          AND spec = vidhi_spec)
        OR (asset_id = 'bg_muhurta_lattice'
          AND spec_sha256 = 'dd96913547048da000efbd94cfc106a9f90fe15b14b2def68aba9f45b4e4db98'
          AND spec = muhurta_spec))) <> 3 THEN
    RAISE EXCEPTION 'migration 628 refuses unknown output digest contract';
  END IF;

  SELECT * INTO registry_row FROM asset_registry
  WHERE asset_id = 'bg_sky_calendar' FOR UPDATE;
  IF NOT FOUND OR (
    registry_row.layer = 'brahmagyan'
    AND registry_row.sort_order = 69
    AND registry_row.scope = 'global'
    AND registry_row.asset_kind = 'data'
    AND registry_row.catalog_status = 'CURRENT'
    AND registry_row.is_active IS TRUE
    AND registry_row.has_writer IS TRUE
    AND registry_row.target_table = 'bg_sky_calendar'
    AND registry_row.count_sql = 'SELECT COUNT(*) FROM bg_sky_calendar'
    AND registry_row.target_floor = 31059
    AND registry_row.depends_on = ARRAY[]::text[]
    AND registry_row.data_disposition IS NULL
    AND (registry_row.natural_key_partition IS NULL
      OR registry_row.natural_key_partition = sky_partition)
    AND (registry_row.integrity_check_sql IS NULL
      OR registry_row.integrity_check_sql = sky_check)
  ) IS NOT TRUE THEN
    RAISE EXCEPTION 'migration 628 refuses unknown bg_sky_calendar registry contract';
  END IF;

  SELECT * INTO registry_row FROM asset_registry
  WHERE asset_id = 'bg_vidhi_primitives' FOR UPDATE;
  IF NOT FOUND OR (
    registry_row.layer = 'brahmagyan'
    AND registry_row.sort_order = 68
    AND registry_row.scope = 'global'
    AND registry_row.asset_kind = 'data'
    AND registry_row.catalog_status IN ('DRAFT','CURRENT')
    AND registry_row.is_active IS TRUE
    AND registry_row.has_writer IS TRUE
    AND registry_row.target_table = 'vidhi_primitives'
    AND registry_row.count_sql = '(SELECT COUNT(*) FROM vidhi_primitives)'
    AND registry_row.target_floor = 60
    AND registry_row.depends_on = ARRAY[]::text[]
    AND registry_row.data_disposition IS NULL
    AND (registry_row.natural_key_partition IS NULL
      OR registry_row.natural_key_partition = vidhi_partition)
    AND (registry_row.integrity_check_sql IS NULL
      OR registry_row.integrity_check_sql = vidhi_check)
  ) IS NOT TRUE THEN
    RAISE EXCEPTION 'migration 628 refuses unknown bg_vidhi_primitives registry contract';
  END IF;

  SELECT * INTO registry_row FROM asset_registry
  WHERE asset_id = 'bg_muhurta_lattice' FOR UPDATE;
  IF NOT FOUND OR (
    registry_row.layer = 'brahmagyan'
    AND registry_row.sort_order = 70
    AND registry_row.scope = 'global'
    AND registry_row.asset_kind = 'data'
    AND registry_row.catalog_status = 'CURRENT'
    AND registry_row.is_active IS TRUE
    AND registry_row.has_writer IS TRUE
    AND registry_row.target_table = 'bg_muhurta_lattice'
    AND registry_row.count_sql = 'SELECT COUNT(*) FROM bg_muhurta_lattice'
    AND registry_row.target_floor = 91477
    AND registry_row.depends_on = ARRAY[]::text[]
    AND registry_row.data_disposition IS NULL
    AND (registry_row.natural_key_partition IS NULL
      OR registry_row.natural_key_partition = muhurta_partition)
    AND (registry_row.integrity_check_sql IS NULL
      OR registry_row.integrity_check_sql = muhurta_check)
  ) IS NOT TRUE THEN
    RAISE EXCEPTION 'migration 628 refuses unknown bg_muhurta_lattice registry contract';
  END IF;

  UPDATE asset_registry
  SET catalog_status = CASE WHEN asset_id = 'bg_vidhi_primitives'
        THEN 'CURRENT' ELSE catalog_status END,
      natural_key_partition = CASE asset_id
        WHEN 'bg_sky_calendar' THEN sky_partition
        WHEN 'bg_vidhi_primitives' THEN vidhi_partition
        WHEN 'bg_muhurta_lattice' THEN muhurta_partition END,
      integrity_check_sql = CASE asset_id
        WHEN 'bg_sky_calendar' THEN sky_check
        WHEN 'bg_vidhi_primitives' THEN vidhi_check
        WHEN 'bg_muhurta_lattice' THEN muhurta_check END
  WHERE asset_id IN ('bg_sky_calendar','bg_vidhi_primitives','bg_muhurta_lattice');

  GET DIAGNOSTICS changed_rows = ROW_COUNT;
  IF changed_rows <> 3 THEN
    RAISE EXCEPTION 'migration 628 expected 3 rows, updated %', changed_rows;
  END IF;

  IF (SELECT count(*) FROM asset_registry
      WHERE (asset_id = 'bg_sky_calendar'
        AND catalog_status = 'CURRENT'
        AND natural_key_partition = sky_partition
        AND integrity_check_sql = sky_check)
         OR (asset_id = 'bg_vidhi_primitives'
        AND catalog_status = 'CURRENT'
        AND natural_key_partition = vidhi_partition
        AND integrity_check_sql = vidhi_check)
         OR (asset_id = 'bg_muhurta_lattice'
        AND catalog_status = 'CURRENT'
        AND natural_key_partition = muhurta_partition
        AND integrity_check_sql = muhurta_check)) <> 3 THEN
    RAISE EXCEPTION 'migration 628 postflight registry mismatch';
  END IF;

  -- Recheck the reviewed JSONB itself after mutation as well as before it. The
  -- SHA column is evidence metadata, not a database-computed constraint.
  IF (SELECT count(*) FROM asset_output_digest_specs
      WHERE retired_at IS NULL
        AND ((asset_id = 'bg_sky_calendar'
          AND spec_sha256 = 'd806c806b7d22231c1266ec8f0f11d84325daaeff03418d418dc460a4074c75c'
          AND spec = sky_spec)
        OR (asset_id = 'bg_vidhi_primitives'
          AND spec_sha256 = '179ab2c22fad87f5f3c21475e3ddc5151eaf5fd88ea1c05cea0a6d73b845804f'
          AND spec = vidhi_spec)
        OR (asset_id = 'bg_muhurta_lattice'
          AND spec_sha256 = 'dd96913547048da000efbd94cfc106a9f90fe15b14b2def68aba9f45b4e4db98'
          AND spec = muhurta_spec))) <> 3 THEN
    RAISE EXCEPTION 'migration 628 postflight output digest contract mismatch';
  END IF;
END $$;
