-- Migration 622: exact bg_doshas integrity contract.
-- Live production and clean source were byte-identical at 79 rows in each of
-- three projections. The writer now replaces them atomically so future drift
-- cannot survive a rebuild. Transaction ownership belongs to migrate.ts.

DO $$
DECLARE
  registry_row asset_registry%ROWTYPE;
  changed_rows integer := 0;
  canonical_partition constant text :=
    'brahma_dosha_catalog.canonical_id; brahma_ontology.(entity_class=dosha,canonical_id); reference_doshas.canonical_id';
  canonical_explanation constant text :=
    '237 owned rows = 79 deterministic dosha definitions × 3 reconciled '
    'projections (catalog + dosha ontology partition + reference_doshas). '
    'Production and clean-source replay were byte-identical before convergence hardening.';
  canonical_count_sql constant text := $count$SELECT
  (SELECT count(*) FROM brahma_dosha_catalog) +
  (SELECT count(*) FROM brahma_ontology WHERE entity_class = 'dosha') +
  (SELECT count(*) FROM reference_doshas) AS count$count$;
  dosha_check constant text := $check$
SELECT
  (SELECT count(*) = 79 FROM brahma_dosha_catalog)
  AND (SELECT count(*) = 79 FROM brahma_ontology WHERE entity_class='dosha')
  AND (SELECT count(*) = 79 FROM reference_doshas)
  AND (SELECT count(*) FILTER (WHERE cardinality(source_chunk_ids)=0
    AND cardinality(associated_remedies)=0) = 79 FROM brahma_dosha_catalog)
  AND NOT EXISTS (
    SELECT 1 FROM brahma_dosha_catalog AS catalog
    FULL JOIN brahma_ontology AS ontology
      ON ontology.entity_class='dosha' AND ontology.canonical_id=catalog.canonical_id
    FULL JOIN reference_doshas AS reference
      ON reference.canonical_id=COALESCE(catalog.canonical_id,ontology.canonical_id)
    WHERE catalog.canonical_id IS NULL OR ontology.canonical_id IS NULL
       OR reference.canonical_id IS NULL
       OR ontology.canonical_name_en IS DISTINCT FROM catalog.name_en
       OR ontology.canonical_name_sa IS DISTINCT FROM catalog.name_sa
       OR reference.name_en IS DISTINCT FROM catalog.name_en
       OR reference.category IS DISTINCT FROM catalog.category
  )
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(canonical_id,name_sa,name_en,category,formation_rule_jsonb,
      formation_text,effects_text,severity_grades,cancellation_conditions,
      classical_citations,source_chunk_ids,associated_remedies,school)::text,
    E'\n' ORDER BY canonical_id COLLATE "C"),''),'UTF8')),'hex') =
    'cfb21a5342bda3a911f55597cac3367b727a79953ccef3349ad7f49c98acfcd4'
   FROM brahma_dosha_catalog)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(entity_class,canonical_id,canonical_name_en,
      canonical_name_sa,synonyms,description,source_citation)::text,
    E'\n' ORDER BY entity_class COLLATE "C",canonical_id COLLATE "C"),''),'UTF8')),'hex') =
    'ee5dedf6e9934f42883ff268c3e485648577c6e528bfb76b7b839937b4572984'
   FROM brahma_ontology WHERE entity_class='dosha')
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(canonical_id,name_en,category)::text,
    E'\n' ORDER BY canonical_id COLLATE "C"),''),'UTF8')),'hex') =
    '3fd442d6e8bfcb54fa5f4752907a2ef057ab1f49ec12aad9536a833b4e04d9a4'
   FROM reference_doshas)
$check$;
BEGIN
  SELECT * INTO registry_row FROM asset_registry WHERE asset_id='bg_doshas' FOR UPDATE;
  IF NOT FOUND OR (
    registry_row.layer='brahmagyan' AND registry_row.sort_order=11
    AND registry_row.scope='global' AND registry_row.asset_kind='data'
    AND registry_row.catalog_status='CURRENT' AND registry_row.is_active IS TRUE
    AND registry_row.has_writer IS TRUE AND registry_row.target_table='brahma_dosha_catalog'
    AND registry_row.count_sql IN ('SELECT count(*) FROM brahma_dosha_catalog',canonical_count_sql)
    AND registry_row.depends_on=ARRAY['bg_ontology']::text[]
    AND registry_row.english_description=
      'Classical dosha definitions — formation rules, effects, severity, cancellation conditions'
    AND (
      ((registry_row.target_floor,registry_row.volume_explanation) IN (
        (50::bigint,'Catalog of named dosha patterns (Manglik, Kala-sarpa, Kemadruma, etc.) per design §3.11'),
        (237::bigint,canonical_explanation))
       AND registry_row.natural_key_partition IS NULL
       AND registry_row.data_disposition IS NULL AND registry_row.integrity_check_sql IS NULL)
      OR (registry_row.target_floor=237 AND registry_row.count_sql=canonical_count_sql
       AND registry_row.volume_explanation=canonical_explanation
       AND registry_row.natural_key_partition=canonical_partition
       AND registry_row.data_disposition IS NULL AND registry_row.integrity_check_sql=dosha_check)
    )
  ) IS NOT TRUE THEN
    RAISE EXCEPTION 'migration 622 refuses unknown bg_doshas registry contract';
  END IF;
  UPDATE asset_registry SET target_floor=237,count_sql=canonical_count_sql,
    volume_explanation=canonical_explanation,natural_key_partition=canonical_partition,
    data_disposition=NULL,integrity_check_sql=dosha_check WHERE asset_id='bg_doshas';
  GET DIAGNOSTICS changed_rows = ROW_COUNT;
  IF changed_rows<>1 THEN RAISE EXCEPTION 'migration 622 expected 1 row, updated %',changed_rows; END IF;
  IF NOT EXISTS (SELECT 1 FROM asset_registry WHERE asset_id='bg_doshas'
    AND target_floor=237 AND count_sql=canonical_count_sql
    AND volume_explanation=canonical_explanation AND natural_key_partition=canonical_partition
    AND data_disposition IS NULL AND integrity_check_sql=dosha_check) THEN
    RAISE EXCEPTION 'migration 622 postflight registry mismatch';
  END IF;
END $$;
