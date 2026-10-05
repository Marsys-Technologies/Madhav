-- readback_1305_snapshot_copy.sql  (READ ONLY — run as the steward AFTER the protected window that applies migration 1305; send the output to the tracker)
-- Every fact the post-apply check of 1305 relies on, read back from the live catalog. Nothing here writes. Expected values are in the comments; any
-- difference is a reason to stop and report, not to repair by hand (never edit an applied migration).
BEGIN READ ONLY;

-- 1. the four additive columns on the snapshot. expected: 4 rows (consumed_fact_rows jsonb, consumed_dasha_rows jsonb, l1_facts_metadata_digest text,
--    dasha_metadata_digest text), all nullable.
SELECT column_name, data_type, is_nullable FROM information_schema.columns
WHERE table_schema = 'public' AND table_name = 'ka_gochara_search_input_snapshot'
  AND column_name IN ('consumed_fact_rows', 'consumed_dasha_rows', 'l1_facts_metadata_digest', 'dasha_metadata_digest') ORDER BY column_name;

-- 2. the copy CHECK is present and NOT VALID (it governs every NEW row and scans no old one). expected: kgsis_l1_copy_ck | f (convalidated false).
SELECT conname, convalidated FROM pg_constraint
WHERE conrelid = 'public.ka_gochara_search_input_snapshot'::regclass AND conname = 'kgsis_l1_copy_ck';

-- 3. the copy-check trigger fires BEFORE INSERT FOR EACH ROW. expected: 1 row, the trigger enabled ('O').
SELECT tgname, tgenabled, (tgtype & 2) <> 0 AS before_row_trigger, (tgtype & 4) <> 0 AS on_insert
FROM pg_trigger WHERE tgrelid = 'public.ka_gochara_search_input_snapshot'::regclass AND tgname = 'ka_gochara_search_input_snapshot_3_copy_check';

-- 4. the new functions exist, all invoker-rights (prosecdef false). expected: 8 rows, secdef f.
SELECT p.proname, pg_get_function_identity_arguments(p.oid) AS args, p.prosecdef AS secdef
FROM pg_proc p WHERE p.pronamespace = 'public'::regnamespace AND p.proname IN
  ('ka_gochara_search_copy_digest', 'ka_gochara_search_facts_copy', 'ka_gochara_search_facts_live_copy', 'ka_gochara_search_dasha_path',
   'ka_gochara_search_dasha_element', 'ka_gochara_search_dasha_copy', 'ka_gochara_search_dasha_live_copy', 'ka_gochara_search_input_snapshot_copy_check')
ORDER BY 1;

-- 5. the two replaced functions carry the 1305 bodies. expected: all three t.
SELECT pg_get_functiondef('public.ka_gochara_search_completeness_violations(uuid,text)'::regprocedure) LIKE '%ka_gochara_search_dasha_live_copy%' AS completeness_has_the_copy_drift_block,
       pg_get_functiondef('public.ka_gochara_search_completeness_violations(uuid,text)'::regprocedure) LIKE '%ka_gochara_search_moon_scope_violations%' AS completeness_keeps_the_1232_scope_call,
       pg_get_functiondef('public.ka_gochara_search_moon_resolved_domain(uuid,text,text,uuid)'::regprocedure) LIKE '%consumed_dasha_rows%' AS moon_domain_reads_the_copy;

-- 6. EXECUTE on the new functions for the three roles that call them (production revokes PUBLIC EXECUTE). expected: every column t for each role that exists.
SELECT r.rolname,
       bool_and(has_function_privilege(r.oid, f.oid, 'EXECUTE')) AS execute_on_all_seven_copy_functions
FROM pg_roles r
CROSS JOIN (SELECT p.oid FROM pg_proc p WHERE p.pronamespace = 'public'::regnamespace AND p.proname IN
  ('ka_gochara_search_copy_digest', 'ka_gochara_search_facts_copy', 'ka_gochara_search_facts_live_copy', 'ka_gochara_search_dasha_path',
   'ka_gochara_search_dasha_element', 'ka_gochara_search_dasha_copy', 'ka_gochara_search_dasha_live_copy')) f
WHERE r.rolname IN ('data_plane_builder', 'gochara_verifier', 'gochara_sealer')
GROUP BY r.rolname ORDER BY 1;

-- 7. the sha256 of the two replaced functions' definitions AFTER 1305 (for the record: they must NOT be the 1232 values 63d9e7e7… / 707bd37c…).
SELECT p.proname, encode(sha256(convert_to(pg_get_functiondef(p.oid), 'UTF8')), 'hex') AS definition_sha256
FROM pg_proc p WHERE p.pronamespace = 'public'::regnamespace
  AND p.proname IN ('ka_gochara_search_completeness_violations', 'ka_gochara_search_moon_resolved_domain') ORDER BY 1;

-- 8. the migration is recorded, and no snapshot exists yet that lacks a copy (0 snapshots on production before the first build).
SELECT (SELECT count(*) FROM public._migrations_applied WHERE filename = '1305_gochara_snapshot_owns_l1_copy.sql') AS ledger_rows,
       (SELECT count(*) FROM public.ka_gochara_search_input_snapshot) AS snapshots,
       (SELECT count(*) FROM public.ka_gochara_search_input_snapshot WHERE consumed_fact_rows IS NULL OR consumed_dasha_rows IS NULL) AS legacy_snapshots;

COMMIT;
