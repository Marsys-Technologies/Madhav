-- FB-21: SELECT-only, AFTER 1306 and BEFORE later migrations. Save output with the apply receipt.
BEGIN READ ONLY;
SELECT current_setting('server_version_num') AS server_version_num;
SELECT filename,sha256 FROM public._migrations_applied WHERE filename='1306_gochara_expected_class_census.sql';
SELECT p.proname,encode(sha256(convert_to(pg_get_functiondef(p.oid),'UTF8')),'hex') AS definition_sha256,
  position('ka_gochara_search_snapshot_copy_violations' IN p.prosrc)>0 AS retains_g12,
  position('expected_class_list_missing' IN p.prosrc)>0 AS class_census,
  position('path_census_mismatch' IN p.prosrc)>0 AS path_census,
  NOT p.prosecdef AS invoker
FROM pg_proc p WHERE p.oid='public.ka_gochara_search_completeness_violations(uuid,text)'::regprocedure;
COMMIT;
