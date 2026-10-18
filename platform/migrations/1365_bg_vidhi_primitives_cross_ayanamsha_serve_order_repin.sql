-- Migration 1365: bg_vidhi_primitives -- cross_ayanamsha_variation.ayanamsha_axis moves to the
-- ayanamsha SERVE ORDER, and the integrity_check_sql content hash is re-pinned to match.
--
-- WHY. "Lahiri primary PR-1" (commit 16cfc2868) made vidhi REAL_AYANAMSHAS the serve order
-- (lahiri_chitrapaksha, true_chitra, krishnamurti, raman, surya_siddhanta_classical) and
-- regenerated the canonical TS registry (registry_data.ts) and its mirror. The Vidhi parity gate
-- (check_vidhi_registry_parity.mjs) then required the Python seed writer
-- (bg_vidhi_primitives.py) to carry the same array, so the writer's cross_ayanamsha_variation
-- tool_args.ayanamsha_axis changed order. jsonb arrays are ordered, so the 60-row content hash
-- pinned by migration 628 and re-pinned by migration 706 (cc57ac4d...) no longer matches what the
-- writer produces. Without this migration the stored integrity check reads false after the next
-- bg_vidhi_primitives rebuild. 628 and 706 are already applied and are NOT edited.
--
-- WHAT. (1) Set the live cross_ayanamsha_variation row's tool_args.ayanamsha_axis to the serve
-- order (the same value the writer upserts). (2) Replace the 706 pin with the hash of the 60-row
-- content including that row. Row count stays 60; only the one array order and the hash move.
-- The new hash 456086e9... was computed with the check's own expression over the live rows with
-- only that row's axis substituted (the unsubstituted rows reproduce cc57ac4d... exactly).
--
-- GUARDS. Refuses unknown starting states; accepts the converged state (replay no-op); the
-- postflight EXECUTES the stored check and requires true (it is the earned signal, not a proxy).
-- Runner-owned transaction: no BEGIN/COMMIT here.

DO $$
DECLARE
  registry_row asset_registry%ROWTYPE;
  changed_rows integer := 0;
  check_ok boolean;
  old_axis constant jsonb := '["krishnamurti","lahiri_chitrapaksha","raman","surya_siddhanta_classical","true_chitra"]'::jsonb;
  new_axis constant jsonb := '["lahiri_chitrapaksha","true_chitra","krishnamurti","raman","surya_siddhanta_classical"]'::jsonb;
  live_axis jsonb;
  old_check constant text := $oldcheck$
SELECT
  (SELECT count(*) = 60 FROM vidhi_primitives)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(
      primitive_id,version,definition,category,live_tool,tool_args,
      fallback_face,known_gap,mandatory_tags,cr27_prevents
    )::text,E'\n' ORDER BY primitive_id COLLATE "C"),''),'UTF8')),'hex') =
    'cc57ac4d59218bcb818dda0288151f2d72107afa0c0ef664df7520cffea90320'
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
    '456086e9277cc25edf068a1e083340c1d0a2dc165e1df5b377a29ce4b43c4cdc'
   FROM vidhi_primitives)
$newcheck$;
BEGIN
  SELECT * INTO registry_row FROM asset_registry
  WHERE asset_id='bg_vidhi_primitives' FOR UPDATE;
  IF NOT FOUND
     OR (registry_row.integrity_check_sql IS DISTINCT FROM old_check
         AND registry_row.integrity_check_sql IS DISTINCT FROM new_check) THEN
    RAISE EXCEPTION 'migration 1365 refuses unknown bg_vidhi_primitives integrity_check_sql (expected the migration 706 pin or this migration''s pin)';
  END IF;

  IF (SELECT count(*) FROM vidhi_primitives) <> 60 THEN
    RAISE EXCEPTION 'migration 1365 refuses: live vidhi_primitives row count is %, expected 60',
      (SELECT count(*) FROM vidhi_primitives);
  END IF;

  SELECT tool_args -> 'ayanamsha_axis' INTO live_axis FROM vidhi_primitives
  WHERE primitive_id = 'cross_ayanamsha_variation';
  IF live_axis IS DISTINCT FROM old_axis AND live_axis IS DISTINCT FROM new_axis THEN
    RAISE EXCEPTION 'migration 1365 refuses unknown cross_ayanamsha_variation ayanamsha_axis: %', live_axis;
  END IF;

  UPDATE vidhi_primitives
  SET tool_args = jsonb_set(tool_args, '{ayanamsha_axis}', new_axis)
  WHERE primitive_id = 'cross_ayanamsha_variation'
    AND tool_args -> 'ayanamsha_axis' IS DISTINCT FROM new_axis;

  UPDATE asset_registry SET integrity_check_sql = new_check
  WHERE asset_id = 'bg_vidhi_primitives'
    AND integrity_check_sql IS DISTINCT FROM new_check;
  GET DIAGNOSTICS changed_rows = ROW_COUNT;
  IF changed_rows > 1 THEN
    RAISE EXCEPTION 'migration 1365 expected at most 1 registry row, updated %', changed_rows;
  END IF;

  IF NOT EXISTS (SELECT 1 FROM asset_registry WHERE asset_id='bg_vidhi_primitives'
    AND integrity_check_sql = new_check) THEN
    RAISE EXCEPTION 'migration 1365 postflight registry mismatch';
  END IF;

  EXECUTE new_check INTO check_ok;
  IF check_ok IS DISTINCT FROM true THEN
    RAISE EXCEPTION 'migration 1365 postflight: the re-pinned bg_vidhi_primitives integrity check does not evaluate true';
  END IF;
END $$;
