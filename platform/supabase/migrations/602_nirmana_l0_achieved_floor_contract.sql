-- 602_nirmana_l0_achieved_floor_contract.sql
-- Restore evidence-backed L0 floors and the current bg_reference measurement.
-- 599-601 are reserved by the dependent T0/output-digest stack.
-- Transaction ownership belongs to platform/scripts/migrate.ts.

DO $$
DECLARE
  text_index_row asset_registry%ROWTYPE;
  concordance_row asset_registry%ROWTYPE;
  reference_row asset_registry%ROWTYPE;
  reference_count_sql TEXT;
BEGIN
  SELECT * INTO text_index_row FROM asset_registry WHERE asset_id = 'bg_text_index';
  IF NOT FOUND THEN
    RAISE EXCEPTION 'migration 602 requires bg_text_index registry row';
  END IF;
  IF (
    (text_index_row.target_floor = 400 AND text_index_row.volume_explanation =
      'Distinct topic_tag count from embedded chunks. Floor 400 = topic-vocabulary coverage target; not scaled with chunk count (vocabulary size is independent of corpus depth). Per design §2.2.') OR
    (text_index_row.target_floor = 361 AND text_index_row.volume_explanation =
      'Distinct topic_tag values present on embedded classical_text_chunks. Grew from 327 to 361 after classifying 1,493 new chunks from bhrigu_nandi_nadi (608) and nadi_navamsa_patel (1,850); 3,716 nadi chunks had no keyword match and remain NULL topic_tag.') OR
    (text_index_row.target_floor = 361 AND text_index_row.volume_explanation =
      '361 distinct topic_tag values is the achieved deterministic-classifier coverage ratified by migrations 196 and 231. Raise this floor only with an evidence-backed classifier or corpus expansion; never fabricate assignments to meet the former aspirational 400.')
  ) IS NOT TRUE THEN
    RAISE EXCEPTION 'migration 602 refuses unknown bg_text_index contract: floor=%',
      text_index_row.target_floor;
  END IF;

  SELECT * INTO concordance_row FROM asset_registry WHERE asset_id = 'bg_concordance';
  IF NOT FOUND THEN
    RAISE EXCEPTION 'migration 602 requires bg_concordance registry row';
  END IF;
  IF (
    (concordance_row.target_floor = 800 AND concordance_row.volume_explanation =
      '800 = topic×school concordance rows. Cross-product metric: cardinality is topic_count × school_count, not chunk-proportional. Chunk-pointer index per (topic, school); synthesis at L1+ query-time.') OR
    (concordance_row.target_floor = 720 AND concordance_row.volume_explanation =
      'Rows in classical_attributions: one per (topic_id × school) pair where the corpus has ≥1 classified chunk. Grew from 477 to 720 after the nadi school dimension was added for bhrigu_nandi_nadi and nadi_navamsa_patel, contributing 243 new (topic × nadi) rows across 361 distinct topics.') OR
    (concordance_row.target_floor = 720 AND concordance_row.volume_explanation =
      '720 achieved topic×school concordance rows, measured in production and ratified by migration 231. Cross-product metric: cardinality is topic_count × school_count, not chunk-proportional. Raise the floor only after a verified corpus expansion.')
  ) IS NOT TRUE THEN
    RAISE EXCEPTION 'migration 602 refuses unknown bg_concordance contract: floor=%',
      concordance_row.target_floor;
  END IF;

  SELECT * INTO reference_row FROM asset_registry WHERE asset_id = 'bg_reference';
  IF NOT FOUND THEN
    RAISE EXCEPTION 'migration 602 requires bg_reference registry row';
  END IF;
  reference_count_sql := regexp_replace(trim(reference_row.count_sql), '[[:space:]]+', ' ', 'g');
  IF reference_row.target_floor IS NULL OR
     reference_row.target_floor NOT IN (1242, 1485) OR
     reference_row.target_table IS NULL OR
     reference_row.target_table NOT IN ('reference_nakshatras', 'reference_planets') OR
     reference_row.size_sql IS NULL OR
     reference_row.size_sql NOT IN (
       'SELECT pg_total_relation_size(''reference_nakshatras'')',
       'SELECT pg_total_relation_size(''reference_planets'')'
     ) OR reference_count_sql IS NULL OR reference_count_sql NOT IN (
       'SELECT (SELECT count(*) FROM reference_planets) + (SELECT count(*) FROM reference_signs) + (SELECT count(*) FROM reference_aspects) + (SELECT count(*) FROM reference_vargas) + (SELECT count(*) FROM reference_houses) + (SELECT count(*) FROM reference_strength_systems) + (SELECT count(*) FROM reference_karakas) + (SELECT count(*) FROM reference_upagrahas) + (SELECT count(*) FROM reference_constants) + (SELECT count(*) FROM reference_topic_tags) + (SELECT count(*) FROM reference_glossary) AS count',
       'SELECT (SELECT count(*) FROM reference_planets) + (SELECT count(*) FROM reference_nakshatras) + (SELECT count(*) FROM reference_signs) + (SELECT count(*) FROM reference_aspects) + (SELECT count(*) FROM reference_vargas) + (SELECT count(*) FROM reference_houses) + (SELECT count(*) FROM reference_strength_systems) + (SELECT count(*) FROM reference_karakas) + (SELECT count(*) FROM reference_upagrahas) + (SELECT count(*) FROM reference_constants) + (SELECT count(*) FROM reference_topic_tags) + (SELECT count(*) FROM reference_glossary) + (SELECT count(*) FROM reference_yogas) + (SELECT count(*) FROM reference_doshas) + (SELECT count(*) FROM reference_dasha_systems) AS count',
       'SELECT (SELECT count(*) FROM reference_planets) + (SELECT count(*) FROM reference_signs) + (SELECT count(*) FROM reference_aspects) + (SELECT count(*) FROM reference_vargas) + (SELECT count(*) FROM reference_houses) + (SELECT count(*) FROM reference_strength_systems) + (SELECT count(*) FROM reference_karakas) + (SELECT count(*) FROM reference_upagrahas) + (SELECT count(*) FROM reference_constants) + (SELECT count(*) FROM reference_topic_tags) + (SELECT count(*) FROM reference_glossary) + (SELECT count(*) FROM reference_yogas) + (SELECT count(*) FROM reference_doshas) + (SELECT count(*) FROM reference_dasha_systems) AS count'
     ) OR reference_row.english_description IS NULL OR reference_row.english_description NOT IN (
       'The holy grail of L0 — structured properties of every classical Jyotish concept across 15 specialized typed tables.',
       'Structured properties owned by bg_reference across 11 current typed tables; yoga, dosha, and dasha reference rows belong to their dedicated assets.'
     ) OR reference_row.volume_explanation IS NULL OR reference_row.volume_explanation NOT IN (
       'Sum of 15 reference_* tables (per design §3.2). Each table is normalized + typed; ontology resolves names, reference holds properties.',
       'bg_reference: 1,269 rows across 12 own reference tables seeded in Tier 0 campaign build 2026-06-09. Tables: reference_planets(11), reference_nakshatras(27), reference_signs(12), reference_aspects(19), reference_vargas(19), reference_houses(12), reference_strength_systems(33), reference_karakas(77), reference_upagrahas(11), reference_constants(203), reference_topic_tags(481), reference_glossary(364). Brief aspiration was ≥1,225 own-12-tables. Floor set to achieved count (1,269).',
       '1,242 achieved rows across the 11 tables owned by bg_reference, as measured in the BA full-asset audit after migration 371 removed cross-asset double-counting. reference_yogas, reference_doshas, and reference_dasha_systems are owned by their dedicated assets; deprecated reference_nakshatras is excluded.'
     ) THEN
    RAISE EXCEPTION 'migration 602 refuses unknown bg_reference measurement contract';
  END IF;
