-- Migration 700: bg_dasha_systems integrity_check_sql -- join-scope fix +
-- catalog_hash re-pin (C12, D-L0-GG).
--
-- Two independent defects found in migration 621's check, same family
-- as bg_doshas (692) / bg_vidhi_floors (693) / bg_gochara_arcs (694):
--
-- 1. JOIN SCOPE BUG (same root cause as 692): the FULL JOIN puts
--    `ontology.entity_class='dasha_system'` in the ON clause instead of
--    pre-filtering brahma_ontology (a table shared across every L0
--    entity class) before the join. FULL OUTER JOIN semantics mean an
--    ON-clause filter on one side does not exclude that side's
--    non-matching rows -- every OTHER entity_class row in brahma_ontology
--    (nakshatras, doshas, yogas, ...) leaks in as an unmatched
--    (catalog.canonical_id IS NULL) row and trips the NOT EXISTS check.
--    Verified live (read-only, rolled back): the corrected form -- a
--    subquery pre-filtered to entity_class='dasha_system' joined instead
--    of the bare table -- returns 0 violation rows against current data.
--
-- 2. STALE catalog_hash PIN: a direct, rolled-back replay of
--    seed_dasha_systems() against the live schema confirms ontology_hash
--    and reference_hash are correct, but catalog_hash was pinned wrong
--    at 621's authoring time -- the writer's own DASHA_SYSTEMS content
--    (unchanged since 5f47906bc, the commit that authored 621 itself)
--    produces 8e35495ffef68342f7e88e2adee00654701feeee7852634cdada8df39-
--    32bf906, not the pinned 30742da6005fc977124192ae27ee1ca0bb29dd53632-
--    67860dfd8260e8bb3173a.
--
-- No rebuild/dispatch is required: the data was already correct (20/20/20,
-- kp present, jaimini_chara absent, all cross-table names/school agree
-- once ontology is scoped correctly); only the check was wrong, twice.

DO $$
DECLARE
  registry_row asset_registry%ROWTYPE;
  changed_rows integer := 0;
  dasha_check constant text := $check$
SELECT
  (SELECT count(*) = 20 FROM brahma_dasha_systems)
  AND (SELECT count(*) = 20 FROM brahma_ontology WHERE entity_class='dasha_system')
  AND (SELECT count(*) = 20 FROM reference_dasha_systems)
  AND NOT EXISTS (
    SELECT 1 FROM brahma_dasha_systems AS catalog
    FULL JOIN (SELECT * FROM brahma_ontology WHERE entity_class='dasha_system') AS ontology
      ON ontology.canonical_id=catalog.canonical_id
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
    '8e35495ffef68342f7e88e2adee00654701feeee7852634cdada8df3932bf906'
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
  old_check constant text := $oldcheck$
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
$oldcheck$;
BEGIN
  SELECT * INTO registry_row FROM asset_registry
  WHERE asset_id='bg_dasha_systems' FOR UPDATE;
  IF NOT FOUND OR registry_row.integrity_check_sql IS DISTINCT FROM old_check THEN
    RAISE EXCEPTION 'migration 700 refuses unknown bg_dasha_systems integrity_check_sql (expected the 621 pin)';
  END IF;

  UPDATE asset_registry SET integrity_check_sql=dasha_check
  WHERE asset_id='bg_dasha_systems';
  GET DIAGNOSTICS changed_rows = ROW_COUNT;
  IF changed_rows <> 1 THEN
    RAISE EXCEPTION 'migration 700 expected 1 registry row, updated %',changed_rows;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM asset_registry WHERE asset_id='bg_dasha_systems'
    AND integrity_check_sql=dasha_check) THEN
    RAISE EXCEPTION 'migration 700 postflight registry mismatch';
  END IF;
END $$;
