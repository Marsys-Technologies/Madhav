-- Migration 620: install the exact bg_yogas integrity contract.
--
-- Production has 233 catalog rows but only 229 ontology/reference rows. Four
-- detector identities arrived through historical migration 434 rather than the
-- writer, while 11 shared rows retained older source semantics through no-op
-- conflicts. The writer now owns those four identities and transactionally
-- replaces all three projections. Production-shaped replays under
-- PYTHONHASHSEED=0 and 3 both produced the exact digests below.
-- The detector is expected to remain false after deploy until bg_yogas rebuilds.
--
-- Registry metadata only; transaction ownership belongs to migrate.ts.

DO $$
DECLARE
  registry_row asset_registry%ROWTYPE;
  changed_rows integer := 0;
  canonical_partition constant text :=
    'brahma_yoga_catalog.canonical_id; brahma_ontology.(entity_class=yoga,canonical_id); reference_yogas.canonical_id';
  canonical_explanation constant text :=
    '699 owned rows = 233 deterministic yoga definitions × 3 reconciled '
    'projections (catalog + yoga ontology partition + reference_yogas). Source '
    'definition count is 144 inline core + 4 detector-registry identities + 85 '
    'corpus-extracted rows.';
  canonical_count_sql constant text := $count$SELECT
  (SELECT count(*) FROM brahma_yoga_catalog) +
  (SELECT count(*) FROM brahma_ontology WHERE entity_class = 'yoga') +
  (SELECT count(*) FROM reference_yogas) AS count$count$;
  yoga_check constant text := $check$
SELECT
  (SELECT count(*) = 233 FROM brahma_yoga_catalog)
  AND (SELECT count(*) = 233 FROM brahma_ontology WHERE entity_class = 'yoga')
  AND (SELECT count(*) = 233 FROM reference_yogas)
  AND (SELECT count(*) FILTER (WHERE cardinality(source_chunk_ids) = 0) = 233
       FROM brahma_yoga_catalog)
  AND NOT EXISTS (
    SELECT 1 FROM brahma_yoga_catalog AS catalog
    FULL JOIN brahma_ontology AS ontology
      ON ontology.entity_class = 'yoga'
     AND ontology.canonical_id = catalog.canonical_id
    FULL JOIN reference_yogas AS reference
      ON reference.canonical_id = COALESCE(catalog.canonical_id,ontology.canonical_id)
    WHERE catalog.canonical_id IS NULL
       OR ontology.canonical_id IS NULL
       OR reference.canonical_id IS NULL
       OR ontology.canonical_name_en IS DISTINCT FROM catalog.name_en
       OR ontology.canonical_name_sa IS DISTINCT FROM catalog.name_sa
       OR reference.name_en IS DISTINCT FROM catalog.name_en
       OR reference.category IS DISTINCT FROM catalog.category
  )
  AND (SELECT count(*) = 4 FROM brahma_yoga_catalog
       WHERE canonical_id IN (
         'dhana_yoga_house_lords','raja_yoga_kendra_trikona',
         'sarasvati_yoga','vipareeta_raja_yoga'
       ))
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(canonical_id,name_sa,name_en,category,formation_rule_jsonb,
      formation_text,significations_jsonb,significations_text,
      cancellation_conditions,classical_citations,source_chunk_ids,school,rare,
      computed_strength_formula,bhanga_rules_jsonb,partial_formation_threshold,
      strength_formula_ref,result_class)::text,
    E'\n' ORDER BY canonical_id COLLATE "C"
  ),''),'UTF8')),'hex') =
    '4d4cd60f7cffe728f2d01c3146f9bf54279e5c747973ab60b2e69b7921023fa8'
   FROM brahma_yoga_catalog)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(entity_class,canonical_id,canonical_name_en,
      canonical_name_sa,synonyms,description,source_citation)::text,
    E'\n' ORDER BY entity_class COLLATE "C",canonical_id COLLATE "C"
  ),''),'UTF8')),'hex') =
    '7af1d138c492bd16bbca93b06faab6b3ff781d87aa91f8573fce6378f968fdab'
   FROM brahma_ontology WHERE entity_class = 'yoga')
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(canonical_id,name_en,category)::text,
    E'\n' ORDER BY canonical_id COLLATE "C"
  ),''),'UTF8')),'hex') =
    '1c79af1127b8e624e12c95afecf09e73f23546fe87272f5dff8146ed30d6f564'
   FROM reference_yogas)
$check$;
BEGIN
  SELECT * INTO registry_row FROM asset_registry
  WHERE asset_id = 'bg_yogas' FOR UPDATE;

  IF NOT FOUND OR (
    registry_row.layer = 'brahmagyan'
    AND registry_row.sort_order = 9
    AND registry_row.scope = 'global'
    AND registry_row.asset_kind = 'data'
    AND registry_row.catalog_status = 'CURRENT'
    AND registry_row.is_active IS TRUE
    AND registry_row.has_writer IS TRUE
    AND registry_row.target_table = 'brahma_yoga_catalog'
    AND registry_row.count_sql IN (
      'SELECT count(*) FROM brahma_yoga_catalog',
      canonical_count_sql
    )
    AND registry_row.depends_on = ARRAY['bg_ontology']::text[]
    AND registry_row.english_description =
      'Classical yoga definitions — formation rules, significations, classical citations'
    AND (
      (
        (registry_row.target_floor,registry_row.volume_explanation) IN (
          (250::bigint,
           'Catalog of named yoga patterns from BPHS / Saravali / Phaladeepika / Jaimini per design §3.9. Floor 250 (contingent on 8,193-chunk extraction yield; corrects seed value of 200).'),
          (175::bigint,
           'Rows in brahma_yoga_catalog: 81 inline core yogas + 94 corpus-verse extracted yoga definitions. Unchanged at 175 after Nadi expansion — all nadi yoga references already captured in the existing extracted set (ON CONFLICT DO NOTHING, 0 net new insertions).'),
          (699::bigint,canonical_explanation)
        )
        AND registry_row.natural_key_partition IS NULL
        AND registry_row.data_disposition IS NULL
        AND registry_row.integrity_check_sql IS NULL
      ) OR (
        registry_row.target_floor = 699
        AND registry_row.volume_explanation = canonical_explanation
        AND registry_row.count_sql = canonical_count_sql
        AND registry_row.natural_key_partition = canonical_partition
        AND registry_row.data_disposition IS NULL
        AND registry_row.integrity_check_sql = yoga_check
      )
    )
  ) IS NOT TRUE THEN
    RAISE EXCEPTION 'migration 620 refuses unknown bg_yogas registry contract';
  END IF;

  UPDATE asset_registry
  SET target_floor = 699,
      volume_explanation = canonical_explanation,
      count_sql = canonical_count_sql,
      natural_key_partition = canonical_partition,
      data_disposition = NULL,
      integrity_check_sql = yoga_check
  WHERE asset_id = 'bg_yogas';
  GET DIAGNOSTICS changed_rows = ROW_COUNT;
  IF changed_rows <> 1 THEN
    RAISE EXCEPTION 'migration 620 expected 1 registry row, updated %', changed_rows;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM asset_registry
    WHERE asset_id = 'bg_yogas'
      AND target_floor = 699
      AND volume_explanation = canonical_explanation
      AND count_sql = canonical_count_sql
      AND natural_key_partition = canonical_partition
      AND data_disposition IS NULL
      AND integrity_check_sql = yoga_check
  ) THEN
    RAISE EXCEPTION 'migration 620 postflight registry mismatch';
  END IF;
END $$;
