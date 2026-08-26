-- Migration 606: install executable integrity contracts for five L0 wave-0 assets.
--
-- The original analysis proposals described violation queries that returned zero
-- rows when healthy. The frozen orchestrator contract requires exactly one row
-- whose first column is truthy. These checks preserve the writer-derived
-- invariants while returning one boolean and failing closed on an empty,
-- malformed, incomplete, or structurally inconsistent output.
--
-- bg_ontology's 623-row floor was stale; production contains the 737 rows
-- produced by the current writer. This migration ratifies that achieved count.
-- It changes registry metadata only and does not rewrite asset output.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

DO $$
DECLARE
  registry_row asset_registry%ROWTYPE;
  changed_rows INTEGER := 0;
  ontology_explanation CONSTANT TEXT :=
    '737 achieved ontology rows in the authoritative production corpus; closed classical sets are enforced by integrity SQL while extensible classes may grow.';
  cohort_check CONSTANT TEXT := $check$
SELECT
  (SELECT COUNT(*) = 10000 AND COUNT(DISTINCT synthetic_id) = 10000
      AND MIN(synthetic_id) = 1 AND MAX(synthetic_id) = 10000
   FROM bg_synthetic_cohort)
  AND NOT EXISTS (
    SELECT 1 FROM bg_synthetic_cohort
    WHERE jsonb_typeof(positions) IS DISTINCT FROM 'object'
       OR (SELECT COUNT(*) FROM jsonb_object_keys(positions)) <> 10
       OR NOT positions ?& ARRAY['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu','Lagna']
       OR jsonb_typeof(positions->'Sun') IS DISTINCT FROM 'object'
       OR jsonb_typeof(positions->'Moon') IS DISTINCT FROM 'object'
       OR jsonb_typeof(positions->'Mars') IS DISTINCT FROM 'object'
       OR jsonb_typeof(positions->'Mercury') IS DISTINCT FROM 'object'
       OR jsonb_typeof(positions->'Jupiter') IS DISTINCT FROM 'object'
       OR jsonb_typeof(positions->'Venus') IS DISTINCT FROM 'object'
       OR jsonb_typeof(positions->'Saturn') IS DISTINCT FROM 'object'
       OR jsonb_typeof(positions->'Rahu') IS DISTINCT FROM 'object'
       OR jsonb_typeof(positions->'Ketu') IS DISTINCT FROM 'object'
       OR (positions->'Lagna' <> 'null'::jsonb AND jsonb_typeof(positions->'Lagna') IS DISTINCT FROM 'object')
  )
  AND NOT EXISTS (
    SELECT 1 FROM bg_synthetic_cohort b
    CROSS JOIN LATERAL jsonb_each(b.positions) AS kv(graha, pos)
    WHERE kv.pos <> 'null'::jsonb
      AND (jsonb_typeof(pos) IS DISTINCT FROM 'object'
        OR jsonb_typeof(pos->'sign_id') IS DISTINCT FROM 'number'
        OR jsonb_typeof(pos->'nakshatra_id') IS DISTINCT FROM 'number'
        OR jsonb_typeof(pos->'nakshatra_pada') IS DISTINCT FROM 'number'
        OR (pos->>'sign_id')::int NOT BETWEEN 1 AND 12
        OR (pos->>'nakshatra_id')::int NOT BETWEEN 1 AND 27
        OR (pos->>'nakshatra_pada')::int NOT BETWEEN 1 AND 4)
  )
  AND NOT EXISTS (
    SELECT 1 FROM bg_synthetic_cohort b
    LEFT JOIN bg_synthetic_cohort_md md ON md.synthetic_id = b.synthetic_id
    GROUP BY b.synthetic_id
    HAVING COUNT(md.synthetic_id) NOT IN (9,10)
       OR MIN(md.md_index) <> 1
       OR MAX(md.md_index) <> COUNT(md.synthetic_id)
       OR ABS(MIN(md.start_age_years)) > 0.000001
       OR ABS(MAX(md.end_age_years) - 120.0) > 0.000001
  )
  AND NOT EXISTS (
    SELECT 1 FROM (
      SELECT synthetic_id, md_index, start_age_years, end_age_years,
             LAG(end_age_years) OVER (PARTITION BY synthetic_id ORDER BY md_index) AS previous_end
      FROM bg_synthetic_cohort_md
    ) chain
    WHERE end_age_years <= start_age_years
       OR (md_index > 1 AND ABS(start_age_years - previous_end) > 0.000001)
  )
