-- Migration 1154: ka_gochara rule-path registries — rule_path, predicate,
--                 factor, the §2.1 typed contracts with composite
--                 (id, rule_version) primary keys and composite version-bound
--                 references (GOCHARA_DESIGN_SPECS_v1_4 §2.1, amendment 1).
-- Created: 2026-09-30. Author: pravaha/a5-migrations (Stream A, A5.1).
--
-- Numbering: 1154 sits inside this lane's granted block (1150–1159 per
-- ADK-0026 §4; 1150/1151/1152 are used). Verified free by a fresh scan of
-- every origin/* ref across BOTH platform/migrations/ and
-- platform/supabase/migrations/ (2026-09-30: max in use anywhere is 1152;
-- no 1154 anywhere). `npm run guard:migration-numbers` green on this branch.
--
-- Spec: GOCHARA_DESIGN_SPECS_v1_4 (FROZEN 2026-09-30). Encoded as:
--   * CONSTRAINT: composite PKs (path_id, rule_version) / (predicate_id,
--     rule_version) / (factor_id, rule_version) (§2.1 amendment 1 — a path
--     change inserts a new version row, never mutates in place);
--     prerequisites / soft_factors composite-ref jsonb shape (array of
--     objects each carrying BOTH the id key and rule_version — a bare id is
--     rejected at write time, §2.1; enforced via the immutable helper
--     ka_gochara_composite_refs_ok); provenance ∈ {verse_cited,
--     uncited_extension} and operator_role ∈ {scored, testimony} (§0, S-04);
--     ruling_ref required iff provenance='uncited_extension' OR
--     operator_role='testimony' (§0/§1.2 inv 2, biconditional per the A5.1
--     brief); predicate operator 7-enum; unknown_is_false = false (§2.1
--     "unknown ≠ false", §2.2 inv 2 — CHECK pins the DEFAULT and forbids
--     true); factor direction ∈ {higher_stronger, lower_stronger}; range
--     codomain ⊆ [0,1] via CHECK 0 ≤ lower ≤ upper ≤ 1 (§2.1: "every scored
--     factor's range ⊆ [0,1]", a factor value is never negative — direction
--     carries the sign); units 4-enum; calibration_status ∈
--     {uncalibrated_default, calibrated} NOT NULL DEFAULT
--     'uncalibrated_default' (§2.1 new field, D-RQ1); null_state ∈ {omit,
--     unqualified} (§2.1: a missing operand takes its null_state, never 0 or
--     1 by default).
--   * TRIGGER: all three registries are insert-only — a change is a new
--     rule_version row, never UPDATE/DELETE (§2.1 amendment 1).
--   * COMMENT ONLY: frame enum+arg (§0) on rule_path is modelled as the same
--     frame_kind/frame_arg pair used by 1155 (CHECK encodes the closed set
--     and the arg rule); predicate evaluation states {true|false|unknown}
--     are evaluator semantics, not stored data; "every L1/L0 input named, no
--     free prose" in operands is authoring discipline; the within-path
--     product / cross-path max score algebra and the shared-root evidence
--     reduction (§2.1, NK-4/R2-S03, R4-S01) are evaluator behaviour.
--   * DELIBERATELY NOT ENCODED: agent_set/relation_set/object_selector
--     value-level CHECKs (§2.1 exhaustive sets are registry content authored
--     at B5.1; the exhaustive agent set = 7 grahas + Rāhu/Ketu + running
--     MD/AD/PD lords is documented in the table comment).
--
-- asset_registry: deliberately NOT registered (asset_registry.layer CHECK
-- has no 'L2' value; these are contract tables of the already-registered
-- ka_gochara writer family — same disposition as 1081).
--
-- Operational properties: pure CREATE TABLE / FUNCTION / TRIGGER; no
-- existing object or data touched; no production data writes; ONE
-- TRANSACTION (BEGIN/COMMIT, 1081 style); replay-idempotent by construction
-- (IF NOT EXISTS / CREATE OR REPLACE / DROP TRIGGER IF EXISTS everywhere),
-- though migrate.ts never replays; SET LOCAL bounds stated honestly.
--
-- ROLLBACK (dependents first):
--   DROP TRIGGER IF EXISTS ka_gochara_factor_immutable     ON ka_gochara_factor;
--   DROP TRIGGER IF EXISTS ka_gochara_predicate_immutable  ON ka_gochara_predicate;
--   DROP TRIGGER IF EXISTS ka_gochara_rule_path_immutable  ON ka_gochara_rule_path;
--   DROP FUNCTION IF EXISTS ka_gochara_factor_no_mutation();
--   DROP FUNCTION IF EXISTS ka_gochara_predicate_no_mutation();
--   DROP FUNCTION IF EXISTS ka_gochara_rule_path_no_mutation();
--   DROP TABLE IF EXISTS ka_gochara_factor;
--   DROP TABLE IF EXISTS ka_gochara_predicate;
--   DROP TABLE IF EXISTS ka_gochara_rule_path;
--   DROP FUNCTION IF EXISTS ka_gochara_composite_refs_ok(jsonb, text);
-- ─────────────────────────────────────────────────────────────────────────────

BEGIN;

SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '120s';

-- ── 0. Shared helper: composite version-bound reference shape (§2.1) ───────
-- Immutable, no table access — safe in CHECK constraints. Every element of
-- the array must be an object carrying BOTH the id key (predicate_id or
-- factor_id) AND rule_version, both as strings; a bare id is rejected (§2.1:
-- "composite references; a bare id is rejected at write time (the same rule
-- as path FKs)").

CREATE OR REPLACE FUNCTION ka_gochara_composite_refs_ok(refs jsonb, id_key text)
RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
  SELECT CASE
    WHEN jsonb_typeof(refs) <> 'array' THEN false
    ELSE NOT EXISTS (
      SELECT 1 FROM jsonb_array_elements(refs) el
      WHERE jsonb_typeof(el.value) <> 'object'
         OR NOT (el.value ? id_key)
         OR NOT (el.value ? 'rule_version')
         OR jsonb_typeof(el.value -> id_key) <> 'string'
         OR jsonb_typeof(el.value -> 'rule_version') <> 'string'
    )
  END;
$$;

COMMENT ON FUNCTION ka_gochara_composite_refs_ok(jsonb, text) IS
  '§2.1 composite version-bound reference shape: jsonb array whose every element is an '
  'object with string keys id_key and rule_version. Used in CHECKs on '
  'ka_gochara_rule_path (prerequisites, soft_factors) and '
  'ka_gochara_relationship_record (prerequisites). Bare ids are rejected.';

-- ── 1. rule_path (§2.1) ────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS ka_gochara_rule_path (
  path_id           TEXT NOT NULL,               -- 'P1'…'P6', 'P9' behind D-T2 (§1.1)
  rule_version      TEXT NOT NULL,               -- a path change inserts a new version row
  frame_kind        TEXT NOT NULL CHECK (frame_kind IN
                      ('moon','lagna','graha','dasha_lord','bhavat_bhavam')), -- §0 frame enum
  frame_arg         TEXT,                        -- graha:<X> / bhavat_bhavam:<house> arg;
                                                 -- NULL only for moon/lagna/dasha_lord
  agent_set         JSONB NOT NULL,              -- §2.1 exhaustive set: 7 grahas + Rāhu/Ketu
                                                 --   (agents and targets, never dṛṣṭi
                                                 --   sources — N-14) + running MD/AD/PD
                                                 --   lords in their period role
  relation_set      JSONB NOT NULL,
  object_selector   JSONB NOT NULL,              -- enumeration is qualification-driven:
                                                 --   names (agent, relation, object_role)
                                                 --   tuples (§2.1, O-RP-8)
  prerequisites     JSONB NOT NULL,              -- ordered [(predicate_id, rule_version)],
                                                 --   cheapest necessary predicate first
  soft_factors      JSONB NOT NULL,              -- [(factor_id, rule_version)]
  provenance        TEXT NOT NULL CHECK (provenance IN
                      ('verse_cited','uncited_extension')),       -- §0 (S-04)
  operator_role     TEXT NOT NULL CHECK (operator_role IN
                      ('scored','testimony')),                    -- §0 (S-04); testimony
                                                 --   annotates, never weights/gates/admits
  ruling_ref        TEXT,                        -- e.g. 'D-P4', 'D-PADMIT'
  score_rule        TEXT,                        -- within-path algebra reference (NK-4)
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),

  PRIMARY KEY (path_id, rule_version),
  CHECK ((frame_arg IS NULL) = (frame_kind IN ('moon','lagna','dasha_lord'))),
  CHECK (ka_gochara_composite_refs_ok(prerequisites, 'predicate_id')),
  CHECK (ka_gochara_composite_refs_ok(soft_factors, 'factor_id')),
  CHECK ((ruling_ref IS NOT NULL)
         = (provenance = 'uncited_extension' OR operator_role = 'testimony'))
    -- §0/§1.1: ruling_ref required iff uncited_extension OR testimony
);

COMMENT ON TABLE ka_gochara_rule_path IS
  'Rule-path registry (GOCHARA_DESIGN_SPECS_v1_4 §2.1): W_event = union over admitted '
  'paths of the conjunction of their prerequisites; inside, a score ranks and never '
  'admits. Composite (path_id, rule_version) PK (amendment 1); all FKs into this table '
  'are composite version-bound (path_id, rule_version) — an unversioned reference is '
  'rejected at write time. Admission (§0): scored output iff verse_cited from served '
  'corpus [D], or uncited_extension with a ruling whose text grants scoring; every '
  'D-PADMIT element and all P6 operators are testimony until the §2.2 promotion gate. '
  'Insert-only (trigger): a path change is a new rule_version row.';

CREATE OR REPLACE FUNCTION ka_gochara_rule_path_no_mutation()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'ka_gochara_rule_path is insert-only (GOCHARA_DESIGN_SPECS_v1_4 §2.1 amendment 1): % not permitted; a path change inserts a new rule_version row', TG_OP;
END;
$$;

DROP TRIGGER IF EXISTS ka_gochara_rule_path_immutable ON ka_gochara_rule_path;
CREATE TRIGGER ka_gochara_rule_path_immutable
  BEFORE UPDATE OR DELETE ON ka_gochara_rule_path
  FOR EACH ROW EXECUTE FUNCTION ka_gochara_rule_path_no_mutation();

-- ── 2. predicate (§2.1) ────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS ka_gochara_predicate (
  predicate_id      TEXT NOT NULL,
  rule_version      TEXT NOT NULL,
  operator          TEXT NOT NULL CHECK (operator IN
                      ('eq','in_set','within_orb','house_from','overlaps',
                       'period_running_at','declaration_exists')),  -- §2.1 closed enum
  operands          JSONB NOT NULL,              -- named selectors — every L1/L0 input
                                                 -- named, no free prose (§2.1); authoring
                                                 -- discipline, enforced at B5.1 review
  unknown_is_false  BOOLEAN NOT NULL DEFAULT false
                    CHECK (unknown_is_false = false),
                    -- §2.1: states {true|false|unknown}; unknown ≠ false (§2.2 inv 2).
                    -- An unknown necessary predicate makes admission unqualified, never
                    -- excluded. The CHECK pins this: unknown can NEVER be read as false.
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),

  PRIMARY KEY (predicate_id, rule_version)
);

COMMENT ON TABLE ka_gochara_predicate IS
  'Predicate registry (GOCHARA_DESIGN_SPECS_v1_4 §2.1): composite (predicate_id, '
  'rule_version) PK; evaluation states are {true|false|unknown} (evaluator semantics, '
  'not stored); unknown_is_false is pinned false — unknown-admission propagates '
  'unqualified (§2.2 inv 2), never false. Insert-only (trigger).';

CREATE OR REPLACE FUNCTION ka_gochara_predicate_no_mutation()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'ka_gochara_predicate is insert-only (GOCHARA_DESIGN_SPECS_v1_4 §2.1 amendment 1): % not permitted; a predicate change inserts a new rule_version row', TG_OP;
END;
$$;

DROP TRIGGER IF EXISTS ka_gochara_predicate_immutable ON ka_gochara_predicate;
CREATE TRIGGER ka_gochara_predicate_immutable
  BEFORE UPDATE OR DELETE ON ka_gochara_predicate
  FOR EACH ROW EXECUTE FUNCTION ka_gochara_predicate_no_mutation();

-- ── 3. factor (§2.1) ───────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS ka_gochara_factor (
  factor_id         TEXT NOT NULL,
  rule_version      TEXT NOT NULL,
  operand_selector  JSONB NOT NULL,              -- named operand selector (§2.1)
  direction         TEXT NOT NULL CHECK (direction IN
                      ('higher_stronger','lower_stronger')),      -- §2.1; direction, with
                                                 --   §3 class-relative polarity, carries
                                                 --   the sign (O-RP-7)
  function          TEXT NOT NULL,               -- numeric form: 'step','linear','ratio',…
  range_lower       REAL NOT NULL,
  range_upper       REAL NOT NULL,
  units             TEXT NOT NULL CHECK (units IN
                      ('degrees','days','count','unitless')),     -- §2.1
  calibration_status TEXT NOT NULL DEFAULT 'uncalibrated_default'
                    CHECK (calibration_status IN ('uncalibrated_default','calibrated')),
                    -- §2.1: until L5 calibration the numeric mapping is
                    -- uncalibrated_default — rank-only, preserving the doctrine's stated
                    -- ordering, entering no served claim of magnitude; calibration
                    -- replaces it under a NEW rule_version (D:237, D-RQ1)
  null_state        TEXT NOT NULL CHECK (null_state IN ('omit','unqualified')),
                    -- §2.1: a missing operand takes its null_state — 'omit' drops the
                    -- factor from the product, 'unqualified' propagates — never 0 or 1
                    -- by default (NK-4)
  effect            TEXT NOT NULL,               -- declared effect on the score (#20),
                                                 -- with its numeric function and scale
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),

  PRIMARY KEY (factor_id, rule_version),
  CHECK (range_lower >= 0 AND range_lower <= range_upper AND range_upper <= 1)
    -- §2.1 codomain: every scored factor's range ⊆ [0,1], so the within-path product
    -- lies in [0,1] and the cross-path max compares like with like; a factor value is
    -- never negative
);

COMMENT ON TABLE ka_gochara_factor IS
  'Soft-factor registry (GOCHARA_DESIGN_SPECS_v1_4 §2.1): composite (factor_id, '
  'rule_version) PK. No soft factor zeroes an admitted window (§1.2 inv 7, §2.3 inv 3); '
  'exclusion only via L0 absence or a failed necessary predicate. Codomain ⊆ [0,1] '
  '(CHECK). Insert-only (trigger): calibration or any change is a new rule_version row.';

CREATE OR REPLACE FUNCTION ka_gochara_factor_no_mutation()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'ka_gochara_factor is insert-only (GOCHARA_DESIGN_SPECS_v1_4 §2.1 amendment 1): % not permitted; a factor change inserts a new rule_version row', TG_OP;
END;
$$;

DROP TRIGGER IF EXISTS ka_gochara_factor_immutable ON ka_gochara_factor;
CREATE TRIGGER ka_gochara_factor_immutable
  BEFORE UPDATE OR DELETE ON ka_gochara_factor
  FOR EACH ROW EXECUTE FUNCTION ka_gochara_factor_no_mutation();

COMMIT;
