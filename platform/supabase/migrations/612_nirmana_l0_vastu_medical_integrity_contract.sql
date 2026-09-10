-- Migration 612: install exact integrity contracts for the Vastu and medical
-- L0 producers and repair the medical producer's stale registry floor.
--
-- Read-only production fingerprints were independently matched to the current
-- deterministic Python seeders on 2026-08-26. The accepted disposition is
-- PRESERVE + GOVERNED REBUILD. This migration changes registry metadata only;
-- transaction ownership belongs to platform/scripts/migrate.ts.

DO $$
DECLARE
  registry_row asset_registry%ROWTYPE;
  changed_rows integer := 0;
  legacy_medical_description constant text :=
    'Classical Ayurvedic graha → dosha/dhatu/organ/body-part mappings per BPHS Ch.18, Ashtanga Hridayam, Charaka Samhita. 9 grahas (Sun–Ketu). L0 static reference.';
  canonical_medical_description constant text :=
    'Classical Ayurvedic Jyotish mappings per BPHS Ch.18, Ashtanga Hridayam, and Charaka Samhita: 9 grahas, 6 planetary combinations, and 6 dignity modifiers. L0 static reference.';
  legacy_medical_explanation constant text :=
    '9 rows = one row per classical graha (Sun through Ketu).';
  canonical_medical_explanation constant text :=
    '21 deterministic medical mapping rows: 9 classical grahas + 6 planetary combinations + 6 dignity modifiers.';
  vastu_check constant text := $check$
SELECT
  (SELECT count(*) = 8 FROM bg_vastu_directions)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(direction,direction_deg,ruling_graha,secondary_graha,
      favorable_color,element,classical_citation)::text,
    E'\n' ORDER BY direction COLLATE "C"
  ),''),'UTF8')),'hex') =
    '1d18e307f87fa65932cb96ea4cff1dc8487262986ff5de4c969ab0b48497bb07'
  FROM bg_vastu_directions)
  AND (SELECT count(*) = 24 FROM bg_vastu_direction_remedials)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(direction,remedy_type,remedy_description,
      classical_citation)::text,
    E'\n' ORDER BY direction COLLATE "C",remedy_type COLLATE "C"
  ),''),'UTF8')),'hex') =
    '0c9c3378e7f7ddb5205996d6f1d0a1b9ef5e47b7334f65d0225c5c88f2cbffe7'
  FROM bg_vastu_direction_remedials)
$check$;
  medical_check constant text := $check$
SELECT
  (SELECT count(*) = 21 FROM bg_medical_mappings)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(graha,dosha,dhatu,organ_systems,body_part,
      disease_tendency,classical_citation)::text,
    E'\n' ORDER BY graha COLLATE "C"
  ),''),'UTF8')),'hex') =
    'b28082a5c41537272e5b7f31a0b8ccd3581fb5d7cf931d265ff20cc2c6879aea'
  FROM bg_medical_mappings)
  AND (SELECT count(*) = 27 FROM bg_nakshatra_medical)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(nakshatra_name,nakshatra_number,body_part,
      classical_citation,dosha)::text,
    E'\n' ORDER BY nakshatra_number
  ),''),'UTF8')),'hex') =
    '52b968862b08590761b6fa6e3adef72e598965965f33694f4731e5d21c6e1ca9'
  FROM bg_nakshatra_medical)
  AND (SELECT count(*) = 12 FROM bg_sign_medical)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(sign_number,sign_name,body_part,organ_systems,element,
      dosha,classical_citation)::text,
    E'\n' ORDER BY sign_number
  ),''),'UTF8')),'hex') =
    'fc143d3109d4ffc20e1c78d952581d1b01ac7c4653f4a29ffc46396fa751769f'
  FROM bg_sign_medical)
$check$;
  nakshatra_check constant text := $check$
SELECT
  (SELECT count(*) = 27 FROM bg_nakshatra_medical)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(nakshatra_name,nakshatra_number,body_part,
      classical_citation,dosha)::text,
    E'\n' ORDER BY nakshatra_number
  ),''),'UTF8')),'hex') =
    '52b968862b08590761b6fa6e3adef72e598965965f33694f4731e5d21c6e1ca9'
  FROM bg_nakshatra_medical)
$check$;
  sign_check constant text := $check$
SELECT
  (SELECT count(*) = 12 FROM bg_sign_medical)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(sign_number,sign_name,body_part,organ_systems,element,
      dosha,classical_citation)::text,
    E'\n' ORDER BY sign_number
  ),''),'UTF8')),'hex') =
    'fc143d3109d4ffc20e1c78d952581d1b01ac7c4653f4a29ffc46396fa751769f'
  FROM bg_sign_medical)
