-- 608_nirmana_bg_remedies_integrity_contract.sql
--
-- Install the executable integrity contract for the governed bg_remedies
-- repair/rebuild. The corpus is intentionally untouched: production remains
-- false until the deterministic writer is replayed from the frozen sources.
-- Disposition: REPAIR. Execution mode: GOVERNED REBUILD.
-- Transaction ownership belongs to platform/scripts/migrate.ts.

DO $$
DECLARE
  registry_row asset_registry%ROWTYPE;
  changed_rows integer;
  canonical_description constant text :=
    'Classical remedies: mantras, gemstones, charity, vrata, yantras, puja, tantric, ayurvedic, vastu, behavioral';
  legacy_seed_volume constant text :=
    '266 remedies = writer''s designed deterministic ceiling: gen_planet_matrix(108) + dosha-linked(102) + legacy(54) + corpus_sweep net-new(2). Floor = achieved count per floors-are-aspirational policy (CLAUDE.md §N.4); ZERO LLM, ZERO fabrication is a hard writer constraint, so this floor cannot be raised without a native-judgment decision to expand the deterministic corpus design.';
  legacy_production_volume constant text :=
    '266 remedies = writer''s designed deterministic ceiling: gen_planet_matrix(108) + dosha-linked(102) + legacy(54) + corpus_sweep net-new(2). Floor = achieved count per floors-are-aspirational policy (CLAUDE.md §N.4); ZERO LLM, ZERO fabrication is a hard writer constraint, so this floor cannot be raised without a native-judgment decision to expand the deterministic corpus design. Re-corrected 2026-07-05 after drifting back to a stale 800 via asset_registry_seed.ts.';
  canonical_volume constant text :=
    '341 achieved remedies from the frozen deterministic build: 283 static writer rows + 54 bg_texts-derived sweep rows + 4 accepted tantric rows. Integrity enforces exact source-derived identity and closed taxonomies; ZERO LLM and ZERO fabrication.';
  remedy_check constant text := $integrity$
