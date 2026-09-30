-- Migration 1154: ka_gochara rule-path registries — rule_path, predicate,
--                 factor, the NORMALISED ordered version-bound membership
--                 tables, and the rule-version SEAL that makes a complete
--                 rule definition immutable after construction (F3).
--                 Round-3 rewrite per ASTRA_REVIEW_A5_1_MIGRATIONS v1_1
--                 (F3, F5, F6, F8, F9, F11) under the steward rulings.
--                 Depends on 1153 (shared helpers + definition verifier).
--                 1153–1157 were never applied anywhere — in-place rewrite.
-- Created: 2026-09-30. Author: pravaha/a5-migrations (Stream A, A5.1).
--
-- Numbering: 1154 sits inside this lane's granted block (1150–1159 per
-- ADK-0026 §4). Verified free by a fresh scan of every origin/* ref across
-- BOTH migration directories (2026-09-30). `npm run guard:migration-numbers`
-- green.
--
-- Transaction ownership: NO BEGIN/COMMIT — migrate.ts owns ONE transaction
-- around DDL + ledger insert (see the 1153 header). Effective ordered gate:
-- pinned schema → preflight gate (byte-identical to
-- preflight_1154_rule_path_registry.sql) → DDL → post-DDL definition
-- verification (1153's ka_gochara_verify_definitions) — see the 1153 header
-- for the four distinct outcomes.
--
-- ── F3 — rule-version membership is immutable after construction ─────────
-- prerequisites / soft_factors are membership rows with real composite FKs
-- (round-2 amendment 3, kept). A version's definition is CONSTRUCTED by
-- inserting the rule_path row and its membership rows, then SEALED by
-- inserting a ka_gochara_rule_path_seal row (any transaction; the seal is
-- the explicit completion boundary). After the seal:
--   * INSERT into either membership table for that (path_id, rule_version)
--     is refused (ka_gochara_membership_guard);
--   * UPDATE/DELETE were never allowed (insert-only), TRUNCATE is refused;
--   * a relationship record or eval window may reference ONLY a sealed
--     version (ka_gochara_require_sealed_rule_path, installed by 1155/1156)
--     — so a "used" version is always a sealed version, and its
--     interpretation can never change without a new rule_version.
--
-- ── F6 — factor discipline exactly as the binding C2 ruling ──────────────
-- Enforced: range ⊆ [0,1] (finite); calibration_status NOT NULL ∈
-- {uncalibrated_default, calibrated}; calibrated ⇒ a machine-readable
-- category_mapping (non-empty JSON object) is present. NOT enforced (the
-- round-2 over-restriction is withdrawn): an uncalibrated_default row MAY
-- carry an authored default mapping (S:173–178 places the B5.1 mapping on
-- the row while it stays uncalibrated); doctrine_ordering is optional and
-- shape-checked only when present. No numeric value is invented or seeded.
--
-- ── F5/F11 — total validators and a declared selector encoding ───────────
-- Every helper returns a total boolean (NULL input ⇒ false, never SQL NULL)
-- and every CHECK asks `… IS TRUE`. Selector encoding (§2.1 "named
-- selectors — every L1/L0 input named, no free prose"): a selector token is
-- `^[a-z][a-z0-9_]*([.:/][a-z0-9_]+)*$` (a dotted/colon path naming an
-- L0/L1 input, e.g. chart_facts.graha_position:mars); an operand object maps
-- identifier keys to a token, a non-empty array of tokens, or a JSON number
-- (a declared numeric parameter such as an orb). Empty strings, prose with
-- whitespace, null, booleans and nested objects are rejected.
--
-- Encoded as:
--   * CONSTRAINT: composite PKs; provenance/operator_role/operator/direction/
--     units/null_state/calibration_status enums; unknown_is_false pinned
--     false (§2.2 inv 2); ruling_ref REQUIRED iff needed for
--     uncited_extension and never forbidden otherwise (S:110 as frozen);
--     typed frame (ka_gochara_frame_ok); agent_set ⊆ 9 grahas, relation_set
--     ⊆ 8 relations, object_selector = non-empty array of exact
--     {agent, relation, object_role} tuples consistent with the row's own
--     sets (O-RP-8 qualification-driven enumeration); score_rule NOT NULL.
--   * TRIGGER: all registry tables insert-only + TRUNCATE refused; membership
--     insert refused once sealed; seal insert-only.
--   * COMMENT ONLY: predicate evaluation states {true|false|unknown} are
--     evaluator semantics; the within-path product / cross-path max and the
--     shared-root evidence reduction (§2.1) are evaluator behaviour.
--
-- asset_registry: deliberately NOT registered (same disposition as 1081).
--
-- ROLLBACK (dependents first; 1155–1157 before this):
--   DROP TABLE IF EXISTS ka_gochara_rule_path_seal;
--   DROP TABLE IF EXISTS ka_gochara_rule_path_soft_factor;
--   DROP TABLE IF EXISTS ka_gochara_rule_path_prerequisite;
--   DROP TABLE IF EXISTS ka_gochara_rule_path;
--   DROP TABLE IF EXISTS ka_gochara_factor;
--   DROP TABLE IF EXISTS ka_gochara_predicate;
--   DROP FUNCTION IF EXISTS ka_gochara_require_sealed_rule_path();
--   DROP FUNCTION IF EXISTS ka_gochara_membership_guard();
--   DROP FUNCTION IF EXISTS ka_gochara_object_selector_consistent_ok(jsonb, jsonb, jsonb);
--   DROP FUNCTION IF EXISTS ka_gochara_object_selector_ok(jsonb);
--   DROP FUNCTION IF EXISTS ka_gochara_named_operands_ok(jsonb);
--   DROP FUNCTION IF EXISTS ka_gochara_vocab_array_ok(jsonb, text[]);
--   DROP FUNCTION IF EXISTS ka_gochara_string_array_ok(jsonb);
--   DROP FUNCTION IF EXISTS ka_gochara_selector_token_ok(text);
--   DROP FUNCTION IF EXISTS ka_gochara_frame_ok(text, text);
-- ─────────────────────────────────────────────────────────────────────────────

SET LOCAL search_path = public, pg_catalog;   -- pinned schema resolution (F9)
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '120s';

-- ── GATE (byte-identical to preflight_1154_rule_path_registry.sql) ─────────
DO $$
DECLARE
  replay   boolean := COALESCE(current_setting('ka_gochara.deliberate_replay', true), '') = 'on';
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
    SELECT 'relation_already_exists', 'public.' || c.relname
    FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE NOT replay AND n.nspname = 'public'
      AND c.relname IN ('ka_gochara_predicate', 'ka_gochara_predicate_pkey',
                        'ka_gochara_factor', 'ka_gochara_factor_pkey',
                        'ka_gochara_rule_path', 'ka_gochara_rule_path_pkey',
                        'ka_gochara_rule_path_prerequisite', 'ka_gochara_rule_path_prerequisite_pkey',
                        'kgrpp_no_dup_uq',
                        'ka_gochara_rule_path_soft_factor', 'ka_gochara_rule_path_soft_factor_pkey',
                        'ka_gochara_rule_path_seal', 'ka_gochara_rule_path_seal_pkey')
    UNION ALL
    SELECT 'trigger_already_exists', 'public.' || c.relname || '.' || t.tgname
    FROM pg_trigger t
    JOIN pg_class c ON c.oid = t.tgrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE NOT replay AND n.nspname = 'public' AND NOT t.tgisinternal
      AND ( (c.relname = 'ka_gochara_predicate'
               AND t.tgname IN ('ka_gochara_predicate_immutable', 'ka_gochara_predicate_no_truncate'))
         OR (c.relname = 'ka_gochara_factor'
               AND t.tgname IN ('ka_gochara_factor_immutable', 'ka_gochara_factor_no_truncate'))
         OR (c.relname = 'ka_gochara_rule_path'
               AND t.tgname IN ('ka_gochara_rule_path_immutable', 'ka_gochara_rule_path_no_truncate'))
         OR (c.relname = 'ka_gochara_rule_path_prerequisite'
               AND t.tgname IN ('ka_gochara_rp_prereq_sealed_check', 'ka_gochara_rp_prereq_immutable',
                                'ka_gochara_rp_prereq_no_truncate'))
         OR (c.relname = 'ka_gochara_rule_path_soft_factor'
               AND t.tgname IN ('ka_gochara_rp_soft_factor_sealed_check', 'ka_gochara_rp_soft_factor_immutable',
                                'ka_gochara_rp_soft_factor_no_truncate'))
         OR (c.relname = 'ka_gochara_rule_path_seal'
               AND t.tgname IN ('ka_gochara_rule_path_seal_immutable', 'ka_gochara_rule_path_seal_no_truncate')) )
    UNION ALL
    -- function collisions by EXACT ARGUMENT TYPES (F8)
    SELECT 'function_already_exists',
           'public.' || p.proname || '(' || array_to_string(e.argtypes, ',') || ')'
    FROM (VALUES
            ('ka_gochara_frame_ok',                       ARRAY['text','text']),
            ('ka_gochara_selector_token_ok',              ARRAY['text']),
            ('ka_gochara_string_array_ok',                ARRAY['jsonb']),
            ('ka_gochara_vocab_array_ok',                 ARRAY['jsonb','text[]']),
            ('ka_gochara_named_operands_ok',              ARRAY['jsonb']),
            ('ka_gochara_object_selector_ok',             ARRAY['jsonb']),
            ('ka_gochara_object_selector_consistent_ok',  ARRAY['jsonb','jsonb','jsonb']),
            ('ka_gochara_membership_guard',               ARRAY[]::text[]),
            ('ka_gochara_require_sealed_rule_path',       ARRAY[]::text[])
         ) AS e(fname, argtypes)
    JOIN pg_proc p ON p.proname = e.fname
    JOIN pg_namespace n ON n.oid = p.pronamespace AND n.nspname = 'public'
    WHERE NOT replay
      AND (SELECT COALESCE(array_agg(format_type(u.oid, NULL) ORDER BY u.ord), '{}')
           FROM unnest(p.proargtypes) WITH ORDINALITY AS u(oid, ord)) = e.argtypes
    UNION ALL
    -- shared helpers from 1153 must be present with their exact signatures
    SELECT 'helper_function_missing', e.sig
    FROM (VALUES ('ka_gochara_refuse_truncate()'),
                 ('ka_gochara_insert_only()'),
                 ('ka_gochara_finite_ok(double precision)'),
                 ('ka_gochara_verify_definitions(text,jsonb)')) AS e(sig)
    WHERE to_regprocedure('public.' || e.sig) IS NULL
    UNION ALL
    -- ordered execution gate: 1153 recorded, 1154 not
    SELECT 'prerequisite_migration_not_applied', p.prefix
    FROM (VALUES ('1153_')) AS p(prefix)
    WHERE to_regclass('public._migrations_applied') IS NOT NULL
      AND NOT EXISTS (SELECT 1 FROM _migrations_applied m WHERE starts_with(m.filename, p.prefix))
    UNION ALL
    SELECT 'migration_already_applied', m.filename
    FROM _migrations_applied m
    WHERE NOT replay AND to_regclass('public._migrations_applied') IS NOT NULL
      AND starts_with(m.filename, '1154_')
  )
  SELECT string_agg(f.failure || ' :: ' || f.detail, E'\n' ORDER BY f.failure, f.detail)
  INTO failures
  FROM f;
  IF failures IS NOT NULL THEN
    RAISE EXCEPTION 'preflight 1154 BLOCKED — migration 1154 must NOT be applied:% %', E'\n', failures;
  END IF;
  IF replay THEN
    RAISE NOTICE 'preflight 1154: deliberate replay — existence checks skipped; definitions are verified post-DDL';
  END IF;
  RAISE NOTICE 'preflight 1154: all checks passed';
END;
$$;

-- ── 0. Typed helpers — TOTAL booleans (F5), declared encodings (F11) ──────

-- §0 frame rule: moon/lagna/dasha_lord carry no arg; graha carries one of the
-- 9 grahas; bhavat_bhavam carries a house 1..12. NULL kind or a NULL arg
-- where one is required ⇒ FALSE (never SQL NULL).
CREATE OR REPLACE FUNCTION public.ka_gochara_frame_ok(frame_kind text, frame_arg text)
RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
  SELECT COALESCE(CASE frame_kind
    WHEN 'moon'          THEN frame_arg IS NULL
    WHEN 'lagna'         THEN frame_arg IS NULL
    WHEN 'dasha_lord'    THEN frame_arg IS NULL
    WHEN 'graha'         THEN frame_arg IS NOT NULL AND frame_arg IN
      ('sun','moon','mars','mercury','jupiter','venus','saturn','rahu','ketu')
    WHEN 'bhavat_bhavam' THEN frame_arg IS NOT NULL AND frame_arg ~ '^([1-9]|1[0-2])$'
    ELSE false
  END, false);
$$;

COMMENT ON FUNCTION public.ka_gochara_frame_ok(text, text) IS
  '§0 frame enum+arg rule: arg NULL exactly for moon/lagna/dasha_lord; graha arg ∈ 9 '
  'grahas; bhavat_bhavam arg ∈ 1..12. TOTAL: NULL kind or NULL-where-required ⇒ false '
  '(F5). Counting is inclusive of the reference sign (§0).';

-- Declared selector-token encoding (F11).
CREATE OR REPLACE FUNCTION public.ka_gochara_selector_token_ok(t text)
RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
  SELECT t IS NOT NULL AND t ~ '^[a-z][a-z0-9_]*([.:/][a-z0-9_]+)*$';
$$;

-- jsonb array whose every element is a non-empty, whitespace-free string.
CREATE OR REPLACE FUNCTION public.ka_gochara_string_array_ok(j jsonb)
RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
  SELECT j IS NOT NULL
     AND jsonb_typeof(j) = 'array'
     AND NOT EXISTS (
       SELECT 1 FROM jsonb_array_elements(j) el
       WHERE jsonb_typeof(el.value) <> 'string'
          OR (el.value #>> '{}') !~ '^\S+$'
     );
$$;

-- non-empty jsonb string array whose every element is inside a closed vocab.
CREATE OR REPLACE FUNCTION public.ka_gochara_vocab_array_ok(j jsonb, vocab text[])
RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
  SELECT public.ka_gochara_string_array_ok(j)
     AND jsonb_array_length(j) >= 1
     AND NOT EXISTS (
       SELECT 1 FROM jsonb_array_elements_text(j) v
       WHERE v <> ALL (vocab)
     );
$$;

-- §2.1 named operands: a non-empty jsonb OBJECT; identifier keys; values are
-- a selector token, a non-empty array of selector tokens, or a JSON number.
CREATE OR REPLACE FUNCTION public.ka_gochara_named_operands_ok(j jsonb)
RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
  SELECT j IS NOT NULL
     AND jsonb_typeof(j) = 'object'
     AND j <> '{}'::jsonb
     AND NOT EXISTS (
       SELECT 1 FROM jsonb_each(j) e
       WHERE e.key !~ '^[a-z][a-z0-9_]*$'
          OR NOT (
               (jsonb_typeof(e.value) = 'string'
                  AND public.ka_gochara_selector_token_ok(e.value #>> '{}'))
            OR (jsonb_typeof(e.value) = 'number')
            OR (jsonb_typeof(e.value) = 'array'
                  AND jsonb_array_length(e.value) >= 1
                  AND NOT EXISTS (
                        SELECT 1 FROM jsonb_array_elements(e.value) x
                        WHERE jsonb_typeof(x.value) <> 'string'
                           OR NOT public.ka_gochara_selector_token_ok(x.value #>> '{}')))
          )
     );
$$;

-- §2.1 object_selector: NON-EMPTY array of exact {agent, relation,
-- object_role} tuples, each validated against the closed vocabularies.
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
                     'period_lord','yoga_constituent','pada','signature_house'])
     );
$$;

-- Every selector tuple names an agent in agent_set and a relation in
-- relation_set (the sets are the row's own declared universe).
CREATE OR REPLACE FUNCTION public.ka_gochara_object_selector_consistent_ok(sel jsonb, agents jsonb, relations jsonb)
RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
  SELECT public.ka_gochara_object_selector_ok(sel)
     AND jsonb_typeof(agents) = 'array' AND jsonb_typeof(relations) = 'array'
     AND NOT EXISTS (
       SELECT 1 FROM jsonb_array_elements(sel) el
       WHERE NOT (agents    @> to_jsonb(el.value ->> 'agent'))
          OR NOT (relations @> to_jsonb(el.value ->> 'relation'))
     );
$$;

-- ── 1. predicate (§2.1) ────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.ka_gochara_predicate (
  predicate_id      TEXT NOT NULL,
  rule_version      TEXT NOT NULL,
  operator          TEXT NOT NULL,
  operands          JSONB NOT NULL,              -- named selectors (declared encoding)
  unknown_is_false  BOOLEAN NOT NULL DEFAULT false,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),

  PRIMARY KEY (predicate_id, rule_version),
  CONSTRAINT kgp_ids_nonblank_ck CHECK (btrim(predicate_id) <> '' AND btrim(rule_version) <> ''),
  CONSTRAINT kgp_operator_ck CHECK (operator IN
    ('eq','in_set','within_orb','house_from','overlaps',
     'period_running_at','declaration_exists')),
  CONSTRAINT kgp_unknown_is_false_ck CHECK (unknown_is_false = false),
    -- §2.1/§2.2 inv 2: unknown ≠ false; an unknown necessary predicate makes
    -- admission unqualified, never excluded
  CONSTRAINT kgp_operands_typed_ck CHECK (public.ka_gochara_named_operands_ok(operands) IS TRUE)
);

COMMENT ON TABLE public.ka_gochara_predicate IS
  'Predicate registry (GOCHARA_DESIGN_SPECS_v1_4 §2.1): composite (predicate_id, '
  'rule_version) PK; states {true|false|unknown} are evaluator semantics; '
  'unknown_is_false pinned false. operands use the declared selector encoding (F11). '
  'Insert-only (trigger); TRUNCATE refused.';

DROP TRIGGER IF EXISTS ka_gochara_predicate_immutable ON public.ka_gochara_predicate;
CREATE TRIGGER ka_gochara_predicate_immutable
  BEFORE UPDATE OR DELETE ON public.ka_gochara_predicate
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_insert_only('§2.1 amendment 1 — a predicate change is a new rule_version row');
DROP TRIGGER IF EXISTS ka_gochara_predicate_no_truncate ON public.ka_gochara_predicate;
CREATE TRIGGER ka_gochara_predicate_no_truncate
  BEFORE TRUNCATE ON public.ka_gochara_predicate
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_refuse_truncate();

-- ── 2. factor (§2.1; C2 as ruled — F6) ────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.ka_gochara_factor (
  factor_id          TEXT NOT NULL,
  rule_version       TEXT NOT NULL,
  operand_selector   JSONB NOT NULL,             -- named operand selector (declared encoding)
  direction          TEXT NOT NULL,
  function           TEXT NOT NULL,              -- numeric form name: 'step','linear','ratio',…
  range_lower        REAL NOT NULL,
  range_upper        REAL NOT NULL,
  units              TEXT NOT NULL,
  calibration_status TEXT NOT NULL DEFAULT 'uncalibrated_default',
  doctrine_ordering  JSONB,                      -- optional: the doctrine's stated category
                                                 --   ORDERING (array of strings; B5.1 content)
  category_mapping   JSONB,                      -- machine-readable mapping/parameters
                                                 --   (object; B5.1 / L5 content) — REQUIRED
                                                 --   when calibrated, PERMITTED otherwise
  null_state         TEXT NOT NULL,
  effect             TEXT NOT NULL,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),

  PRIMARY KEY (factor_id, rule_version),
  CONSTRAINT kgf_ids_nonblank_ck CHECK (btrim(factor_id) <> '' AND btrim(rule_version) <> ''),
  CONSTRAINT kgf_function_nonblank_ck CHECK (btrim(function) <> ''),
  CONSTRAINT kgf_effect_nonblank_ck CHECK (btrim(effect) <> ''),
  CONSTRAINT kgf_direction_ck CHECK (direction IN
    ('higher_stronger','lower_stronger')),
  CONSTRAINT kgf_units_ck CHECK (units IN
    ('degrees','days','count','unitless')),
  CONSTRAINT kgf_calibration_status_ck CHECK (calibration_status IN
    ('uncalibrated_default','calibrated')),
  CONSTRAINT kgf_null_state_ck CHECK (null_state IN ('omit','unqualified')),
  CONSTRAINT kgf_range_unit_interval_ck
    CHECK (public.ka_gochara_finite_ok(range_lower) IS TRUE
           AND public.ka_gochara_finite_ok(range_upper) IS TRUE
           AND range_lower >= 0 AND range_lower <= range_upper AND range_upper <= 1),
    -- §2.1 codomain: every scored factor's range ⊆ [0,1]; never negative
  CONSTRAINT kgf_operand_selector_typed_ck
    CHECK (public.ka_gochara_named_operands_ok(operand_selector) IS TRUE),
  CONSTRAINT kgf_doctrine_ordering_shape_ck
    CHECK (doctrine_ordering IS NULL
           OR (public.ka_gochara_string_array_ok(doctrine_ordering) IS TRUE
               AND jsonb_array_length(doctrine_ordering) >= 1)),
  CONSTRAINT kgf_category_mapping_shape_ck
    CHECK (category_mapping IS NULL
           OR (jsonb_typeof(category_mapping) = 'object' AND category_mapping <> '{}'::jsonb)),
  CONSTRAINT kgf_calibrated_requires_mapping_ck
    CHECK (calibration_status <> 'calibrated' OR category_mapping IS NOT NULL)
    -- steward ruling / D-SPECS C2 (F6): calibrated rows CARRY a mapping; an
    -- uncalibrated_default row may carry an authored default mapping; no
    -- ordering is demanded of continuous factors
);

COMMENT ON TABLE public.ka_gochara_factor IS
  'Soft-factor registry (GOCHARA_DESIGN_SPECS_v1_4 §2.1): composite (factor_id, '
  'rule_version) PK. Codomain ⊆ [0,1] (CHECK). Calibration discipline exactly per D-SPECS '
  'C2 (F6): calibration_status NOT NULL; calibrated ⇒ category_mapping present; an '
  'uncalibrated_default row is rank-only and may carry an authored default mapping; no '
  'factor number is invented by this migration. Insert-only (trigger); TRUNCATE refused.';

DROP TRIGGER IF EXISTS ka_gochara_factor_immutable ON public.ka_gochara_factor;
CREATE TRIGGER ka_gochara_factor_immutable
  BEFORE UPDATE OR DELETE ON public.ka_gochara_factor
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_insert_only('§2.1 amendment 1 — a factor change is a new rule_version row');
DROP TRIGGER IF EXISTS ka_gochara_factor_no_truncate ON public.ka_gochara_factor;
CREATE TRIGGER ka_gochara_factor_no_truncate
  BEFORE TRUNCATE ON public.ka_gochara_factor
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_refuse_truncate();

-- ── 3. rule_path (§2.1) ────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.ka_gochara_rule_path (
  path_id           TEXT NOT NULL,               -- 'P1'…'P6', 'P9' behind D-T2 (§1.1)
  rule_version      TEXT NOT NULL,
  frame_kind        TEXT NOT NULL,
  frame_arg         TEXT,                        -- typed by ka_gochara_frame_ok (§0)
  agent_set         JSONB NOT NULL,              -- ⊆ 9 grahas, non-empty
  relation_set      JSONB NOT NULL,              -- ⊆ 8 §1.1 relations, non-empty
  object_selector   JSONB NOT NULL,              -- [(agent, relation, object_role)] tuples
  provenance        TEXT NOT NULL,
  operator_role     TEXT NOT NULL,
  ruling_ref        TEXT,                        -- e.g. 'D-P4', 'D-PADMIT'
  score_rule        TEXT NOT NULL,               -- within-path algebra reference (NK-4);
                                                 --   declared on every row
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),

  PRIMARY KEY (path_id, rule_version),
  CONSTRAINT kgrp_ids_nonblank_ck CHECK (btrim(path_id) <> '' AND btrim(rule_version) <> ''),
  CONSTRAINT kgrp_score_rule_nonblank_ck CHECK (btrim(score_rule) <> ''),
  CONSTRAINT kgrp_frame_ck CHECK (public.ka_gochara_frame_ok(frame_kind, frame_arg) IS TRUE),
  CONSTRAINT kgrp_agent_set_ck CHECK (public.ka_gochara_vocab_array_ok(agent_set,
    ARRAY['sun','moon','mars','mercury','jupiter','venus','saturn','rahu','ketu']) IS TRUE),
  CONSTRAINT kgrp_relation_set_ck CHECK (public.ka_gochara_vocab_array_ok(relation_set,
    ARRAY['residence','aspect','conjunction','dispositorship',
          'association','ownership','occupancy','period_running']) IS TRUE),
  CONSTRAINT kgrp_object_selector_ck
    CHECK (public.ka_gochara_object_selector_consistent_ok(object_selector, agent_set, relation_set) IS TRUE),
  CONSTRAINT kgrp_provenance_ck CHECK (provenance IN
    ('verse_cited','uncited_extension')),
  CONSTRAINT kgrp_operator_role_ck CHECK (operator_role IN ('scored','testimony')),
  CONSTRAINT kgrp_ruling_ck
    CHECK (provenance <> 'uncited_extension' OR ruling_ref IS NOT NULL)
    -- §0/S:110 as frozen: uncited_extension REQUIRES a ruling_ref; a ruling
    -- ref is never forbidden otherwise
);

COMMENT ON TABLE public.ka_gochara_rule_path IS
  'Rule-path registry (GOCHARA_DESIGN_SPECS_v1_4 §2.1): composite (path_id, rule_version) '
  'PK; all FKs into this table are composite version-bound. prerequisites and '
  'soft_factors are NORMALISED into ka_gochara_rule_path_prerequisite / '
  'ka_gochara_rule_path_soft_factor with real composite FKs; a version''s definition is '
  'complete once a ka_gochara_rule_path_seal row exists — after that no membership row '
  'can be added (F3) and only sealed versions may be referenced by records/windows. '
  'Admission per §0 (S-04). Insert-only (trigger); TRUNCATE refused.';

DROP TRIGGER IF EXISTS ka_gochara_rule_path_immutable ON public.ka_gochara_rule_path;
CREATE TRIGGER ka_gochara_rule_path_immutable
  BEFORE UPDATE OR DELETE ON public.ka_gochara_rule_path
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_insert_only('§2.1 amendment 1 — a path change is a new rule_version row');
DROP TRIGGER IF EXISTS ka_gochara_rule_path_no_truncate ON public.ka_gochara_rule_path;
CREATE TRIGGER ka_gochara_rule_path_no_truncate
  BEFORE TRUNCATE ON public.ka_gochara_rule_path
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_refuse_truncate();

-- ── 4. Membership tables: ordered, version-bound, real FKs, sealable (F3) ─

CREATE TABLE IF NOT EXISTS public.ka_gochara_rule_path_prerequisite (
  path_id                TEXT NOT NULL,
  rule_version           TEXT NOT NULL,
  ordinal                INTEGER NOT NULL,       -- §1.1/§2.1: ordered, cheapest
                                                 --   necessary predicate first
  predicate_id           TEXT NOT NULL,
  predicate_rule_version TEXT NOT NULL,

  PRIMARY KEY (path_id, rule_version, ordinal),
  CONSTRAINT kgrpp_ordinal_ck CHECK (ordinal >= 1),
  CONSTRAINT kgrpp_path_fk FOREIGN KEY (path_id, rule_version)
    REFERENCES public.ka_gochara_rule_path (path_id, rule_version),
  CONSTRAINT kgrpp_predicate_fk FOREIGN KEY (predicate_id, predicate_rule_version)
    REFERENCES public.ka_gochara_predicate (predicate_id, rule_version),
  CONSTRAINT kgrpp_no_dup_uq
    UNIQUE (path_id, rule_version, predicate_id, predicate_rule_version)
);

CREATE TABLE IF NOT EXISTS public.ka_gochara_rule_path_soft_factor (
  path_id              TEXT NOT NULL,
  rule_version         TEXT NOT NULL,
  factor_id            TEXT NOT NULL,
  factor_rule_version  TEXT NOT NULL,

  PRIMARY KEY (path_id, rule_version, factor_id, factor_rule_version),
  CONSTRAINT kgrps_path_fk FOREIGN KEY (path_id, rule_version)
    REFERENCES public.ka_gochara_rule_path (path_id, rule_version),
  CONSTRAINT kgrps_factor_fk FOREIGN KEY (factor_id, factor_rule_version)
    REFERENCES public.ka_gochara_factor (factor_id, rule_version)
);

-- The completion boundary (F3).
CREATE TABLE IF NOT EXISTS public.ka_gochara_rule_path_seal (
  path_id      TEXT NOT NULL,
  rule_version TEXT NOT NULL,
  sealed_at    TIMESTAMPTZ NOT NULL DEFAULT now(),

  PRIMARY KEY (path_id, rule_version),
  CONSTRAINT kgrpseal_path_fk FOREIGN KEY (path_id, rule_version)
    REFERENCES public.ka_gochara_rule_path (path_id, rule_version)
);

COMMENT ON TABLE public.ka_gochara_rule_path_seal IS
  'Rule-version completion boundary (F3): a (path_id, rule_version) is CONSTRUCTED '
  '(rule_path row + membership rows) and then SEALED by this row. After the seal no '
  'prerequisite/soft-factor row can be added to that version (membership guard), and only '
  'sealed versions may be referenced by relationship records and eval windows '
  '(ka_gochara_require_sealed_rule_path). A change is a new rule_version. Insert-only; '
  'TRUNCATE refused.';

CREATE OR REPLACE FUNCTION public.ka_gochara_membership_guard()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
BEGIN
  IF EXISTS (SELECT 1 FROM public.ka_gochara_rule_path_seal s
             WHERE s.path_id = NEW.path_id AND s.rule_version = NEW.rule_version) THEN
    RAISE EXCEPTION '% refused (F3 / GOCHARA_DESIGN_SPECS_v1_4 §2.1): rule version (%, %) is SEALED — its prerequisite/soft-factor membership is complete and immutable; a definition change is a NEW rule_version',
      TG_TABLE_NAME, NEW.path_id, NEW.rule_version;
  END IF;
  RETURN NEW;
END;
$$;

-- Used by 1155/1156: a record/window may reference only a sealed version.
CREATE OR REPLACE FUNCTION public.ka_gochara_require_sealed_rule_path()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM public.ka_gochara_rule_path_seal s
                 WHERE s.path_id = NEW.path_id AND s.rule_version = NEW.rule_version) THEN
    RAISE EXCEPTION '% refused (F3): rule version (%, %) is not sealed — only a completed (sealed) rule version may produce records or windows',
      TG_TABLE_NAME, NEW.path_id, NEW.rule_version;
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS ka_gochara_rp_prereq_sealed_check ON public.ka_gochara_rule_path_prerequisite;
CREATE TRIGGER ka_gochara_rp_prereq_sealed_check
  BEFORE INSERT ON public.ka_gochara_rule_path_prerequisite
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_membership_guard();
DROP TRIGGER IF EXISTS ka_gochara_rp_prereq_immutable ON public.ka_gochara_rule_path_prerequisite;
CREATE TRIGGER ka_gochara_rp_prereq_immutable
  BEFORE UPDATE OR DELETE ON public.ka_gochara_rule_path_prerequisite
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_insert_only('§2.1 amendment 1 — a membership change rides a new rule_version');
DROP TRIGGER IF EXISTS ka_gochara_rp_prereq_no_truncate ON public.ka_gochara_rule_path_prerequisite;
CREATE TRIGGER ka_gochara_rp_prereq_no_truncate
  BEFORE TRUNCATE ON public.ka_gochara_rule_path_prerequisite
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_refuse_truncate();

DROP TRIGGER IF EXISTS ka_gochara_rp_soft_factor_sealed_check ON public.ka_gochara_rule_path_soft_factor;
CREATE TRIGGER ka_gochara_rp_soft_factor_sealed_check
  BEFORE INSERT ON public.ka_gochara_rule_path_soft_factor
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_membership_guard();
DROP TRIGGER IF EXISTS ka_gochara_rp_soft_factor_immutable ON public.ka_gochara_rule_path_soft_factor;
CREATE TRIGGER ka_gochara_rp_soft_factor_immutable
  BEFORE UPDATE OR DELETE ON public.ka_gochara_rule_path_soft_factor
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_insert_only('§2.1 amendment 1 — a membership change rides a new rule_version');
DROP TRIGGER IF EXISTS ka_gochara_rp_soft_factor_no_truncate ON public.ka_gochara_rule_path_soft_factor;
CREATE TRIGGER ka_gochara_rp_soft_factor_no_truncate
  BEFORE TRUNCATE ON public.ka_gochara_rule_path_soft_factor
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_refuse_truncate();

DROP TRIGGER IF EXISTS ka_gochara_rule_path_seal_immutable ON public.ka_gochara_rule_path_seal;
CREATE TRIGGER ka_gochara_rule_path_seal_immutable
  BEFORE UPDATE OR DELETE ON public.ka_gochara_rule_path_seal
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_insert_only('F3 — a seal is permanent');
DROP TRIGGER IF EXISTS ka_gochara_rule_path_seal_no_truncate ON public.ka_gochara_rule_path_seal;
CREATE TRIGGER ka_gochara_rule_path_seal_no_truncate
  BEFORE TRUNCATE ON public.ka_gochara_rule_path_seal
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_refuse_truncate();

-- ── 5. Post-DDL verification (F9): helper self-tests, then definitions ────
DO $$
BEGIN
  IF NOT (public.ka_gochara_frame_ok('graha', NULL) IS FALSE
          AND public.ka_gochara_frame_ok('bhavat_bhavam', NULL) IS FALSE
          AND public.ka_gochara_frame_ok(NULL, NULL) IS FALSE
          AND public.ka_gochara_frame_ok('bhavat_bhavam', '13') IS FALSE
          AND public.ka_gochara_frame_ok('bhavat_bhavam', '9') IS TRUE
          AND public.ka_gochara_frame_ok('moon', 'x') IS FALSE
          AND public.ka_gochara_frame_ok('moon', NULL) IS TRUE
          AND public.ka_gochara_frame_ok('graha', 'pluto') IS FALSE
          AND public.ka_gochara_frame_ok('graha', 'saturn') IS TRUE
          AND public.ka_gochara_named_operands_ok(NULL) IS FALSE
          AND public.ka_gochara_named_operands_ok('{}'::jsonb) IS FALSE
          AND public.ka_gochara_named_operands_ok('{"a":"free prose here"}'::jsonb) IS FALSE
          AND public.ka_gochara_named_operands_ok('{"a":""}'::jsonb) IS FALSE
          AND public.ka_gochara_named_operands_ok('{"a":null}'::jsonb) IS FALSE
          AND public.ka_gochara_named_operands_ok('{"a":true}'::jsonb) IS FALSE
          AND public.ka_gochara_named_operands_ok('{"a":[]}'::jsonb) IS FALSE
          AND public.ka_gochara_named_operands_ok('{"orb":3.0,"left":"chart_facts.graha_position:mars","set":["sign:aries","sign:leo"]}'::jsonb) IS TRUE
          AND public.ka_gochara_string_array_ok('[null]'::jsonb) IS FALSE
          AND public.ka_gochara_string_array_ok('["a b"]'::jsonb) IS FALSE
          AND public.ka_gochara_string_array_ok(NULL) IS FALSE
          AND public.ka_gochara_vocab_array_ok('[]'::jsonb, ARRAY['x']) IS FALSE
          AND public.ka_gochara_object_selector_ok('[]'::jsonb) IS FALSE
          AND public.ka_gochara_object_selector_ok('[{"agent":"pluto","relation":"aspect","object_role":"lord"}]'::jsonb) IS FALSE
          AND public.ka_gochara_object_selector_ok('[{"agent":"mars","relation":"aspect","object_role":"lord","extra":1}]'::jsonb) IS FALSE
          AND public.ka_gochara_object_selector_consistent_ok('[{"agent":"mars","relation":"aspect","object_role":"lord"}]'::jsonb, '["saturn"]'::jsonb, '["aspect"]'::jsonb) IS FALSE
          AND public.ka_gochara_object_selector_consistent_ok('[{"agent":"mars","relation":"aspect","object_role":"lord"}]'::jsonb, '["mars"]'::jsonb, '["aspect"]'::jsonb) IS TRUE) THEN
    RAISE EXCEPTION 'migration 1154 post-DDL verification failed (amendment 8): helper self-test failed';
  END IF;
END;
$$;

DO $$
BEGIN
  PERFORM public.ka_gochara_verify_definitions('1154', $expected$
{
  "functions": {
    "ka_gochara_frame_ok(text,text)": [
      "boolean",
      "i",
      "sql",
      false,
      "f"
    ],
    "ka_gochara_membership_guard()": [
      "trigger",
      "v",
      "plpgsql",
      false,
      "f"
    ],
    "ka_gochara_named_operands_ok(jsonb)": [
      "boolean",
      "i",
      "sql",
      false,
      "f"
    ],
    "ka_gochara_object_selector_consistent_ok(jsonb,jsonb,jsonb)": [
      "boolean",
      "i",
      "sql",
      false,
      "f"
    ],
    "ka_gochara_object_selector_ok(jsonb)": [
      "boolean",
      "i",
      "sql",
      false,
      "f"
    ],
    "ka_gochara_require_sealed_rule_path()": [
      "trigger",
      "v",
      "plpgsql",
      false,
      "f"
    ],
    "ka_gochara_selector_token_ok(text)": [
      "boolean",
      "i",
      "sql",
      false,
      "f"
    ],
    "ka_gochara_string_array_ok(jsonb)": [
      "boolean",
      "i",
      "sql",
      false,
      "f"
    ],
    "ka_gochara_vocab_array_ok(jsonb,text[])": [
      "boolean",
      "i",
      "sql",
      false,
      "f"
    ]
  },
  "tables": {
    "ka_gochara_factor": {
      "columns": {
        "calibration_status": [
          "text",
          true
        ],
        "category_mapping": [
          "jsonb",
          false
        ],
        "created_at": [
          "timestamp with time zone",
          true
        ],
        "direction": [
          "text",
          true
        ],
        "doctrine_ordering": [
          "jsonb",
          false
        ],
        "effect": [
          "text",
          true
        ],
        "factor_id": [
          "text",
          true
        ],
        "function": [
          "text",
          true
        ],
        "null_state": [
          "text",
          true
        ],
        "operand_selector": [
          "jsonb",
          true
        ],
        "range_lower": [
          "real",
          true
        ],
        "range_upper": [
          "real",
          true
        ],
        "rule_version": [
          "text",
          true
        ],
        "units": [
          "text",
          true
        ]
      },
      "constraints": {
        "ka_gochara_factor_pkey": [
          "p",
          "primarykeyfactor_id,rule_version",
          true
        ],
        "kgf_calibrated_requires_mapping_ck": [
          "c",
          "checkcalibration_status<>'calibrated'orcategory_mappingisnotnull",
          true
        ],
        "kgf_calibration_status_ck": [
          "c",
          "checkcalibration_status=anyarray['uncalibrated_default','calibrated']",
          true
        ],
        "kgf_category_mapping_shape_ck": [
          "c",
          "checkcategory_mappingisnullorjsonb_typeofcategory_mapping='object'andcategory_mapping<>'{}'",
          true
        ],
        "kgf_direction_ck": [
          "c",
          "checkdirection=anyarray['higher_stronger','lower_stronger']",
          true
        ],
        "kgf_doctrine_ordering_shape_ck": [
          "c",
          "checkdoctrine_orderingisnullorka_gochara_string_array_okdoctrine_orderingistrueandjsonb_array_lengthdoctrine_ordering>=1",
          true
        ],
        "kgf_effect_nonblank_ck": [
          "c",
          "checkbtrimeffect<>''",
          true
        ],
        "kgf_function_nonblank_ck": [
          "c",
          "checkbtrimfunction<>''",
          true
        ],
        "kgf_ids_nonblank_ck": [
          "c",
          "checkbtrimfactor_id<>''andbtrimrule_version<>''",
          true
        ],
        "kgf_null_state_ck": [
          "c",
          "checknull_state=anyarray['omit','unqualified']",
          true
        ],
        "kgf_operand_selector_typed_ck": [
          "c",
          "checkka_gochara_named_operands_okoperand_selectoristrue",
          true
        ],
        "kgf_range_unit_interval_ck": [
          "c",
          "checkka_gochara_finite_okrange_loweristrueandka_gochara_finite_okrange_upperistrueandrange_lower>=0andrange_lower<=range_upperandrange_upper<=1",
          true
        ],
        "kgf_units_ck": [
          "c",
          "checkunits=anyarray['degrees','days','count','unitless']",
          true
        ]
      },
      "indexes": {
        "ka_gochara_factor_pkey": "createuniqueindexka_gochara_factor_pkeyonka_gochara_factorusingbtreefactor_id,rule_version"
      },
      "triggers": {
        "ka_gochara_factor_immutable": [
          "createtriggerka_gochara_factor_immutablebeforedeleteorupdateonka_gochara_factorforeachrowexecutefunctionka_gochara_insert_only'§2.1amendment1—afactorchangeisanewrule_versionrow'",
          "O"
        ],
        "ka_gochara_factor_no_truncate": [
          "createtriggerka_gochara_factor_no_truncatebeforetruncateonka_gochara_factorforeachstatementexecutefunctionka_gochara_refuse_truncate",
          "O"
        ]
      }
    },
    "ka_gochara_predicate": {
      "columns": {
        "created_at": [
          "timestamp with time zone",
          true
        ],
        "operands": [
          "jsonb",
          true
        ],
        "operator": [
          "text",
          true
        ],
        "predicate_id": [
          "text",
          true
        ],
        "rule_version": [
          "text",
          true
        ],
        "unknown_is_false": [
          "boolean",
          true
        ]
      },
      "constraints": {
        "ka_gochara_predicate_pkey": [
          "p",
          "primarykeypredicate_id,rule_version",
          true
        ],
        "kgp_ids_nonblank_ck": [
          "c",
          "checkbtrimpredicate_id<>''andbtrimrule_version<>''",
          true
        ],
        "kgp_operands_typed_ck": [
          "c",
          "checkka_gochara_named_operands_okoperandsistrue",
          true
        ],
        "kgp_operator_ck": [
          "c",
          "checkoperator=anyarray['eq','in_set','within_orb','house_from','overlaps','period_running_at','declaration_exists']",
          true
        ],
        "kgp_unknown_is_false_ck": [
          "c",
          "checkunknown_is_false=false",
          true
        ]
      },
      "indexes": {
        "ka_gochara_predicate_pkey": "createuniqueindexka_gochara_predicate_pkeyonka_gochara_predicateusingbtreepredicate_id,rule_version"
      },
      "triggers": {
        "ka_gochara_predicate_immutable": [
          "createtriggerka_gochara_predicate_immutablebeforedeleteorupdateonka_gochara_predicateforeachrowexecutefunctionka_gochara_insert_only'§2.1amendment1—apredicatechangeisanewrule_versionrow'",
          "O"
        ],
        "ka_gochara_predicate_no_truncate": [
          "createtriggerka_gochara_predicate_no_truncatebeforetruncateonka_gochara_predicateforeachstatementexecutefunctionka_gochara_refuse_truncate",
          "O"
        ]
      }
    },
    "ka_gochara_rule_path": {
      "columns": {
        "agent_set": [
          "jsonb",
          true
        ],
        "created_at": [
          "timestamp with time zone",
          true
        ],
        "frame_arg": [
          "text",
          false
        ],
        "frame_kind": [
          "text",
          true
        ],
        "object_selector": [
          "jsonb",
          true
        ],
        "operator_role": [
          "text",
          true
        ],
        "path_id": [
          "text",
          true
        ],
        "provenance": [
          "text",
          true
        ],
        "relation_set": [
          "jsonb",
          true
        ],
        "rule_version": [
          "text",
          true
        ],
        "ruling_ref": [
          "text",
          false
        ],
        "score_rule": [
          "text",
          true
        ]
      },
      "constraints": {
        "ka_gochara_rule_path_pkey": [
          "p",
          "primarykeypath_id,rule_version",
          true
        ],
        "kgrp_agent_set_ck": [
          "c",
          "checkka_gochara_vocab_array_okagent_set,array['sun','moon','mars','mercury','jupiter','venus','saturn','rahu','ketu']istrue",
          true
        ],
        "kgrp_frame_ck": [
          "c",
          "checkka_gochara_frame_okframe_kind,frame_argistrue",
          true
        ],
        "kgrp_ids_nonblank_ck": [
          "c",
          "checkbtrimpath_id<>''andbtrimrule_version<>''",
          true
        ],
        "kgrp_object_selector_ck": [
          "c",
          "checkka_gochara_object_selector_consistent_okobject_selector,agent_set,relation_setistrue",
          true
        ],
        "kgrp_operator_role_ck": [
          "c",
          "checkoperator_role=anyarray['scored','testimony']",
          true
        ],
        "kgrp_provenance_ck": [
          "c",
          "checkprovenance=anyarray['verse_cited','uncited_extension']",
          true
        ],
        "kgrp_relation_set_ck": [
          "c",
          "checkka_gochara_vocab_array_okrelation_set,array['residence','aspect','conjunction','dispositorship','association','ownership','occupancy','period_running']istrue",
          true
        ],
        "kgrp_ruling_ck": [
          "c",
          "checkprovenance<>'uncited_extension'orruling_refisnotnull",
          true
        ],
        "kgrp_score_rule_nonblank_ck": [
          "c",
          "checkbtrimscore_rule<>''",
          true
        ]
      },
      "indexes": {
        "ka_gochara_rule_path_pkey": "createuniqueindexka_gochara_rule_path_pkeyonka_gochara_rule_pathusingbtreepath_id,rule_version"
      },
      "triggers": {
        "ka_gochara_rule_path_immutable": [
          "createtriggerka_gochara_rule_path_immutablebeforedeleteorupdateonka_gochara_rule_pathforeachrowexecutefunctionka_gochara_insert_only'§2.1amendment1—apathchangeisanewrule_versionrow'",
          "O"
        ],
        "ka_gochara_rule_path_no_truncate": [
          "createtriggerka_gochara_rule_path_no_truncatebeforetruncateonka_gochara_rule_pathforeachstatementexecutefunctionka_gochara_refuse_truncate",
          "O"
        ]
      }
    },
    "ka_gochara_rule_path_prerequisite": {
      "columns": {
        "ordinal": [
          "integer",
          true
        ],
        "path_id": [
          "text",
          true
        ],
        "predicate_id": [
          "text",
          true
        ],
        "predicate_rule_version": [
          "text",
          true
        ],
        "rule_version": [
          "text",
          true
        ]
      },
      "constraints": {
        "ka_gochara_rule_path_prerequisite_pkey": [
          "p",
          "primarykeypath_id,rule_version,ordinal",
          true
        ],
        "kgrpp_no_dup_uq": [
          "u",
          "uniquepath_id,rule_version,predicate_id,predicate_rule_version",
          true
        ],
        "kgrpp_ordinal_ck": [
          "c",
          "checkordinal>=1",
          true
        ],
        "kgrpp_path_fk": [
          "f",
          "foreignkeypath_id,rule_versionreferenceska_gochara_rule_pathpath_id,rule_version",
          true
        ],
        "kgrpp_predicate_fk": [
          "f",
          "foreignkeypredicate_id,predicate_rule_versionreferenceska_gochara_predicatepredicate_id,rule_version",
          true
        ]
      },
      "indexes": {
        "ka_gochara_rule_path_prerequisite_pkey": "createuniqueindexka_gochara_rule_path_prerequisite_pkeyonka_gochara_rule_path_prerequisiteusingbtreepath_id,rule_version,ordinal",
        "kgrpp_no_dup_uq": "createuniqueindexkgrpp_no_dup_uqonka_gochara_rule_path_prerequisiteusingbtreepath_id,rule_version,predicate_id,predicate_rule_version"
      },
      "triggers": {
        "ka_gochara_rp_prereq_immutable": [
          "createtriggerka_gochara_rp_prereq_immutablebeforedeleteorupdateonka_gochara_rule_path_prerequisiteforeachrowexecutefunctionka_gochara_insert_only'§2.1amendment1—amembershipchangeridesanewrule_version'",
          "O"
        ],
        "ka_gochara_rp_prereq_no_truncate": [
          "createtriggerka_gochara_rp_prereq_no_truncatebeforetruncateonka_gochara_rule_path_prerequisiteforeachstatementexecutefunctionka_gochara_refuse_truncate",
          "O"
        ],
        "ka_gochara_rp_prereq_sealed_check": [
          "createtriggerka_gochara_rp_prereq_sealed_checkbeforeinsertonka_gochara_rule_path_prerequisiteforeachrowexecutefunctionka_gochara_membership_guard",
          "O"
        ]
      }
    },
    "ka_gochara_rule_path_seal": {
      "columns": {
        "path_id": [
          "text",
          true
        ],
        "rule_version": [
          "text",
          true
        ],
        "sealed_at": [
          "timestamp with time zone",
          true
        ]
      },
      "constraints": {
        "ka_gochara_rule_path_seal_pkey": [
          "p",
          "primarykeypath_id,rule_version",
          true
        ],
        "kgrpseal_path_fk": [
          "f",
          "foreignkeypath_id,rule_versionreferenceska_gochara_rule_pathpath_id,rule_version",
          true
        ]
      },
      "indexes": {
        "ka_gochara_rule_path_seal_pkey": "createuniqueindexka_gochara_rule_path_seal_pkeyonka_gochara_rule_path_sealusingbtreepath_id,rule_version"
      },
      "triggers": {
        "ka_gochara_rule_path_seal_immutable": [
          "createtriggerka_gochara_rule_path_seal_immutablebeforedeleteorupdateonka_gochara_rule_path_sealforeachrowexecutefunctionka_gochara_insert_only'f3—asealispermanent'",
          "O"
        ],
        "ka_gochara_rule_path_seal_no_truncate": [
          "createtriggerka_gochara_rule_path_seal_no_truncatebeforetruncateonka_gochara_rule_path_sealforeachstatementexecutefunctionka_gochara_refuse_truncate",
          "O"
        ]
      }
    },
    "ka_gochara_rule_path_soft_factor": {
      "columns": {
        "factor_id": [
          "text",
          true
        ],
        "factor_rule_version": [
          "text",
          true
        ],
        "path_id": [
          "text",
          true
        ],
        "rule_version": [
          "text",
          true
        ]
      },
      "constraints": {
        "ka_gochara_rule_path_soft_factor_pkey": [
          "p",
          "primarykeypath_id,rule_version,factor_id,factor_rule_version",
          true
        ],
        "kgrps_factor_fk": [
          "f",
          "foreignkeyfactor_id,factor_rule_versionreferenceska_gochara_factorfactor_id,rule_version",
          true
        ],
        "kgrps_path_fk": [
          "f",
          "foreignkeypath_id,rule_versionreferenceska_gochara_rule_pathpath_id,rule_version",
          true
        ]
      },
      "indexes": {
        "ka_gochara_rule_path_soft_factor_pkey": "createuniqueindexka_gochara_rule_path_soft_factor_pkeyonka_gochara_rule_path_soft_factorusingbtreepath_id,rule_version,factor_id,factor_rule_version"
      },
      "triggers": {
        "ka_gochara_rp_soft_factor_immutable": [
          "createtriggerka_gochara_rp_soft_factor_immutablebeforedeleteorupdateonka_gochara_rule_path_soft_factorforeachrowexecutefunctionka_gochara_insert_only'§2.1amendment1—amembershipchangeridesanewrule_version'",
          "O"
        ],
        "ka_gochara_rp_soft_factor_no_truncate": [
          "createtriggerka_gochara_rp_soft_factor_no_truncatebeforetruncateonka_gochara_rule_path_soft_factorforeachstatementexecutefunctionka_gochara_refuse_truncate",
          "O"
        ],
        "ka_gochara_rp_soft_factor_sealed_check": [
          "createtriggerka_gochara_rp_soft_factor_sealed_checkbeforeinsertonka_gochara_rule_path_soft_factorforeachrowexecutefunctionka_gochara_membership_guard",
          "O"
        ]
      }
    }
  }
}
$expected$::jsonb);
END;
$$;
