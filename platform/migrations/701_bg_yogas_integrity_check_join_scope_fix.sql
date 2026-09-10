-- Migration 701: bg_yogas integrity_check_sql join-scope fix (C12).
--
-- NIRMANA L0-W4 CONFORM: bg_yogas' integrity_check_sql fails against a
-- genuine, correct writer replay (233/233/233/85, all three content-hash
-- pins matching byte-for-byte) because of the same FULL-JOIN scope bug
-- already fixed for bg_doshas (692) and bg_dasha_systems (700): the check
-- puts `ontology.entity_class='yoga'` in the ON clause instead of
-- pre-filtering brahma_ontology (a table shared across every L0 entity
-- class) to yoga rows before the join. FULL OUTER JOIN semantics mean an
-- ON-clause filter on one side does not exclude that side's non-matching
-- rows -- every OTHER entity_class row in brahma_ontology leaks in as an
-- unmatched (catalog.canonical_id IS NULL) row and trips the alignment
-- NOT EXISTS. Verified live (rolled-back tx, genuine seed_yogas() replay):
-- the raw violation count is 508, and `count(*) FROM brahma_ontology WHERE
-- entity_class != 'yoga'` is also 508 -- an exact match, zero real yoga
-- misalignments. All other subclauses (four counts, source_chunk_ids
-- empty-array check, three content-hash pins) already evaluate TRUE
-- against the same genuine replay -- only the join scope is wrong.
--
-- Fix: pre-filter brahma_ontology to entity_class='yoga' in a subquery
-- before the join, mirroring 692/700's exact pattern. No writer change --
-- the data was already correct; only the check was wrong.

DO $$
DECLARE
  registry_row asset_registry%ROWTYPE;
  changed_rows integer := 0;
  yoga_check constant text := $check$
SELECT
  (SELECT count(*) = 233 FROM brahma_yoga_catalog)
  AND (SELECT count(*) = 233 FROM brahma_ontology WHERE entity_class='yoga')
  AND (SELECT count(*) = 233 FROM reference_yogas)
  AND (SELECT count(*) = 85 FROM brahma_yoga_source_chunks)
  AND (SELECT count(DISTINCT canonical_id) = 85 FROM brahma_yoga_source_chunks)
  AND (SELECT count(*) FILTER (WHERE cardinality(source_chunk_ids)=0) = 233
       FROM brahma_yoga_catalog)
  AND NOT EXISTS (
    SELECT 1 FROM brahma_yoga_catalog AS catalog
    FULL JOIN (SELECT * FROM brahma_ontology WHERE entity_class='yoga') AS ontology
      ON ontology.canonical_id=catalog.canonical_id
    FULL JOIN reference_yogas AS reference
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
      formation_text,significations_jsonb,significations_text,
      cancellation_conditions,classical_citations,source_chunk_ids,school,rare,
      computed_strength_formula,bhanga_rules_jsonb,partial_formation_threshold,
      strength_formula_ref,result_class)::text,
    E'\n' ORDER BY canonical_id COLLATE "C"),''),'UTF8')),'hex') =
    '4d4cd60f7cffe728f2d01c3146f9bf54279e5c747973ab60b2e69b7921023fa8'
   FROM brahma_yoga_catalog)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(entity_class,canonical_id,canonical_name_en,
      canonical_name_sa,synonyms,description,source_citation)::text,
    E'\n' ORDER BY entity_class COLLATE "C",canonical_id COLLATE "C"),''),'UTF8')),'hex') =
    '7af1d138c492bd16bbca93b06faab6b3ff781d87aa91f8573fce6378f968fdab'
   FROM brahma_ontology WHERE entity_class='yoga')
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(canonical_id,name_en,category)::text,
    E'\n' ORDER BY canonical_id COLLATE "C"),''),'UTF8')),'hex') =
    '1c79af1127b8e624e12c95afecf09e73f23546fe87272f5dff8146ed30d6f564'
   FROM reference_yogas)
$check$;
  old_check constant text := $oldcheck$
SELECT
  (SELECT count(*) = 233 FROM brahma_yoga_catalog)
  AND (SELECT count(*) = 233 FROM brahma_ontology WHERE entity_class='yoga')
  AND (SELECT count(*) = 233 FROM reference_yogas)
  AND (SELECT count(*) = 85 FROM brahma_yoga_source_chunks)
  AND (SELECT count(DISTINCT canonical_id) = 85 FROM brahma_yoga_source_chunks)
  AND (SELECT count(*) FILTER (WHERE cardinality(source_chunk_ids)=0) = 233
       FROM brahma_yoga_catalog)
  AND NOT EXISTS (
    SELECT 1 FROM brahma_yoga_catalog AS catalog
    FULL JOIN brahma_ontology AS ontology
      ON ontology.entity_class='yoga' AND ontology.canonical_id=catalog.canonical_id
    FULL JOIN reference_yogas AS reference
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
      formation_text,significations_jsonb,significations_text,
      cancellation_conditions,classical_citations,source_chunk_ids,school,rare,
      computed_strength_formula,bhanga_rules_jsonb,partial_formation_threshold,
      strength_formula_ref,result_class)::text,
    E'\n' ORDER BY canonical_id COLLATE "C"),''),'UTF8')),'hex') =
    '4d4cd60f7cffe728f2d01c3146f9bf54279e5c747973ab60b2e69b7921023fa8'
   FROM brahma_yoga_catalog)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(entity_class,canonical_id,canonical_name_en,
      canonical_name_sa,synonyms,description,source_citation)::text,
    E'\n' ORDER BY entity_class COLLATE "C",canonical_id COLLATE "C"),''),'UTF8')),'hex') =
    '7af1d138c492bd16bbca93b06faab6b3ff781d87aa91f8573fce6378f968fdab'
   FROM brahma_ontology WHERE entity_class='yoga')
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(canonical_id,name_en,category)::text,
    E'\n' ORDER BY canonical_id COLLATE "C"),''),'UTF8')),'hex') =
    '1c79af1127b8e624e12c95afecf09e73f23546fe87272f5dff8146ed30d6f564'
   FROM reference_yogas)
$oldcheck$;
BEGIN
  SELECT * INTO registry_row FROM asset_registry
  WHERE asset_id='bg_yogas' FOR UPDATE;
  IF NOT FOUND OR registry_row.integrity_check_sql IS DISTINCT FROM old_check THEN
    RAISE EXCEPTION 'migration 701 refuses unknown bg_yogas integrity_check_sql (expected the pre-fix pin)';
  END IF;

  UPDATE asset_registry SET integrity_check_sql=yoga_check
  WHERE asset_id='bg_yogas';
  GET DIAGNOSTICS changed_rows = ROW_COUNT;
  IF changed_rows <> 1 THEN
    RAISE EXCEPTION 'migration 701 expected 1 registry row, updated %',changed_rows;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM asset_registry WHERE asset_id='bg_yogas'
    AND integrity_check_sql=yoga_check) THEN
    RAISE EXCEPTION 'migration 701 postflight registry mismatch';
  END IF;
END $$;