$check$;
  ontology_check CONSTANT TEXT := $check$
SELECT
  (SELECT COUNT(*) >= 737 FROM brahma_ontology)
  AND (SELECT ARRAY_AGG(canonical_id ORDER BY canonical_id) = ARRAY[
    'nak_01_ashwini','nak_02_bharani','nak_03_krittika','nak_04_rohini','nak_05_mrigasira',
    'nak_06_ardra','nak_07_punarvasu','nak_08_pushya','nak_09_ashlesha','nak_10_magha',
    'nak_11_purva_phalguni','nak_12_uttara_phalguni','nak_13_hasta','nak_14_chitra',
    'nak_15_swati','nak_16_vishakha','nak_17_anuradha','nak_18_jyeshtha','nak_19_moola',
    'nak_20_purva_ashadha','nak_21_uttara_ashadha','nak_22_shravana','nak_23_dhanishtha',
    'nak_24_shatabhisha','nak_25_purva_bhadrapada','nak_26_uttara_bhadrapada','nak_27_revati'
  ]::text[] FROM brahma_ontology WHERE entity_class='nakshatra')
  AND (SELECT ARRAY_AGG(canonical_id ORDER BY canonical_id) = ARRAY[
    'aquarius','aries','cancer','capricorn','gemini','leo','libra','pisces','sagittarius','scorpio','taurus','virgo'
  ]::text[] FROM brahma_ontology WHERE entity_class='sign')
  AND (SELECT ARRAY_AGG(canonical_id ORDER BY canonical_id) = ARRAY[
    'house_01','house_02','house_03','house_04','house_05','house_06',
    'house_07','house_08','house_09','house_10','house_11','house_12'
  ]::text[] FROM brahma_ontology WHERE entity_class='house')
  AND (SELECT ARRAY_AGG(canonical_id ORDER BY canonical_id) = ARRAY[
    'ascendant','jupiter','ketu','mars','mercury','midheaven','moon','rahu','saturn','sun','venus'
  ]::text[] FROM brahma_ontology WHERE entity_class='planet')
  AND NOT EXISTS (
    SELECT 1 FROM brahma_ontology
    WHERE canonical_id IS NULL OR canonical_name_en IS NULL OR entity_class IS NULL OR source_citation IS NULL
  )
  AND NOT EXISTS (
    SELECT 1 FROM brahma_ontology GROUP BY entity_class, canonical_id HAVING COUNT(*) > 1
  )
$check$;
  ephemeris_check CONSTANT TEXT := $check$
SELECT
  (SELECT COUNT(*) = 825084 AND MIN(date) = DATE '1900-01-01' AND MAX(date) = DATE '2150-12-31'
     AND COUNT(DISTINCT body) = 9 AND COUNT(DISTINCT ayanamsha_id) = 1
   FROM ephemeris_daily)
  AND (SELECT MIN(ayanamsha_id) = 'tropical' FROM ephemeris_daily)
  AND (SELECT ARRAY_AGG(DISTINCT body ORDER BY body) = ARRAY['Jupiter','Ketu','Mars','Mercury','Moon','Rahu','Saturn','Sun','Venus']::text[] FROM ephemeris_daily)
  AND NOT EXISTS (
    SELECT 1 FROM ephemeris_daily GROUP BY date HAVING COUNT(*) <> 9 OR COUNT(DISTINCT body) <> 9
  )
  AND NOT EXISTS (
    SELECT 1 FROM ephemeris_daily
    WHERE tropical_longitude IS NULL OR tropical_longitude < 0 OR tropical_longitude >= 360
  )
$check$;
  nakshatra_check CONSTANT TEXT := $check$
