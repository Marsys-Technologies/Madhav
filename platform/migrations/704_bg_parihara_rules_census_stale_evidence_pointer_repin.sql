-- Migration 704: bg_parihara_rules -- correct one stale bg_muhurta_factor_census
-- content field + re-pin its content hash (D-L0-PP).
--
-- Root cause (verified live, read-only, rolled back before writing this
-- migration): migration 703 (#2081) correctly cleaned up 9 orphaned rows and
-- re-pinned counts to 60/329/51, but its `bg_muhurta_factor_census` content
-- hash was computed FROM THE THEN-COMMITTED DATA, which was already stale --
-- writer commit `4a78a5c40` ("reconcile and pin the 128-asset T0 denominator",
-- #1539) had already corrected the writer's in-code `CENSUS_ROWS` constant's
-- `('astronomical','eclipse_proximity')` entry's `evidence_pointer` from
-- `bg_sky_events` (not a real asset id) to `bg_sky_calendar` (the real Night-1
-- sibling asset the row is actually documenting), but the committed table row
-- was never refreshed to match, and 703 (authored against committed data, not
-- a fresh writer replay) carried the stale value forward into its new pin.
--
-- Confirmed via two independent rolled-back replays against live production
-- data (2026-09-06): (1) running `BgPariharaRulesWriter().run(ctx)` inside an
-- uncommitted transaction reproduces the exact production failure -- writer
-- reports correct counts (60/329/51), but the in-transaction
-- `integrity_check_sql` (703's pin) evaluates false; isolating clause-by-
-- clause shows only `census_hash` fails, and diffing pre/post-write rows
-- shows exactly one field on exactly one row differs, confirming this is the
-- ONLY discrepancy (no other content, no count change). (2) Running the raw
-- SQL UPDATE below (not the writer) in a second rolled-back transaction
-- reproduces the identical corrected hash. This is the two dispatch-attempt
-- failures (runs 230ed9e8, 7a12b137) explained precisely.
--
-- No writer change is made here (would touch a writer file and re-trigger
-- the writer_inventory_sha256 / adjudication #1715 requirement-3 wall) --
-- this is a DATA-only correction, syncing the one stale field to the value
-- the writer's already-merged code has produced since #1539, then re-pinning
-- the content hash to match. `bg_parihara_rules` (60 rows) and
-- `bg_muhurta_activity_rules` (329 rows) have no discrepancy; their pins and
-- content are unchanged from migration 703.

DO $$
DECLARE
  registry_row asset_registry%ROWTYPE;
  changed_rows integer := 0;
  census_updated integer := 0;
  new_check constant text := $check$
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
      'e5df888ca6fcfd703fd6e9f4f3d50b48738463768bdad01721751fb8346e75c7'
    FROM bg_muhurta_factor_census)
$check$;
  old_check constant text := $oldcheck$
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
$oldcheck$;
BEGIN
  SELECT * INTO registry_row FROM asset_registry
  WHERE asset_id='bg_parihara_rules' FOR UPDATE;
  IF NOT FOUND OR registry_row.integrity_check_sql IS DISTINCT FROM old_check THEN
    RAISE EXCEPTION 'migration 704 refuses unknown bg_parihara_rules integrity_check_sql (expected the 703 pin)';
  END IF;

  -- Refuse if the live row isn't in the exact stale state this migration was
  -- authored against -- a stale assumption here must halt, not silently
  -- rewrite the wrong thing.
  IF (SELECT count(*) FROM bg_muhurta_factor_census
      WHERE factor_family='astronomical' AND factor_name='eclipse_proximity'
        AND evidence_pointer='bg_sky_events (event_type IN eclipse_solar, eclipse_lunar)') <> 1 THEN
    RAISE EXCEPTION 'migration 704 refuses: the eclipse_proximity census row is not in the expected stale state';
  END IF;
  IF (SELECT count(*) FROM bg_parihara_rules) <> 60
     OR (SELECT count(*) FROM bg_muhurta_factor_census) <> 51
     OR (SELECT count(*) FROM bg_muhurta_activity_rules) <> 329 THEN
    RAISE EXCEPTION 'migration 704 refuses: live row counts (%,%,%) do not match the 60/329/51 this migration was authored against',
      (SELECT count(*) FROM bg_parihara_rules),
      (SELECT count(*) FROM bg_muhurta_activity_rules),
      (SELECT count(*) FROM bg_muhurta_factor_census);
  END IF;

  UPDATE bg_muhurta_factor_census
     SET evidence_pointer = 'bg_sky_calendar (event_type IN eclipse_solar, eclipse_lunar)'
   WHERE factor_family='astronomical' AND factor_name='eclipse_proximity'
     AND evidence_pointer = 'bg_sky_events (event_type IN eclipse_solar, eclipse_lunar)';
  GET DIAGNOSTICS census_updated = ROW_COUNT;
  IF census_updated <> 1 THEN
    RAISE EXCEPTION 'migration 704 expected to update exactly 1 bg_muhurta_factor_census row, updated %', census_updated;
  END IF;

  UPDATE asset_registry SET integrity_check_sql=new_check
  WHERE asset_id='bg_parihara_rules';
  GET DIAGNOSTICS changed_rows = ROW_COUNT;
  IF changed_rows <> 1 THEN
    RAISE EXCEPTION 'migration 704 expected 1 registry row, updated %', changed_rows;
  END IF;

  IF NOT EXISTS (SELECT 1 FROM asset_registry WHERE asset_id='bg_parihara_rules'
    AND integrity_check_sql=new_check) THEN
    RAISE EXCEPTION 'migration 704 postflight registry mismatch';
  END IF;
  IF (SELECT count(*) FROM bg_muhurta_factor_census
      WHERE factor_family='astronomical' AND factor_name='eclipse_proximity'
        AND evidence_pointer='bg_sky_calendar (event_type IN eclipse_solar, eclipse_lunar)') <> 1 THEN
    RAISE EXCEPTION 'migration 704 postflight eclipse_proximity row mismatch';
  END IF;
END $$;
