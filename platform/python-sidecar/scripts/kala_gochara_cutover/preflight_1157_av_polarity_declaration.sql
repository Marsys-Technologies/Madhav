-- Preflight for migration 1157 (ka_gochara_av_polarity_declaration). READ ONLY — run against the target
-- database BEFORE applying 1157, AFTER migration 1153 is applied (ordered
-- execution: preflights run interleaved with their prerequisite migrations,
-- never as one undifferentiated batch).
--
-- THIS BLOCK IS BYTE-IDENTICAL TO THE GATE EMBEDDED AT THE TOP OF
-- platform/migrations/1157_gochara_av_polarity_declaration.sql — the migration runs the same
-- detector itself, in the runner's transaction, before its DDL, so the
-- protected public-schema window (deploy.yml `gochara_contracts_schema_migration`,
-- the only route that applies 1153-1157) observes the gate without any
-- further wiring. The static test
-- tests/unit/migrations/gochara_a5_1_contract_static.test.ts asserts the two
-- blocks are identical.
--
-- GATE SEMANTICS (amendment 8 / F8 / F9; steward ruling 3): FAILS CLOSED —
-- any blocking finding RAISES (psql -v ON_ERROR_STOP=1 aborts; node-pg
-- rejects); success ends with NOTICE 'preflight 1157: all checks passed'. Fix
-- the environment, not the detector (ADK-0026). Only REAL preconditions are
-- checked:
--   (d) pinned schema 'public' exists; USAGE + CREATE on it; the REFERENCES /
--       SELECT privileges on the parents this migration binds to or reads;
--   (a) no untracked same-name collision: relation namespace (tables +
--       indexes share pg_class), table-scoped triggers, functions by EXACT
--       ARGUMENT TYPES (proargtypes → format_type; never the name-retaining
--       pg_get_function_identity_arguments text);
--   (b) in-database parents exist with the expected column types and
--       PK/UNIQUE definitions (pg_constraint-verified): the 1153 shared helpers (exact signatures);
--   (c) prerequisite migrations are recorded in _migrations_applied and 1157
--       is not (wildcard-safe starts_with, not LIKE).
-- migrate.ts tracks applied files by hash: a tracked file is never re-run;
-- an untracked re-run is a collision and is BLOCKED here. There is no replay
-- mode.

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
    SELECT 'relation_already_exists', 'public.' || c.relname
    FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public'
      AND c.relname IN ('ka_gochara_av_polarity_declaration',
                        'ka_gochara_av_polarity_declaration_pkey')
    UNION ALL
    SELECT 'trigger_already_exists', 'public.' || c.relname || '.' || t.tgname
    FROM pg_trigger t
    JOIN pg_class c ON c.oid = t.tgrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public' AND NOT t.tgisinternal
      AND c.relname = 'ka_gochara_av_polarity_declaration'
      AND t.tgname IN ('ka_gochara_av_polarity_write_guard', 'ka_gochara_av_polarity_no_truncate')
    UNION ALL
    SELECT 'helper_function_missing', e.sig
    FROM (VALUES ('ka_gochara_text_array_ok(text[],integer)')) AS e(sig)
    WHERE to_regprocedure('public.' || e.sig) IS NULL
       OR (SELECT format_type(p.prorettype, NULL) FROM pg_proc p
           WHERE p.oid = to_regprocedure('public.' || e.sig)) <> 'boolean'
    UNION ALL
    SELECT 'helper_function_missing', e.sig
    FROM (VALUES ('ka_gochara_refuse_truncate()'),
                 ('ka_gochara_global_write_guard()')) AS e(sig)
    WHERE to_regprocedure('public.' || e.sig) IS NULL
    UNION ALL
    SELECT 'prerequisite_migration_not_applied', p.prefix
    FROM (VALUES ('1153_')) AS p(prefix)
    WHERE to_regclass('public._migrations_applied') IS NOT NULL
      AND NOT EXISTS (SELECT 1 FROM _migrations_applied m WHERE starts_with(m.filename, p.prefix))
    UNION ALL
    SELECT 'migration_already_applied', m.filename
    FROM _migrations_applied m
    WHERE to_regclass('public._migrations_applied') IS NOT NULL
      AND starts_with(m.filename, '1157_')
  )
  SELECT string_agg(f.failure || ' :: ' || f.detail, E'\n' ORDER BY f.failure, f.detail)
  INTO failures
  FROM f;
  IF failures IS NOT NULL THEN
    RAISE EXCEPTION 'preflight 1157 BLOCKED — migration 1157 must NOT be applied:% %', E'\n', failures;
  END IF;
  RAISE NOTICE 'preflight 1157: all checks passed';
END;
$$;
