-- Preflight for migration 1155 (ka_gochara_relationship_record). READ ONLY —
-- run against the target database BEFORE applying 1155 and AFTER migrations
-- 1153 and 1154 are applied (ordered execution, amendment 8 — the checks
-- below require those newly created parents to exist; never run the
-- preflights as one undifferentiated batch against the original database).
--
-- GATE SEMANTICS (amendment 8): FAILS CLOSED — any blocking finding RAISES;
-- success ends with NOTICE. Fix the environment, not the detector (ADK-0026).
--
--   (a) the new table/index names do not already exist (relation namespace,
--       pg_class — not pg_indexes)
--   (b) the referenced parents exist with the expected PK/UNIQUE definitions
--       (verified against pg_constraint, not just column presence):
--       charts(id uuid) PK — 001_baseline.sql §3;
--       kala_gochara_coverage PK (chart_id, generation, partition_kind,
--         partition_key) — 1081;
--       ka_gochara_contact + kgc_identity_uq (contact_id, body,
--         physical_object_id) — 1153;
--       ka_gochara_physical_object PK — 1153;
--       ka_gochara_rule_path PK (path_id, rule_version) — 1154;
--       ka_gochara_predicate PK (predicate_id, rule_version) — 1154;
--       helpers ka_gochara_frame_ok(text,text),
--       ka_gochara_string_array_ok(jsonb) — 1154 (exact signatures)
--   (c) prerequisite migrations 1153/1154 are recorded in the ledger, and
--       1155 is not (wildcard-safe: starts_with)
--   (d) the executing role holds CREATE on schema public

DO $$
DECLARE failures text;
BEGIN
  WITH f(failure, detail) AS (
    SELECT 'no_create_privilege_on_public', current_user
    WHERE NOT has_schema_privilege(current_user, 'public', 'CREATE')
    UNION ALL
    SELECT 'table_already_exists', n.nspname || '.' || c.relname
    FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public'
      AND c.relname IN ('ka_gochara_relationship_record',
                        'ka_gochara_record_prerequisite')
    UNION ALL
    SELECT 'relation_name_already_exists', n.nspname || '.' || c.relname
    FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public'
      AND c.relname IN ('ka_gochara_relationship_record_pkey',
                        'ka_gochara_record_prerequisite_pkey',
                        'kgrr_identity_uq', 'kgrpr_no_dup_uq',
                        'idx_kgrr_chart_gen', 'idx_kgrr_contact',
                        'idx_kgrr_object', 'idx_kgrr_path', 'idx_kgrr_coverage')
    UNION ALL
    -- (b1) parent tables exist
    SELECT 'parent_table_missing', t.table_name
    FROM (VALUES ('charts'),
                 ('kala_gochara_coverage'),
                 ('ka_gochara_contact'),
                 ('ka_gochara_physical_object'),
                 ('ka_gochara_rule_path'),
                 ('ka_gochara_predicate')) AS t(table_name)
    WHERE NOT EXISTS (
      SELECT 1 FROM information_schema.tables
      WHERE table_schema = 'public' AND table_name = t.table_name
    )
    UNION ALL
    -- (b2) parent key columns exist with expected types (expected side named)
    SELECT 'parent_column_missing_or_type',
           e.table_name || '.' || e.column_name || ' expected ' || e.expected_type
    FROM (VALUES ('charts',                    'id',                 'uuid'),
                 ('kala_gochara_coverage',     'chart_id',           'uuid'),
                 ('kala_gochara_coverage',     'generation',         'text'),
                 ('kala_gochara_coverage',     'partition_kind',     'text'),
                 ('kala_gochara_coverage',     'partition_key',      'text'),
                 ('ka_gochara_contact',        'contact_id',         'uuid'),
                 ('ka_gochara_contact',        'body',               'text'),
                 ('ka_gochara_contact',        'physical_object_id', 'uuid'),
                 ('ka_gochara_physical_object','physical_object_id', 'uuid'),
                 ('ka_gochara_rule_path',      'path_id',            'text'),
                 ('ka_gochara_rule_path',      'rule_version',       'text'),
                 ('ka_gochara_predicate',      'predicate_id',       'text'),
                 ('ka_gochara_predicate',      'rule_version',       'text'))
         AS e(table_name, column_name, expected_type)
    LEFT JOIN information_schema.columns c
      ON c.table_schema = 'public'
     AND c.table_name = e.table_name
     AND c.column_name = e.column_name
    WHERE c.data_type IS DISTINCT FROM e.expected_type
    UNION ALL
    -- (b3) parent PK/UNIQUE definitions actually present
    SELECT 'parent_key_missing', e.what
    FROM (VALUES
      ('charts primary key',
       EXISTS (SELECT 1 FROM pg_constraint
               WHERE conrelid = to_regclass('public.charts') AND contype = 'p')),
      ('kala_gochara_coverage primary key',
       EXISTS (SELECT 1 FROM pg_constraint
               WHERE conrelid = to_regclass('public.kala_gochara_coverage') AND contype = 'p')),
      ('ka_gochara_contact kgc_identity_uq',
       EXISTS (SELECT 1 FROM pg_constraint
               WHERE conrelid = to_regclass('public.ka_gochara_contact')
                 AND conname = 'kgc_identity_uq' AND contype = 'u')),
      ('ka_gochara_physical_object primary key',
       EXISTS (SELECT 1 FROM pg_constraint
               WHERE conrelid = to_regclass('public.ka_gochara_physical_object') AND contype = 'p')),
      ('ka_gochara_rule_path primary key',
       EXISTS (SELECT 1 FROM pg_constraint
               WHERE conrelid = to_regclass('public.ka_gochara_rule_path') AND contype = 'p')),
      ('ka_gochara_predicate primary key',
       EXISTS (SELECT 1 FROM pg_constraint
               WHERE conrelid = to_regclass('public.ka_gochara_predicate') AND contype = 'p'))
    ) AS e(what, present)
    WHERE NOT e.present
    UNION ALL
    -- (b4) helper functions with exact signatures
    SELECT 'helper_function_missing', e.sig
    FROM (VALUES
      ('ka_gochara_frame_ok(text,text)',
       'ka_gochara_frame_ok', 'text, text'),
      ('ka_gochara_string_array_ok(jsonb)',
       'ka_gochara_string_array_ok', 'jsonb')
    ) AS e(sig, proname, args)
    WHERE NOT EXISTS (
      SELECT 1 FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
      WHERE n.nspname = 'public' AND p.proname = e.proname
        AND pg_get_function_identity_arguments(p.oid) = e.args
    )
    UNION ALL
    -- (c1) prerequisites applied (ordered execution gate)
    SELECT 'prerequisite_migration_not_applied', p.prefix
    FROM (VALUES ('1153_'), ('1154_')) AS p(prefix)
    WHERE NOT EXISTS (
      SELECT 1 FROM _migrations_applied WHERE starts_with(filename, p.prefix)
    )
    UNION ALL
    -- (c2) this migration not already applied
    SELECT 'migration_already_applied', filename
    FROM _migrations_applied
    WHERE starts_with(filename, '1155_')
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
