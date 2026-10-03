-- Preflight for migration 1204 (kgrr_object_role_ck + 'av_qualifier'). READ ONLY — run
-- against the target database BEFORE applying 1204, AFTER migration 1155 is
-- applied (ordered execution: preflights run interleaved with their
-- prerequisite migrations, never as one undifferentiated batch).
--
-- THIS BLOCK IS BYTE-IDENTICAL TO THE GATE EMBEDDED AT THE TOP OF
-- platform/migrations/1204_gochara_av_qualifier_object_role.sql — the migration runs the same
-- detector itself, in the runner's transaction, before its DDL, so the
-- protected public-schema window (deploy.yml `gochara_contracts_schema_migration`,
-- the only route that applies the gochara contract migrations) observes the
-- gate without any further wiring. The static test
-- tests/unit/migrations/gochara_b6_v15_contract_static.test.ts asserts the two
-- blocks are identical.
--
-- GATE SEMANTICS: FAILS CLOSED — any blocking finding RAISES (psql -v
-- ON_ERROR_STOP=1 aborts; node-pg rejects); success ends with NOTICE
-- 'preflight 1204: all checks passed'. Fix the environment, not the detector.
-- Only REAL preconditions are checked: the pinned schema and its privileges;
-- the 1155 table and the constraint this migration swaps exist; the
-- prerequisite migration is recorded in _migrations_applied and 1204 is not
-- (wildcard-safe starts_with, not LIKE). migrate.ts tracks applied files by
-- hash: a tracked file is never re-run; an untracked re-run is a collision
-- and is BLOCKED here. There is no replay mode.

DO $$
DECLARE
  failures text;
BEGIN
  WITH f(failure, detail) AS (
    SELECT 'schema_missing', 'public'
    WHERE to_regnamespace('public') IS NULL
    UNION ALL
    SELECT 'no_usage_privilege_on_public', current_user
    WHERE NOT has_schema_privilege('public', 'USAGE')
    UNION ALL
    SELECT 'no_create_privilege_on_public', current_user
    WHERE NOT has_schema_privilege('public', 'CREATE')
    UNION ALL
    SELECT 'table_missing', 'public.ka_gochara_relationship_record'
    WHERE to_regclass('public.ka_gochara_relationship_record') IS NULL
    UNION ALL
    SELECT 'constraint_missing', 'ka_gochara_relationship_record.kgrr_object_role_ck'
    WHERE to_regclass('public.ka_gochara_relationship_record') IS NOT NULL
      AND NOT EXISTS (
        SELECT 1 FROM pg_constraint c
        WHERE c.conrelid = 'public.ka_gochara_relationship_record'::regclass
          AND c.conname = 'kgrr_object_role_ck')
    UNION ALL
    SELECT 'function_missing', 'ka_gochara_object_selector_ok(jsonb)'
    WHERE to_regprocedure('public.ka_gochara_object_selector_ok(jsonb)') IS NULL
    UNION ALL
    -- ordered execution gate: 1155 recorded, 1204 not
    SELECT 'prerequisite_migration_not_applied', p.prefix
    FROM (VALUES ('1155_')) AS p(prefix)
    WHERE to_regclass('public._migrations_applied') IS NOT NULL
      AND NOT EXISTS (SELECT 1 FROM _migrations_applied m WHERE starts_with(m.filename, p.prefix))
    UNION ALL
    SELECT 'migration_already_applied', m.filename
    FROM _migrations_applied m
    WHERE to_regclass('public._migrations_applied') IS NOT NULL
      AND starts_with(m.filename, '1204_')
  )
  SELECT string_agg(f.failure || ' :: ' || f.detail, E'\n' ORDER BY f.failure, f.detail)
  INTO failures
  FROM f;
  IF failures IS NOT NULL THEN
    RAISE EXCEPTION 'preflight 1204 BLOCKED — migration 1204 must NOT be applied:% %', E'\n', failures;
  END IF;
  RAISE NOTICE 'preflight 1204: all checks passed';
END;
$$;