SELECT
  (SELECT COUNT(*) = 28 FROM reference_nakshatra)
  AND NOT EXISTS (SELECT 1 FROM reference_nakshatra WHERE nakshatra_id NOT BETWEEN 1 AND 28)
  AND (SELECT STRING_AGG(nakshatra_id::text, ',' ORDER BY nakshatra_id) = '23,24,25,26,27' FROM reference_nakshatra WHERE is_panchaka)
  AND NOT EXISTS (SELECT 1 FROM reference_nakshatra WHERE is_abhijit IS DISTINCT FROM (nakshatra_id = 28))
  AND (SELECT COUNT(*) = 108 FROM reference_nakshatra_pada)
  AND NOT EXISTS (
    SELECT 1 FROM reference_nakshatra_pada
    WHERE nakshatra_id NOT BETWEEN 1 AND 27 OR pada_number NOT BETWEEN 1 AND 4
  )
  AND NOT EXISTS (
    SELECT 1 FROM reference_nakshatra_pada GROUP BY nakshatra_id HAVING COUNT(*) <> 4 OR COUNT(DISTINCT pada_number) <> 4
  )
  AND (SELECT COUNT(*) = 2721 AND COUNT(DISTINCT matrix_type) = 12 FROM reference_nakshatra_matrix)
  AND NOT EXISTS (
    SELECT 1 FROM reference_nakshatra_matrix
    GROUP BY matrix_type
    HAVING COUNT(*) <> CASE matrix_type
      WHEN 'gana_kuta' THEN 9 WHEN 'nadi_kuta' THEN 9 WHEN 'yoni_kuta' THEN 196
      WHEN 'tara_kuta' THEN 729 WHEN 'rajju' THEN 27 WHEN 'varna_kuta' THEN 49
      WHEN 'graha_maitri_kuta' THEN 49 WHEN 'bhakoot_kuta' THEN 144 WHEN 'vedha' THEN 26
      WHEN 'vashya_kuta' THEN 25 WHEN 'mahendra' THEN 729 WHEN 'stree_deergha' THEN 729
      ELSE -1 END
  )
  AND NOT EXISTS (
    SELECT 1 FROM reference_nakshatra_matrix
    GROUP BY matrix_type, from_key, to_key HAVING COUNT(*) <> 1
  )
  AND NOT EXISTS (
    SELECT 1 FROM reference_nakshatra_matrix
    WHERE CASE matrix_type
      WHEN 'gana_kuta' THEN from_key = ANY(ARRAY['Deva','Manushya','Rakshasa']) AND to_key = ANY(ARRAY['Deva','Manushya','Rakshasa'])
      WHEN 'nadi_kuta' THEN from_key = ANY(ARRAY['Adi','Madhya','Antya']) AND to_key = ANY(ARRAY['Adi','Madhya','Antya'])
      WHEN 'yoni_kuta' THEN from_key = ANY(ARRAY['Horse','Elephant','Goat','Serpent','Dog','Cat','Rat','Cow','Buffalo','Tiger','Hare','Mongoose','Monkey','Lion']) AND to_key = ANY(ARRAY['Horse','Elephant','Goat','Serpent','Dog','Cat','Rat','Cow','Buffalo','Tiger','Hare','Mongoose','Monkey','Lion'])
      WHEN 'varna_kuta' THEN from_key = ANY(ARRAY['Brahmin','Kshatriya','Vaishya','Shudra','Farmer','Butcher','Mleccha']) AND to_key = ANY(ARRAY['Brahmin','Kshatriya','Vaishya','Shudra','Farmer','Butcher','Mleccha'])
      WHEN 'graha_maitri_kuta' THEN from_key = ANY(ARRAY['sun','moon','mars','mercury','jupiter','venus','saturn']) AND to_key = ANY(ARRAY['sun','moon','mars','mercury','jupiter','venus','saturn'])
      WHEN 'vashya_kuta' THEN from_key = ANY(ARRAY['Dwipada','Chaturpada','Jalasheela','Keeta','Vanachara']) AND to_key = ANY(ARRAY['Dwipada','Chaturpada','Jalasheela','Keeta','Vanachara'])
      WHEN 'tara_kuta' THEN CASE WHEN from_key ~ '^[0-9]+$' AND to_key ~ '^[0-9]+$' THEN from_key::int BETWEEN 1 AND 27 AND to_key::int BETWEEN 1 AND 27 ELSE FALSE END
      WHEN 'mahendra' THEN CASE WHEN from_key ~ '^[0-9]+$' AND to_key ~ '^[0-9]+$' THEN from_key::int BETWEEN 1 AND 27 AND to_key::int BETWEEN 1 AND 27 ELSE FALSE END
      WHEN 'stree_deergha' THEN CASE WHEN from_key ~ '^[0-9]+$' AND to_key ~ '^[0-9]+$' THEN from_key::int BETWEEN 1 AND 27 AND to_key::int BETWEEN 1 AND 27 ELSE FALSE END
      WHEN 'bhakoot_kuta' THEN CASE WHEN from_key ~ '^[0-9]+$' AND to_key ~ '^[0-9]+$' THEN from_key::int BETWEEN 1 AND 12 AND to_key::int BETWEEN 1 AND 12 ELSE FALSE END
      WHEN 'rajju' THEN (from_key || ':' || to_key) = ANY(string_to_array('1:Kantha_Avaroha,2:Padha_Aroha,3:Kati_Aroha,4:Nabhi_Aroha,5:Kantha_Aroha,6:Padha_Avaroha,7:Kati_Avaroha,8:Nabhi_Avaroha,9:Kantha_Aroha,10:Shira,11:Padha_Avaroha,12:Kati_Avaroha,13:Nabhi_Avaroha,14:Nabhi_Aroha,15:Kati_Aroha,16:Padha_Aroha,17:Shira,18:Kantha_Aroha,19:Nabhi_Aroha,20:Kati_Aroha,21:Padha_Aroha,22:Kantha_Avaroha,23:Shira,24:Kantha_Avaroha,25:Nabhi_Avaroha,26:Kati_Avaroha,27:Padha_Avaroha', ','))
      WHEN 'vedha' THEN (from_key || ':' || to_key) = ANY(string_to_array('1:16,2:15,3:14,4:13,5:12,6:11,7:10,8:9,9:8,10:7,11:6,12:5,13:4,14:3,15:2,16:1,17:27,18:26,19:25,20:24,21:23,23:21,24:20,25:19,26:18,27:17', ','))
      ELSE FALSE
    END IS NOT TRUE
  )
