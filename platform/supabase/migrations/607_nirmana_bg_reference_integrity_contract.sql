-- Migration 607: install the executable bg_reference integrity contract.
--
-- bg_reference owns exactly 11 current typed relations. The deprecated
-- reference_nakshatras relation belongs outside this asset's measurement and
-- digest boundary. Migration 599 supplies the writer's hidden bg_ontology edge;
-- migration 602 supplies the canonical 1,242-row registry measurement.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

DO $$
DECLARE
  registry_row asset_registry%ROWTYPE;
  changed_rows INTEGER := 0;
  reference_check CONSTANT TEXT := $check$
SELECT
  (SELECT COUNT(*) = 11 AND COUNT(DISTINCT planet_id) = 11 FROM reference_planets)
  AND (SELECT md5(COALESCE(string_agg(jsonb_build_array(planet_id,canonical_name_en,canonical_name_sa,exaltation_sign,exaltation_degree,debilitation_sign,mooltrikona_sign,own_signs,natural_benefic,karak_domains,dasha_years,source_citation)::text, E'\n' ORDER BY planet_id),'')) = '2a24fff91ac1c6fe56410769461c797d' FROM reference_planets)
  AND (SELECT ARRAY_AGG(planet_id ORDER BY planet_id) = ARRAY[
    'ascendant','jupiter','ketu','mars','mercury','midheaven','moon','rahu','saturn','sun','venus'
  ]::text[] FROM reference_planets)
  AND (SELECT COUNT(*) = 12 AND COUNT(DISTINCT sign_id) = 12 FROM reference_signs)
  AND (SELECT md5(COALESCE(string_agg(jsonb_build_array(sign_id,canonical_name_en,canonical_name_sa,lord,element,modality,natural_house,is_odd,is_biped,significations,source_citation)::text, E'\n' ORDER BY sign_id),'')) = 'd8384f552b0f9bd507fe1ac83fa8d5a0' FROM reference_signs)
  AND (SELECT ARRAY_AGG(sign_id ORDER BY sign_id) = ARRAY[1,2,3,4,5,6,7,8,9,10,11,12]::smallint[] FROM reference_signs)
  AND (SELECT COUNT(*) = 19 AND COUNT(DISTINCT (planet_id, aspect_house)) = 19 FROM reference_aspects)
  AND (SELECT md5(COALESCE(string_agg(jsonb_build_array(planet_id,aspect_house,aspect_strength,strength_value,is_special,notes,source_citation)::text, E'\n' ORDER BY planet_id,aspect_house),'')) = 'c92a24b7eda3fe2382bf3943a95ae900' FROM reference_aspects)
  AND (SELECT COUNT(*) = 19 AND COUNT(DISTINCT varga_id) = 19 FROM reference_vargas)
  AND (SELECT md5(COALESCE(string_agg(jsonb_build_array(varga_id,varga_number,canonical_name_en,canonical_name_sa,division_count,primary_signification,secondary_signification,source_citation)::text, E'\n' ORDER BY varga_id),'')) = '6ea911e25c1592f24b7383e8c8ec5f16' FROM reference_vargas)
  AND (SELECT ARRAY_AGG(varga_id ORDER BY varga_id) = ARRAY[
    'D1','D10','D12','D16','D2','D20','D24','D27','D3','D30','D4','D40','D45','D5','D6','D60','D7','D8','D9'
  ]::text[] FROM reference_vargas)
  AND (SELECT COUNT(*) = 12 AND COUNT(DISTINCT house_num) = 12 FROM reference_houses)
  AND (SELECT md5(COALESCE(string_agg(jsonb_build_array(house_num,name_sa,name_en,category,natural_significations,karakas,classical_doctrine_jsonb,source_citation)::text, E'\n' ORDER BY house_num),'')) = 'ba0be72447cf4e69ec249f7682fc6044' FROM reference_houses)
  AND (SELECT ARRAY_AGG(house_num ORDER BY house_num) = ARRAY[1,2,3,4,5,6,7,8,9,10,11,12]::integer[] FROM reference_houses)
  AND (SELECT COUNT(*) = 33 AND COUNT(DISTINCT strength_id) = 33 FROM reference_strength_systems)
  AND (SELECT md5(COALESCE(string_agg(jsonb_build_array(strength_id,name_sa,name_en,category,formula_text,max_value,units,classical_interpretation,source_citation)::text, E'\n' ORDER BY strength_id),'')) = 'a62ee26273919321094aa3a9cc53b0cf' FROM reference_strength_systems)
  AND (SELECT COUNT(*) = 77 AND COUNT(DISTINCT karaka_id) = 77 FROM reference_karakas)
  AND (SELECT md5(COALESCE(string_agg(jsonb_build_array(karaka_id,name_sa,name_en,karaka_type,applies_to,classical_significations,source_citation)::text, E'\n' ORDER BY karaka_id),'')) = 'd5b06b1bd27fd7e9e853621b9779a964' FROM reference_karakas)
  AND (SELECT COUNT(*) = 11 AND COUNT(DISTINCT upagraha_id) = 11 FROM reference_upagrahas)
  AND (SELECT md5(COALESCE(string_agg(jsonb_build_array(upagraha_id,name_sa,name_en,parent_planet,computation_method,significations,source_citation)::text, E'\n' ORDER BY upagraha_id),'')) = '3e089533a087c7540fcdde628524a27a' FROM reference_upagrahas)
  AND (SELECT COUNT(*) = 203 AND COUNT(DISTINCT constant_id) = 203 FROM reference_constants)
  AND (SELECT md5(COALESCE(string_agg(jsonb_build_array(constant_id,name,value_numeric,value_text,unit,category,source_citation,classical_context)::text, E'\n' ORDER BY constant_id),'')) = 'ff504cadcd864211bf258b39eee2154b' FROM reference_constants)
  AND (SELECT COUNT(*) = 481 AND COUNT(DISTINCT canonical_id) = 481 FROM reference_topic_tags)
  AND (SELECT md5(COALESCE(string_agg(jsonb_build_array(canonical_id,name,category,description,example_chunks)::text, E'\n' ORDER BY canonical_id),'')) = '7ad2a364dc208f9f8b9f2e131bbf8514' FROM reference_topic_tags)
  AND (SELECT COUNT(*) = 364 AND COUNT(DISTINCT term_id) = 364 FROM reference_glossary)
  AND (SELECT md5(COALESCE(string_agg(jsonb_build_array(term_id,term_sa,term_en,definition,category,classical_citation,related_concepts)::text, E'\n' ORDER BY term_id),'')) = '384e62806770d312773a70e6e91ad768' FROM reference_glossary)
  AND NOT EXISTS (SELECT 1 FROM reference_planets WHERE COALESCE(btrim(source_citation), '') = '')
  AND NOT EXISTS (SELECT 1 FROM reference_signs WHERE COALESCE(btrim(source_citation), '') = '')
  AND NOT EXISTS (SELECT 1 FROM reference_aspects WHERE COALESCE(btrim(source_citation), '') = '')
  AND NOT EXISTS (SELECT 1 FROM reference_vargas WHERE COALESCE(btrim(source_citation), '') = '')
  AND NOT EXISTS (SELECT 1 FROM reference_houses WHERE COALESCE(btrim(source_citation), '') = '')
  AND NOT EXISTS (SELECT 1 FROM reference_strength_systems WHERE COALESCE(btrim(source_citation), '') = '')
  AND NOT EXISTS (SELECT 1 FROM reference_karakas WHERE COALESCE(btrim(source_citation), '') = '')
  AND NOT EXISTS (SELECT 1 FROM reference_upagrahas WHERE COALESCE(btrim(source_citation), '') = '')
  AND NOT EXISTS (SELECT 1 FROM reference_constants WHERE COALESCE(btrim(source_citation), '') = '')
  AND NOT EXISTS (
    SELECT 1 FROM reference_topic_tags
    WHERE COALESCE(btrim(canonical_id), '') = ''
       OR COALESCE(btrim(name), '') = ''
       OR COALESCE(btrim(category), '') = ''
  )
  AND NOT EXISTS (SELECT 1 FROM reference_glossary WHERE COALESCE(btrim(classical_citation), '') = '')
