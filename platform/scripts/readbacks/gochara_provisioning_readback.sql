WITH
-- J4B preparation only: one SELECT/WITH accepted by executor readback_sql.
-- Independent catalog readback of the 1378 v7 grants, L1 reads and principals.
-- No function under audit is executed; no write or password read is attempted.
-- Each row names its expected and observed value; missing inputs are failures.
-- Expected ACL is reviewed here separately from the migration's own closure.
spec AS (SELECT $spec$
{
  "roles": {
    "gochara_verifier": {
      "tables": [
        ["ka_gochara_eval_window_verification","SELECT",null,"1240"],
        ["ka_gochara_eval_window_verification","INSERT",null,"1240"],
        ["ka_gochara_eval_window_verification","DELETE",null,"1240"],
        ["ka_gochara_eval_window","SELECT",null,"1240"],
        ["ka_gochara_eval_window_record","SELECT",null,"1240"],
        ["ka_gochara_relationship_record","SELECT",null,"1240"],
        ["ka_gochara_record_prerequisite","SELECT",null,"1240"],
        ["ka_gochara_contact","SELECT",null,"1240"],
        ["ka_gochara_physical_object","SELECT",null,"1240"],
        ["kala_gochara_coverage","SELECT",null,"1240"],
        ["ka_gochara_search_inventory","SELECT",null,"1240"],
        ["ka_gochara_search_path_pin","SELECT",null,"1240"],
        ["ka_gochara_search_input_snapshot","SELECT",null,"1240"],
        ["ka_gochara_generation_seal","SELECT",null,"1240"],
        ["ka_gochara_rule_path","SELECT",null,"1240"],
        ["ka_gochara_rule_path_seal","SELECT",null,"1240"],
        ["ka_gochara_rule_path_soft_factor","SELECT",null,"1240"],
        ["ka_gochara_factor","SELECT",null,"1240"],
        ["kala_gochara_publication","SELECT",null,"1240"],
        ["ka_gochara_search_inventory_verification","SELECT",null,"1378"],
        ["ka_gochara_search_inventory_verification","INSERT",null,"1378"],
        ["ka_gochara_sky_convention","SELECT",null,"1378"],
        ["ka_gochara_rule_path_prerequisite","SELECT",null,"1378"],
        ["ka_gochara_predicate","SELECT",null,"1378"],
        ["ka_gochara_search_obligation","SELECT",null,"1378"],
        ["ka_gochara_convention_bridge","SELECT",null,"1378"],
        ["ka_gochara_search_interval","SELECT",null,"1378"],
        ["_migrations_applied","SELECT",["filename","sha256","applied_at"],"1378"],
        ["kala_gochara_contacts","SELECT",null,"1378"],
        ["kala_gochara_windows","SELECT",["chart_id","generation"],"1378"],
        ["ka_gochara_seal_brief","SELECT",null,"1378"],
        ["ka_gochara_seal_brief","INSERT",null,"1378"],
        ["chart_facts","SELECT",null,"L1 ACL owner"],
        ["chart_dashas","SELECT",null,"L1 ACL owner"]
      ],
      "functions": [
        ["ka_gochara_lock_chart(uuid)","1240"],
        ["ka_gochara_lock_global_shared()","1240"],
        ["ka_gochara_generation_is_sealed(uuid,text)","1240"],
        ["ka_gochara_generation_governed(text)","1240"],
        ["ka_gochara_eval_window_content_digest(uuid,text,text,text,text)","1240"],
        ["ka_gochara_eval_window_stored_digest(uuid,text,text,text,text)","1240"],
        ["ka_gochara_eval_window_expected_digest(uuid,text,text,text,text)","1240"],
        ["ka_gochara_eval_window_inputs_digest(uuid,text,text,text,text)","1240"],
        ["ka_gochara_canonical_json(jsonb)","1240"],
        ["ka_gochara_sha256_hex(text)","1240"],
        ["ka_gochara_f4_token(real)","1240"],
        ["ka_gochara_candidate_gate_violations(uuid,text)","1240"],
        ["ka_gochara_window_verification_violations(uuid,text)","1378"],
        ["ka_gochara_search_completeness_violations(uuid,text)","1378"],
        ["ka_gochara_search_l1_facts_digest(uuid,text[])","1378"],
        ["ka_gochara_search_dasha_digest(uuid,uuid[])","1378"],
        ["ka_gochara_search_inventory_digest(uuid,text,text)","1378"],
        ["ka_gochara_search_ledger_digest(uuid,text,text)","1378"],
        ["ka_gochara_search_inventory_preimage(uuid,text,text)","1378"],
        ["ka_gochara_utc_ts(timestamptz)","1378"],
        ["ka_gochara_search_moon_scope_violations(uuid,text)","1378"],
        ["ka_gochara_search_moon_resolved_domain(uuid,text,text,uuid)","1378"],
        ["ka_gochara_legacy_projection_rows(uuid,text)","1378"],
        ["ka_gochara_brief_state_digest(uuid,text)","1378"]
      ]
    },
    "gochara_sealer": {
      "tables": [
        ["ka_gochara_eval_window_verification","SELECT",null,"1240"],
        ["ka_gochara_eval_window","SELECT",null,"1240"],
        ["ka_gochara_eval_window_record","SELECT",null,"1240"],
        ["ka_gochara_relationship_record","SELECT",null,"1240"],
        ["ka_gochara_search_path_pin","SELECT",null,"1240"],
        ["ka_gochara_search_input_snapshot","SELECT",null,"1240"],
        ["ka_gochara_generation_seal","SELECT",null,"1240"],
        ["kala_gochara_publication","SELECT",null,"1240"],
        ["ka_gochara_record_prerequisite","SELECT",null,"1240"],
        ["ka_gochara_contact","SELECT",null,"1240"],
        ["ka_gochara_physical_object","SELECT",null,"1240"],
        ["ka_gochara_seal_approval","SELECT",null,"1378"],
        ["ka_gochara_seal_approval","INSERT",null,"1378"],
        ["_migrations_applied","SELECT",["filename","sha256","applied_at"],"1378"],
        ["ka_gochara_seal_brief","SELECT",null,"1378"],
        ["ka_gochara_generation_seal","INSERT",null,"1378"],
        ["kala_gochara_publication","UPDATE",["status","published_at","content_digest","row_counts"],"1378"],
        ["kala_gochara_windows","SELECT",["chart_id","generation"],"1378"],
        ["kala_gochara_coverage","SELECT",null,"1378"],
        ["kala_gochara_contacts","SELECT",null,"1378"],
        ["ka_gochara_rule_path_seal","SELECT",null,"1378"],
        ["ka_gochara_rule_path","SELECT",null,"1378"],
        ["ka_gochara_rule_path_prerequisite","SELECT",null,"1378"],
        ["ka_gochara_rule_path_soft_factor","SELECT",null,"1378"],
        ["ka_gochara_predicate","SELECT",null,"1378"],
        ["ka_gochara_factor","SELECT",null,"1378"],
        ["ka_gochara_convention_bridge","SELECT",null,"1378"],
        ["ka_gochara_search_inventory","SELECT",null,"1378"],
        ["ka_gochara_search_obligation","SELECT",null,"1378"],
        ["ka_gochara_search_interval","SELECT",null,"1378"],
        ["ka_gochara_search_inventory_verification","SELECT",null,"1378"],
        ["chart_facts","SELECT",null,"L1 ACL owner"],
        ["chart_dashas","SELECT",null,"L1 ACL owner"]
      ],
      "functions": [
        ["ka_gochara_window_verification_violations(uuid,text)","1240"],
        ["ka_gochara_window_verification_replay_violations(uuid,text)","1240"],
        ["ka_gochara_candidate_gate_violations(uuid,text)","1240"],
        ["ka_gochara_eval_window_content_digest(uuid,text,text,text,text)","1240"],
        ["ka_gochara_eval_window_stored_digest(uuid,text,text,text,text)","1240"],
        ["ka_gochara_eval_window_expected_digest(uuid,text,text,text,text)","1240"],
        ["ka_gochara_eval_window_inputs_digest(uuid,text,text,text,text)","1240"],
        ["ka_gochara_f4_token(real)","1240"],
        ["ka_gochara_canonical_json(jsonb)","1240"],
        ["ka_gochara_sha256_hex(text)","1240"],
        ["ka_gochara_lock_chart(uuid)","1240"],
        ["ka_gochara_lock_global_shared()","1240"],
        ["ka_gochara_seal_generation(uuid,text)","1378"],
        ["ka_gochara_coverage_drift(uuid,text)","1378"],
        ["ka_gochara_horizon_finite_ok(tstzrange)","1378"],
        ["ka_gochara_coverage_facts(text,tstzrange,text[])","1378"],
        ["ka_gochara_facts_horizon(jsonb)","1378"],
        ["ka_gochara_membership_violations(uuid,text)","1378"],
        ["ka_gochara_membership_violation(jsonb,uuid,text,jsonb,tstzrange[])","1378"],
        ["ka_gochara_search_completeness_violations(uuid,text)","1378"],
        ["ka_gochara_search_replay_violations(uuid,text)","1378"],
        ["ka_gochara_search_l1_facts_digest(uuid,text[])","1378"],
        ["ka_gochara_search_dasha_digest(uuid,uuid[])","1378"],
        ["ka_gochara_search_inventory_digest(uuid,text,text)","1378"],
        ["ka_gochara_search_ledger_digest(uuid,text,text)","1378"],
        ["ka_gochara_search_inventory_preimage(uuid,text,text)","1378"],
        ["ka_gochara_utc_ts(timestamptz)","1378"],
        ["ka_gochara_search_moon_scope_violations(uuid,text)","1378"],
        ["ka_gochara_search_moon_resolved_domain(uuid,text,text,uuid)","1378"],
        ["ka_gochara_generation_governed(text)","1378"],
        ["ka_gochara_seal_receipt_missing(uuid,text)","1378"],
        ["ka_gochara_legacy_projection_rows(uuid,text)","1378"],
        ["ka_gochara_brief_state_digest(uuid,text)","1378"],
        ["ka_gochara_seal_brief_problem(uuid,text,uuid,text)","1378"]
      ]
    }
  },
  "builder_backfill": {"role": "data_plane_builder", "functions": ["ka_gochara_window_qualification_ok(jsonb)"]},
  "ledger": {
  "1204_gochara_av_qualifier_object_role.sql": "a0b267f7ef6002a1997c30d34595ec3b86147ca617bf70ef8a05de55b8407ca1",
  "1206_gochara_search_inventory_completeness.sql": "941c79f59f2d3d3125dc5ca680430d4a91a7dcddb53fc6daa9a9da8819e410d7",
  "1232_gochara_search_moon_scope_domain.sql": "f2ef6406604b819d5f443e32c1e70914f2337ead8867f12e0aecd96d13f1ec44",
  "1233_gochara_p1_period_anchor.sql": "958b911703eee3528e1db75624984020964b8d31fe3fe286d64071368bd5a705",
  "1240_gochara_window_verification_gate.sql": "05a8f897a0b8ae6b955915eced717ad30c98af485d490185333a88355707bc6b",
  "1378_gochara_verifier_sealer_inventory_grants.sql": "04540a995e849517d03d80835a4dfaae0ee588c081485337d976814e44a70108"
}
}
$spec$::jsonb AS body),
principals AS (
  SELECT name, r.oid, r.rolcanlogin, r.rolinherit, r.rolsuper, r.rolcreatedb,
         r.rolcreaterole, r.rolreplication, r.rolbypassrls, r.rolconnlimit
  FROM (VALUES ('gochara_verifier'), ('gochara_sealer'), ('data_plane_builder'), ('amjis_app')) names(name)
  LEFT JOIN pg_catalog.pg_roles r ON r.rolname = names.name
),
table_spec AS (
  SELECT role.key AS principal, e->>0 AS object, e->>1 AS privilege, e->2 AS columns
  FROM spec, jsonb_each(body->'roles') role,
       LATERAL jsonb_array_elements(role.value->'tables') e
),
function_spec AS (
  SELECT role.key AS principal, e->>0 AS signature
  FROM spec, jsonb_each(body->'roles') role,
       LATERAL jsonb_array_elements(role.value->'functions') e
),
relations AS (
  SELECT DISTINCT name, to_regclass('public.' || quote_ident(name))::oid AS oid
  FROM (
    SELECT object AS name FROM table_spec
    UNION
    SELECT relname FROM pg_catalog.pg_class
    WHERE relnamespace = 'public'::regnamespace AND relkind IN ('r','p','v','m','f')
      AND relname ~ '^ka(la)?_gochara_'
  ) names
),
columns AS (
  SELECT rel.name AS object, att.attname AS name, att.attnum, rel.oid
  FROM relations rel JOIN pg_catalog.pg_attribute att ON att.attrelid = rel.oid
  WHERE att.attnum > 0 AND NOT att.attisdropped
  UNION
  SELECT rel.name, col.name, att.attnum, rel.oid
  FROM table_spec e JOIN relations rel ON rel.name = e.object
       CROSS JOIN LATERAL jsonb_array_elements_text(CASE WHEN jsonb_typeof(e.columns) = 'array' THEN e.columns ELSE '[]'::jsonb END) col(name)
       LEFT JOIN pg_catalog.pg_attribute att ON att.attrelid = rel.oid AND att.attname = col.name AND NOT att.attisdropped
),
functions AS (
  SELECT DISTINCT oid, COALESCE(oid::regprocedure::text, signature) AS signature
  FROM (
    SELECT to_regprocedure('public.' || signature)::oid AS oid, signature FROM function_spec
    UNION
    SELECT p.oid, p.oid::regprocedure::text FROM pg_catalog.pg_proc p
    WHERE p.pronamespace = 'public'::regnamespace AND p.proname ~ '^ka_gochara_'
  ) names
),
checks AS (
  SELECT 'principal'::text AS kind, p.name AS principal, p.name AS object, a.key AS privilege,
         a.expected, a.observed
  FROM principals p CROSS JOIN LATERAL (VALUES
    ('exists', true, p.oid IS NOT NULL),
    -- Object ACLs alone do not permit access without namespace USAGE.
    -- PostgreSQL includes PUBLIC pseudo-role grants in this effective check.
    ('schema-usage', true, has_schema_privilege(p.oid, 'public', 'USAGE')),
    ('schema-create', false, has_schema_privilege(p.oid, 'public', 'CREATE'))
  ) a(key, expected, observed)
  UNION ALL
  SELECT 'principal', p.name, p.name, a.key, a.expected, a.observed
  FROM principals p CROSS JOIN LATERAL (VALUES
    ('login', true, p.rolcanlogin), ('inherit', false, p.rolinherit),
    ('superuser', false, p.rolsuper), ('createdb', false, p.rolcreatedb),
    ('createrole', false, p.rolcreaterole), ('replication', false, p.rolreplication),
    ('bypassrls', false, p.rolbypassrls),
    ('connection-limit', true, p.rolconnlimit = CASE WHEN p.name = 'gochara_verifier' THEN 4 ELSE 2 END),
    ('database-connect', true, has_database_privilege(p.oid, current_database(), 'CONNECT')),
    ('no-memberships', true, NOT EXISTS (
      SELECT 1 FROM pg_catalog.pg_roles other WHERE other.oid <> p.oid AND pg_has_role(p.oid, other.oid, 'MEMBER')))
  ) a(key, expected, observed)
  WHERE p.name IN ('gochara_verifier','gochara_sealer')
  UNION ALL
  SELECT 'table', p.name, rel.name, priv.name,
         EXISTS (SELECT 1 FROM table_spec e WHERE e.principal = p.name AND e.object = rel.name
                 AND e.privilege = priv.name AND e.columns = 'null'::jsonb),
         has_table_privilege(p.oid, rel.oid, priv.name)
  FROM principals p CROSS JOIN relations rel
  CROSS JOIN (VALUES ('SELECT'),('INSERT'),('UPDATE'),('DELETE'),('TRUNCATE'),('REFERENCES'),('TRIGGER')) priv(name)
  WHERE p.name IN ('gochara_verifier','gochara_sealer')
  UNION ALL
  SELECT 'table-grant-option', p.name, rel.name, priv.name, false,
         has_table_privilege(p.oid, rel.oid, priv.name || ' WITH GRANT OPTION')
  FROM principals p CROSS JOIN relations rel
  CROSS JOIN (VALUES ('SELECT'),('INSERT'),('UPDATE'),('DELETE'),('TRUNCATE'),('REFERENCES'),('TRIGGER')) priv(name)
  WHERE p.name IN ('gochara_verifier','gochara_sealer')
  UNION ALL
  SELECT 'column', p.name, col.object || '.' || col.name, priv.name,
         EXISTS (SELECT 1 FROM table_spec e WHERE e.principal = p.name AND e.object = col.object
                 AND e.privilege = priv.name AND (e.columns = 'null'::jsonb OR e.columns ? col.name)),
         has_column_privilege(p.oid, col.oid, col.attnum, priv.name)
  FROM principals p CROSS JOIN columns col
  CROSS JOIN (VALUES ('SELECT'),('INSERT'),('UPDATE'),('REFERENCES')) priv(name)
  WHERE p.name IN ('gochara_verifier','gochara_sealer')
  UNION ALL
  SELECT 'column-grant-option', p.name, col.object || '.' || col.name, priv.name, false,
         has_column_privilege(p.oid, col.oid, col.attnum, priv.name || ' WITH GRANT OPTION')
  FROM principals p CROSS JOIN columns col
  CROSS JOIN (VALUES ('SELECT'),('INSERT'),('UPDATE'),('REFERENCES')) priv(name)
  WHERE p.name IN ('gochara_verifier','gochara_sealer')
  UNION ALL
  SELECT 'function', p.name, f.signature, 'EXECUTE',
         EXISTS (SELECT 1 FROM function_spec e WHERE e.principal = p.name
                 AND to_regprocedure('public.' || e.signature)::oid = f.oid),
         has_function_privilege(p.oid, f.oid, 'EXECUTE')
  FROM principals p CROSS JOIN functions f WHERE p.name IN ('gochara_verifier','gochara_sealer')
  UNION ALL
  SELECT 'function-grant-option', p.name, f.signature, 'EXECUTE', false,
         has_function_privilege(p.oid, f.oid, 'EXECUTE WITH GRANT OPTION')
  FROM principals p CROSS JOIN functions f WHERE p.name IN ('gochara_verifier','gochara_sealer')
  UNION ALL
  SELECT 'builder-write', p.name, rel.name, priv.name, false,
         has_table_privilege(p.oid, rel.oid, priv.name)
  FROM principals p CROSS JOIN relations rel
  CROSS JOIN (VALUES ('INSERT'),('UPDATE'),('DELETE'),('TRUNCATE'),('REFERENCES'),('TRIGGER')) priv(name)
  WHERE p.name = 'data_plane_builder'
    AND rel.name IN ('ka_gochara_search_inventory_verification','ka_gochara_eval_window_verification')
  UNION ALL
  SELECT 'builder-column-write', p.name, col.object || '.' || col.name, priv.name, false,
         has_column_privilege(p.oid, col.oid, col.attnum, priv.name)
  FROM principals p CROSS JOIN columns col
  CROSS JOIN (VALUES ('INSERT'),('UPDATE'),('REFERENCES')) priv(name)
  WHERE p.name = 'data_plane_builder'
    AND col.object IN ('ka_gochara_search_inventory_verification','ka_gochara_eval_window_verification')
  UNION ALL
  SELECT 'builder-function', p.name, f.signature, 'EXECUTE', f.expected,
         has_function_privilege(p.oid, to_regprocedure('public.' || f.signature)::oid, 'EXECUTE')
  FROM principals p CROSS JOIN (VALUES ('ka_gochara_window_qualification_ok(jsonb)', true),
                                       ('ka_gochara_seal_generation(uuid,text)', false)) f(signature, expected)
  WHERE p.name = 'data_plane_builder'
  UNION ALL
  SELECT 'builder-membership', b.name, p.name, 'MEMBER', false, pg_has_role(b.oid, p.oid, 'MEMBER')
  FROM principals b CROSS JOIN principals p
  WHERE b.name = 'data_plane_builder' AND p.name IN ('gochara_verifier','gochara_sealer')
  UNION ALL
  SELECT 'ledger', 'amjis_app', e.key, 'sha256', true,
         (SELECT count(*) = 1 AND bool_and(a.sha256 = e.value)
          FROM public._migrations_applied a WHERE a.filename = e.key)
  FROM spec, jsonb_each_text(body->'ledger') e
)
SELECT kind, principal, object, privilege, expected, observed,
       observed IS NOT NULL AND observed = expected AS ok,
       current_user AS readback_user, session_user AS readback_session_user,
       current_database() AS database, host(inet_server_addr()) AS server_address,
       inet_server_port() AS server_port
FROM checks
ORDER BY kind COLLATE "C", principal COLLATE "C", object COLLATE "C", privilege COLLATE "C";
