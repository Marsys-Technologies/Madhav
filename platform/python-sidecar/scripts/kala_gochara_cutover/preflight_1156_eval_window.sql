-- Preflight for migration 1156 (ka_gochara_eval_window). READ ONLY — run
-- against the target database before applying 1156.
--
-- Must return 0 rows total. Any row returned is a blocking failure: the
-- migration must NOT be applied until the row is understood (fix the
-- environment, not the detector — ADK-0026).
--
--   (a) the new table/index names do not already exist
--   (b) the referenced parents exist with the expected PK columns/types:
--       charts(id uuid) — 001_baseline.sql §3;
--       ka_gochara_rule_path(path_id text, rule_version text) — 1154;
--       kala_gochara_publication(manifest_id uuid) — 1081 (coverage_ref
--       target; kala_gochara_coverage's PK is composite — see 1155 header)
--   (c) migration 1156 is not already recorded in the _migrations_applied
--       ledger (tracked runner: platform/scripts/migrate.ts)

-- (a1) table-name collision
SELECT 'table_already_exists' AS failure, n.nspname, c.relname
FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public'
  AND c.relname = 'ka_gochara_eval_window';

-- (a2) index-name collisions
SELECT 'index_already_exists' AS failure, indexname
FROM pg_indexes
WHERE schemaname = 'public'
  AND indexname IN ('ka_gochara_eval_window_pkey',
                    'idx_kgew_chart_gen', 'idx_kgew_path');

-- (b1) parent tables exist
SELECT 'parent_table_missing' AS failure, t.table_name
FROM (VALUES ('charts'),
             ('ka_gochara_rule_path'),
             ('kala_gochara_publication')) AS t(table_name)
WHERE NOT EXISTS (
  SELECT 1 FROM information_schema.tables
  WHERE table_schema = 'public' AND table_name = t.table_name
);

-- (b2) parent PK columns exist with the expected types
SELECT 'parent_column_missing_or_type' AS failure, c.table_name, c.column_name,
       c.data_type
FROM (VALUES ('charts',                   'id',           'uuid'),
             ('ka_gochara_rule_path',     'path_id',      'text'),
             ('ka_gochara_rule_path',     'rule_version', 'text'),
             ('kala_gochara_publication', 'manifest_id',  'uuid'))
     AS e(table_name, column_name, expected_type)
LEFT JOIN information_schema.columns c
  ON c.table_schema = 'public'
 AND c.table_name = e.table_name
 AND c.column_name = e.column_name
WHERE c.data_type IS DISTINCT FROM e.expected_type;

-- (c) migration number not already applied
SELECT 'migration_already_applied' AS failure, filename
FROM _migrations_applied
WHERE filename LIKE '1156_%';
