-- Preflight for migration 1153 (ka_gochara sky-event substrate). READ ONLY —
-- run against the target database before applying 1153.
--
-- Must return 0 rows total. Any row returned is a blocking failure: the
-- migration must NOT be applied until the row is understood (fix the
-- environment, not the detector — ADK-0026).
--
--   (a) none of the new table/constraint/trigger/function names already exist
--   (c) migration 1153 is not already recorded in the _migrations_applied
--       ledger (tracked runner: platform/scripts/migrate.ts)
-- (1153 creates the substrate root tables; its only in-database parent is
--  none — the parent-existence check for ka_gochara_physical_object /
--  ka_gochara_sky_event belongs to the 1155 preflight.)

-- (a1) table-name collisions
SELECT 'table_already_exists' AS failure, n.nspname, c.relname
FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public'
  AND c.relname IN ('ka_gochara_sky_convention',
                    'ka_gochara_physical_object',
                    'ka_gochara_sky_event');

-- (a2) index-name collisions (index names are schema-global; constraint
-- names are only per-table in Postgres, so a name match on an unrelated
-- table would not block the migration — tables themselves are covered by
-- (a1))
SELECT 'index_already_exists' AS failure, indexname
FROM pg_indexes
WHERE schemaname = 'public'
  AND indexname IN ('ka_gochara_sky_convention_pkey',
                    'ka_gochara_physical_object_pkey',
                    'ka_gochara_physical_object_natural_uq',
                    'ka_gochara_sky_event_pkey',
                    'ka_gochara_sky_event_ordinal_uq',
                    'idx_kgse_object',
                    'idx_kgse_convention_time');

-- (a3) trigger-name collisions
SELECT 'trigger_already_exists' AS failure, tgname
FROM pg_trigger
WHERE NOT tgisinternal
  AND tgname IN ('ka_gochara_sky_convention_immutable',
                 'ka_gochara_physical_object_immutable',
                 'ka_gochara_sky_event_mutation_guard');

-- (a4) function-name collisions
SELECT 'function_already_exists' AS failure, p.proname
FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE n.nspname = 'public'
  AND p.proname IN ('ka_gochara_sky_convention_no_mutation',
                    'ka_gochara_physical_object_no_mutation',
                    'ka_gochara_sky_event_guard');

-- (c) migration number not already applied
SELECT 'migration_already_applied' AS failure, filename
FROM _migrations_applied
WHERE filename LIKE '1153_%';
