-- Migration 611: install exact integrity contracts for three closed L0 tables.
--
-- The Kota-Chakra partition and the two Phaladeepika vedha tables are small,
-- deterministic, versioned source transcriptions. Read-only production
-- fingerprints were independently matched to the current Python seeders on
-- 2026-08-26. Their accepted disposition is PRESERVE + GOVERNED REBUILD: the
-- writer may replay the exact reviewed version, but an unreviewed version or
-- any count-preserving semantic mutation fails closed.
--
-- This migration changes registry metadata only. Transaction ownership belongs
-- to platform/scripts/migrate.ts.

DO $$
DECLARE
  registry_row asset_registry%ROWTYPE;
  changed_rows integer := 0;
  kota_check constant text := $check$
SELECT
  (SELECT count(*) = 27 FROM bg_kota_chakra_rings)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(table_version,ring_position,ring_name,ring_index,
      dvara_assignment,citation,corpus_status,ratified_by)::text,
    E'\n' ORDER BY table_version COLLATE "C",ring_position
  ),''),'UTF8')),'hex') =
    'ec9c877dd2c143d4deb7a74dc490ced4761a90b61e0e23e7aa7589a40cc91bf7'
  FROM bg_kota_chakra_rings)
$check$;
  vedha_check constant text := $check$
SELECT
  (SELECT count(*) = 5 FROM bg_vedha_malefic_scale)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(table_version,malefic_count,effect_grade,
      effect_description,source_citation,verse_ref)::text,
    E'\n' ORDER BY table_version COLLATE "C",malefic_count
  ),''),'UTF8')),'hex') =
    '9ee5d8436059fa96d5fa60d8be6d0cc25cc8865e1013ef1bed8ff6810342ff1c'
  FROM bg_vedha_malefic_scale)
$check$;
  latta_check constant text := $check$
SELECT
  (SELECT count(*) = 8 FROM bg_phaladeepika_latta)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(table_version,graha,count_from_graha,direction,
      effect_description,affliction_condition,source_citation,verse_ref)::text,
    E'\n' ORDER BY table_version COLLATE "C",graha COLLATE "C"
  ),''),'UTF8')),'hex') =
    '11fdcce56802e2fd5aab056b426cb6eb2a75cb6c2b1fd705df52113b44010e88'
  FROM bg_phaladeepika_latta)
$check$;
BEGIN
  SELECT * INTO registry_row
  FROM asset_registry WHERE asset_id = 'bg_kota_chakra_rings' FOR UPDATE;
  IF NOT FOUND OR (
    registry_row.layer = 'brahmagyan'
    AND registry_row.sort_order = 72
    AND registry_row.scope = 'global'
    AND registry_row.asset_kind = 'data'
    AND registry_row.catalog_status = 'CURRENT'
    AND registry_row.is_active IS TRUE
    AND registry_row.has_writer IS TRUE
    AND registry_row.target_table = 'bg_kota_chakra_rings'
    AND registry_row.count_sql = 'SELECT COUNT(*) FROM bg_kota_chakra_rings'
    AND registry_row.target_floor = 27
    AND registry_row.depends_on = ARRAY[]::text[]
    AND (registry_row.integrity_check_sql IS NULL
      OR registry_row.integrity_check_sql = kota_check)
  ) IS NOT TRUE THEN
    RAISE EXCEPTION
      'migration 611 refuses unknown registry contract for bg_kota_chakra_rings';
  END IF;

  SELECT * INTO registry_row
  FROM asset_registry WHERE asset_id = 'bg_vedha_malefic_scale' FOR UPDATE;
  IF NOT FOUND OR (
    registry_row.layer = 'brahmagyan'
    AND registry_row.sort_order = 74
    AND registry_row.scope = 'global'
    AND registry_row.asset_kind = 'data'
    AND registry_row.catalog_status = 'CURRENT'
    AND registry_row.is_active IS TRUE
    AND registry_row.has_writer IS TRUE
    AND registry_row.target_table = 'bg_vedha_malefic_scale'
    AND registry_row.count_sql = 'SELECT COUNT(*) FROM bg_vedha_malefic_scale'
    AND registry_row.target_floor = 5
    AND registry_row.depends_on = ARRAY[]::text[]
    AND (registry_row.integrity_check_sql IS NULL
      OR registry_row.integrity_check_sql = vedha_check)
  ) IS NOT TRUE THEN
    RAISE EXCEPTION
      'migration 611 refuses unknown registry contract for bg_vedha_malefic_scale';
  END IF;

  SELECT * INTO registry_row
  FROM asset_registry WHERE asset_id = 'bg_phaladeepika_latta' FOR UPDATE;
  IF NOT FOUND OR (
    registry_row.layer = 'brahmagyan'
    AND registry_row.sort_order = 75
    AND registry_row.scope = 'global'
    AND registry_row.asset_kind = 'data'
    AND registry_row.catalog_status = 'CURRENT'
    AND registry_row.is_active IS TRUE
    AND registry_row.has_writer IS TRUE
    AND registry_row.target_table = 'bg_phaladeepika_latta'
    AND registry_row.count_sql = 'SELECT COUNT(*) FROM bg_phaladeepika_latta'
    AND registry_row.target_floor = 8
    AND registry_row.depends_on = ARRAY[]::text[]
    AND (registry_row.integrity_check_sql IS NULL
      OR registry_row.integrity_check_sql = latta_check)
  ) IS NOT TRUE THEN
    RAISE EXCEPTION
      'migration 611 refuses unknown registry contract for bg_phaladeepika_latta';
  END IF;

  UPDATE asset_registry
  SET integrity_check_sql = CASE asset_id
    WHEN 'bg_kota_chakra_rings' THEN kota_check
    WHEN 'bg_vedha_malefic_scale' THEN vedha_check
    WHEN 'bg_phaladeepika_latta' THEN latta_check
  END
  WHERE asset_id IN (
    'bg_kota_chakra_rings',
    'bg_vedha_malefic_scale',
    'bg_phaladeepika_latta'
  );
  GET DIAGNOSTICS changed_rows = ROW_COUNT;
  IF changed_rows <> 3 THEN
    RAISE EXCEPTION 'migration 611 expected 3 registry rows, updated %', changed_rows;
  END IF;

  IF (SELECT count(*) FROM asset_registry
      WHERE (asset_id = 'bg_kota_chakra_rings' AND integrity_check_sql = kota_check)
         OR (asset_id = 'bg_vedha_malefic_scale' AND integrity_check_sql = vedha_check)
         OR (asset_id = 'bg_phaladeepika_latta' AND integrity_check_sql = latta_check)) <> 3 THEN
    RAISE EXCEPTION 'migration 611 postflight registry mismatch';
  END IF;
END $$;