END
$$;

UPDATE asset_registry
SET target_floor = 361,
    volume_explanation =
      '361 distinct topic_tag values is the achieved deterministic-classifier coverage ratified by migrations 196 and 231. Raise this floor only with an evidence-backed classifier or corpus expansion; never fabricate assignments to meet the former aspirational 400.'
WHERE asset_id = 'bg_text_index';

UPDATE asset_registry
SET target_floor = 720,
    volume_explanation =
      '720 achieved topic×school concordance rows, measured in production and ratified by migration 231. Cross-product metric: cardinality is topic_count × school_count, not chunk-proportional. Raise the floor only after a verified corpus expansion.'
WHERE asset_id = 'bg_concordance';

UPDATE asset_registry
SET target_floor = 1242,
    target_table = 'reference_planets',
    size_sql = 'SELECT pg_total_relation_size(''reference_planets'')',
    count_sql = 'SELECT (SELECT count(*) FROM reference_planets) + (SELECT count(*) FROM reference_signs) + (SELECT count(*) FROM reference_aspects) + (SELECT count(*) FROM reference_vargas) + (SELECT count(*) FROM reference_houses) + (SELECT count(*) FROM reference_strength_systems) + (SELECT count(*) FROM reference_karakas) + (SELECT count(*) FROM reference_upagrahas) + (SELECT count(*) FROM reference_constants) + (SELECT count(*) FROM reference_topic_tags) + (SELECT count(*) FROM reference_glossary) AS count',
    english_description = 'Structured properties owned by bg_reference across 11 current typed tables; yoga, dosha, and dasha reference rows belong to their dedicated assets.',
    volume_explanation = '1,242 achieved rows across the 11 tables owned by bg_reference, as measured in the BA full-asset audit after migration 371 removed cross-asset double-counting. reference_yogas, reference_doshas, and reference_dasha_systems are owned by their dedicated assets; deprecated reference_nakshatras is excluded.'
