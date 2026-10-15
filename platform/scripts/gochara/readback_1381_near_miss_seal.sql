-- FB-20/21: SELECT-only catalogue readback, one receipt per migration, no production operation inferred by code tests.
BEGIN READ ONLY;
SELECT current_setting('server_version_num') AS server_version_num;
SELECT filename,sha256 FROM public._migrations_applied WHERE filename='1381_gochara_near_miss_seal_integration.sql';
SELECT p.proname,pg_get_function_identity_arguments(p.oid) AS arguments,
  encode(sha256(convert_to(pg_get_functiondef(p.oid),'UTF8')),'hex') AS definition_sha256,NOT p.prosecdef AS invoker
FROM pg_proc p WHERE p.pronamespace='public'::regnamespace AND p.proname IN
  ('ka_gochara_brief_state_digest','ka_gochara_candidate_gate_violations',
   'ka_gochara_near_miss_digest','ka_gochara_near_miss_violations','ka_gochara_near_miss_seal_guard') ORDER BY 1;
SELECT tgname,tgenabled,pg_get_triggerdef(oid) FROM pg_trigger WHERE
  tgrelid='public.ka_gochara_near_miss_verification'::regclass OR tgname='ka_gochara_generation_seal_0_near_miss' ORDER BY 1;
SELECT r.rolname,has_table_privilege(r.oid,'public.ka_gochara_near_miss_verification','SELECT') AS can_read,
 has_table_privilege(r.oid,'public.ka_gochara_near_miss_verification','INSERT') AS can_insert,
 has_table_privilege(r.oid,'public.ka_gochara_near_miss_verification','DELETE') AS can_delete,
 has_table_privilege(r.oid,'public.ka_gochara_near_miss_verification','UPDATE') AS can_update
FROM pg_roles r WHERE r.rolname IN ('data_plane_builder','gochara_verifier','gochara_sealer') ORDER BY 1;
COMMIT;