$check$;
BEGIN
  SELECT * INTO registry_row FROM asset_registry
  WHERE asset_id = 'bg_sign_medical' FOR UPDATE;
  IF NOT FOUND OR (
    registry_row.layer = 'brahmagyan'
    AND registry_row.sort_order = 0
    AND registry_row.scope = 'global'
    AND registry_row.asset_kind = 'data'
    AND registry_row.catalog_status = 'CURRENT'
    AND registry_row.is_active IS TRUE
    AND registry_row.has_writer IS TRUE
    AND registry_row.target_table = 'bg_sign_medical'
    AND registry_row.count_sql = 'SELECT COUNT(*) FROM bg_sign_medical'
    AND registry_row.target_floor = 12
    AND registry_row.depends_on = ARRAY[]::text[]
    AND (registry_row.integrity_check_sql IS NULL
      OR registry_row.integrity_check_sql = sign_check)
  ) IS NOT TRUE THEN
    RAISE EXCEPTION
      'migration 612 refuses unknown registry contract for bg_sign_medical';
  END IF;

  SELECT * INTO registry_row FROM asset_registry
  WHERE asset_id = 'bg_vastu_directions' FOR UPDATE;
  IF NOT FOUND OR (
    registry_row.layer = 'brahmagyan'
    AND registry_row.sort_order = 56
    AND registry_row.scope = 'global'
    AND registry_row.asset_kind = 'data'
    AND registry_row.catalog_status = 'CURRENT'
    AND registry_row.is_active IS TRUE
    AND registry_row.has_writer IS TRUE
    AND registry_row.target_table = 'bg_vastu_directions'
    AND registry_row.count_sql = 'SELECT (SELECT COUNT(*) FROM bg_vastu_directions) + (SELECT COUNT(*) FROM bg_vastu_direction_remedials) AS count'
    AND registry_row.target_floor = 32
    AND registry_row.depends_on = ARRAY[]::text[]
    AND (registry_row.integrity_check_sql IS NULL
      OR registry_row.integrity_check_sql = vastu_check)
  ) IS NOT TRUE THEN
    RAISE EXCEPTION
      'migration 612 refuses unknown registry contract for bg_vastu_directions';
  END IF;

  SELECT * INTO registry_row FROM asset_registry
  WHERE asset_id = 'bg_medical_mappings' FOR UPDATE;
  IF NOT FOUND OR (
    registry_row.layer = 'brahmagyan'
    AND registry_row.sort_order = 64
    AND registry_row.scope = 'global'
    AND registry_row.asset_kind = 'data'
    AND registry_row.catalog_status = 'CURRENT'
    AND registry_row.is_active IS TRUE
    AND registry_row.has_writer IS TRUE
    AND registry_row.target_table = 'bg_medical_mappings'
    AND registry_row.count_sql = 'SELECT COUNT(*) FROM bg_medical_mappings'
    AND registry_row.depends_on = ARRAY[]::text[]
    AND (
      (
        registry_row.target_floor = 9
        AND registry_row.english_description = legacy_medical_description
        AND registry_row.volume_explanation = legacy_medical_explanation
        AND registry_row.integrity_check_sql IS NULL
      ) OR (
        registry_row.target_floor = 21
        AND registry_row.english_description = canonical_medical_description
        AND registry_row.volume_explanation = canonical_medical_explanation
        AND (registry_row.integrity_check_sql IS NULL
          OR registry_row.integrity_check_sql = medical_check)
      )
    )
  ) IS NOT TRUE THEN
    RAISE EXCEPTION
      'migration 612 refuses unknown registry contract for bg_medical_mappings';
  END IF;

  SELECT * INTO registry_row FROM asset_registry
  WHERE asset_id = 'bg_nakshatra_medical' FOR UPDATE;
  IF NOT FOUND OR (
    registry_row.layer = 'brahmagyan'
    AND registry_row.sort_order = 65
    AND registry_row.scope = 'global'
    AND registry_row.asset_kind = 'data'
    AND registry_row.catalog_status = 'CURRENT'
    AND registry_row.is_active IS TRUE
    AND registry_row.has_writer IS FALSE
    AND registry_row.target_table = 'bg_nakshatra_medical'
    AND registry_row.count_sql = 'SELECT COUNT(*) FROM bg_nakshatra_medical'
    AND registry_row.target_floor = 27
    AND registry_row.depends_on = ARRAY[]::text[]
    AND (registry_row.integrity_check_sql IS NULL
      OR registry_row.integrity_check_sql = nakshatra_check)
  ) IS NOT TRUE THEN
    RAISE EXCEPTION
      'migration 612 refuses unknown registry contract for bg_nakshatra_medical';
  END IF;

  UPDATE asset_registry
  SET integrity_check_sql = CASE asset_id
        WHEN 'bg_sign_medical' THEN sign_check
        WHEN 'bg_vastu_directions' THEN vastu_check
        WHEN 'bg_medical_mappings' THEN medical_check
        WHEN 'bg_nakshatra_medical' THEN nakshatra_check
      END,
      target_floor = CASE asset_id
        WHEN 'bg_medical_mappings' THEN 21
        ELSE target_floor
      END,
      english_description = CASE asset_id
        WHEN 'bg_medical_mappings' THEN canonical_medical_description
        ELSE english_description
      END,
      volume_explanation = CASE asset_id
        WHEN 'bg_medical_mappings' THEN canonical_medical_explanation
        ELSE volume_explanation
      END
  WHERE asset_id IN (
    'bg_sign_medical',
    'bg_vastu_directions',
    'bg_medical_mappings',
    'bg_nakshatra_medical'
  );
  GET DIAGNOSTICS changed_rows = ROW_COUNT;
  IF changed_rows <> 4 THEN
    RAISE EXCEPTION 'migration 612 expected 4 registry rows, updated %', changed_rows;
  END IF;

  IF (SELECT count(*) FROM asset_registry
      WHERE (asset_id = 'bg_sign_medical' AND integrity_check_sql = sign_check)
         OR (asset_id = 'bg_vastu_directions' AND integrity_check_sql = vastu_check)
         OR (asset_id = 'bg_medical_mappings'
             AND target_floor = 21
             AND english_description = canonical_medical_description
             AND volume_explanation = canonical_medical_explanation
             AND integrity_check_sql = medical_check)
         OR (asset_id = 'bg_nakshatra_medical'
             AND integrity_check_sql = nakshatra_check)) <> 4 THEN
    RAISE EXCEPTION 'migration 612 postflight registry mismatch';
  END IF;
END $$;
