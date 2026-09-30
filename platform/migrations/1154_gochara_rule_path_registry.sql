-- Migration 1154: ka_gochara rule-path registries — rule_path, predicate,
--                 factor, the NORMALISED ordered version-bound membership
--                 tables, and the rule-version SEAL that makes a complete
--                 rule definition immutable after construction (F3), all
--                 serialised under the orchestrator's global-assets lock (N5).
--                 Round-4 rewrite per ASTRA_REVIEW_A5_1_MIGRATIONS v1_2 under
--                 the steward's simplification ruling. Depends on 1153.
--                 1153–1157 were never applied anywhere — in-place rewrite.
-- Created: 2026-09-30. Author: pravaha/a5-migrations (Stream A, A5.1).
--
-- Numbering: 1154 sits inside this lane's granted block (1150–1159 per
-- ADK-0026 §4). Verified free by a fresh scan of every origin/* ref across
-- BOTH migration directories (2026-09-30). `npm run guard:migration-numbers`
-- green.
--
-- Transaction ownership: NO BEGIN/COMMIT — migrate.ts owns ONE transaction
-- (see the 1153 header). Gate: pinned schema → preflight gate (byte-identical
-- to preflight_1154_rule_path_registry.sql; real preconditions only) → DDL →
-- presence checks. Deploy route: the protected public-schema window
-- (deploy.yml `gochara_contracts_schema_migration`).
--
-- ── F3 + N5 — rule-version completion, serialised (steward ruling 2) ─────
-- prerequisites / soft_factors are membership rows with real composite FKs.
-- A version is CONSTRUCTED (rule_path row + membership rows) and then SEALED
-- (ka_gochara_rule_path_seal row). Every write to the registries, the
-- memberships and the seal FIRST takes pg_advisory_xact_lock on the
-- orchestrator's global-assets key (hashtext('nirmana-global-assets')) and
-- only then reads seal state, so:
--   * a membership INSERT and a seal INSERT for the same version SERIALISE:
--     whichever commits first wins — a seal committed first refuses the
--     later membership; a membership committed first is part of the sealed
--     definition; neither can interleave (N5 both orders);
--   * a record/window produced against a version (1155/1156's
--     ka_gochara_require_sealed_rule_path, which takes the chart lock and
--     then this lock) waits for any in-flight construction and then sees the
--     committed seal state — production against an unsealed version is
--     refused (N5's "record production before the membership commits");
--   * UPDATE/DELETE were never allowed (insert-only), TRUNCATE is refused.
--
-- ── F6 — factor discipline exactly as the binding C2 ruling (kept) ───────
-- range ⊆ [0,1] (finite); calibration_status NOT NULL ∈ {uncalibrated_default,
-- calibrated}; calibrated ⇒ category_mapping present. An uncalibrated row MAY
-- carry an authored default mapping; doctrine_ordering is optional.
--
-- ── F5/F11 — total validators and the declared selector encoding (kept) ──
-- Every helper returns a total boolean and every CHECK asks `… IS TRUE`.
-- Selector token: `^[a-z][a-z0-9_]*([.:/][a-z0-9_]+)*$`; an operand object
-- maps identifier keys to a token, a non-empty array of tokens, or a number.
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
    WHERE n.nspname = 'public'
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
    WHERE n.nspname = 'public' AND NOT t.tgisinternal
      AND ( (c.relname = 'ka_gochara_predicate'
               AND t.tgname IN ('ka_gochara_predicate_write_guard', 'ka_gochara_predicate_no_truncate'))
         OR (c.relname = 'ka_gochara_factor'
               AND t.tgname IN ('ka_gochara_factor_write_guard', 'ka_gochara_factor_no_truncate'))
         OR (c.relname = 'ka_gochara_rule_path'
               AND t.tgname IN ('ka_gochara_rule_path_write_guard', 'ka_gochara_rule_path_no_truncate'))
         OR (c.relname = 'ka_gochara_rule_path_prerequisite'
               AND t.tgname IN ('ka_gochara_rp_prereq_sealed_check', 'ka_gochara_rp_prereq_write_guard',
                                'ka_gochara_rp_prereq_no_truncate'))
         OR (c.relname = 'ka_gochara_rule_path_soft_factor'
               AND t.tgname IN ('ka_gochara_rp_soft_factor_sealed_check', 'ka_gochara_rp_soft_factor_write_guard',
                                'ka_gochara_rp_soft_factor_no_truncate'))
         OR (c.relname = 'ka_gochara_rule_path_seal'
               AND t.tgname IN ('ka_gochara_rule_path_seal_write_guard', 'ka_gochara_rule_path_seal_no_truncate')) )
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
    WHERE (SELECT COALESCE(array_agg(format_type(u.oid, NULL) ORDER BY u.ord), '{}')
           FROM unnest(p.proargtypes) WITH ORDINALITY AS u(oid, ord)) = e.argtypes
    UNION ALL
    -- shared helpers from 1153 must be present with their exact signatures
    SELECT 'helper_function_missing', e.sig
    FROM (VALUES ('ka_gochara_refuse_truncate()'),
                 ('ka_gochara_global_write_guard()'),
                 ('ka_gochara_lock_global()'),
                 ('ka_gochara_lock_chart(uuid)'),
                 ('ka_gochara_finite_ok(double precision)')) AS e(sig)
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
    WHERE to_regclass('public._migrations_applied') IS NOT NULL
      AND starts_with(m.filename, '1154_')
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

-- ── 0. Typed helpers — TOTAL booleans (F5), declared encodings (F11) ──────

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

CREATE OR REPLACE FUNCTION public.ka_gochara_selector_token_ok(t text)
RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
  SELECT t IS NOT NULL AND t ~ '^[a-z][a-z0-9_]*([.:/][a-z0-9_]+)*$';
$$;

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

CREATE OR REPLACE FUNCTION public.ka_gochara_vocab_array_ok(j jsonb, vocab text[])
RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
  SELECT public.ka_gochara_string_array_ok(j)
     AND jsonb_array_length(j) >= 1
     AND NOT EXISTS (
       SELECT 1 FROM jsonb_array_elements_text(j) v
       WHERE v <> ALL (vocab)
     );
$$;

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
    -- §2.1/§2.2 inv 2: unknown ≠ false
  CONSTRAINT kgp_operands_typed_ck CHECK (public.ka_gochara_named_operands_ok(operands) IS TRUE)
);

COMMENT ON TABLE public.ka_gochara_predicate IS
  'Predicate registry (GOCHARA_DESIGN_SPECS_v1_4 §2.1): composite (predicate_id, '
  'rule_version) PK; states {true|false|unknown} are evaluator semantics; '
  'unknown_is_false pinned false. Insert-only under the global-assets lock; TRUNCATE refused.';

DROP TRIGGER IF EXISTS ka_gochara_predicate_write_guard ON public.ka_gochara_predicate;
CREATE TRIGGER ka_gochara_predicate_write_guard
  BEFORE INSERT OR UPDATE OR DELETE ON public.ka_gochara_predicate
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_global_write_guard('§2.1 amendment 1 — a predicate change is a new rule_version row');
DROP TRIGGER IF EXISTS ka_gochara_predicate_no_truncate ON public.ka_gochara_predicate;
CREATE TRIGGER ka_gochara_predicate_no_truncate
  BEFORE TRUNCATE ON public.ka_gochara_predicate
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_refuse_truncate();

-- ── 2. factor (§2.1; C2 as ruled — F6) ────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.ka_gochara_factor (
  factor_id          TEXT NOT NULL,
  rule_version       TEXT NOT NULL,
  operand_selector   JSONB NOT NULL,
  direction          TEXT NOT NULL,
  function           TEXT NOT NULL,
  range_lower        REAL NOT NULL,
  range_upper        REAL NOT NULL,
  units              TEXT NOT NULL,
  calibration_status TEXT NOT NULL DEFAULT 'uncalibrated_default',
  doctrine_ordering  JSONB,
  category_mapping   JSONB,
  null_state         TEXT NOT NULL,
  effect             TEXT NOT NULL,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),

  PRIMARY KEY (factor_id, rule_version),
  CONSTRAINT kgf_ids_nonblank_ck CHECK (btrim(factor_id) <> '' AND btrim(rule_version) <> ''),
  CONSTRAINT kgf_function_nonblank_ck CHECK (btrim(function) <> ''),
  CONSTRAINT kgf_effect_nonblank_ck CHECK (btrim(effect) <> ''),
  CONSTRAINT kgf_direction_ck CHECK (direction IN ('higher_stronger','lower_stronger')),
  CONSTRAINT kgf_units_ck CHECK (units IN ('degrees','days','count','unitless')),
  CONSTRAINT kgf_calibration_status_ck CHECK (calibration_status IN
    ('uncalibrated_default','calibrated')),
  CONSTRAINT kgf_null_state_ck CHECK (null_state IN ('omit','unqualified')),
  CONSTRAINT kgf_range_unit_interval_ck
    CHECK (public.ka_gochara_finite_ok(range_lower) IS TRUE
           AND public.ka_gochara_finite_ok(range_upper) IS TRUE
           AND range_lower >= 0 AND range_lower <= range_upper AND range_upper <= 1),
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
    -- D-SPECS C2 (F6): calibrated rows CARRY a mapping; nothing more is imposed
);

COMMENT ON TABLE public.ka_gochara_factor IS
  'Soft-factor registry (GOCHARA_DESIGN_SPECS_v1_4 §2.1): composite (factor_id, '
  'rule_version) PK. Codomain ⊆ [0,1]. Calibration discipline exactly per D-SPECS C2 (F6). '
  'Insert-only under the global-assets lock; TRUNCATE refused.';

DROP TRIGGER IF EXISTS ka_gochara_factor_write_guard ON public.ka_gochara_factor;
CREATE TRIGGER ka_gochara_factor_write_guard
  BEFORE INSERT OR UPDATE OR DELETE ON public.ka_gochara_factor
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_global_write_guard('§2.1 amendment 1 — a factor change is a new rule_version row');
DROP TRIGGER IF EXISTS ka_gochara_factor_no_truncate ON public.ka_gochara_factor;
CREATE TRIGGER ka_gochara_factor_no_truncate
  BEFORE TRUNCATE ON public.ka_gochara_factor
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_refuse_truncate();

-- ── 3. rule_path (§2.1) ────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.ka_gochara_rule_path (
  path_id           TEXT NOT NULL,
  rule_version      TEXT NOT NULL,
  frame_kind        TEXT NOT NULL,
  frame_arg         TEXT,
  agent_set         JSONB NOT NULL,
  relation_set      JSONB NOT NULL,
  object_selector   JSONB NOT NULL,
  provenance        TEXT NOT NULL,
  operator_role     TEXT NOT NULL,
  ruling_ref        TEXT,
  score_rule        TEXT NOT NULL,
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
  CONSTRAINT kgrp_provenance_ck CHECK (provenance IN ('verse_cited','uncited_extension')),
  CONSTRAINT kgrp_operator_role_ck CHECK (operator_role IN ('scored','testimony')),
  CONSTRAINT kgrp_ruling_ck
    CHECK (provenance <> 'uncited_extension' OR ruling_ref IS NOT NULL)
    -- §0/S:110 as frozen: uncited_extension REQUIRES a ruling_ref; never forbidden otherwise
);

COMMENT ON TABLE public.ka_gochara_rule_path IS
  'Rule-path registry (GOCHARA_DESIGN_SPECS_v1_4 §2.1): composite (path_id, rule_version) '
  'PK. prerequisites/soft_factors are NORMALISED into membership tables with real '
  'composite FKs; a version is complete once its ka_gochara_rule_path_seal row exists (F3), '
  'all under the orchestrator''s global-assets lock (N5). Insert-only; TRUNCATE refused.';

DROP TRIGGER IF EXISTS ka_gochara_rule_path_write_guard ON public.ka_gochara_rule_path;
CREATE TRIGGER ka_gochara_rule_path_write_guard
  BEFORE INSERT OR UPDATE OR DELETE ON public.ka_gochara_rule_path
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_global_write_guard('§2.1 amendment 1 — a path change is a new rule_version row');
DROP TRIGGER IF EXISTS ka_gochara_rule_path_no_truncate ON public.ka_gochara_rule_path;
CREATE TRIGGER ka_gochara_rule_path_no_truncate
  BEFORE TRUNCATE ON public.ka_gochara_rule_path
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_refuse_truncate();

-- ── 4. Membership tables + the completion seal (F3/N5) ────────────────────

CREATE TABLE IF NOT EXISTS public.ka_gochara_rule_path_prerequisite (
  path_id                TEXT NOT NULL,
  rule_version           TEXT NOT NULL,
  ordinal                INTEGER NOT NULL,
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

CREATE TABLE IF NOT EXISTS public.ka_gochara_rule_path_seal (
  path_id      TEXT NOT NULL,
  rule_version TEXT NOT NULL,
  sealed_at    TIMESTAMPTZ NOT NULL DEFAULT now(),

  PRIMARY KEY (path_id, rule_version),
  CONSTRAINT kgrpseal_path_fk FOREIGN KEY (path_id, rule_version)
    REFERENCES public.ka_gochara_rule_path (path_id, rule_version)
);

COMMENT ON TABLE public.ka_gochara_rule_path_seal IS
  'Rule-version completion boundary (F3/N5): after this row exists no prerequisite/'
  'soft-factor row can be added to the version, and only sealed versions may be referenced '
  'by records/windows. Written and read under the orchestrator''s global-assets lock, so '
  'sealing and membership construction serialise in both orders. Insert-only; TRUNCATE refused.';

-- Membership INSERT: lock first, THEN read the seal (N5).
CREATE OR REPLACE FUNCTION public.ka_gochara_membership_guard()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
BEGIN
  PERFORM public.ka_gochara_lock_global();
  IF EXISTS (SELECT 1 FROM public.ka_gochara_rule_path_seal s
             WHERE s.path_id = NEW.path_id AND s.rule_version = NEW.rule_version) THEN
    RAISE EXCEPTION '% refused (F3 / GOCHARA_DESIGN_SPECS_v1_4 §2.1): rule version (%, %) is SEALED — its membership is complete and immutable; a definition change is a NEW rule_version',
      TG_TABLE_NAME, NEW.path_id, NEW.rule_version;
  END IF;
  RETURN NEW;
END;
$$;

-- Used by 1155/1156 (after the chart lock): lock global, THEN read the seal.
CREATE OR REPLACE FUNCTION public.ka_gochara_require_sealed_rule_path()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
BEGIN
  PERFORM public.ka_gochara_lock_global();
  IF NOT EXISTS (SELECT 1 FROM public.ka_gochara_rule_path_seal s
                 WHERE s.path_id = NEW.path_id AND s.rule_version = NEW.rule_version) THEN
    RAISE EXCEPTION '% refused (F3/N5): rule version (%, %) is not sealed — only a completed (sealed) rule version may produce records or windows',
      TG_TABLE_NAME, NEW.path_id, NEW.rule_version;
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS ka_gochara_rp_prereq_sealed_check ON public.ka_gochara_rule_path_prerequisite;
CREATE TRIGGER ka_gochara_rp_prereq_sealed_check
  BEFORE INSERT ON public.ka_gochara_rule_path_prerequisite
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_membership_guard();
DROP TRIGGER IF EXISTS ka_gochara_rp_prereq_write_guard ON public.ka_gochara_rule_path_prerequisite;
CREATE TRIGGER ka_gochara_rp_prereq_write_guard
  BEFORE UPDATE OR DELETE ON public.ka_gochara_rule_path_prerequisite
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_global_write_guard('§2.1 amendment 1 — a membership change rides a new rule_version');
DROP TRIGGER IF EXISTS ka_gochara_rp_prereq_no_truncate ON public.ka_gochara_rule_path_prerequisite;
CREATE TRIGGER ka_gochara_rp_prereq_no_truncate
  BEFORE TRUNCATE ON public.ka_gochara_rule_path_prerequisite
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_refuse_truncate();

DROP TRIGGER IF EXISTS ka_gochara_rp_soft_factor_sealed_check ON public.ka_gochara_rule_path_soft_factor;
CREATE TRIGGER ka_gochara_rp_soft_factor_sealed_check
  BEFORE INSERT ON public.ka_gochara_rule_path_soft_factor
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_membership_guard();
DROP TRIGGER IF EXISTS ka_gochara_rp_soft_factor_write_guard ON public.ka_gochara_rule_path_soft_factor;
CREATE TRIGGER ka_gochara_rp_soft_factor_write_guard
  BEFORE UPDATE OR DELETE ON public.ka_gochara_rule_path_soft_factor
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_global_write_guard('§2.1 amendment 1 — a membership change rides a new rule_version');
DROP TRIGGER IF EXISTS ka_gochara_rp_soft_factor_no_truncate ON public.ka_gochara_rule_path_soft_factor;
CREATE TRIGGER ka_gochara_rp_soft_factor_no_truncate
  BEFORE TRUNCATE ON public.ka_gochara_rule_path_soft_factor
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_refuse_truncate();

DROP TRIGGER IF EXISTS ka_gochara_rule_path_seal_write_guard ON public.ka_gochara_rule_path_seal;
CREATE TRIGGER ka_gochara_rule_path_seal_write_guard
  BEFORE INSERT OR UPDATE OR DELETE ON public.ka_gochara_rule_path_seal
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_global_write_guard('F3 — a seal is permanent');
DROP TRIGGER IF EXISTS ka_gochara_rule_path_seal_no_truncate ON public.ka_gochara_rule_path_seal;
CREATE TRIGGER ka_gochara_rule_path_seal_no_truncate
  BEFORE TRUNCATE ON public.ka_gochara_rule_path_seal
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_refuse_truncate();

-- ── 5. Post-apply PRESENCE checks (steward ruling 3) + helper self-tests ───
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
    RAISE EXCEPTION 'migration 1154 post-apply check failed: helper self-test failed';
  END IF;
END;
$$;

DO $$
DECLARE missing text;
BEGIN
  SELECT string_agg(t, ', ' ORDER BY t) INTO missing
  FROM unnest(ARRAY['ka_gochara_predicate','ka_gochara_factor','ka_gochara_rule_path',
                    'ka_gochara_rule_path_prerequisite','ka_gochara_rule_path_soft_factor',
                    'ka_gochara_rule_path_seal']) t
  WHERE to_regclass('public.' || t) IS NULL;
  IF missing IS NOT NULL THEN
    RAISE EXCEPTION 'migration 1154 post-apply check failed: missing table: %', missing;
  END IF;

  WITH expected(conrelid, conname) AS (VALUES
      ('ka_gochara_predicate','ka_gochara_predicate_pkey'),
      ('ka_gochara_predicate','kgp_ids_nonblank_ck'),
      ('ka_gochara_predicate','kgp_operator_ck'),
      ('ka_gochara_predicate','kgp_unknown_is_false_ck'),
      ('ka_gochara_predicate','kgp_operands_typed_ck'),
      ('ka_gochara_factor','ka_gochara_factor_pkey'),
      ('ka_gochara_factor','kgf_ids_nonblank_ck'),
      ('ka_gochara_factor','kgf_function_nonblank_ck'),
      ('ka_gochara_factor','kgf_effect_nonblank_ck'),
      ('ka_gochara_factor','kgf_direction_ck'),
      ('ka_gochara_factor','kgf_units_ck'),
      ('ka_gochara_factor','kgf_calibration_status_ck'),
      ('ka_gochara_factor','kgf_null_state_ck'),
      ('ka_gochara_factor','kgf_range_unit_interval_ck'),
      ('ka_gochara_factor','kgf_operand_selector_typed_ck'),
      ('ka_gochara_factor','kgf_doctrine_ordering_shape_ck'),
      ('ka_gochara_factor','kgf_category_mapping_shape_ck'),
      ('ka_gochara_factor','kgf_calibrated_requires_mapping_ck'),
      ('ka_gochara_rule_path','ka_gochara_rule_path_pkey'),
      ('ka_gochara_rule_path','kgrp_ids_nonblank_ck'),
      ('ka_gochara_rule_path','kgrp_score_rule_nonblank_ck'),
      ('ka_gochara_rule_path','kgrp_frame_ck'),
      ('ka_gochara_rule_path','kgrp_agent_set_ck'),
      ('ka_gochara_rule_path','kgrp_relation_set_ck'),
      ('ka_gochara_rule_path','kgrp_object_selector_ck'),
      ('ka_gochara_rule_path','kgrp_provenance_ck'),
      ('ka_gochara_rule_path','kgrp_operator_role_ck'),
      ('ka_gochara_rule_path','kgrp_ruling_ck'),
      ('ka_gochara_rule_path_prerequisite','ka_gochara_rule_path_prerequisite_pkey'),
      ('ka_gochara_rule_path_prerequisite','kgrpp_ordinal_ck'),
      ('ka_gochara_rule_path_prerequisite','kgrpp_path_fk'),
      ('ka_gochara_rule_path_prerequisite','kgrpp_predicate_fk'),
      ('ka_gochara_rule_path_prerequisite','kgrpp_no_dup_uq'),
      ('ka_gochara_rule_path_soft_factor','ka_gochara_rule_path_soft_factor_pkey'),
      ('ka_gochara_rule_path_soft_factor','kgrps_path_fk'),
      ('ka_gochara_rule_path_soft_factor','kgrps_factor_fk'),
      ('ka_gochara_rule_path_seal','ka_gochara_rule_path_seal_pkey'),
      ('ka_gochara_rule_path_seal','kgrpseal_path_fk'))
  SELECT string_agg(e.conrelid || '.' || e.conname, ', ' ORDER BY 1) INTO missing
  FROM expected e
  WHERE NOT EXISTS (
    SELECT 1 FROM pg_constraint c
    WHERE c.conrelid = to_regclass('public.' || e.conrelid) AND c.conname = e.conname AND c.convalidated);
  IF missing IS NOT NULL THEN
    RAISE EXCEPTION 'migration 1154 post-apply check failed: missing or unvalidated constraint: %', missing;
  END IF;

  WITH expected(tgrelid, tgname) AS (VALUES
      ('ka_gochara_predicate','ka_gochara_predicate_write_guard'),
      ('ka_gochara_predicate','ka_gochara_predicate_no_truncate'),
      ('ka_gochara_factor','ka_gochara_factor_write_guard'),
      ('ka_gochara_factor','ka_gochara_factor_no_truncate'),
      ('ka_gochara_rule_path','ka_gochara_rule_path_write_guard'),
      ('ka_gochara_rule_path','ka_gochara_rule_path_no_truncate'),
      ('ka_gochara_rule_path_prerequisite','ka_gochara_rp_prereq_sealed_check'),
      ('ka_gochara_rule_path_prerequisite','ka_gochara_rp_prereq_write_guard'),
      ('ka_gochara_rule_path_prerequisite','ka_gochara_rp_prereq_no_truncate'),
      ('ka_gochara_rule_path_soft_factor','ka_gochara_rp_soft_factor_sealed_check'),
      ('ka_gochara_rule_path_soft_factor','ka_gochara_rp_soft_factor_write_guard'),
      ('ka_gochara_rule_path_soft_factor','ka_gochara_rp_soft_factor_no_truncate'),
      ('ka_gochara_rule_path_seal','ka_gochara_rule_path_seal_write_guard'),
      ('ka_gochara_rule_path_seal','ka_gochara_rule_path_seal_no_truncate'))
  SELECT string_agg(e.tgrelid || '.' || e.tgname, ', ' ORDER BY 1) INTO missing
  FROM expected e
  WHERE NOT EXISTS (
    SELECT 1 FROM pg_trigger t
    WHERE t.tgrelid = to_regclass('public.' || e.tgrelid) AND t.tgname = e.tgname
      AND NOT t.tgisinternal AND t.tgenabled = 'O');
  IF missing IS NOT NULL THEN
    RAISE EXCEPTION 'migration 1154 post-apply check failed: missing trigger: %', missing;
  END IF;
  RAISE NOTICE 'migration 1154: presence checks passed';
END;
$$;
