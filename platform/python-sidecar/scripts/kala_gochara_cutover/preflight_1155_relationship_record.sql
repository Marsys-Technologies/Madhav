-- Preflight for migration 1155 (ka_gochara_relationship_record). READ ONLY —
-- run against the target database before applying 1155.
--
-- Must return 0 rows total. Any row returned is a blocking failure: the
-- migration must NOT be applied until the row is understood (fix the
-- environment, not the detector — ADK-0026).
--
--   (a) the new table/constraint/index names do not already exist
--   (b) the referenced parents exist with the expected PK columns/types:
--       charts(id uuid) — 001_baseline.sql §3;
--       ka_gochara_sky_event(event_id uuid) — 1153;
--       ka_gochara_physical_object(physical_object_id uuid) — 1153;
--       ka_gochara_rule_path(path_id text, rule_version text) — 1154;
--       ka_gochara_composite_refs_ok(jsonb, text) — 1154;
--       kala_gochara_publication(manifest_id uuid) — 1081
--       (kala_gochara_coverage's PK is composite — verified from 1081 — so
--       coverage_ref references the uuid-keyed publication manifest; see the
--       1155 header)
--   (c) migration 1155 is not already recorded in the _migrations_applied
--       ledger (tracked runner: platform/scripts/migrate.ts)

-- (a1) table-name collision
SELECT 'table_already_exists' AS failure, n.nspname, c.relname
FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public'
  AND c.relname = 'ka_gochara_relationship_record';

-- (a2) index-name collisions
SELECT 'index_already_exists' AS failure, indexname
FROM pg_indexes
WHERE schemaname = 'public'
  AND indexname IN ('ka_gochara_relationship_record_pkey',
                    'idx_kgrr_chart_gen', 'idx_kgrr_contact',
                    'idx_kgrr_object', 'idx_kgrr_path');

-- (b1) parent tables exist
SELECT 'parent_table_missing' AS failure, t.table_name
FROM (VALUES ('charts'),
             ('ka_gochara_sky_event'),
             ('ka_gochara_physical_object'),
             ('ka_gochara_rule_path'),
             ('kala_gochara_publication')) AS t(table_name)
WHERE NOT EXISTS (
  SELECT 1 FROM information_schema.tables
  WHERE table_schema = 'public' AND table_name = t.table_name
);

-- (b2) parent PK columns exist with the expected types
SELECT 'parent_column_missing_or_type' AS failure, c.table_name, c.column_name,
       c.data_type
FROM (VALUES ('charts',                    'id',                 'uuid'),
             ('ka_gochara_sky_event',      'event_id',           'uuid'),
             ('ka_gochara_physical_object','physical_object_id', 'uuid'),
             ('ka_gochara_rule_path',      'path_id',            'text'),
             ('ka_gochara_rule_path',      'rule_version',       'text'),
             ('kala_gochara_publication',  'manifest_id',        'uuid'))
     AS e(table_name, column_name, expected_type)
LEFT JOIN information_schema.columns c
  ON c.table_schema = 'public'
 AND c.table_name = e.table_name
 AND c.column_name = e.column_name
WHERE c.data_type IS DISTINCT FROM e.expected_type;

-- (b3) the 1154 CHECK helper exists
SELECT 'helper_function_missing' AS failure, 'ka_gochara_composite_refs_ok(jsonb,text)' AS missing
WHERE NOT EXISTS (
  SELECT 1 FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
  WHERE n.nspname = 'public' AND p.proname = 'ka_gochara_composite_refs_ok'
);

-- (c) migration number not already applied
SELECT 'migration_already_applied' AS failure, filename
FROM _migrations_applied
WHERE filename LIKE '1155_%';
