-- Migration 703: bg_parihara_rules orphaned-row cleanup + integrity_check_sql
-- re-pin (D-L0-OO).
--
-- Root cause (verified live, read-only, rolled back before writing this
-- migration): `BgPariharaRulesWriter._upsert_parihara` / `_upsert_census`
-- (platform/python-sidecar/pipeline/orchestrator/writers/bg_parihara_rules.py)
-- use `ON CONFLICT (...) DO UPDATE` -- upsert-only, no DELETE. When either
-- source shrinks (fewer qualifying rows than a prior seed produced), the
-- stale rows are never cleaned up; they accrete forever. Two of the writer's
-- three sources have shrunk since the committed tables were last seeded:
--
-- 1. `brahma_dosha_catalog` no longer has a citable `rahu_kalam` entry (its
--    `_DOSHA_QUERY` WHERE clause -- cited, non-placeholder `classical_citations`
--    -- no longer matches it). A fresh, real dispatch of bg_parihara_rules
--    (run d0dd1573-65f4-4ab0-b70c-5e43d8ed6be0, 2026-09-06) confirmed this
--    live: the writer's own log reports `parihara=60`, not the committed 61.
--    The orchestrator rolled back that run on the integrity mismatch --
--    no data was changed by it.
-- 2. The writer's in-code `CENSUS_ROWS` constant (a pure in-memory list, not
--    DB-derived) is currently 51 entries, not 59 -- confirmed directly via
--    `len(CENSUS_ROWS)` against the live writer source.
--
-- No writer change is made here (would touch a writer file and re-trigger
-- the writer_inventory_sha256 / adjudication #1715 requirement-3 wall the
-- bg_yogas extraction fix already hit this campaign) -- this is a DATA-only
-- correction: delete the exact orphaned rows, then re-pin the two affected
-- counts and their content hashes. `bg_muhurta_activity_rules` (329 rows) has
-- no discrepancy and its content hash is unchanged.
--
-- The 9 orphaned rows and the two corrected content hashes below were
-- computed via a rolled-back replay against live production data (delete,
-- recompute counts + hashes with the exact same SQL the check itself uses,
-- rollback) -- not invented.

DO $$
DECLARE
  registry_row asset_registry%ROWTYPE;
  changed_rows integer := 0;
  parihara_deleted integer := 0;
  census_deleted integer := 0;
  parihara_check constant text := $check$
SELECT
  (SELECT count(*) = 60 FROM bg_parihara_rules)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
      jsonb_build_array(dosha_canonical_id,dosha_name_en,dosha_category,cancellation_index,
        cancellation_condition_text,net_standing,scope,source_text_id,source_chapter,
        source_citation,extraction_context)::text,
      E'\n' ORDER BY dosha_canonical_id COLLATE "C",cancellation_index
    ),''),'UTF8')),'hex') =
      '353b1cad0ff6dfb6e57289b30ce600e83254e8ee505d8c9e35edfbe2c18a35cf'
    FROM bg_parihara_rules)
  AND (SELECT count(*) = 329 FROM bg_muhurta_activity_rules)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
      jsonb_build_array(activity_class,factor_type,factor_id,quality_score,source_citation)::text,
      E'\n' ORDER BY activity_class COLLATE "C",factor_type COLLATE "C",factor_id
    ),''),'UTF8')),'hex') =
      '5bb06a35f57b299187b8c6182b057627ea9f4406b26854c856bbdd6902fb4c71'
    FROM bg_muhurta_activity_rules)
  AND (SELECT count(*) = 51 FROM bg_muhurta_factor_census)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
      jsonb_build_array(factor_family,factor_name,disposition,citation_or_gap_note,
        evidence_pointer,school_tag)::text,
      E'\n' ORDER BY factor_family COLLATE "C",factor_name COLLATE "C"
    ),''),'UTF8')),'hex') =
      '42f23d0b20d6dabf4e3f0dd4414c71fe7d54273f3c3d1d064a284f54b99f2b14'
    FROM bg_muhurta_factor_census)
$check$;
  old_check constant text := $oldcheck$
