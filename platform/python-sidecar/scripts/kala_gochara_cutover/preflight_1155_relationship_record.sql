-- Preflight for migration 1155 (ka_gochara_relationship_record). READ ONLY — run against the target
-- database BEFORE applying 1155, AFTER migrations 1153 and 1154 are applied (ordered
-- execution: preflights run interleaved with their prerequisite migrations,
-- never as one undifferentiated batch).
--
-- THIS BLOCK IS BYTE-IDENTICAL TO THE GATE EMBEDDED AT THE TOP OF
-- platform/migrations/1155_gochara_relationship_record.sql — the migration runs the same
-- detector itself, in the runner's transaction, before its DDL, so the
-- protected public-schema window (deploy.yml `gochara_contracts_schema_migration`,
-- the only route that applies 1153-1157) observes the gate without any
-- further wiring. The static test
-- tests/unit/migrations/gochara_a5_1_contract_static.test.ts asserts the two
-- blocks are identical.
--
-- GATE SEMANTICS (amendment 8 / F8 / F9; steward ruling 3): FAILS CLOSED —
-- any blocking finding RAISES (psql -v ON_ERROR_STOP=1 aborts; node-pg
-- rejects); success ends with NOTICE 'preflight 1155: all checks passed'. Fix
-- the environment, not the detector (ADK-0026). Only REAL preconditions are
-- checked:
--   (d) pinned schema 'public' exists; USAGE + CREATE on it; the REFERENCES /
--       SELECT privileges on the parents this migration binds to or reads;
--   (a) no untracked same-name collision: relation namespace (tables +
--       indexes share pg_class), table-scoped triggers, functions by EXACT
--       ARGUMENT TYPES (proargtypes → format_type; never the name-retaining
--       pg_get_function_identity_arguments text);
--   (b) in-database parents exist with the expected column types and
--       PK/UNIQUE definitions (pg_constraint-verified): charts, kala_gochara_coverage (incl. the columns the applicability guard reads), ka_gochara_contact + kgc_reference_uq, ka_gochara_physical_object, ka_gochara_rule_path(+seal), ka_gochara_predicate, ka_gochara_convention_bridge, ka_gochara_generation_seal, helpers by exact signature and return type;
--   (c) prerequisite migrations are recorded in _migrations_applied and 1155
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
    SELECT 'no_references_privilege', p.t
    FROM (VALUES ('public.charts'), ('public.kala_gochara_coverage')) AS p(t)
    WHERE to_regclass(p.t) IS NOT NULL AND NOT has_table_privilege(p.t, 'REFERENCES')
    UNION ALL
    SELECT 'relation_already_exists', 'public.' || c.relname
    FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public'
      AND c.relname IN ('ka_gochara_relationship_record', 'ka_gochara_relationship_record_pkey',
                        'kgrr_identity_uq', 'kgrr_membership_uq',
                        'ka_gochara_record_prerequisite', 'ka_gochara_record_prerequisite_pkey',
                        'kgrpr_no_dup_uq',
                        'idx_kgrr_chart_gen', 'idx_kgrr_contact', 'idx_kgrr_object',
                        'idx_kgrr_path', 'idx_kgrr_coverage', 'idx_kgrpr_record')
    UNION ALL
    SELECT 'trigger_already_exists', 'public.' || c.relname || '.' || t.tgname
    FROM pg_trigger t
    JOIN pg_class c ON c.oid = t.tgrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public' AND NOT t.tgisinternal
      AND ( (c.relname = 'ka_gochara_relationship_record'
               AND t.tgname IN ('ka_gochara_rr_1_write_guard', 'ka_gochara_rr_2_coverage_guard',
                                'ka_gochara_rr_3_sealed_path_check', 'ka_gochara_rr_finalize',
                                'ka_gochara_rr_no_truncate'))
         OR (c.relname = 'ka_gochara_record_prerequisite'
               AND t.tgname IN ('ka_gochara_rpr_1_write_guard', 'ka_gochara_rpr_finalize',
                                'ka_gochara_rpr_no_truncate'))
         OR (c.relname = 'ka_gochara_contact'
               AND t.tgname = 'ka_gochara_contact_2_propagate_precision') )
    UNION ALL
    -- function collisions by EXACT ARGUMENT TYPES (F8) — this file's own helpers
    SELECT 'function_already_exists',
           'public.' || p.proname || '(' || array_to_string(e.argtypes, ',') || ')'
    FROM (VALUES
            ('ka_gochara_precision_ok',                ARRAY['jsonb']),
            ('ka_gochara_intervals_ok',                ARRAY['tstzrange[]']),
            ('ka_gochara_coverage_digest',             ARRAY['text','tstzrange','text[]']),
            ('ka_gochara_chart_write_guard',           ARRAY[]::text[]),
            ('ka_gochara_record_coverage_guard',       ARRAY[]::text[]),
            ('ka_gochara_record_finalize_check',       ARRAY[]::text[]),
            ('ka_gochara_contact_propagate_precision', ARRAY[]::text[])
         ) AS e(fname, argtypes)
    JOIN pg_proc p ON p.proname = e.fname
    JOIN pg_namespace n ON n.oid = p.pronamespace AND n.nspname = 'public'
    WHERE (SELECT COALESCE(array_agg(format_type(u.oid, NULL) ORDER BY u.ord), '{}')
           FROM unnest(p.proargtypes) WITH ORDINALITY AS u(oid, ord)) = e.argtypes
    UNION ALL
    -- (b1) parents exist
    SELECT 'parent_table_missing', p.t
    FROM (VALUES ('charts'), ('kala_gochara_coverage'), ('ka_gochara_contact'),
                 ('ka_gochara_physical_object'), ('ka_gochara_rule_path'),
                 ('ka_gochara_rule_path_seal'), ('ka_gochara_predicate'),
                 ('ka_gochara_convention_bridge'), ('ka_gochara_generation_seal')) AS p(t)
    WHERE to_regclass('public.' || p.t) IS NULL
    UNION ALL
    -- (b2) parent columns with expected types (the coverage columns the
    -- applicability guard reads are included)
    SELECT 'parent_column_missing_or_type',
           e.t || '.' || e.col || ' expected ' || e.typ
    FROM (VALUES ('charts',                     'id',                 'uuid'),
                 ('kala_gochara_coverage',      'chart_id',           'uuid'),
                 ('kala_gochara_coverage',      'generation',         'text'),
                 ('kala_gochara_coverage',      'partition_kind',     'text'),
                 ('kala_gochara_coverage',      'partition_key',      'text'),
                 ('kala_gochara_coverage',      'convention_id',      'text'),
                 ('kala_gochara_coverage',      'completed_horizon',  'tstzrange'),
                 ('kala_gochara_coverage',      'relations_searched', 'text[]'),
                 ('ka_gochara_contact',         'chart_id',           'uuid'),
                 ('ka_gochara_contact',         'generation',         'text'),
                 ('ka_gochara_contact',         'contact_id',         'uuid'),
                 ('ka_gochara_contact',         'body',               'text'),
                 ('ka_gochara_contact',         'relation_kind',      'text'),
                 ('ka_gochara_contact',         'physical_object_id', 'uuid'),
                 ('ka_gochara_contact',         'convention_id',      'text'),
                 ('ka_gochara_contact',         't_in',               'timestamp with time zone'),
                 ('ka_gochara_contact',         'solver_method',      'text'),
                 ('ka_gochara_contact',         'delta_lambda',       'real'),
                 ('ka_gochara_contact',         'delta_t',            'real'),
                 ('ka_gochara_physical_object', 'physical_object_id', 'uuid'),
                 ('ka_gochara_rule_path',       'path_id',            'text'),
                 ('ka_gochara_rule_path',       'rule_version',       'text'),
                 ('ka_gochara_predicate',       'predicate_id',       'text'),
                 ('ka_gochara_predicate',       'rule_version',       'text'),
                 ('ka_gochara_convention_bridge','kala_convention_id', 'text'),
                 ('ka_gochara_convention_bridge','sky_convention_id',  'text')) AS e(t, col, typ)
    LEFT JOIN pg_attribute a
      ON a.attrelid = to_regclass('public.' || e.t) AND a.attname = e.col AND NOT a.attisdropped
    WHERE a.attname IS NULL OR format_type(a.atttypid, a.atttypmod) IS DISTINCT FROM e.typ
    UNION ALL
    -- (b3) parent PK/UNIQUE definitions verified against pg_constraint
    SELECT 'parent_key_missing', e.t || ' must carry a PK/UNIQUE over ' || e.cols::text
    FROM (VALUES ('charts',                     ARRAY['id']),
                 ('kala_gochara_coverage',      ARRAY['chart_id','generation','partition_kind','partition_key']),
                 ('ka_gochara_contact',         ARRAY['chart_id','generation','contact_id','body','relation_kind','physical_object_id']),
                 ('ka_gochara_physical_object', ARRAY['physical_object_id']),
                 ('ka_gochara_rule_path',       ARRAY['path_id','rule_version']),
                 ('ka_gochara_rule_path_seal',  ARRAY['path_id','rule_version']),
                 ('ka_gochara_predicate',       ARRAY['predicate_id','rule_version']),
                 ('ka_gochara_convention_bridge', ARRAY['kala_convention_id'])) AS e(t, cols)
    WHERE to_regclass('public.' || e.t) IS NOT NULL
      AND NOT EXISTS (
        SELECT 1 FROM pg_constraint c
        WHERE c.conrelid = to_regclass('public.' || e.t) AND c.contype IN ('p','u')
          AND (SELECT array_agg(a.attname::text ORDER BY a.attname)
               FROM unnest(c.conkey) k JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = k)
              = (SELECT array_agg(x ORDER BY x) FROM unnest(e.cols) x))
    UNION ALL
    -- (b4) helper functions with exact signatures AND boolean return
    SELECT 'helper_function_missing', e.sig
    FROM (VALUES ('ka_gochara_frame_ok(text,text)'),
                 ('ka_gochara_string_array_ok(jsonb)'),
                 ('ka_gochara_finite_ok(double precision)'),
                 ('ka_gochara_finite_nonneg_ok(double precision)'),
                 ('ka_gochara_generation_governed(text)'),
                 ('ka_gochara_generation_is_sealed(uuid,text)')) AS e(sig)
    WHERE to_regprocedure('public.' || e.sig) IS NULL
       OR (SELECT format_type(p.prorettype, NULL) FROM pg_proc p
           WHERE p.oid = to_regprocedure('public.' || e.sig)) <> 'boolean'
    UNION ALL
    SELECT 'helper_function_missing', e.sig
    FROM (VALUES ('ka_gochara_refuse_truncate()'),
                 ('ka_gochara_lock_chart(uuid)'),
                 ('ka_gochara_lock_global()'),
                 ('ka_gochara_require_sealed_rule_path()')) AS e(sig)
    WHERE to_regprocedure('public.' || e.sig) IS NULL
    UNION ALL
    -- (c1) ordered execution gate
    SELECT 'prerequisite_migration_not_applied', p.prefix
    FROM (VALUES ('1153_'), ('1154_')) AS p(prefix)
    WHERE to_regclass('public._migrations_applied') IS NOT NULL
      AND NOT EXISTS (SELECT 1 FROM _migrations_applied m WHERE starts_with(m.filename, p.prefix))
    UNION ALL
    SELECT 'migration_already_applied', m.filename
    FROM _migrations_applied m
    WHERE to_regclass('public._migrations_applied') IS NOT NULL
      AND starts_with(m.filename, '1155_')
  )
  SELECT string_agg(f.failure || ' :: ' || f.detail, E'\n' ORDER BY f.failure, f.detail)
  INTO failures
  FROM f;
  IF failures IS NOT NULL THEN
    RAISE EXCEPTION 'preflight 1155 BLOCKED — migration 1155 must NOT be applied:% %', E'\n', failures;
  END IF;
  RAISE NOTICE 'preflight 1155: all checks passed';
END;
$$;
