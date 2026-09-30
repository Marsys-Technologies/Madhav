-- Preflight for migration 1157 (ka_gochara_av_polarity_declaration). READ
-- ONLY — run against the target database before applying 1157.
--
-- Must return 0 rows total. Any row returned is a blocking failure: the
-- migration must NOT be applied until the row is understood (fix the
-- environment, not the detector — ADK-0026).
--
--   (a) the new table/trigger/function names do not already exist
--   (c) migration 1157 is not already recorded in the _migrations_applied
--       ledger (tracked runner: platform/scripts/migrate.ts)
-- (1157 has no in-database parents: the §8.1 'convention' column deliberately
--  carries no FK — the spec does not name which convention relation it
--  references; see the 1157 header.)

-- (a1) table-name collision
SELECT 'table_already_exists' AS failure, n.nspname, c.relname
FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public'
  AND c.relname = 'ka_gochara_av_polarity_declaration';

-- (a2) index-name collision
SELECT 'index_already_exists' AS failure, indexname
FROM pg_indexes
WHERE schemaname = 'public'
  AND indexname = 'ka_gochara_av_polarity_declaration_pkey';

-- (a3) trigger-name collision
SELECT 'trigger_already_exists' AS failure, tgname
FROM pg_trigger
WHERE NOT tgisinternal
  AND tgname = 'ka_gochara_av_polarity_immutable';

-- (a3) function-name collision
SELECT 'function_already_exists' AS failure, p.proname
FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE n.nspname = 'public'
  AND p.proname = 'ka_gochara_av_polarity_no_mutation';

-- (c) migration number not already applied
SELECT 'migration_already_applied' AS failure, filename
FROM _migrations_applied
WHERE filename LIKE '1157_%';
