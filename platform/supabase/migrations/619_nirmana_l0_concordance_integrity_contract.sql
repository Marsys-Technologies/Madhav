-- Migration 619: install the exact bg_concordance integrity contract.
--
-- The production table has 720 historical rows, but its source topic index
-- already contains two chunks tagged lord_1st_in_11th. A production-shaped
-- replay proved the no-op conflict path had preserved stale output: 473 shared
-- rows had stale rule pointers, 32 stale text pointers, 6 stale confidence
-- values, and the source-backed lord_1st_in_11th row was absent. The convergent
-- writer produces 721 rows with the digest below under PYTHONHASHSEED=0 and 3.
-- The detector is expected to remain false after deploy until bg_rules and
-- bg_concordance rebuild in dependency order.
--
-- Registry metadata only; transaction ownership belongs to migrate.ts.

DO $$
DECLARE
  registry_row asset_registry%ROWTYPE;
  changed_rows integer := 0;
  canonical_partition constant text :=
    'classical_attributions.(topic_id,school)';
  canonical_explanation constant text :=
    '721 deterministic topic×school concordance rows from the frozen 10,651-chunk '
    'topic index and canonical 3,002-rule projection. The convergent rebuild '
    'repairs stale pointers and includes lord_1st_in_11th, whose tagged chunks '
    'existed in production while its historical concordance row was absent.';
  canonical_dependencies constant text[] :=
    ARRAY['bg_texts','bg_text_index','bg_reference','bg_rules']::text[];
  concordance_check constant text := $check$
SELECT
  count(*) = 721
  AND count(DISTINCT topic_id) = 361
  AND count(DISTINCT (topic_id,school)) = 721
  AND array_agg(DISTINCT school ORDER BY school) =
    ARRAY['jaimini','nadi','parashari','phaladeepika']::text[]
  AND count(*) FILTER (WHERE cardinality(source_text_ids) > 0) = 721
  AND count(*) FILTER (WHERE cardinality(source_chunk_ids) = 0) = 721
  AND count(*) FILTER (WHERE cardinality(rule_ids) > 0) = 721
  AND count(*) FILTER (WHERE match_method = 'topic_tag') = 721
  AND count(*) FILTER (
    WHERE match_confidence IN (0.200,0.400,0.600,0.800,1.000)
  ) = 721
  AND NOT EXISTS (
    SELECT 1 FROM classical_attributions AS attribution
    LEFT JOIN reference_topic_tags AS topic
      ON topic.canonical_id = attribution.topic_id
    WHERE topic.canonical_id IS NULL
       OR topic.name IS DISTINCT FROM attribution.topic_canonical_name
       OR topic.category IS DISTINCT FROM attribution.topic_category
  )
  AND NOT EXISTS (
    SELECT 1
    FROM classical_attributions AS attribution
    CROSS JOIN LATERAL unnest(attribution.source_text_ids) AS source(text_id)
    WHERE NOT EXISTS (
      SELECT 1 FROM classical_text_chunks AS chunk
      WHERE chunk.topic_tag = attribution.topic_id
        AND chunk.text_id = source.text_id
    )
  )
  AND NOT EXISTS (
    SELECT 1
    FROM classical_attributions AS attribution
    CROSS JOIN LATERAL unnest(attribution.rule_ids) AS source(rule_id)
    WHERE NOT EXISTS (
      SELECT 1 FROM sutravali_rules AS rule
      WHERE rule.rule_id = source.rule_id
        AND rule.text_id = ANY(attribution.source_text_ids)
    )
  )
  AND encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(topic_id,topic_canonical_name,topic_category,school,
      source_text_ids,source_chunk_ids,rule_ids,match_method,match_confidence)::text,
    E'\n' ORDER BY topic_id COLLATE "C",school COLLATE "C"
  ),''),'UTF8')),'hex') =
    '9e2837388c783be0dc57361e52d8de344b2b041f9bb5e9eb39fa4b67412f5893'
FROM classical_attributions
$check$;
BEGIN
  SELECT * INTO registry_row FROM asset_registry
  WHERE asset_id = 'bg_concordance' FOR UPDATE;

  IF NOT FOUND OR (
    registry_row.layer = 'brahmagyan'
    AND registry_row.sort_order = 8
    AND registry_row.scope = 'global'
    AND registry_row.asset_kind = 'data'
    AND registry_row.catalog_status = 'CURRENT'
    AND registry_row.is_active IS TRUE
    AND registry_row.has_writer IS TRUE
    AND registry_row.target_table = 'classical_attributions'
    AND registry_row.count_sql = 'SELECT count(*) FROM classical_attributions'
    AND registry_row.depends_on IN (
      ARRAY['bg_rules']::text[],
      canonical_dependencies
    )
    AND registry_row.english_description =
      'Cross-school chunk-pointer index per (topic, school) — chunk refs for L1+ synthesis at query-time'
    AND (
      (
        (registry_row.target_floor,registry_row.volume_explanation) IN (
          (800::bigint,
           '800 = topic×school concordance rows. Cross-product metric: cardinality is topic_count × school_count, not chunk-proportional. Chunk-pointer index per (topic, school); synthesis at L1+ query-time.'),
          (720::bigint,
           'Rows in classical_attributions: one per (topic_id × school) pair where the corpus has ≥1 classified chunk. Grew from 477 to 720 after the nadi school dimension was added for bhrigu_nandi_nadi and nadi_navamsa_patel, contributing 243 new (topic × nadi) rows across 361 distinct topics.'),
          (720::bigint,
           '720 achieved topic×school concordance rows, measured in production and ratified by migration 231. Cross-product metric: cardinality is topic_count × school_count, not chunk-proportional. Raise the floor only after a verified corpus expansion.'),
          (721::bigint,canonical_explanation)
        )
        AND registry_row.natural_key_partition IS NULL
        AND registry_row.data_disposition IS NULL
        AND registry_row.integrity_check_sql IS NULL
      ) OR (
        registry_row.target_floor = 721
        AND registry_row.volume_explanation = canonical_explanation
        AND registry_row.depends_on = canonical_dependencies
        AND registry_row.natural_key_partition = canonical_partition
        AND registry_row.data_disposition IS NULL
        AND registry_row.integrity_check_sql = concordance_check
      )
    )
  ) IS NOT TRUE THEN
    RAISE EXCEPTION 'migration 619 refuses unknown bg_concordance registry contract';
  END IF;

  UPDATE asset_registry
  SET target_floor = 721,
      volume_explanation = canonical_explanation,
      depends_on = canonical_dependencies,
      natural_key_partition = canonical_partition,
      data_disposition = NULL,
      integrity_check_sql = concordance_check
  WHERE asset_id = 'bg_concordance';
  GET DIAGNOSTICS changed_rows = ROW_COUNT;
  IF changed_rows <> 1 THEN
    RAISE EXCEPTION 'migration 619 expected 1 registry row, updated %', changed_rows;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM asset_registry
    WHERE asset_id = 'bg_concordance'
      AND target_floor = 721
      AND volume_explanation = canonical_explanation
      AND depends_on = canonical_dependencies
      AND natural_key_partition = canonical_partition
      AND data_disposition IS NULL
      AND integrity_check_sql = concordance_check
  ) THEN
    RAISE EXCEPTION 'migration 619 postflight registry mismatch';
  END IF;
END $$;
