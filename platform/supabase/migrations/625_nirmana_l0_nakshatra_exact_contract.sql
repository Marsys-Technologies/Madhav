-- Migration 625: exact bg_nakshatra integrity and ownership contract.
--
-- Production has all 2,857 expected rows, but 22 reference_nakshatra
-- body_part values predate the current governed source. Counts and structural
-- checks therefore cannot establish convergence. This migration pins every
-- reviewed semantic column for all three writer-owned projections. It changes
-- registry metadata only; the governed rebuild performs the data correction.
-- Transaction ownership belongs to platform/scripts/migrate.ts.

DO $$
DECLARE
  registry_row asset_registry%ROWTYPE;
  changed_rows integer := 0;
  legacy_structural_check_sha256 constant text :=
    '4a1baa4fe0641d8231bdc53463365bf54c701305107f66a625d9a132d6764757';
  canonical_partition constant text :=
    'reference_nakshatra.nakshatra_id; '
    'reference_nakshatra_pada.(nakshatra_id,pada_number); '
    'reference_nakshatra_matrix.(matrix_type,from_key,to_key)';
  canonical_count_sql constant text :=
    'SELECT (SELECT COUNT(*) FROM reference_nakshatra) + (SELECT COUNT(*) FROM reference_nakshatra_pada) + (SELECT COUNT(*) FROM reference_nakshatra_matrix) AS count';
  exact_check constant text := $check$
SELECT
  (SELECT count(*) = 28 FROM reference_nakshatra)
  AND (SELECT count(*) = 108 FROM reference_nakshatra_pada)
  AND (SELECT count(*) = 2721 FROM reference_nakshatra_matrix)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(
      nakshatra_id,name_sa_iast,name_sa_devanagari,name_en,alt_names,
      start_longitude,end_longitude,span_degrees,rashis_spanned,
      degree_in_rashi_ranges,vimshottari_lord,presiding_deity,
      secondary_deities,ruling_planet,gana,nadi,yoni_en,yoni_sa,yoni_sex,
      varna,tatva,guna,pakshi,nakshatra_gender,muhurta_type,disha,
      favorable_acts,prohibited_acts,symbol,shakti,basis_above,basis_below,
      net_result,motivation,body_part,paramayus,naisargika_maturity_age,
      deity_domain,is_gandanta,is_mula_sangya,is_panchaka,is_abhijit,
      tradition_scope,classical_source
    )::text,E'\n' ORDER BY nakshatra_id),''),'UTF8')),'hex') =
    'bbbf686205c208efe0a7f6dbd192b27e63931a9b37f442d194d8d17b72ee3fde'
   FROM reference_nakshatra)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(
      pada_id,nakshatra_id,pada_number,absolute_pada,start_longitude,
      end_longitude,pada_navamsa_sign,pada_lord,pada_akshara,bija_sound,
      mantra_prefix,pada_deity_nuance,element_shading,dosha_shading,
      tradition_scope,classical_source
    )::text,E'\n' ORDER BY nakshatra_id,pada_number),''),'UTF8')),'hex') =
    '09eeb0e2027486201274b36427a17cee7eb1c60eceb3c3bf334c53b6fbc990a9'
   FROM reference_nakshatra_pada)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(
      matrix_type,from_key,to_key,relation_value,guna_points,max_points,notes,
      tradition_scope,classical_source
    )::text,E'\n' ORDER BY matrix_type COLLATE "C",from_key COLLATE "C",to_key COLLATE "C"),''),'UTF8')),'hex') =
    '143ce4a335d0cc7fac4b7bb3137c713c238e7f6b06f2477d7ecf7aa14d88d9bb'
   FROM reference_nakshatra_matrix)
$check$;
BEGIN
  SELECT * INTO registry_row
  FROM asset_registry
  WHERE asset_id = 'bg_nakshatra'
  FOR UPDATE;

  IF NOT FOUND OR (
    registry_row.layer = 'brahmagyan'
    AND registry_row.sort_order = 15
    AND registry_row.scope = 'global'
    AND registry_row.asset_kind = 'data'
    AND registry_row.catalog_status = 'CURRENT'
    AND registry_row.is_active IS TRUE
    AND registry_row.has_writer IS TRUE
    AND registry_row.target_table = 'reference_nakshatra'
    AND registry_row.count_sql = canonical_count_sql
    AND registry_row.target_floor = 2857
    AND registry_row.depends_on = ARRAY[]::text[]
    AND registry_row.data_disposition IS NULL
    AND (
      registry_row.natural_key_partition IS NULL
      OR registry_row.natural_key_partition = canonical_partition
    )
    AND (
      registry_row.integrity_check_sql IS NULL
      OR registry_row.integrity_check_sql = exact_check
      OR encode(sha256(convert_to(registry_row.integrity_check_sql,'UTF8')),'hex') =
        legacy_structural_check_sha256
    )
  ) IS NOT TRUE THEN
    RAISE EXCEPTION 'migration 625 refuses unknown bg_nakshatra registry contract';
  END IF;

  UPDATE asset_registry
  SET natural_key_partition = canonical_partition,
      integrity_check_sql = exact_check
  WHERE asset_id = 'bg_nakshatra';

  GET DIAGNOSTICS changed_rows = ROW_COUNT;
  IF changed_rows <> 1 THEN
    RAISE EXCEPTION 'migration 625 expected 1 row, updated %', changed_rows;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM asset_registry
    WHERE asset_id = 'bg_nakshatra'
      AND natural_key_partition = canonical_partition
      AND integrity_check_sql = exact_check
  ) THEN
    RAISE EXCEPTION 'migration 625 postflight registry mismatch';
  END IF;
END $$;
