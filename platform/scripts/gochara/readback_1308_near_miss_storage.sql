-- FB-21: 1308 owns ONLY storage. Stacked functions and verification are 1381, never inferred here.
BEGIN READ ONLY;
SELECT current_setting('server_version_num') AS server_version_num;
SELECT filename,sha256 FROM public._migrations_applied WHERE filename='1308_gochara_near_miss_storage.sql';
SELECT c.relname,t.tgname,t.tgenabled,pg_get_triggerdef(t.oid) AS definition
FROM pg_class c JOIN pg_trigger t ON t.tgrelid=c.oid AND NOT t.tgisinternal
WHERE c.oid IN ('public.ka_gochara_near_miss_object'::regclass,'public.ka_gochara_near_miss'::regclass,
  'public.ka_gochara_near_miss_search'::regclass) ORDER BY c.relname,t.tgname;
SELECT r.rolname,t.name,has_table_privilege(r.oid,t.name,'SELECT') AS can_read,
  has_table_privilege(r.oid,t.name,'INSERT') AS can_insert,has_table_privilege(r.oid,t.name,'DELETE') AS can_delete
FROM pg_roles r CROSS JOIN (VALUES ('public.ka_gochara_near_miss_object'),('public.ka_gochara_near_miss'),
  ('public.ka_gochara_near_miss_search')) t(name)
WHERE r.rolname IN ('data_plane_builder','gochara_verifier','gochara_sealer') ORDER BY 1,2;
COMMIT;
