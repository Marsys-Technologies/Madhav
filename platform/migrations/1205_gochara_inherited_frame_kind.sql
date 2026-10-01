-- Migration 1205: ka_gochara_frame_ok admits the 'inherited' frame-kind —
--                 Pravāha v1.5 contract amendment AM-8
--                 (GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT §AM-8; stream-A
--                 rule_binding report M20261001T080615-a232; deferral D1 at
--                 services/gochara_rules/rule_registry.py:45-47). P6's frame
--                 is the frame of the path whose admitted window the day row
--                 annotates: a new frame-kind 'inherited' (arg NULL) — "the
--                 admitting path's frame, resolved at annotation time." P6
--                 being testimony, the frame never scopes a scored window of
--                 P6's own; it names where the day-resolution row hangs.
--                 Counting rules of the inherited frame apply unchanged.
--                 Migration 1154 is APPLIED and never edited; this is the new
--                 migration it requires.
-- Created: 2026-10-01. Author: pravaha/b6-v15-contract-migrations (Stream B,
-- B6.0 PART 1).
--
-- Numbering: 1204/1205 verified free by a fresh scan of every origin/* ref
-- across BOTH migration directories (2026-10-01). `npm run
-- guard:migration-numbers` green.
--
-- Transaction ownership: NO BEGIN/COMMIT — migrate.ts owns ONE transaction
-- (see the 1153 header). Gate: pinned schema → preflight gate (byte-identical
-- to preflight_1205_inherited_frame_kind.sql; requires 1154 recorded) →
-- CREATE OR REPLACE → presence checks. Deploy route: the protected
-- public-schema window (deploy.yml `gochara_contracts_schema_migration`).
--
-- The change: CREATE OR REPLACE FUNCTION keeps the function's oid, so every
-- dependent CHECK (kgrr_frame_ck, kgrp_frame_ck, …) binds unchanged. The
-- replacement is a WIDENING only: one new arm
--   WHEN 'inherited' THEN frame_arg IS NULL
-- is added; every v1.0 arm is byte-identical, so no previously-true call
-- changes value and no stored row can violate its CHECK after the swap. The
-- validator stays TOTAL (NULL kind or NULL-where-required ⇒ false, F5).
--
-- ROLLBACK:
--   CREATE OR REPLACE FUNCTION public.ka_gochara_frame_ok(text, text) with
--   the v1.0 body (1154) — safe only while no 'inherited' row exists.
-- ─────────────────────────────────────────────────────────────────────────────

SET LOCAL search_path = public, pg_catalog;   -- pinned schema resolution (F9)
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '120s';

-- ── GATE (byte-identical to preflight_1205_inherited_frame_kind.sql) ────────
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

-- ── The widened validator ───────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION public.ka_gochara_frame_ok(frame_kind text, frame_arg text)
RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
  SELECT COALESCE(CASE frame_kind
    WHEN 'moon'          THEN frame_arg IS NULL
    WHEN 'lagna'         THEN frame_arg IS NULL
    WHEN 'dasha_lord'    THEN frame_arg IS NULL
    WHEN 'graha'         THEN frame_arg IS NOT NULL AND frame_arg IN
      ('sun','moon','mars','mercury','jupiter','venus','saturn','rahu','ketu')
    WHEN 'bhavat_bhavam' THEN frame_arg IS NOT NULL AND frame_arg ~ '^([1-9]|1[0-2])$'
    WHEN 'inherited'     THEN frame_arg IS NULL
    ELSE false
  END, false);
$$;

COMMENT ON FUNCTION public.ka_gochara_frame_ok(text, text) IS
  '§0 frame enum+arg rule: arg NULL exactly for moon/lagna/dasha_lord/inherited; graha '
  'arg ∈ 9 grahas; bhavat_bhavam arg ∈ 1..12. TOTAL: NULL kind or NULL-where-required ⇒ '
  'false (F5). Counting is inclusive of the reference sign (§0). ''inherited'' (1205, '
  'spec amendment AM-8): the admitting path''s frame, resolved at annotation time — P6 '
  'testimony rows only; it never scopes a scored window of P6''s own.';

-- ── Presence checks: the live body admits 'inherited' and keeps v1.0 ───────
DO $$
DECLARE
  src text;
BEGIN
  SELECT p.prosrc INTO src
  FROM pg_proc p
  WHERE p.oid = 'public.ka_gochara_frame_ok(text,text)'::regprocedure;
  IF src IS NULL THEN
    RAISE EXCEPTION 'migration 1205 post-apply check failed: ka_gochara_frame_ok(text,text) missing';
  END IF;
  IF src NOT LIKE '%inherited%' THEN
    RAISE EXCEPTION 'migration 1205 post-apply check failed: ka_gochara_frame_ok lacks the inherited arm';
  END IF;
  IF src NOT LIKE '%bhavat_bhavam%' THEN
    RAISE EXCEPTION 'migration 1205 post-apply check failed: ka_gochara_frame_ok lost a v1.0 arm';
  END IF;
  -- Behavioural: new kind admitted with NULL arg only; v1.0 kinds unchanged.
  IF public.ka_gochara_frame_ok('inherited', NULL) IS NOT TRUE THEN
    RAISE EXCEPTION 'migration 1205 post-apply check failed: (inherited, NULL) is not TRUE';
  END IF;
  IF public.ka_gochara_frame_ok('inherited', 'moon') IS NOT FALSE THEN
    RAISE EXCEPTION 'migration 1205 post-apply check failed: (inherited, arg) is not FALSE';
  END IF;
  IF public.ka_gochara_frame_ok('moon', NULL) IS NOT TRUE
     OR public.ka_gochara_frame_ok('graha', 'mars') IS NOT TRUE
     OR public.ka_gochara_frame_ok('bhavat_bhavam', '12') IS NOT TRUE
     OR public.ka_gochara_frame_ok('moon', 'x') IS NOT FALSE
     OR public.ka_gochara_frame_ok(NULL, NULL) IS NOT FALSE THEN
    RAISE EXCEPTION 'migration 1205 post-apply check failed: a v1.0 arm changed value';
  END IF;
  RAISE NOTICE 'migration 1205: presence checks passed';
END;
$$;