$check$;
  dignity_check CONSTANT TEXT := $check$
SELECT
  (SELECT ARRAY_AGG(graha ORDER BY graha) = ARRAY['Jupiter','Ketu','Mars','Mercury','Moon','Rahu','Saturn','Sun','Venus']::text[] FROM bg_dignity_reference)
  AND (SELECT COUNT(*) = 72 FROM bg_graha_naisargika_friendship)
  AND (SELECT ARRAY_AGG(DISTINCT graha ORDER BY graha) = ARRAY['Jupiter','Ketu','Mars','Mercury','Moon','Rahu','Saturn','Sun','Venus']::text[] FROM bg_graha_naisargika_friendship)
  AND (SELECT ARRAY_AGG(DISTINCT other_graha ORDER BY other_graha) = ARRAY['Jupiter','Ketu','Mars','Mercury','Moon','Rahu','Saturn','Sun','Venus']::text[] FROM bg_graha_naisargika_friendship)
  AND NOT EXISTS (
    SELECT 1 FROM bg_graha_naisargika_friendship
    WHERE graha = other_graha OR relation NOT IN ('friend','neutral','enemy')
  )
  AND NOT EXISTS (
    SELECT 1 FROM bg_graha_naisargika_friendship GROUP BY graha
    HAVING COUNT(*) <> 8 OR COUNT(DISTINCT other_graha) <> 8
  )
  AND (SELECT COUNT(*) = 35 FROM bg_avastha_schemes)
  AND (SELECT STRING_AGG(scheme_name || ':' || state_name, ',' ORDER BY scheme_name,state_name) =
    'baladi:bala,baladi:kumara,baladi:mrita,baladi:vriddha,baladi:yuva,deeptaadi:deepta,deeptaadi:dina,deeptaadi:khala,deeptaadi:mudita,deeptaadi:peedit,deeptaadi:shakta,deeptaadi:shanta,deeptaadi:swastha,deeptaadi:vikala,jagradadi:jagrata,jagradadi:sushupti,jagradadi:svapna,lajjitaadi:garvita,lajjitaadi:kshobhita,lajjitaadi:kshudhita,lajjitaadi:lajjita,lajjitaadi:mudita,lajjitaadi:trishita,sayanadi:agama,sayanadi:agamana,sayanadi:bhojanaprapta,sayanadi:deeptamsa,sayanadi:gamana,sayanadi:kautuka,sayanadi:netrapani,sayanadi:nidraksita,sayanadi:prakasana,sayanadi:sabha,sayanadi:sayana,sayanadi:upavesana'
    FROM bg_avastha_schemes)
  AND (SELECT STRING_AGG(graha || ':' || motion_state, ',' ORDER BY graha,motion_state) =
    'Jupiter:anuvakra,Jupiter:atichara,Jupiter:sama,Jupiter:vakra,Ketu:vakra,Mars:anuvakra,Mars:atichara,Mars:manda,Mars:sama,Mars:vakra,Mercury:anuvakra,Mercury:atichara,Mercury:sama,Mercury:vakra,Moon:atichara,Moon:sama,Rahu:vakra,Saturn:anuvakra,Saturn:atichara,Saturn:sama,Saturn:vakra,Sun:atichara,Sun:sama,Venus:anuvakra,Venus:atichara,Venus:sama,Venus:vakra'
    FROM bg_motion_state_thresholds)
  AND (SELECT ARRAY_AGG(graha ORDER BY graha) = ARRAY['Jupiter','Ketu','Mars','Mercury','Moon','Rahu','Saturn','Venus']::text[] FROM bg_combustion_orbs)
