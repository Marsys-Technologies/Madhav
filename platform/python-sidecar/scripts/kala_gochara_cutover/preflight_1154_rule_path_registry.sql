-- Preflight for migration 1154 (ka_gochara rule-path registries). READ ONLY —
-- run against the target database BEFORE applying 1154, after migration 1153
-- is applied (ordered execution, amendment 8: preflights run interleaved with
-- their prerequisite migrations, never as one undifferentiated batch).
--
-- GATE SEMANTICS (amendment 8): FAILS CLOSED — any blocking finding RAISES;
-- success ends with NOTICE. Fix the environment, not the detector (ADK-0026).
--
--   (a) none of the new tables exists; no relation-namespace (index) name,
--       table-scoped trigger name, or exact-signature function collides
--       (function checks pin the full identity signature — the typed helpers
--       included)
--   (c) migration 1154 is not already recorded in the _migrations_applied
--       ledger (wildcard-safe: starts_with)
--   (d) the executing role holds CREATE on schema public
-- (1154's tables are registry roots; they have no in-database parents.)

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
      AND c.relname IN ('ka_gochara_predicate',
                        'ka_gochara_factor',
                        'ka_gochara_rule_path',
                        'ka_gochara_rule_path_prerequisite',
                        'ka_gochara_rule_path_soft_factor')
    UNION ALL
    SELECT 'relation_name_already_exists', n.nspname || '.' || c.relname
    FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public'
      AND c.relname IN ('ka_gochara_predicate_pkey',
                        'ka_gochara_factor_pkey',
                        'ka_gochara_rule_path_pkey',
                        'ka_gochara_rule_path_prerequisite_pkey',
                        'ka_gochara_rule_path_soft_factor_pkey',
                        'kgrpp_no_dup_uq')
    UNION ALL
    SELECT 'trigger_already_exists', n.nspname || '.' || c.relname || '.' || t.tgname
    FROM pg_trigger t
    JOIN pg_class c ON c.oid = t.tgrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public' AND NOT t.tgisinternal
      AND ( (c.relname = 'ka_gochara_predicate'
               AND t.tgname = 'ka_gochara_predicate_immutable')
         OR (c.relname = 'ka_gochara_factor'
               AND t.tgname = 'ka_gochara_factor_immutable')
         OR (c.relname = 'ka_gochara_rule_path'
               AND t.tgname = 'ka_gochara_rule_path_immutable')
         OR (c.relname = 'ka_gochara_rule_path_prerequisite'
               AND t.tgname = 'ka_gochara_rp_prereq_immutable')
         OR (c.relname = 'ka_gochara_rule_path_soft_factor'
               AND t.tgname = 'ka_gochara_rp_soft_factor_immutable') )
    UNION ALL
    -- exact-signature function collisions (trigger fns take no args; the
    -- typed helpers pin their full signatures)
    SELECT 'function_already_exists',
           n.nspname || '.' || p.proname || '(' ||
           pg_get_function_identity_arguments(p.oid) || ')'
    FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = 'public'
      AND ( (p.proname IN ('ka_gochara_predicate_no_mutation',
                           'ka_gochara_factor_no_mutation',
                           'ka_gochara_rule_path_no_mutation',
                           'ka_gochara_membership_no_mutation')
             AND pg_get_function_identity_arguments(p.oid) = '')
         OR (p.proname = 'ka_gochara_frame_ok'
             AND pg_get_function_identity_arguments(p.oid) = 'text, text')
         OR (p.proname = 'ka_gochara_string_array_ok'
             AND pg_get_function_identity_arguments(p.oid) = 'jsonb')
         OR (p.proname = 'ka_gochara_vocab_array_ok'
             AND pg_get_function_identity_arguments(p.oid) = 'jsonb, text[]')
         OR (p.proname = 'ka_gochara_object_selector_ok'
             AND pg_get_function_identity_arguments(p.oid) = 'jsonb')
         OR (p.proname = 'ka_gochara_named_operands_ok'
             AND pg_get_function_identity_arguments(p.oid) = 'jsonb') )
    UNION ALL
    SELECT 'migration_already_applied', filename
    FROM _migrations_applied
    WHERE starts_with(filename, '1154_')
  )
  SELECT string_agg(f.failure || ' :: ' || f.detail, E'\n' ORDER BY f.failure, f.detail)
  INTO failures
  FROM f;
  IF failures IS NOT NULL THEN
    RAISE EXCEPTION 'preflight 1154 BLOCKED — migration 1154 must NOT be applied:% %', E'\n', failures;
  END IF;
  RAISE NOTICE 'preflight 1154: all checks passed';
END;
$$;
