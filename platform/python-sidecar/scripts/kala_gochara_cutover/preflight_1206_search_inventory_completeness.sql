-- Preflight for migration 1206 (AM-5 search-completeness storage + seal checks). READ ONLY —
-- run against the target database BEFORE applying 1206, AFTER migration 1157 is applied
-- (ordered execution: preflights run interleaved with their prerequisite migrations,
-- never as one undifferentiated batch).
--
-- THIS BLOCK IS BYTE-IDENTICAL TO THE GATE EMBEDDED AT THE TOP OF
-- platform/migrations/1206_gochara_search_inventory_completeness.sql — the migration runs the
-- same detector itself, in the runner's transaction, before its DDL, so the protected
-- public-schema window (deploy.yml `gochara_contracts_schema_migration`) observes the gate
-- without further wiring. The static test
-- tests/unit/migrations/gochara_b6_am5_search_inventory_static.test.ts asserts the two blocks
-- are identical.
--
-- GATE SEMANTICS: FAILS CLOSED — any blocking finding RAISES; success ends with NOTICE
-- 'preflight 1206: all checks passed'. Only REAL preconditions are checked: the pinned schema
-- and its privileges; the tables/functions the new objects depend on exist (including the L1
-- chart_facts/chart_dashas the input digests read); none of the six new tables exists yet; the
-- prerequisite migration 1157 is recorded and 1206 is not.

DO $$
DECLARE
  failures text;
BEGIN
  WITH f(failure, detail) AS (
    SELECT 'schema_missing', 'public'
    WHERE to_regnamespace('public') IS NULL
    UNION ALL
    SELECT 'no_usage_privilege_on_public', current_user
    WHERE NOT has_schema_privilege('public', 'USAGE')
    UNION ALL
    SELECT 'no_create_privilege_on_public', current_user
    WHERE NOT has_schema_privilege('public', 'CREATE')
    UNION ALL
    SELECT 'table_missing', t.rel
    FROM (VALUES ('public.charts'), ('public.ka_gochara_generation_seal'),
                 ('public.ka_gochara_rule_path_seal'), ('public.ka_gochara_sky_convention'),
                 ('public.ka_gochara_av_polarity_declaration'),
                 ('public.kala_gochara_coverage'), ('public.kala_gochara_publication'),
                 ('public.chart_facts'), ('public.chart_dashas')) AS t(rel)
    WHERE to_regclass(t.rel) IS NULL
    UNION ALL
    SELECT 'function_missing', p.sig
    FROM (VALUES ('public.ka_gochara_lock_chart(uuid)'),
                 ('public.ka_gochara_lock_global_shared()'),
                 ('public.ka_gochara_generation_is_sealed(uuid,text)'),
                 ('public.ka_gochara_generation_governed(text)'),
                 ('public.ka_gochara_horizon_finite_ok(tstzrange)'),
                 ('public.ka_gochara_chart_statement_lock()'),
                 ('public.ka_gochara_refuse_truncate()'),
                 ('public.ka_gochara_require_sealed_rule_path()')) AS p(sig)
    WHERE to_regprocedure(p.sig) IS NULL
    UNION ALL
    SELECT 'object_already_exists', o.rel
    FROM (VALUES ('public.ka_gochara_search_input_snapshot'), ('public.ka_gochara_search_inventory'),
                 ('public.ka_gochara_search_path_pin'), ('public.ka_gochara_search_obligation'),
                 ('public.ka_gochara_search_interval'),
                 ('public.ka_gochara_search_inventory_verification')) AS o(rel)
    WHERE to_regclass(o.rel) IS NOT NULL
    UNION ALL
    -- ordered execution gate: 1157 recorded, 1206 not
    SELECT 'prerequisite_migration_not_applied', p.prefix
    FROM (VALUES ('1157_')) AS p(prefix)
    WHERE to_regclass('public._migrations_applied') IS NOT NULL
      AND NOT EXISTS (SELECT 1 FROM _migrations_applied m WHERE starts_with(m.filename, p.prefix))
    UNION ALL
    SELECT 'migration_already_applied', m.filename
    FROM _migrations_applied m
    WHERE to_regclass('public._migrations_applied') IS NOT NULL
      AND starts_with(m.filename, '1206_')
  )
  SELECT string_agg(f.failure || ' :: ' || f.detail, E'\n' ORDER BY f.failure, f.detail)
  INTO failures
  FROM f;
  IF failures IS NOT NULL THEN
    RAISE EXCEPTION 'preflight 1206 BLOCKED — migration 1206 must NOT be applied:% %', E'\n', failures;
  END IF;
  RAISE NOTICE 'preflight 1206: all checks passed';
END;
$$;