$check$;
BEGIN
  SELECT * INTO registry_row FROM asset_registry WHERE asset_id = 'bg_cohort' FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'migration 606 requires bg_cohort registry row'; END IF;
  IF (registry_row.layer = 'brahmagyan' AND registry_row.sort_order = 20
      AND registry_row.scope = 'global' AND registry_row.asset_kind = 'data'
      AND registry_row.catalog_status = 'CURRENT' AND registry_row.is_active IS TRUE
      AND registry_row.has_writer IS TRUE AND registry_row.target_table = 'bg_synthetic_cohort'
      AND registry_row.count_sql = 'SELECT COUNT(*) FROM bg_synthetic_cohort'
      AND registry_row.target_floor = 10000
      AND (registry_row.integrity_check_sql IS NULL OR registry_row.integrity_check_sql = cohort_check)) IS NOT TRUE THEN
    RAISE EXCEPTION 'migration 606 refuses unknown bg_cohort registry contract';
  END IF;

  SELECT * INTO registry_row FROM asset_registry WHERE asset_id = 'bg_ontology' FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'migration 606 requires bg_ontology registry row'; END IF;
  IF (registry_row.layer = 'brahmagyan' AND registry_row.sort_order = 4
      AND registry_row.scope = 'global' AND registry_row.asset_kind = 'data'
      AND registry_row.catalog_status = 'CURRENT' AND registry_row.is_active IS TRUE
      AND registry_row.has_writer IS TRUE AND registry_row.target_table = 'brahma_ontology'
      AND registry_row.count_sql = 'SELECT count(*) FROM brahma_ontology'
      AND ((registry_row.target_floor = 623 AND registry_row.volume_explanation = 'Static vocabulary — count established at seed; used by resolve_entity retrieval tool')
        OR (registry_row.target_floor = 737 AND registry_row.volume_explanation = ontology_explanation))
      AND (registry_row.integrity_check_sql IS NULL OR registry_row.integrity_check_sql = ontology_check)) IS NOT TRUE THEN
    RAISE EXCEPTION 'migration 606 refuses unknown bg_ontology registry contract';
  END IF;

  SELECT * INTO registry_row FROM asset_registry WHERE asset_id = 'bg_ephemeris' FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'migration 606 requires bg_ephemeris registry row'; END IF;
  IF (registry_row.layer = 'brahmagyan' AND registry_row.sort_order = 1
      AND registry_row.scope = 'global' AND registry_row.asset_kind = 'data'
      AND registry_row.catalog_status = 'CURRENT' AND registry_row.is_active IS TRUE
      AND registry_row.has_writer IS TRUE AND registry_row.target_table = 'ephemeris_daily'
      AND registry_row.count_sql = 'SELECT count(*) FROM ephemeris_daily'
      AND registry_row.target_floor = 825084
      AND (registry_row.integrity_check_sql IS NULL OR registry_row.integrity_check_sql = ephemeris_check)) IS NOT TRUE THEN
    RAISE EXCEPTION 'migration 606 refuses unknown bg_ephemeris registry contract';
  END IF;

  SELECT * INTO registry_row FROM asset_registry WHERE asset_id = 'bg_nakshatra' FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'migration 606 requires bg_nakshatra registry row'; END IF;
  IF (registry_row.layer = 'brahmagyan' AND registry_row.sort_order = 15
      AND registry_row.scope = 'global' AND registry_row.asset_kind = 'data'
      AND registry_row.catalog_status = 'CURRENT' AND registry_row.is_active IS TRUE
      AND registry_row.has_writer IS TRUE AND registry_row.target_table = 'reference_nakshatra'
      AND registry_row.count_sql = 'SELECT (SELECT COUNT(*) FROM reference_nakshatra) + (SELECT COUNT(*) FROM reference_nakshatra_pada) + (SELECT COUNT(*) FROM reference_nakshatra_matrix) AS count'
      AND registry_row.target_floor = 2857
      AND (registry_row.integrity_check_sql IS NULL OR registry_row.integrity_check_sql = nakshatra_check)) IS NOT TRUE THEN
    RAISE EXCEPTION 'migration 606 refuses unknown bg_nakshatra registry contract';
  END IF;

  SELECT * INTO registry_row FROM asset_registry WHERE asset_id = 'bg_dignity_reference' FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'migration 606 requires bg_dignity_reference registry row'; END IF;
  IF (registry_row.layer = 'brahmagyan' AND registry_row.sort_order = 66
      AND registry_row.scope = 'global' AND registry_row.asset_kind = 'data'
      AND registry_row.catalog_status = 'CURRENT' AND registry_row.is_active IS TRUE
      AND registry_row.has_writer IS TRUE AND registry_row.target_table = 'bg_dignity_reference'
      AND registry_row.count_sql = 'SELECT (SELECT COUNT(*) FROM bg_dignity_reference) + (SELECT COUNT(*) FROM bg_avastha_schemes) + (SELECT COUNT(*) FROM bg_combustion_orbs) + (SELECT COUNT(*) FROM bg_graha_naisargika_friendship) + (SELECT COUNT(*) FROM bg_motion_state_thresholds) AS count'
      AND registry_row.target_floor = 151
      AND (registry_row.integrity_check_sql IS NULL OR registry_row.integrity_check_sql = dignity_check)) IS NOT TRUE THEN
    RAISE EXCEPTION 'migration 606 refuses unknown bg_dignity_reference registry contract';
  END IF;

  UPDATE asset_registry
  SET integrity_check_sql = CASE asset_id
        WHEN 'bg_cohort' THEN cohort_check
        WHEN 'bg_ontology' THEN ontology_check
        WHEN 'bg_ephemeris' THEN ephemeris_check
        WHEN 'bg_nakshatra' THEN nakshatra_check
        WHEN 'bg_dignity_reference' THEN dignity_check
      END,
      target_floor = CASE WHEN asset_id = 'bg_ontology' THEN 737 ELSE target_floor END,
      volume_explanation = CASE WHEN asset_id = 'bg_ontology' THEN ontology_explanation ELSE volume_explanation END
  WHERE asset_id IN ('bg_cohort','bg_ontology','bg_ephemeris','bg_nakshatra','bg_dignity_reference');
  GET DIAGNOSTICS changed_rows = ROW_COUNT;
  IF changed_rows <> 5 THEN
    RAISE EXCEPTION 'migration 606 expected to update 5 registry rows, updated %', changed_rows;
  END IF;

  IF (SELECT COUNT(*) FROM asset_registry
      WHERE (asset_id = 'bg_cohort' AND integrity_check_sql = cohort_check AND target_floor = 10000)
         OR (asset_id = 'bg_ontology' AND integrity_check_sql = ontology_check AND target_floor = 737 AND volume_explanation = ontology_explanation)
         OR (asset_id = 'bg_ephemeris' AND integrity_check_sql = ephemeris_check AND target_floor = 825084)
         OR (asset_id = 'bg_nakshatra' AND integrity_check_sql = nakshatra_check AND target_floor = 2857)
         OR (asset_id = 'bg_dignity_reference' AND integrity_check_sql = dignity_check AND target_floor = 151)) <> 5 THEN
    RAISE EXCEPTION 'migration 606 failed registry postflight';
  END IF;
END $$;
