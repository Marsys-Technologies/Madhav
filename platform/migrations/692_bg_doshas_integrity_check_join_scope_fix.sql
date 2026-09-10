-- 692_bg_doshas_integrity_check_join_scope_fix.sql
--
-- NIRMANA L0-W4 CONFORM (C12 wave-1 defect investigation): bg_doshas'
-- integrity_check_sql reports 658 "FULL-JOIN violations" against live data
-- that is in fact perfectly aligned (79/79/79 rows, all names/categories
-- match, all three content-hash pins already match byte-for-byte). This
-- migration corrects a bug in the CHECK, not the data -- C12 "correct the
-- check" path (same class as the bg_gochara_arcs stale-pin rewrite),
-- verified live in a read-only session before writing.
--
-- Root cause: the check's FULL JOIN puts `ontology.entity_class='dosha'`
-- in the ON clause instead of pre-filtering brahma_ontology (a table
-- shared across all 16 L0 entity classes, 737 rows total) to dosha rows
-- before the join. FULL OUTER JOIN semantics mean an ON-clause filter on
-- one side does not exclude that side's non-matching rows -- they still
-- surface as unmatched (NULL-catalog) rows. The result: all 658 non-dosha
-- ontology rows (yoga=229, concept=136, karaka=77, domain=45, ... per
-- `SELECT entity_class, count(*) FROM brahma_ontology GROUP BY 1`) leak
-- into the join and trip `catalog.canonical_id IS NULL`, none of them
-- real defects. Verified live: the raw FULL JOIN (no WHERE) returns 737
-- rows = 79 (real dosha matches) + 658 (leaked non-dosha ontology rows);
-- `count(*) FROM brahma_ontology WHERE entity_class != 'dosha'` = 658,
-- an exact match.
--
-- Fix: pre-filter brahma_ontology to entity_class='dosha' in a subquery
-- before the join, so only dosha rows ever enter the FULL JOIN. Verified
-- live (read-only) that the corrected NOT EXISTS clause returns 0 rows,
-- and that the full composed integrity_check_sql (all AND-ed conditions,
-- unchanged otherwise -- counts, empty-array check, all three content
-- hashes) evaluates TRUE against current production data as-is. No
-- rebuild/dispatch is required for bg_doshas: the data was already
-- correct; only the check was wrong.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

UPDATE asset_registry
   SET integrity_check_sql = $check$
SELECT
  (SELECT count(*) = 79 FROM brahma_dosha_catalog)
  AND (SELECT count(*) = 79 FROM brahma_ontology WHERE entity_class='dosha')
  AND (SELECT count(*) = 79 FROM reference_doshas)
  AND (SELECT count(*) FILTER (WHERE cardinality(source_chunk_ids)=0
    AND cardinality(associated_remedies)=0) = 79 FROM brahma_dosha_catalog)
  AND NOT EXISTS (
    SELECT 1 FROM brahma_dosha_catalog AS catalog
    FULL JOIN (SELECT * FROM brahma_ontology WHERE entity_class='dosha') AS ontology
      ON ontology.canonical_id=catalog.canonical_id
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
$check$
 WHERE asset_id = 'bg_doshas';

-- Forward reversal (safe at any time -- additive value correction, not a
-- schema change): re-run 09-01's original bg_doshas integrity_check_sql
-- (the buggy bare-ON-clause FULL JOIN version) to restore prior behavior.
