-- Preflight for migration 1153 (ka_gochara sky-event substrate). READ ONLY — run against the target
-- database BEFORE applying 1153, after every prior migration (through 1152) is applied (ordered
-- execution: preflights run interleaved with their prerequisite migrations,
-- never as one undifferentiated batch).
--
-- THIS BLOCK IS BYTE-IDENTICAL TO THE GATE EMBEDDED AT THE TOP OF
-- platform/migrations/1153_gochara_sky_event_substrate.sql — the migration runs the same
-- detector itself, in the runner's transaction, before its DDL, so the
-- protected public-schema window (deploy.yml `gochara_contracts_schema_migration`,
-- the only route that applies 1153-1157) observes the gate without any
-- further wiring. The static test
-- tests/unit/migrations/gochara_a5_1_contract_static.test.ts asserts the two
-- blocks are identical.
--
-- GATE SEMANTICS (amendment 8 / F8 / F9; steward ruling 3): FAILS CLOSED —
-- any blocking finding RAISES (psql -v ON_ERROR_STOP=1 aborts; node-pg
-- rejects); success ends with NOTICE 'preflight 1153: all checks passed'. Fix
-- the environment, not the detector (ADK-0026). Only REAL preconditions are
-- checked:
--   (d) pinned schema 'public' exists; USAGE + CREATE on it; the REFERENCES /
--       SELECT privileges on the parents this migration binds to or reads;
--   (a) no untracked same-name collision: relation namespace (tables +
--       indexes share pg_class), table-scoped triggers, functions by EXACT
--       ARGUMENT TYPES (proargtypes → format_type; never the name-retaining
--       pg_get_function_identity_arguments text);
--   (b) in-database parents exist with the expected column types and
--       PK/UNIQUE definitions (pg_constraint-verified): charts, kala_gochara_publication (read by the seal function: manifest_id / (chart_id, generation) keys, status), kala_gochara_convention;
--   (c) prerequisite migrations are recorded in _migrations_applied and 1153
--       is not (wildcard-safe starts_with, not LIKE).
-- migrate.ts tracks applied files by hash: a tracked file is never re-run;
-- an untracked re-run is a collision and is BLOCKED here. There is no replay
-- mode.

DO $$
DECLARE
  failures text;
