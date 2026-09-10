-- Migration 706: bg_vidhi_primitives -- re-pin integrity_check_sql content hash after
-- migration 705's from_moon_view correction (F-D21/F-D23, #2122).
--
-- Migration 705 (this same PR) corrected vidhi_primitives.from_moon_view's live_tool/tool_args
-- (ganita_chart_facts_get + inert reference_point -> ganita_transit_anchors_get). bg_vidhi_
-- primitives' integrity_check_sql (originally pinned by migration 628) hashes the full 60-row
-- vidhi_primitives content over exactly those two columns among others, so correcting the row's
-- content necessarily moves the pinned hash. This migration re-pins it to the corrected value --
-- it does not touch migration 628 itself (already applied; never edit an applied migration).
--
-- Verified via a rolled-back replay against live production data (apply 705, then re-pin, then
-- run the corrected check) before authoring this file: the closed-loop check evaluates true.
-- Row count is unchanged (60 -> 60); only the content hash moves.

DO $$
DECLARE
  registry_row asset_registry%ROWTYPE;
  changed_rows integer := 0;
  old_check constant text := $oldcheck$
SELECT
  (SELECT count(*) = 60 FROM vidhi_primitives)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(
      primitive_id,version,definition,category,live_tool,tool_args,
      fallback_face,known_gap,mandatory_tags,cr27_prevents
    )::text,E'\n' ORDER BY primitive_id COLLATE "C"),''),'UTF8')),'hex') =
    '41463a2be208bc33c645cc943a242a2cd5b4906e8babd3dc68fe5ef566738cce'
   FROM vidhi_primitives)
$oldcheck$;
  new_check constant text := $newcheck$
SELECT
  (SELECT count(*) = 60 FROM vidhi_primitives)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(
      primitive_id,version,definition,category,live_tool,tool_args,
      fallback_face,known_gap,mandatory_tags,cr27_prevents
    )::text,E'\n' ORDER BY primitive_id COLLATE "C"),''),'UTF8')),'hex') =
    'cc57ac4d59218bcb818dda0288151f2d72107afa0c0ef664df7520cffea90320'
   FROM vidhi_primitives)
$newcheck$;
BEGIN
  SELECT * INTO registry_row FROM asset_registry
  WHERE asset_id='bg_vidhi_primitives' FOR UPDATE;
  IF NOT FOUND OR registry_row.integrity_check_sql IS DISTINCT FROM old_check THEN
    RAISE EXCEPTION 'migration 706 refuses unknown bg_vidhi_primitives integrity_check_sql (expected the migration 628 pin)';
  END IF;

  IF (SELECT count(*) FROM vidhi_primitives) <> 60 THEN
    RAISE EXCEPTION 'migration 706 refuses: live vidhi_primitives row count is %, expected 60',
      (SELECT count(*) FROM vidhi_primitives);
  END IF;

  UPDATE asset_registry SET integrity_check_sql=new_check
  WHERE asset_id='bg_vidhi_primitives';
  GET DIAGNOSTICS changed_rows = ROW_COUNT;
  IF changed_rows <> 1 THEN
    RAISE EXCEPTION 'migration 706 expected 1 registry row, updated %', changed_rows;
  END IF;

  IF NOT EXISTS (SELECT 1 FROM asset_registry WHERE asset_id='bg_vidhi_primitives'
    AND integrity_check_sql=new_check) THEN
    RAISE EXCEPTION 'migration 706 postflight registry mismatch';
  END IF;
END $$;
