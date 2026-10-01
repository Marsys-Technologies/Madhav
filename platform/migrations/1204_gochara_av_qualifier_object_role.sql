-- Migration 1204: extend kgrr_object_role_ck on ka_gochara_relationship_record
--                 with 'av_qualifier' — Pravāha v1.5 contract amendment AM-7
--                 (GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT §AM-7; stream-A gap
--                 report M20261001T113409-04cd; steward acceptance
--                 M20261001T121451-1a8d item 4). The P5 enumeration carries
--                 object_role='av_qualifier' (services/gochara_kernel/
--                 evaluator.py:512): the aṣṭakavarga qualifier — the house-span
--                 whose BAV/SAV bindu strength qualifies a P5 window (P5a
--                 AV-quality / P5b SARVA-floor). Migration 1155 is APPLIED and
--                 never edited; this is the new migration it requires.
-- Created: 2026-10-01. Author: pravaha/b6-v15-contract-migrations (Stream B,
-- B6.0 PART 1).
--
-- Numbering: 1204/1205 verified free by a fresh scan of every origin/* ref
-- across BOTH migration directories (2026-10-01). `npm run
-- guard:migration-numbers` green.
--
-- Transaction ownership: NO BEGIN/COMMIT — migrate.ts owns ONE transaction
-- (see the 1153 header). Gate: pinned schema → preflight gate (byte-identical
-- to preflight_1204_av_qualifier_object_role.sql; requires 1155 recorded) →
-- constraint swap → presence checks. Deploy route: the protected
-- public-schema window (deploy.yml `gochara_contracts_schema_migration`).
--
-- RACE CLAIM, corrected per ASTRA_REVIEW_A5_5_SPEC_AMENDMENTS_v1_0 (rank 7):
-- the transactional ALTER TABLE takes the requisite table lock, so there is
-- no committed unconstrained interval — but the protected environment and the
-- deployment's concurrency controls do NOT demonstrate that existing writers
-- are paused. A concurrent '5.0' (or any) write against this table can block
-- on the lock or trip the 5s lock_timeout below; constraint validation can
-- hold the lock while scanning. Writer quiescence during the window is an
-- OPERATIONAL PRECONDITION to be verified at dispatch time (no '5.0' writer
-- run in flight), not a property this migration or the window asserts.
--
-- The swap: DROP + ADD of kgrr_object_role_ck inside this one transaction.
-- The new vocabulary is the v1.0 set
--   ('lord','occupant','karaka','dispositor','maraka_of_house','period_lord',
--    'yoga_constituent','pada','signature_house')
-- plus 'av_qualifier'. The v1.0 set is a strict subset, so every existing row
-- satisfies the widened CHECK and the re-validation scan cannot fail on
-- v1.0 content. No role is removed, renamed or redefined.
--
-- SAME VOCABULARY, ONE OTHER PLACE (flagged for the A5.5 gate): the role
-- vocabulary also lives in ka_gochara_object_selector_ok (1154:252-261), the
-- JSONB selector validator every rule_path row passes. AM-7's draft names
-- only kgrr_object_role_ck; leaving the selector at v1.0 would make the
-- contract internally inconsistent — a P5 path could never SELECT the role
-- its records carry. This migration therefore also CREATE OR REPLACEs that
-- validator with the same single-value widening (oid preserved, v1.0 arms
-- byte-identical, TOTAL). If the gate rules the selector stays v1.0, the
-- rollback below restores it and only the record CHECK keeps the widening.
--
-- ROLLBACK:
--   ALTER TABLE public.ka_gochara_relationship_record
--     DROP CONSTRAINT kgrr_object_role_ck,
--     ADD CONSTRAINT kgrr_object_role_ck CHECK (object_role IN
--       ('lord','occupant','karaka','dispositor','maraka_of_house',
--        'period_lord','yoga_constituent','pada','signature_house'));
--   (refuses while any 'av_qualifier' row exists — intended)
--   CREATE OR REPLACE FUNCTION public.ka_gochara_object_selector_ok(jsonb)
--   with the v1.0 body (1154) — safe only while no selector carries the role.
-- ─────────────────────────────────────────────────────────────────────────────

SET LOCAL search_path = public, pg_catalog;   -- pinned schema resolution (F9)
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '120s';

-- ── GATE (byte-identical to preflight_1204_av_qualifier_object_role.sql) ────
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

-- ── The swap ────────────────────────────────────────────────────────────────
ALTER TABLE public.ka_gochara_relationship_record
  DROP CONSTRAINT kgrr_object_role_ck,
  ADD CONSTRAINT kgrr_object_role_ck CHECK (object_role IN
    ('lord','occupant','karaka','dispositor','maraka_of_house',
     'period_lord','yoga_constituent','pada','signature_house',
     'av_qualifier'));

COMMENT ON CONSTRAINT kgrr_object_role_ck ON public.ka_gochara_relationship_record IS
  'v1.0 role vocabulary (1155) + ''av_qualifier'' (1204, spec amendment AM-7): '
  'the aṣṭakavarga qualifier — the house-span whose BAV/SAV bindu strength '
  'qualifies a P5 window (P5a AV-quality / P5b SARVA-floor).';

-- ── The same widening in the selector validator (see the header) ──────────
CREATE OR REPLACE FUNCTION public.ka_gochara_object_selector_ok(j jsonb)
RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
  SELECT j IS NOT NULL
     AND jsonb_typeof(j) = 'array'
     AND jsonb_array_length(j) >= 1
     AND NOT EXISTS (
       SELECT 1 FROM jsonb_array_elements(j) el
       WHERE jsonb_typeof(el.value) <> 'object'
          OR (el.value - 'agent' - 'relation' - 'object_role') <> '{}'::jsonb
          OR COALESCE(el.value ->> 'agent', '') <> ALL (
               ARRAY['sun','moon','mars','mercury','jupiter','venus','saturn','rahu','ketu'])
          OR COALESCE(el.value ->> 'relation', '') <> ALL (
               ARRAY['residence','aspect','conjunction','dispositorship',
                     'association','ownership','occupancy','period_running'])
          OR COALESCE(el.value ->> 'object_role', '') <> ALL (
               ARRAY['lord','occupant','karaka','dispositor','maraka_of_house',
                     'period_lord','yoga_constituent','pada','signature_house',
                     'av_qualifier'])
     );
$$;

COMMENT ON FUNCTION public.ka_gochara_object_selector_ok(jsonb) IS
  '§0 selector shape+typed domains (F11): array of {agent, relation, object_role} only; '
  'agent ∈ 9 grahas; relation ∈ the §0 relation enum; object_role ∈ the v1.0 role '
  'vocabulary + ''av_qualifier'' (1204, spec amendment AM-7). TOTAL: malformed ⇒ false.';

-- ── Presence checks: the widened definition is the live one ────────────────
DO $$
DECLARE
  def text;
BEGIN
  SELECT pg_get_constraintdef(c.oid) INTO def
  FROM pg_constraint c
  WHERE c.conrelid = 'public.ka_gochara_relationship_record'::regclass
    AND c.conname = 'kgrr_object_role_ck' AND c.convalidated;
  IF def IS NULL THEN
    RAISE EXCEPTION 'migration 1204 post-apply check failed: kgrr_object_role_ck missing or unvalidated';
  END IF;
  IF def NOT LIKE '%av_qualifier%' THEN
    RAISE EXCEPTION 'migration 1204 post-apply check failed: kgrr_object_role_ck does not admit av_qualifier: %', def;
  END IF;
  IF def NOT LIKE '%signature_house%' THEN
    RAISE EXCEPTION 'migration 1204 post-apply check failed: kgrr_object_role_ck lost a v1.0 role: %', def;
  END IF;
  -- The selector validator carries the same widening, v1.0 arms intact.
  SELECT p.prosrc INTO def
  FROM pg_proc p
  WHERE p.oid = 'public.ka_gochara_object_selector_ok(jsonb)'::regprocedure;
  IF def IS NULL THEN
    RAISE EXCEPTION 'migration 1204 post-apply check failed: ka_gochara_object_selector_ok(jsonb) missing';
  END IF;
  IF def NOT LIKE '%av_qualifier%' OR def NOT LIKE '%signature_house%' THEN
    RAISE EXCEPTION 'migration 1204 post-apply check failed: ka_gochara_object_selector_ok not widened coherently';
  END IF;
  IF public.ka_gochara_object_selector_ok('[{"agent":"mars","relation":"conjunction","object_role":"av_qualifier"}]'::jsonb) IS NOT TRUE THEN
    RAISE EXCEPTION 'migration 1204 post-apply check failed: selector refuses av_qualifier';
  END IF;
  IF public.ka_gochara_object_selector_ok('[{"agent":"mars","relation":"conjunction","object_role":"not_a_role"}]'::jsonb) IS NOT FALSE THEN
    RAISE EXCEPTION 'migration 1204 post-apply check failed: selector admits an unknown role';
  END IF;
  IF public.ka_gochara_object_selector_ok('[{"agent":"mars","relation":"conjunction","object_role":"karaka"}]'::jsonb) IS NOT TRUE THEN
    RAISE EXCEPTION 'migration 1204 post-apply check failed: selector lost a v1.0 role';
  END IF;
  RAISE NOTICE 'migration 1204: presence checks passed';
END;
$$;