SELECT
  (SELECT count(*) = 61 FROM bg_parihara_rules)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
      jsonb_build_array(dosha_canonical_id,dosha_name_en,dosha_category,cancellation_index,
        cancellation_condition_text,net_standing,scope,source_text_id,source_chapter,
        source_citation,extraction_context)::text,
      E'\n' ORDER BY dosha_canonical_id COLLATE "C",cancellation_index
    ),''),'UTF8')),'hex') =
      '3f2755ad5c474c027dff2fb1207b6a478f5c7ea7cfc1970103795b26b81c5175'
    FROM bg_parihara_rules)
  AND (SELECT count(*) = 329 FROM bg_muhurta_activity_rules)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
      jsonb_build_array(activity_class,factor_type,factor_id,quality_score,source_citation)::text,
      E'\n' ORDER BY activity_class COLLATE "C",factor_type COLLATE "C",factor_id
    ),''),'UTF8')),'hex') =
      '5bb06a35f57b299187b8c6182b057627ea9f4406b26854c856bbdd6902fb4c71'
    FROM bg_muhurta_activity_rules)
  AND (SELECT count(*) = 59 FROM bg_muhurta_factor_census)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
      jsonb_build_array(factor_family,factor_name,disposition,citation_or_gap_note,
        evidence_pointer,school_tag)::text,
      E'\n' ORDER BY factor_family COLLATE "C",factor_name COLLATE "C"
    ),''),'UTF8')),'hex') =
      '5efc97659b77eae50abca427e9ba088f43096dacaee16f9f5647ce81539b5535'
    FROM bg_muhurta_factor_census)
$oldcheck$;
BEGIN
  SELECT * INTO registry_row FROM asset_registry
  WHERE asset_id='bg_parihara_rules' FOR UPDATE;
  IF NOT FOUND OR registry_row.integrity_check_sql IS DISTINCT FROM old_check THEN
    RAISE EXCEPTION 'migration 703 refuses unknown bg_parihara_rules integrity_check_sql (expected the 644 pin)';
  END IF;

  -- Refuse if the live data doesn't match the exact 9-row orphan set this
  -- migration was authored against -- a stale assumption here must halt, not
  -- silently delete something else.
  IF (SELECT count(*) FROM bg_parihara_rules) <> 61
     OR (SELECT count(*) FROM bg_muhurta_factor_census) <> 59
     OR (SELECT count(*) FROM bg_muhurta_activity_rules) <> 329 THEN
    RAISE EXCEPTION 'migration 703 refuses: live row counts (%,%,%) do not match the 61/329/59 this migration was authored against',
      (SELECT count(*) FROM bg_parihara_rules),
      (SELECT count(*) FROM bg_muhurta_activity_rules),
      (SELECT count(*) FROM bg_muhurta_factor_census);
  END IF;

  DELETE FROM bg_parihara_rules
   WHERE dosha_canonical_id='rahu_kalam' AND cancellation_index=1;
  GET DIAGNOSTICS parihara_deleted = ROW_COUNT;
  IF parihara_deleted <> 1 THEN
    RAISE EXCEPTION 'migration 703 expected to delete exactly 1 bg_parihara_rules row, deleted %', parihara_deleted;
  END IF;

  DELETE FROM bg_muhurta_factor_census
   WHERE (factor_family, factor_name) IN (
     ('muhurta_lagna','lagna_lord_strength'),
     ('muhurta_lagna','lagna_shuddhi_rules'),
     ('muhurta_lagna','rising_sign_span'),
     ('panchangika','karana_lattice_family'),
     ('panchangika','nityayoga_lattice_family'),
     ('parihara_scope','vishti_conditional_undertaking_exception'),
     ('rite_specific','activity_rule_id_join'),
     ('rite_specific','activity_rule_pareto_axis_in_frozen_engine')
   );
  GET DIAGNOSTICS census_deleted = ROW_COUNT;
  IF census_deleted <> 8 THEN
    RAISE EXCEPTION 'migration 703 expected to delete exactly 8 bg_muhurta_factor_census rows, deleted %', census_deleted;
  END IF;

  UPDATE asset_registry SET integrity_check_sql=parihara_check
  WHERE asset_id='bg_parihara_rules';
  GET DIAGNOSTICS changed_rows = ROW_COUNT;
  IF changed_rows <> 1 THEN
    RAISE EXCEPTION 'migration 703 expected 1 registry row, updated %', changed_rows;
  END IF;

  IF NOT EXISTS (SELECT 1 FROM asset_registry WHERE asset_id='bg_parihara_rules'
    AND integrity_check_sql=parihara_check) THEN
    RAISE EXCEPTION 'migration 703 postflight registry mismatch';
  END IF;
  IF (SELECT count(*) FROM bg_parihara_rules) <> 60 THEN
    RAISE EXCEPTION 'migration 703 postflight bg_parihara_rules count mismatch';
  END IF;
  IF (SELECT count(*) FROM bg_muhurta_factor_census) <> 51 THEN
    RAISE EXCEPTION 'migration 703 postflight bg_muhurta_factor_census count mismatch';
  END IF;
END $$;
