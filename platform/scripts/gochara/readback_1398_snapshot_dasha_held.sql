-- readback_1398_snapshot_dasha_held.sql  (READ ONLY — run as the steward AFTER the protected window (kala_schema_migration=true) that applies migration 1398; send the output to the tracker)
-- Every fact the post-apply check of 1398 relies on, read back from the live catalog. Nothing here writes. Expected values are in the comments; any
-- difference is a reason to stop and report, not to repair by hand (never edit an applied migration).
BEGIN READ ONLY;

-- 1. the one additive column on the snapshot. expected: 1 row (consumed_dasha_held, jsonb, YES nullable).
SELECT column_name, data_type, is_nullable FROM information_schema.columns
WHERE table_schema = 'public' AND table_name = 'ka_gochara_search_input_snapshot' AND column_name = 'consumed_dasha_held';

-- 2. the held-record trigger fires BEFORE INSERT FOR EACH ROW and is enabled, and sorts AFTER 1305's copy-build trigger (it reads the row ids that trigger accepted).
--    expected: 1 row, enabled 'O', before_row_trigger t, on_insert t, fires_after_copy_build t.
SELECT tgname, tgenabled, (tgtype & 2) <> 0 AS before_row_trigger, (tgtype & 4) <> 0 AS on_insert,
       tgname > 'ka_gochara_search_input_snapshot_0z_copy_build' COLLATE "C" AS fires_after_copy_build
FROM pg_trigger WHERE tgrelid = 'public.ka_gochara_search_input_snapshot'::regclass AND tgname = 'ka_gochara_search_input_snapshot_0zz_held_build' AND NOT tgisinternal;

-- 3. the two new functions exist, both invoker-rights (prosecdef false). expected: 2 rows, secdef f.
SELECT p.proname, pg_get_function_identity_arguments(p.oid) AS args, p.prosecdef AS secdef
FROM pg_proc p WHERE p.pronamespace = 'public'::regnamespace
  AND p.proname IN ('ka_gochara_search_dasha_held', 'ka_gochara_search_input_snapshot_held_build') ORDER BY 1;

-- 4. EXECUTE on the new function for the one role that inserts a snapshot (production revokes PUBLIC EXECUTE). expected: data_plane_builder | t (if the role exists).
SELECT r.rolname, has_function_privilege(r.oid, 'public.ka_gochara_search_dasha_held(uuid,uuid[])'::regprocedure, 'EXECUTE') AS execute_on_dasha_held
FROM pg_roles r WHERE r.rolname = 'data_plane_builder' ORDER BY 1;

-- 5. 1305 is untouched by 1398: its copy-build trigger and copy columns are still present. expected: t | t.
SELECT EXISTS (SELECT 1 FROM pg_trigger WHERE tgrelid = 'public.ka_gochara_search_input_snapshot'::regclass
                 AND tgname = 'ka_gochara_search_input_snapshot_0z_copy_build' AND NOT tgisinternal) AS copy_build_trigger_present,
       EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'ka_gochara_search_input_snapshot'
                 AND column_name = 'consumed_dasha_rows') AS copy_column_present;

-- 6. the migration is recorded; snapshots captured BEFORE it keep NULL (no backfill), snapshots captured after it carry the record.
--    expected: ledger_rows 1; null_held counts only snapshots that predate 1398 (0 on a production with no snapshot yet before the first build).
SELECT (SELECT count(*) FROM public._migrations_applied WHERE filename = '1398_gochara_snapshot_dasha_held.sql') AS ledger_rows,
       (SELECT count(*) FROM public.ka_gochara_search_input_snapshot) AS snapshots,
       (SELECT count(*) FROM public.ka_gochara_search_input_snapshot WHERE consumed_dasha_held IS NULL) AS null_held,
       (SELECT count(*) FROM public.ka_gochara_search_input_snapshot WHERE consumed_dasha_held IS NOT NULL) AS recorded_held;

COMMIT;