WITH summary AS (
  SELECT
    count(*) AS total,
    count(DISTINCT remedy_id) AS distinct_ids,
    md5(string_agg(remedy_id, E'\n' ORDER BY remedy_id COLLATE "C")) AS id_md5,
    array_agg(DISTINCT planet ORDER BY planet) AS planets,
    array_agg(DISTINCT domain ORDER BY domain) AS domains,
    array_agg(DISTINCT remedy_type ORDER BY remedy_type) AS remedy_types,
    count(*) FILTER (WHERE category IS NULL) AS uncategorized_rows,
    count(*) FILTER (WHERE category = 'corpus_sweep') AS sweep_rows,
    count(*) FILTER (WHERE category = 'corpus_sweep' AND scaffold_status = 'live') AS sweep_live,
    count(*) FILTER (WHERE category = 'corpus_sweep' AND scaffold_status = 'review') AS sweep_review,
    count(*) FILTER (WHERE category = 'tantric') AS tantric_rows,
    count(*) FILTER (WHERE category = 'nakshatra_shanti') AS nakshatra_rows,
    count(*) FILTER (WHERE scaffold_status = 'live') AS live_rows,
    count(*) FILTER (WHERE scaffold_status = 'review') AS review_rows
  FROM brahma_remedy_corpus
), planet_counts AS (
  SELECT coalesce(jsonb_object_agg(planet, row_count), '{}'::jsonb) AS value
  FROM (
    SELECT planet, count(*) AS row_count
    FROM brahma_remedy_corpus WHERE planet IS NOT NULL GROUP BY planet
  ) counted
), domain_counts AS (
  SELECT coalesce(jsonb_object_agg(domain, row_count), '{}'::jsonb) AS value
  FROM (
    SELECT domain, count(*) AS row_count
    FROM brahma_remedy_corpus WHERE domain IS NOT NULL GROUP BY domain
  ) counted
), type_counts AS (
  SELECT coalesce(jsonb_object_agg(remedy_type, row_count), '{}'::jsonb) AS value
  FROM (
    SELECT remedy_type, count(*) AS row_count
    FROM brahma_remedy_corpus WHERE remedy_type IS NOT NULL GROUP BY remedy_type
  ) counted
)
SELECT (
  summary.total = 341
  AND summary.distinct_ids = 341
  AND summary.id_md5 = '8bac868a1b9708eedee44a7266237d08'
  AND summary.planets = ARRAY['jupiter','ketu','mars','mercury','moon','rahu','saturn','sun','venus']::text[]
  AND summary.domains = ARRAY['career','education','general','health','marriage','spirituality','wealth']::text[]
  AND summary.remedy_types = ARRAY['ayurvedic','behavioral','charity','gemstone','homa','japa','mantra','puja','tantric','vrata','yantra']::text[]
  AND planet_counts.value = '{"jupiter":40,"ketu":26,"mars":33,"mercury":26,"moon":50,"rahu":42,"saturn":39,"sun":53,"venus":32}'::jsonb
  AND domain_counts.value = '{"career":12,"education":5,"general":260,"health":18,"marriage":29,"spirituality":6,"wealth":11}'::jsonb
  AND type_counts.value = '{"ayurvedic":1,"behavioral":9,"charity":67,"gemstone":22,"homa":10,"japa":26,"mantra":68,"puja":76,"tantric":4,"vrata":35,"yantra":23}'::jsonb
  AND summary.uncategorized_rows = 256
  AND summary.sweep_rows = 54
  AND summary.sweep_live = 15
  AND summary.sweep_review = 39
  AND summary.tantric_rows = 4
  AND summary.nakshatra_rows = 27
  AND summary.live_rows = 302
  AND summary.review_rows = 39
  AND NOT EXISTS (
    SELECT 1
    FROM brahma_remedy_corpus
    WHERE remedy_id IS NULL OR btrim(remedy_id) = ''
       OR planet IS NULL OR btrim(planet) = ''
       OR domain IS NULL OR btrim(domain) = ''
       OR remedy_type IS NULL OR btrim(remedy_type) = ''
       OR prescription_text IS NULL OR btrim(prescription_text) = ''
       OR source_canonical_id IS NULL OR btrim(source_canonical_id) = ''
       OR source_citation IS NULL OR btrim(source_citation) = ''
       OR classical_ref IS NULL OR btrim(classical_ref) = ''
       OR confidence IS NULL OR confidence < 0 OR confidence > 1
       OR scaffold_status IS NULL OR scaffold_status NOT IN ('live', 'review')
       OR (category IS DISTINCT FROM 'corpus_sweep'
           AND scaffold_status IS DISTINCT FROM 'live')
       OR ((left(remedy_id, 6) = 'sweep_') IS DISTINCT FROM
           coalesce(category = 'corpus_sweep', false))
       OR ((left(remedy_id, 10) = 'nakshatra_') IS DISTINCT FROM
           coalesce(category = 'nakshatra_shanti', false))
       OR ((left(remedy_id, 4) = 'tan_') IS DISTINCT FROM
           coalesce(category = 'tantric', false))
       OR (category = 'tantric' AND (
           remedy_type IS DISTINCT FROM 'tantric'
           OR classical_attestation_text IS NULL
           OR btrim(classical_attestation_text) = ''
           OR jsonb_typeof(ingredients_jsonb) IS DISTINCT FROM 'object'
           OR ingredients_jsonb = '{}'::jsonb
           OR jsonb_typeof(timing_rules_jsonb) IS DISTINCT FROM 'object'
           OR timing_rules_jsonb = '{}'::jsonb
       ))
  )
) AS integrity_ok
FROM summary CROSS JOIN planet_counts CROSS JOIN domain_counts CROSS JOIN type_counts
$integrity$;
BEGIN
  SELECT * INTO registry_row
  FROM asset_registry
  WHERE asset_id = 'bg_remedies'
  FOR UPDATE;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'migration 608 requires asset_registry.bg_remedies';
  END IF;

  IF (
    registry_row.layer = 'brahmagyan'
    AND registry_row.sort_order = 7
    AND registry_row.scope = 'global'
    AND registry_row.asset_kind = 'data'
    AND registry_row.catalog_status = 'CURRENT'
    AND registry_row.is_active = true
    AND registry_row.has_writer = true
    AND registry_row.english_description = canonical_description
    AND registry_row.target_table = 'brahma_remedy_corpus'
    AND registry_row.count_sql = 'SELECT count(*) FROM brahma_remedy_corpus'
    AND registry_row.size_sql = 'SELECT pg_total_relation_size(''brahma_remedy_corpus'')'
    AND registry_row.depends_on IN (ARRAY[]::text[], ARRAY['bg_texts']::text[])
    AND (
      (registry_row.target_floor = 266
       AND registry_row.volume_explanation IN (legacy_seed_volume, legacy_production_volume)
       AND registry_row.integrity_check_sql IS NULL)
      OR
      (registry_row.target_floor = 341
       AND registry_row.volume_explanation = canonical_volume
       AND (registry_row.integrity_check_sql IS NULL
            OR registry_row.integrity_check_sql = remedy_check))
    )
  ) IS NOT TRUE THEN
    RAISE EXCEPTION
      'migration 608 refuses unknown bg_remedies registry contract';
  END IF;

  UPDATE asset_registry
  SET target_floor = 341,
      english_description = canonical_description,
      volume_explanation = canonical_volume,
      depends_on = ARRAY['bg_texts']::text[],
      integrity_check_sql = remedy_check
  WHERE asset_id = 'bg_remedies';
  GET DIAGNOSTICS changed_rows = ROW_COUNT;

  IF changed_rows <> 1 THEN
    RAISE EXCEPTION 'migration 608 expected one bg_remedies registry row, updated %', changed_rows;
  END IF;

  SELECT * INTO registry_row
  FROM asset_registry
  WHERE asset_id = 'bg_remedies';

  IF (
    registry_row.target_floor = 341
    AND registry_row.english_description = canonical_description
    AND registry_row.volume_explanation = canonical_volume
    AND registry_row.depends_on = ARRAY['bg_texts']::text[]
    AND registry_row.integrity_check_sql = remedy_check
  ) IS NOT TRUE THEN
    RAISE EXCEPTION 'migration 608 failed bg_remedies registry postflight';
  END IF;
END $$;

-- Manual forward reversal: restore the immediately previous exact registry
-- state only after confirming no governed rebuild receipt relies on this
-- contract. Corpus rows are not changed by this migration or its reversal.
