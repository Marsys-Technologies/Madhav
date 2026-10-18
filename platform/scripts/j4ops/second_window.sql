-- Second-window READBACK ONLY. Expected bytes come from the reviewed mirror,
-- never by copying this readback into its own expectation. No first-window
-- "1206 absent" predicate and no obsolete migration-number assumptions.
SELECT jsonb_build_object(
  'server_major', current_setting('server_version_num')::integer / 10000,
  'ledger', (SELECT coalesce(jsonb_agg(to_jsonb(m) ORDER BY m.filename COLLATE "C"), '[]'::jsonb)
    FROM (SELECT filename, sha256 FROM public._migrations_applied) m),
  'functions', (SELECT coalesce(jsonb_agg(to_jsonb(f) ORDER BY f.signature COLLATE "C"), '[]'::jsonb)
    FROM (SELECT p.oid::regprocedure::text AS signature, pg_get_functiondef(p.oid) AS definition
      FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
      WHERE n.nspname = 'public' AND p.proname LIKE 'ka\_gochara\_%' ESCAPE '\'
        AND p.prokind IN ('f','p')) f),
  'triggers', (SELECT coalesce(jsonb_agg(to_jsonb(t) ORDER BY t."table" COLLATE "C", t.name COLLATE "C"), '[]'::jsonb)
    FROM (SELECT c.relname AS "table", t.tgname AS name, t.tgenabled AS enabled,
                 pg_get_triggerdef(t.oid) AS definition
      FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid
      JOIN pg_namespace n ON n.oid = c.relnamespace
      WHERE n.nspname = 'public' AND c.relname ~ '^ka(la)?_gochara_'
        AND NOT t.tgisinternal) t),
  'dormant_writes', (SELECT coalesce(jsonb_agg(to_jsonb(w) ORDER BY w.role COLLATE "C", w."table" COLLATE "C", w.privilege COLLATE "C"), '[]'::jsonb)
    FROM (SELECT r.rolname AS role, c.relname AS "table", p.privilege
      FROM pg_roles r CROSS JOIN pg_class c
      CROSS JOIN (VALUES ('INSERT'), ('UPDATE'), ('DELETE'), ('TRUNCATE')) p(privilege)
      WHERE c.relnamespace = 'public'::regnamespace AND c.relkind IN ('r','p')
        AND (c.relname ~ '^ka(la)?_gochara_' OR c.relname LIKE 'bg\_gochara\_%' ESCAPE '\'
             OR c.relname IN ('gochara_resonance_map', 'gochara_v3_calibration', 'kala_vedha_gochara'))
        AND NOT r.rolcanlogin AND r.rolname !~ '^pg_'
        AND NOT EXISTS (SELECT 1 FROM pg_auth_members m WHERE m.roleid = r.oid)
        AND c.relowner <> r.oid
        AND (has_table_privilege(r.oid, c.oid, p.privilege)
          OR (p.privilege IN ('INSERT','UPDATE') AND has_any_column_privilege(r.oid, c.oid, p.privilege)))) w),
  'app_schema_create', (SELECT has_schema_privilege(oid, 'public', 'CREATE') FROM pg_roles WHERE rolname = 'amjis_app')
);