BEGIN
  WITH f(failure, detail) AS (
    -- (d) pinned schema + effective privileges
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
    FROM (VALUES ('public.charts'), ('public.kala_gochara_convention')) AS p(t)
    WHERE to_regclass(p.t) IS NOT NULL AND NOT has_table_privilege(p.t, 'REFERENCES')
    UNION ALL
    SELECT 'no_select_privilege', 'public.kala_gochara_publication'
    WHERE to_regclass('public.kala_gochara_publication') IS NOT NULL
      AND NOT has_table_privilege('public.kala_gochara_publication', 'SELECT')
    UNION ALL
    -- (a1) relation-namespace collisions (tables, indexes, sequences share pg_class)
    SELECT 'relation_already_exists', 'public.' || c.relname
    FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public'
      AND c.relname IN ('ka_gochara_sky_convention', 'ka_gochara_sky_convention_pkey',
                        'ka_gochara_physical_object', 'ka_gochara_physical_object_pkey',
                        'ka_gochara_physical_object_natural_uq', 'kgpo_identity_uq',
                        'ka_gochara_sky_event', 'ka_gochara_sky_event_pkey',
                        'ka_gochara_sky_event_ordinal_uq', 'kgse_supersedes_uq',
                        'ka_gochara_contact_identity', 'ka_gochara_contact_identity_pkey',
                        'ka_gochara_contact_identity_ordinal_uq', 'kgci_supersedes_uq',
                        'kgci_tuple_uq',
                        'ka_gochara_generation_seal', 'ka_gochara_generation_seal_pkey',
                        'ka_gochara_convention_bridge', 'ka_gochara_convention_bridge_pkey',
                        'ka_gochara_contact', 'ka_gochara_contact_pkey', 'kgc_reference_uq',
                        'idx_kgse_convention_time', 'idx_kgc_chart_gen', 'idx_kgc_object',
                        'idx_kgc_identity')
    UNION ALL
    -- (a2) trigger collisions, scoped to the intended table in public
    SELECT 'trigger_already_exists', 'public.' || c.relname || '.' || t.tgname
    FROM pg_trigger t
    JOIN pg_class c ON c.oid = t.tgrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public' AND NOT t.tgisinternal
      AND ( (c.relname = 'ka_gochara_sky_convention'
               AND t.tgname IN ('ka_gochara_sky_convention_immutable',
                                'ka_gochara_sky_convention_no_truncate'))
         OR (c.relname = 'ka_gochara_physical_object'
               AND t.tgname IN ('ka_gochara_physical_object_immutable',
                                'ka_gochara_physical_object_no_truncate'))
         OR (c.relname = 'ka_gochara_sky_event'
               AND t.tgname IN ('ka_gochara_sky_event_supersede_check',
                                'ka_gochara_sky_event_mutation_guard',
                                'ka_gochara_sky_event_no_truncate'))
         OR (c.relname = 'ka_gochara_contact_identity'
               AND t.tgname IN ('ka_gochara_contact_identity_supersede_check',
                                'ka_gochara_contact_identity_immutable',
                                'ka_gochara_contact_identity_no_truncate'))
         OR (c.relname = 'ka_gochara_generation_seal'
               AND t.tgname IN ('ka_gochara_generation_seal_write_guard',
                                'ka_gochara_generation_seal_no_truncate'))
         OR (c.relname = 'ka_gochara_convention_bridge'
               AND t.tgname IN ('ka_gochara_convention_bridge_immutable',
                                'ka_gochara_convention_bridge_no_truncate'))
         OR (c.relname = 'ka_gochara_contact'
               AND t.tgname IN ('ka_gochara_contact_0_statement_lock',
                                'ka_gochara_contact_1_write_guard',
                                'ka_gochara_contact_no_truncate')) )
    UNION ALL
    -- (a3) function collisions by EXACT ARGUMENT TYPES (F8)
    SELECT 'function_already_exists',
           'public.' || p.proname || '(' || array_to_string(e.argtypes, ',') || ')'
    FROM (VALUES
            ('ka_gochara_refuse_truncate',                  ARRAY[]::text[]),
            ('ka_gochara_text_array_ok',                    ARRAY['text[]','integer']),
            ('ka_gochara_finite_ok',                        ARRAY['double precision']),
            ('ka_gochara_finite_nonneg_ok',                 ARRAY['double precision']),
            ('ka_gochara_generation_governed',              ARRAY['text']),
            ('ka_gochara_lock_chart',                       ARRAY['uuid']),
            ('ka_gochara_lock_global',                      ARRAY[]::text[]),
            ('ka_gochara_lock_global_shared',               ARRAY[]::text[]),
            ('ka_gochara_insert_only',                      ARRAY[]::text[]),
            ('ka_gochara_global_write_guard',               ARRAY[]::text[]),
            ('ka_gochara_chart_statement_lock',             ARRAY[]::text[]),
            ('ka_gochara_generation_is_sealed',             ARRAY['uuid','text']),
            ('ka_gochara_seal_generation',                  ARRAY['uuid','text']),
            ('ka_gochara_generation_seal_guard',            ARRAY[]::text[]),
            ('ka_gochara_sky_event_supersede_guard',        ARRAY[]::text[]),
            ('ka_gochara_sky_event_guard',                  ARRAY[]::text[]),
            ('ka_gochara_contact_identity_supersede_guard', ARRAY[]::text[]),
            ('ka_gochara_contact_guard',                    ARRAY[]::text[])
         ) AS e(fname, argtypes)
    JOIN pg_proc p ON p.proname = e.fname
    JOIN pg_namespace n ON n.oid = p.pronamespace AND n.nspname = 'public'
    WHERE (SELECT COALESCE(array_agg(format_type(u.oid, NULL) ORDER BY u.ord), '{}')
           FROM unnest(p.proargtypes) WITH ORDINALITY AS u(oid, ord)) = e.argtypes
    UNION ALL
    -- (b1) in-database parents exist (publication is READ by the seal path only)
    SELECT 'parent_table_missing', p.t
    FROM (VALUES ('charts'), ('kala_gochara_publication'), ('kala_gochara_convention')) AS p(t)
    WHERE to_regclass('public.' || p.t) IS NULL
    UNION ALL
    -- (b2) parent columns exist with the expected types (expected side named)
    SELECT 'parent_column_missing_or_type',
           e.t || '.' || e.col || ' expected ' || e.typ
    FROM (VALUES ('charts',                   'id',           'uuid'),
                 ('kala_gochara_publication', 'manifest_id',  'uuid'),
                 ('kala_gochara_publication', 'chart_id',     'uuid'),
                 ('kala_gochara_publication', 'generation',   'text'),
                 ('kala_gochara_publication', 'status',       'text'),
                 ('kala_gochara_convention',  'convention_id','text')) AS e(t, col, typ)
    LEFT JOIN pg_attribute a
      ON a.attrelid = to_regclass('public.' || e.t) AND a.attname = e.col AND NOT a.attisdropped
    WHERE a.attname IS NULL OR format_type(a.atttypid, a.atttypmod) IS DISTINCT FROM e.typ
    UNION ALL
    -- (b3) parent PK/UNIQUE definitions verified against pg_constraint
    SELECT 'parent_key_missing', e.t || ' must carry a PK/UNIQUE over ' || e.cols::text
    FROM (VALUES ('charts',                   ARRAY['id']),
                 ('kala_gochara_publication', ARRAY['manifest_id']),
                 ('kala_gochara_publication', ARRAY['chart_id','generation']),
                 ('kala_gochara_convention',  ARRAY['convention_id'])) AS e(t, cols)
    WHERE to_regclass('public.' || e.t) IS NOT NULL
      AND NOT EXISTS (
        SELECT 1 FROM pg_constraint c
        WHERE c.conrelid = to_regclass('public.' || e.t) AND c.contype IN ('p','u')
          AND (SELECT array_agg(a.attname::text ORDER BY a.attname)
               FROM unnest(c.conkey) k JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = k)
              = (SELECT array_agg(x ORDER BY x) FROM unnest(e.cols) x))
    UNION ALL
    -- (c) ledger lookup, wildcard-safe (starts_with, not LIKE)
    SELECT 'migration_already_applied', m.filename
    FROM _migrations_applied m
    WHERE to_regclass('public._migrations_applied') IS NOT NULL
      AND starts_with(m.filename, '1153_')
  )
  SELECT string_agg(f.failure || ' :: ' || f.detail, E'\n' ORDER BY f.failure, f.detail)
  INTO failures
  FROM f;
  IF failures IS NOT NULL THEN
    RAISE EXCEPTION 'preflight 1153 BLOCKED — migration 1153 must NOT be applied:% %', E'\n', failures;
  END IF;
  RAISE NOTICE 'preflight 1153: all checks passed';
END;
$$;
