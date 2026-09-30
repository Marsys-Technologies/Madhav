-- Preflight for migration 1156 (ka_gochara_eval_window). READ ONLY — run
-- against the target database BEFORE applying 1156 and AFTER migrations
-- 1153, 1154 and 1155 are applied (ordered execution, amendment 8 — the
-- relationship-record parent is created by 1155; the round-1 preflight
-- omitted it because the required record FKs were missing from the
-- migration).
--
-- GATE SEMANTICS (amendment 8): FAILS CLOSED — any blocking finding RAISES;
-- success ends with NOTICE. Fix the environment, not the detector (ADK-0026).
--
--   (a) the new table/index names do not already exist (relation namespace)
--   (b) the referenced parents exist with the expected key definitions
--       (pg_constraint-verified): charts PK; ka_gochara_rule_path PK;
--       ka_gochara_relationship_record PK + kgrr_identity_uq (record_id,
--       chart_id, generation) — the membership scope target;
--       kala_gochara_coverage PK (chart_id, generation, partition_kind,
--       partition_key)
--   (c) prerequisite migrations 1153/1154/1155 are recorded in the ledger,
--       and 1156 is not (wildcard-safe: starts_with)
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
      AND c.relname IN ('ka_gochara_eval_window',
                        'ka_gochara_eval_window_record')
    UNION ALL
    SELECT 'relation_name_already_exists', n.nspname || '.' || c.relname
    FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public'
      AND c.relname IN ('ka_gochara_eval_window_pkey',
                        'ka_gochara_eval_window_record_pkey',
                        'kgew_identity_uq',
                        'idx_kgew_chart_gen', 'idx_kgew_path',
                        'idx_kgew_coverage', 'idx_kgewr_record')
    UNION ALL
    SELECT 'parent_table_missing', t.table_name
    FROM (VALUES ('charts'),
                 ('ka_gochara_rule_path'),
                 ('ka_gochara_relationship_record'),
                 ('kala_gochara_coverage')) AS t(table_name)
    WHERE NOT EXISTS (
      SELECT 1 FROM information_schema.tables
      WHERE table_schema = 'public' AND table_name = t.table_name
    )
    UNION ALL
    SELECT 'parent_column_missing_or_type',
           e.table_name || '.' || e.column_name || ' expected ' || e.expected_type
    FROM (VALUES ('charts',                        'id',           'uuid'),
                 ('ka_gochara_rule_path',          'path_id',      'text'),
                 ('ka_gochara_rule_path',          'rule_version', 'text'),
                 ('ka_gochara_relationship_record','record_id',    'uuid'),
                 ('ka_gochara_relationship_record','chart_id',     'uuid'),
                 ('ka_gochara_relationship_record','generation',   'text'),
                 ('kala_gochara_coverage',         'chart_id',     'uuid'),
                 ('kala_gochara_coverage',         'generation',   'text'),
                 ('kala_gochara_coverage',         'partition_kind','text'),
                 ('kala_gochara_coverage',         'partition_key', 'text'))
         AS e(table_name, column_name, expected_type)
    LEFT JOIN information_schema.columns c
      ON c.table_schema = 'public'
     AND c.table_name = e.table_name
     AND c.column_name = e.column_name
    WHERE c.data_type IS DISTINCT FROM e.expected_type
    UNION ALL
    SELECT 'parent_key_missing', e.what
    FROM (VALUES
      ('charts primary key',
       EXISTS (SELECT 1 FROM pg_constraint
               WHERE conrelid = to_regclass('public.charts') AND contype = 'p')),
      ('ka_gochara_rule_path primary key',
       EXISTS (SELECT 1 FROM pg_constraint
               WHERE conrelid = to_regclass('public.ka_gochara_rule_path') AND contype = 'p')),
      ('ka_gochara_relationship_record primary key',
       EXISTS (SELECT 1 FROM pg_constraint
               WHERE conrelid = to_regclass('public.ka_gochara_relationship_record') AND contype = 'p')),
      ('ka_gochara_relationship_record kgrr_identity_uq',
       EXISTS (SELECT 1 FROM pg_constraint
               WHERE conrelid = to_regclass('public.ka_gochara_relationship_record')
                 AND conname = 'kgrr_identity_uq' AND contype = 'u')),
      ('kala_gochara_coverage primary key',
       EXISTS (SELECT 1 FROM pg_constraint
               WHERE conrelid = to_regclass('public.kala_gochara_coverage') AND contype = 'p'))
    ) AS e(what, present)
    WHERE NOT e.present
    UNION ALL
    SELECT 'prerequisite_migration_not_applied', p.prefix
    FROM (VALUES ('1153_'), ('1154_'), ('1155_')) AS p(prefix)
    WHERE NOT EXISTS (
      SELECT 1 FROM _migrations_applied WHERE starts_with(filename, p.prefix)
    )
    UNION ALL
    SELECT 'migration_already_applied', filename
    FROM _migrations_applied
    WHERE starts_with(filename, '1156_')
  )
  SELECT string_agg(f.failure || ' :: ' || f.detail, E'\n' ORDER BY f.failure, f.detail)
  INTO failures
  FROM f;
  IF failures IS NOT NULL THEN
    RAISE EXCEPTION 'preflight 1156 BLOCKED — migration 1156 must NOT be applied:% %', E'\n', failures;
  END IF;
  RAISE NOTICE 'preflight 1156: all checks passed';
END;
$$;