$check$;
  canonical_count_sql CONSTANT TEXT :=
    'SELECT (SELECT count(*) FROM reference_planets) + (SELECT count(*) FROM reference_signs) + (SELECT count(*) FROM reference_aspects) + (SELECT count(*) FROM reference_vargas) + (SELECT count(*) FROM reference_houses) + (SELECT count(*) FROM reference_strength_systems) + (SELECT count(*) FROM reference_karakas) + (SELECT count(*) FROM reference_upagrahas) + (SELECT count(*) FROM reference_constants) + (SELECT count(*) FROM reference_topic_tags) + (SELECT count(*) FROM reference_glossary) AS count';
  canonical_explanation CONSTANT TEXT :=
    '1,242 achieved rows across the 11 tables owned by bg_reference, as measured in the BA full-asset audit after migration 371 removed cross-asset double-counting. reference_yogas, reference_doshas, and reference_dasha_systems are owned by their dedicated assets; deprecated reference_nakshatras is excluded.';
BEGIN
  SELECT * INTO registry_row
  FROM asset_registry WHERE asset_id = 'bg_reference' FOR UPDATE;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'migration 607 requires bg_reference registry row';
  END IF;

  IF (
    registry_row.layer = 'brahmagyan'
    AND registry_row.sort_order = 2
    AND registry_row.scope = 'global'
    AND registry_row.asset_kind = 'data'
    AND registry_row.catalog_status = 'CURRENT'
    AND registry_row.is_active IS TRUE
    AND registry_row.has_writer IS TRUE
    AND registry_row.target_table = 'reference_planets'
    AND registry_row.count_sql = canonical_count_sql
    AND registry_row.target_floor = 1242
    AND registry_row.volume_explanation = canonical_explanation
    AND registry_row.depends_on = ARRAY['bg_ontology']::text[]
    AND (registry_row.integrity_check_sql IS NULL OR registry_row.integrity_check_sql = reference_check)
  ) IS NOT TRUE THEN
    RAISE EXCEPTION 'migration 607 refuses unknown bg_reference registry contract';
  END IF;

  UPDATE asset_registry
  SET integrity_check_sql = reference_check
  WHERE asset_id = 'bg_reference';
  GET DIAGNOSTICS changed_rows = ROW_COUNT;
  IF changed_rows <> 1 THEN
    RAISE EXCEPTION 'migration 607 expected to update bg_reference once, updated %', changed_rows;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM asset_registry
    WHERE asset_id = 'bg_reference'
      AND target_floor = 1242
      AND depends_on = ARRAY['bg_ontology']::text[]
      AND integrity_check_sql = reference_check
  ) THEN
    RAISE EXCEPTION 'migration 607 failed bg_reference postflight';
  END IF;
END $$;

-- Forward reversal: append a new migration that first proves no accepted build
-- receipt depends on this detector, then installs a reviewed replacement.
