-- Preflight for migration 1205 (ka_gochara_frame_ok + 'inherited'). READ ONLY — run
-- against the target database BEFORE applying 1205, AFTER migration 1154 is
-- applied (ordered execution: preflights run interleaved with their
-- prerequisite migrations, never as one undifferentiated batch).
--
-- THIS BLOCK IS BYTE-IDENTICAL TO THE GATE EMBEDDED AT THE TOP OF
-- platform/migrations/1205_gochara_inherited_frame_kind.sql — the migration runs the same
-- detector itself, in the runner's transaction, before its DDL, so the
-- protected public-schema window (deploy.yml `gochara_contracts_schema_migration`,
-- the only route that applies the gochara contract migrations) observes the
-- gate without any further wiring. The static test
-- tests/unit/migrations/gochara_b6_v15_contract_static.test.ts asserts the two
-- blocks are identical.
--
-- GATE SEMANTICS: FAILS CLOSED — any blocking finding RAISES (psql -v
-- ON_ERROR_STOP=1 aborts; node-pg rejects); success ends with NOTICE
-- 'preflight 1205: all checks passed'. Fix the environment, not the detector.
-- Only REAL preconditions are checked: the pinned schema and its privileges;
-- the 1154 validator function exists by EXACT signature (to_regprocedure,
-- never the name-retaining identity-arguments text); the prerequisite
-- migration is recorded in _migrations_applied and 1205 is not
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
    SELECT 'function_missing', 'ka_gochara_frame_ok(text,text)'
    WHERE to_regprocedure('public.ka_gochara_frame_ok(text,text)') IS NULL
    UNION ALL
    -- ordered execution gate: 1154 recorded, 1205 not
    SELECT 'prerequisite_migration_not_applied', p.prefix
    FROM (VALUES ('1154_')) AS p(prefix)
    WHERE to_regclass('public._migrations_applied') IS NOT NULL
      AND NOT EXISTS (SELECT 1 FROM _migrations_applied m WHERE starts_with(m.filename, p.prefix))
    UNION ALL
    SELECT 'migration_already_applied', m.filename
    FROM _migrations_applied m
    WHERE to_regclass('public._migrations_applied') IS NOT NULL
      AND starts_with(m.filename, '1205_')
  )
  SELECT string_agg(f.failure || ' :: ' || f.detail, E'\n' ORDER BY f.failure, f.detail)
  INTO failures
  FROM f;
  IF failures IS NOT NULL THEN
    RAISE EXCEPTION 'preflight 1205 BLOCKED — migration 1205 must NOT be applied:% %', E'\n', failures;
  END IF;
  RAISE NOTICE 'preflight 1205: all checks passed';
END;
$$;
