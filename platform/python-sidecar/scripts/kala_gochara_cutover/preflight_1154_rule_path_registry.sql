-- Preflight for migration 1154 (ka_gochara rule-path registries). READ ONLY — run against the target
-- database BEFORE applying 1154, AFTER migration 1153 is applied (ordered
-- execution: preflights run interleaved with their prerequisite migrations,
-- never as one undifferentiated batch).
--
-- THIS BLOCK IS BYTE-IDENTICAL TO THE GATE EMBEDDED AT THE TOP OF
-- platform/migrations/1154_gochara_rule_path_registry.sql — the migration runs the same
-- detector itself, in the runner's transaction, before its DDL, so the
-- protected public-schema window (deploy.yml `gochara_contracts_schema_migration`,
-- the only route that applies 1153-1157) observes the gate without any
-- further wiring. The static test
-- tests/unit/migrations/gochara_a5_1_contract_static.test.ts asserts the two
-- blocks are identical.
--
-- GATE SEMANTICS (amendment 8 / F8 / F9; steward ruling 3): FAILS CLOSED —
-- any blocking finding RAISES (psql -v ON_ERROR_STOP=1 aborts; node-pg
-- rejects); success ends with NOTICE 'preflight 1154: all checks passed'. Fix
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
--   (c) prerequisite migrations are recorded in _migrations_applied and 1154
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
      AND c.relname IN ('ka_gochara_predicate', 'ka_gochara_predicate_pkey',
                        'ka_gochara_factor', 'ka_gochara_factor_pkey',
                        'ka_gochara_rule_path', 'ka_gochara_rule_path_pkey',
                        'ka_gochara_rule_path_prerequisite', 'ka_gochara_rule_path_prerequisite_pkey',
                        'kgrpp_no_dup_uq',
                        'ka_gochara_rule_path_soft_factor', 'ka_gochara_rule_path_soft_factor_pkey',
                        'ka_gochara_rule_path_seal', 'ka_gochara_rule_path_seal_pkey')
    UNION ALL
    SELECT 'trigger_already_exists', 'public.' || c.relname || '.' || t.tgname
    FROM pg_trigger t
    JOIN pg_class c ON c.oid = t.tgrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public' AND NOT t.tgisinternal
      AND ( (c.relname = 'ka_gochara_predicate'
               AND t.tgname IN ('ka_gochara_predicate_write_guard', 'ka_gochara_predicate_no_truncate'))
         OR (c.relname = 'ka_gochara_factor'
               AND t.tgname IN ('ka_gochara_factor_write_guard', 'ka_gochara_factor_no_truncate'))
         OR (c.relname = 'ka_gochara_rule_path'
               AND t.tgname IN ('ka_gochara_rule_path_write_guard', 'ka_gochara_rule_path_no_truncate'))
         OR (c.relname = 'ka_gochara_rule_path_prerequisite'
               AND t.tgname IN ('ka_gochara_rp_prereq_sealed_check', 'ka_gochara_rp_prereq_write_guard',
                                'ka_gochara_rp_prereq_no_truncate'))
         OR (c.relname = 'ka_gochara_rule_path_soft_factor'
               AND t.tgname IN ('ka_gochara_rp_soft_factor_sealed_check', 'ka_gochara_rp_soft_factor_write_guard',
                                'ka_gochara_rp_soft_factor_no_truncate'))
         OR (c.relname = 'ka_gochara_rule_path_seal'
               AND t.tgname IN ('ka_gochara_rule_path_seal_write_guard', 'ka_gochara_rule_path_seal_no_truncate')) )
    UNION ALL
    -- function collisions by EXACT ARGUMENT TYPES (F8)
    SELECT 'function_already_exists',
           'public.' || p.proname || '(' || array_to_string(e.argtypes, ',') || ')'
    FROM (VALUES
            ('ka_gochara_frame_ok',                       ARRAY['text','text']),
            ('ka_gochara_selector_token_ok',              ARRAY['text']),
            ('ka_gochara_string_array_ok',                ARRAY['jsonb']),
            ('ka_gochara_vocab_array_ok',                 ARRAY['jsonb','text[]']),
            ('ka_gochara_named_operands_ok',              ARRAY['jsonb']),
            ('ka_gochara_object_selector_ok',             ARRAY['jsonb']),
            ('ka_gochara_object_selector_consistent_ok',  ARRAY['jsonb','jsonb','jsonb']),
            ('ka_gochara_membership_guard',               ARRAY[]::text[]),
            ('ka_gochara_require_sealed_rule_path',       ARRAY[]::text[])
         ) AS e(fname, argtypes)
    JOIN pg_proc p ON p.proname = e.fname
    JOIN pg_namespace n ON n.oid = p.pronamespace AND n.nspname = 'public'
    WHERE (SELECT COALESCE(array_agg(format_type(u.oid, NULL) ORDER BY u.ord), '{}')
           FROM unnest(p.proargtypes) WITH ORDINALITY AS u(oid, ord)) = e.argtypes
    UNION ALL
    -- shared helpers from 1153 must be present with their exact signatures
    SELECT 'helper_function_missing', e.sig
    FROM (VALUES ('ka_gochara_refuse_truncate()'),
                 ('ka_gochara_global_write_guard()'),
                 ('ka_gochara_lock_global()'),
                 ('ka_gochara_lock_global_shared()'),
                 ('ka_gochara_lock_chart(uuid)'),
                 ('ka_gochara_finite_ok(double precision)')) AS e(sig)
    WHERE to_regprocedure('public.' || e.sig) IS NULL
    UNION ALL
    -- ordered execution gate: 1153 recorded, 1154 not
    SELECT 'prerequisite_migration_not_applied', p.prefix
    FROM (VALUES ('1153_')) AS p(prefix)
    WHERE to_regclass('public._migrations_applied') IS NOT NULL
      AND NOT EXISTS (SELECT 1 FROM _migrations_applied m WHERE starts_with(m.filename, p.prefix))
    UNION ALL
    SELECT 'migration_already_applied', m.filename
    FROM _migrations_applied m
    WHERE to_regclass('public._migrations_applied') IS NOT NULL
      AND starts_with(m.filename, '1154_')
  )
  SELECT string_agg(f.failure || ' :: ' || f.detail, E'\n' ORDER BY f.failure, f.detail)
  INTO failures
  FROM f;
  IF failures IS NOT NULL THEN
    RAISE EXCEPTION 'preflight 1154 BLOCKED — migration 1154 must NOT be applied:% %', E'\n', failures;
  END IF;
  RAISE NOTICE 'preflight 1154: all checks passed';
END;
$$;
