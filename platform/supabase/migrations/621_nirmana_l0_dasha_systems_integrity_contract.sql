-- Migration 621: exact bg_dasha_systems integrity contract.
-- Production carried KP only in the catalog and an orphan jaimini_chara
-- ontology identity. The writer now owns KP and replaces all three projections.
-- PYTHONHASHSEED=0 and 3 production-shaped replays produced these digests.

DO $$
DECLARE
  registry_row asset_registry%ROWTYPE;
  changed_rows integer := 0;
  canonical_partition constant text :=
    'brahma_dasha_systems.canonical_id; brahma_ontology.(entity_class=dasha_system,canonical_id); reference_dasha_systems.canonical_id';
  canonical_explanation constant text :=
    '60 owned rows = 20 deterministic dasha-system definitions × 3 reconciled '
    'projections (catalog + dasha-system ontology partition + '
    'reference_dasha_systems), including the governed KP subdivision identity.';
  canonical_count_sql constant text := $count$SELECT
  (SELECT count(*) FROM brahma_dasha_systems) +
  (SELECT count(*) FROM brahma_ontology WHERE entity_class = 'dasha_system') +
  (SELECT count(*) FROM reference_dasha_systems) AS count$count$;
  dasha_check constant text := $check$
SELECT
  (SELECT count(*) = 20 FROM brahma_dasha_systems)
  AND (SELECT count(*) = 20 FROM brahma_ontology WHERE entity_class='dasha_system')
  AND (SELECT count(*) = 20 FROM reference_dasha_systems)
  AND NOT EXISTS (
    SELECT 1 FROM brahma_dasha_systems AS catalog
    FULL JOIN brahma_ontology AS ontology
      ON ontology.entity_class='dasha_system'
     AND ontology.canonical_id=catalog.canonical_id
    FULL JOIN reference_dasha_systems AS reference
      ON reference.canonical_id=COALESCE(catalog.canonical_id,ontology.canonical_id)
    WHERE catalog.canonical_id IS NULL OR ontology.canonical_id IS NULL
       OR reference.canonical_id IS NULL
       OR ontology.canonical_name_en IS DISTINCT FROM catalog.name_en
       OR ontology.canonical_name_sa IS DISTINCT FROM catalog.name_sa
       OR reference.name_en IS DISTINCT FROM catalog.name_en
       OR reference.school IS DISTINCT FROM catalog.school
  )
  AND EXISTS (SELECT 1 FROM brahma_dasha_systems WHERE canonical_id='kp')
  AND NOT EXISTS (SELECT 1 FROM brahma_ontology
                  WHERE entity_class='dasha_system' AND canonical_id='jaimini_chara')
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(canonical_id,name_sa,name_en,total_cycle_years,base_unit,
      sequence_jsonb,computation_method,computation_pseudocode,conditions_for_use,
      school,classical_citations,source_chunk_ids,python_impl_module)::text,
    E'\n' ORDER BY canonical_id COLLATE "C"),''),'UTF8')),'hex') =
    '30742da6005fc977124192ae27ee1ca0bb29dd5363267860dfd8260e8bb3173a'
   FROM brahma_dasha_systems)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(entity_class,canonical_id,canonical_name_en,
      canonical_name_sa,synonyms,description,source_citation)::text,
    E'\n' ORDER BY entity_class COLLATE "C",canonical_id COLLATE "C"),''),'UTF8')),'hex') =
    '58a2b8b98dddcc6bb5dec73af8de386af3768457d2b3e2aea739bc435c83d4c9'
   FROM brahma_ontology WHERE entity_class='dasha_system')
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(canonical_id,name_en,school)::text,
    E'\n' ORDER BY canonical_id COLLATE "C"),''),'UTF8')),'hex') =
    '46ec3fd9da97e6e91ec60acd34a1ece858f7e7adefecd7b6955620980f120a04'
   FROM reference_dasha_systems)
$check$;
BEGIN
  SELECT * INTO registry_row FROM asset_registry
  WHERE asset_id='bg_dasha_systems' FOR UPDATE;
  IF NOT FOUND OR (
    registry_row.layer='brahmagyan' AND registry_row.sort_order=10
    AND registry_row.scope='global' AND registry_row.asset_kind='data'
    AND registry_row.catalog_status='CURRENT' AND registry_row.is_active IS TRUE
    AND registry_row.has_writer IS TRUE
    AND registry_row.target_table='brahma_dasha_systems'
    AND registry_row.count_sql IN ('SELECT count(*) FROM brahma_dasha_systems',canonical_count_sql)
    AND registry_row.depends_on=ARRAY['bg_ontology']::text[]
    AND registry_row.english_description=
      'Classical dasha system definitions — sequence rules, computation methods, conditions for use'
    AND (
      ((registry_row.target_floor,registry_row.volume_explanation) IN (
        (18::bigint,'18 named dasha systems (Vimshottari, Yogini, Chara, Kalachakra, etc.) per actual build count.'),
        (60::bigint,canonical_explanation))
       AND registry_row.natural_key_partition IS NULL
       AND registry_row.data_disposition IS NULL
       AND registry_row.integrity_check_sql IS NULL)
      OR (registry_row.target_floor=60
       AND registry_row.volume_explanation=canonical_explanation
       AND registry_row.count_sql=canonical_count_sql
       AND registry_row.natural_key_partition=canonical_partition
       AND registry_row.data_disposition IS NULL
       AND registry_row.integrity_check_sql=dasha_check)
    )
  ) IS NOT TRUE THEN
    RAISE EXCEPTION 'migration 621 refuses unknown bg_dasha_systems registry contract';
  END IF;

  UPDATE asset_registry SET target_floor=60,count_sql=canonical_count_sql,
    volume_explanation=canonical_explanation,natural_key_partition=canonical_partition,
    data_disposition=NULL,integrity_check_sql=dasha_check
  WHERE asset_id='bg_dasha_systems';
  GET DIAGNOSTICS changed_rows = ROW_COUNT;
  IF changed_rows <> 1 THEN
    RAISE EXCEPTION 'migration 621 expected 1 registry row, updated %',changed_rows;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM asset_registry WHERE asset_id='bg_dasha_systems'
    AND target_floor=60 AND count_sql=canonical_count_sql
    AND volume_explanation=canonical_explanation
    AND natural_key_partition=canonical_partition
    AND data_disposition IS NULL AND integrity_check_sql=dasha_check) THEN
    RAISE EXCEPTION 'migration 621 postflight registry mismatch';
  END IF;
END $$;
