-- Preflight for migration 1154 (ka_gochara rule-path registries). READ ONLY —
-- run against the target database before applying 1154.
--
-- Must return 0 rows total. Any row returned is a blocking failure: the
-- migration must NOT be applied until the row is understood (fix the
-- environment, not the detector — ADK-0026).
--
--   (a) none of the new table/constraint/trigger/function names already exist
--   (c) migration 1154 is not already recorded in the _migrations_applied
--       ledger (tracked runner: platform/scripts/migrate.ts)
-- (1154's tables are registry roots; they have no in-database parents.)

-- (a1) table-name collisions
SELECT 'table_already_exists' AS failure, n.nspname, c.relname
FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public'
  AND c.relname IN ('ka_gochara_rule_path',
                    'ka_gochara_predicate',
                    'ka_gochara_factor');

-- (a2) index-name collisions (index names are schema-global; constraint
-- names are only per-table in Postgres — tables themselves are covered by
-- (a1))
SELECT 'index_already_exists' AS failure, indexname
FROM pg_indexes
WHERE schemaname = 'public'
  AND indexname IN ('ka_gochara_rule_path_pkey',
                    'ka_gochara_predicate_pkey',
                    'ka_gochara_factor_pkey');

-- (a3) trigger-name collisions
SELECT 'trigger_already_exists' AS failure, tgname
FROM pg_trigger
WHERE NOT tgisinternal
  AND tgname IN ('ka_gochara_rule_path_immutable',
                 'ka_gochara_predicate_immutable',
                 'ka_gochara_factor_immutable');

-- (a4) function-name collisions
SELECT 'function_already_exists' AS failure, p.proname
FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE n.nspname = 'public'
  AND p.proname IN ('ka_gochara_composite_refs_ok',
                    'ka_gochara_rule_path_no_mutation',
                    'ka_gochara_predicate_no_mutation',
                    'ka_gochara_factor_no_mutation');

-- (c) migration number not already applied
SELECT 'migration_already_applied' AS failure, filename
FROM _migrations_applied
WHERE filename LIKE '1154_%';
