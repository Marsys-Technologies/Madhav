-- Preflight for migration 1153 (ka_gochara sky-event substrate). READ ONLY —
-- run against the target database BEFORE applying 1153, after every prior
-- migration (through 1152) is applied.
--
-- GATE SEMANTICS (amendment 8): this script FAILS CLOSED. On any blocking
-- finding it RAISES (psql -v ON_ERROR_STOP=1 aborts; node-pg rejects), so
-- the caller cannot mistake a nonempty result for success. On success it
-- ends with NOTICE 'preflight 1153: all checks passed'. Fix the
-- environment, not the detector (ADK-0026).
--
--   (a) none of the new tables exists; no relation-namespace (index) name,
--       table-scoped trigger name, or exact-signature function collides
--   (b) the in-database parents exist with the expected keys:
--       charts(id uuid) — 001_baseline.sql §3;
--       kala_gochara_publication(chart_id, generation, status) — 1081 (the
--       contact lifecycle guard reads it)
--   (c) migration 1153 is not already recorded in the _migrations_applied
--       ledger (wildcard-safe lookup: starts_with, not LIKE '1153_%' where
--       '_' is a wildcard)
--   (d) the executing role holds CREATE on schema public (pinned schema)

DO $$
DECLARE failures text;
BEGIN
  WITH f(failure, detail) AS (
    -- (d) schema privilege
    SELECT 'no_create_privilege_on_public', current_user
    WHERE NOT has_schema_privilege(current_user, 'public', 'CREATE')
    UNION ALL
    -- (a1) table-name collisions
    SELECT 'table_already_exists', n.nspname || '.' || c.relname
    FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public'
      AND c.relname IN ('ka_gochara_sky_convention',
                        'ka_gochara_physical_object',
                        'ka_gochara_sky_event',
                        'ka_gochara_contact')
    UNION ALL
    -- (a2) relation-namespace collisions (index names share a namespace with
    -- tables/sequences/views — check pg_class, not pg_indexes)
    SELECT 'relation_name_already_exists', n.nspname || '.' || c.relname
    FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public'
      AND c.relname IN ('ka_gochara_sky_convention_pkey',
                        'ka_gochara_physical_object_pkey',
                        'ka_gochara_physical_object_natural_uq',
                        'kgpo_identity_uq',
                        'ka_gochara_sky_event_pkey',
                        'ka_gochara_sky_event_ordinal_uq',
                        'ka_gochara_contact_pkey',
                        'ka_gochara_contact_ordinal_uq',
                        'kgc_identity_uq',
                        'idx_kgse_convention_time',
                        'idx_kgc_chart_gen',
                        'idx_kgc_object')
    UNION ALL
    -- (a3) trigger collisions, SCOPED to the intended table in public
    SELECT 'trigger_already_exists', n.nspname || '.' || c.relname || '.' || t.tgname
    FROM pg_trigger t
    JOIN pg_class c ON c.oid = t.tgrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public' AND NOT t.tgisinternal
      AND ( (c.relname = 'ka_gochara_sky_convention'
               AND t.tgname = 'ka_gochara_sky_convention_immutable')
         OR (c.relname = 'ka_gochara_physical_object'
               AND t.tgname = 'ka_gochara_physical_object_immutable')
         OR (c.relname = 'ka_gochara_sky_event'
               AND t.tgname IN ('ka_gochara_sky_event_supersede_check',
                                'ka_gochara_sky_event_mutation_guard'))
         OR (c.relname = 'ka_gochara_contact'
               AND t.tgname IN ('ka_gochara_contact_supersede_check',
                                'ka_gochara_contact_lifecycle_guard')) )
    UNION ALL
    -- (a4) function collisions with EXACT identity signatures (trigger
    -- functions take no arguments; an exact-signature same-name function
    -- would be silently replaced by CREATE OR REPLACE)
    SELECT 'function_already_exists',
           n.nspname || '.' || p.proname || '(' ||
           pg_get_function_identity_arguments(p.oid) || ')'
    FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = 'public'
      AND p.proname IN ('ka_gochara_sky_convention_no_mutation',
                        'ka_gochara_physical_object_no_mutation',
                        'ka_gochara_sky_event_supersede_guard',
                        'ka_gochara_sky_event_guard',
                        'ka_gochara_contact_supersede_guard',
                        'ka_gochara_contact_guard')
      AND pg_get_function_identity_arguments(p.oid) = ''
    UNION ALL
    -- (b1) parent tables exist
    SELECT 'parent_table_missing', t.table_name
    FROM (VALUES ('charts'), ('kala_gochara_publication')) AS t(table_name)
    WHERE NOT EXISTS (
      SELECT 1 FROM information_schema.tables
      WHERE table_schema = 'public' AND table_name = t.table_name
    )
    UNION ALL
    -- (b2) parent key columns exist with the expected types (expected side
    -- named in the output — never the NULL side of the join)
    SELECT 'parent_column_missing_or_type',
           e.table_name || '.' || e.column_name || ' expected ' || e.expected_type
    FROM (VALUES ('charts',                 'id',         'uuid'),
                 ('kala_gochara_publication','chart_id',  'uuid'),
                 ('kala_gochara_publication','generation','text'),
                 ('kala_gochara_publication','status',    'text'))
         AS e(table_name, column_name, expected_type)
    LEFT JOIN information_schema.columns c
      ON c.table_schema = 'public'
     AND c.table_name = e.table_name
     AND c.column_name = e.column_name
    WHERE c.data_type IS DISTINCT FROM e.expected_type
    UNION ALL
    -- (b3) parent PK/UNIQUE definitions verified, not just columns
    SELECT 'parent_key_missing', e.table_name || ' must have a key over ' || e.cols
    FROM (VALUES ('charts', '(id)'),
                 ('kala_gochara_publication', '(chart_id, generation)')) AS e(table_name, cols)
    WHERE NOT (
      (e.table_name = 'charts' AND EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = to_regclass('public.charts') AND contype = 'p'))
      OR
      (e.table_name = 'kala_gochara_publication' AND EXISTS (
        SELECT 1 FROM pg_constraint c
        WHERE c.conrelid = to_regclass('public.kala_gochara_publication')
          AND c.contype IN ('p','u')
          AND (SELECT array_agg(a.attname ORDER BY a.attname)
               FROM unnest(c.conkey) k
               JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = k)
              = ARRAY['chart_id','generation']::name[]))
    )
    UNION ALL
    -- (c) ledger lookup, wildcard-safe
    SELECT 'migration_already_applied', filename
    FROM _migrations_applied
    WHERE starts_with(filename, '1153_')
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