WHERE asset_id = 'bg_reference';

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM asset_registry
    WHERE asset_id = 'bg_text_index' AND target_floor = 361
      AND volume_explanation = '361 distinct topic_tag values is the achieved deterministic-classifier coverage ratified by migrations 196 and 231. Raise this floor only with an evidence-backed classifier or corpus expansion; never fabricate assignments to meet the former aspirational 400.'
  ) OR NOT EXISTS (
    SELECT 1 FROM asset_registry
    WHERE asset_id = 'bg_concordance' AND target_floor = 720
      AND volume_explanation = '720 achieved topic×school concordance rows, measured in production and ratified by migration 231. Cross-product metric: cardinality is topic_count × school_count, not chunk-proportional. Raise the floor only after a verified corpus expansion.'
  ) OR NOT EXISTS (
    SELECT 1 FROM asset_registry
    WHERE asset_id = 'bg_reference'
      AND target_floor = 1242
      AND target_table = 'reference_planets'
      AND size_sql = 'SELECT pg_total_relation_size(''reference_planets'')'
      AND count_sql NOT LIKE '%reference_yogas%'
      AND count_sql NOT LIKE '%reference_doshas%'
      AND count_sql NOT LIKE '%reference_dasha_systems%'
      AND count_sql NOT LIKE '%reference_nakshatras%'
      AND english_description = 'Structured properties owned by bg_reference across 11 current typed tables; yoga, dosha, and dasha reference rows belong to their dedicated assets.'
      AND volume_explanation = '1,242 achieved rows across the 11 tables owned by bg_reference, as measured in the BA full-asset audit after migration 371 removed cross-asset double-counting. reference_yogas, reference_doshas, and reference_dasha_systems are owned by their dedicated assets; deprecated reference_nakshatras is excluded.'
  ) THEN
    RAISE EXCEPTION 'migration 602 postflight contract mismatch';
  END IF;
END
$$;

-- Forward reversal: restore prior values only after new evidence ratifies them;
-- never revert mechanically to obsolete floors or deprecated measurement SQL.
