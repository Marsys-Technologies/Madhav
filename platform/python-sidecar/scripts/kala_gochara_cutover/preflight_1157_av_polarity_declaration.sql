-- Preflight for migration 1157 (ka_gochara_av_polarity_declaration). READ
-- ONLY — run against the target database BEFORE applying 1157.
--
-- GATE SEMANTICS (amendment 8): FAILS CLOSED — any blocking finding RAISES;
-- success ends with NOTICE. Fix the environment, not the detector (ADK-0026).
--
--   (a) the new table does not exist; no relation-namespace name,
--       table-scoped trigger name, or exact-signature function collides
--   (c) migration 1157 is not already recorded in the _migrations_applied
--       ledger (wildcard-safe: starts_with)
--   (d) the executing role holds CREATE on schema public
-- (1157 has no in-database parents: the §8.1 'convention' column deliberately
--  carries no FK — see the 1157 header.)

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
      AND c.relname = 'ka_gochara_av_polarity_declaration'
    UNION ALL
    SELECT 'relation_name_already_exists', n.nspname || '.' || c.relname
    FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public'
      AND c.relname = 'ka_gochara_av_polarity_declaration_pkey'
    UNION ALL
    SELECT 'trigger_already_exists', n.nspname || '.' || c.relname || '.' || t.tgname
    FROM pg_trigger t
    JOIN pg_class c ON c.oid = t.tgrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public' AND NOT t.tgisinternal
      AND c.relname = 'ka_gochara_av_polarity_declaration'
      AND t.tgname = 'ka_gochara_av_polarity_immutable'
    UNION ALL
    SELECT 'function_already_exists',
           n.nspname || '.' || p.proname || '(' ||
           pg_get_function_identity_arguments(p.oid) || ')'
    FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = 'public'
      AND p.proname = 'ka_gochara_av_polarity_no_mutation'
      AND pg_get_function_identity_arguments(p.oid) = ''
    UNION ALL
    SELECT 'migration_already_applied', filename
    FROM _migrations_applied
    WHERE starts_with(filename, '1157_')
  )
  SELECT string_agg(f.failure || ' :: ' || f.detail, E'\n' ORDER BY f.failure, f.detail)
  INTO failures
  FROM f;
  IF failures IS NOT NULL THEN
    RAISE EXCEPTION 'preflight 1157 BLOCKED — migration 1157 must NOT be applied:% %', E'\n', failures;
  END IF;
  RAISE NOTICE 'preflight 1157: all checks passed';
END;
$$;
