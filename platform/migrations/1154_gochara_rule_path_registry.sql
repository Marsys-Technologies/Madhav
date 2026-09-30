-- Migration 1154: ka_gochara rule-path registries — rule_path, predicate,
--                 factor, plus NORMALISED membership tables for the §2.1
--                 ordered version-bound references (amendment 3).
--                 Rewritten at A5.1 round 2 per ASTRA_REVIEW_A5_1_MIGRATIONS
--                 v1_0 amendments 2, 3, 7, 8, 9 and the steward rulings.
--                 1153–1157 were never applied anywhere — in-place rewrite.
-- Created: 2026-09-30. Author: pravaha/a5-migrations (Stream A, A5.1).
--
-- Numbering: 1154 sits inside this lane's granted block (1150–1159 per
-- ADK-0026 §4; 1150/1151/1152 are used). Verified free by a fresh scan of
-- every origin/* ref across BOTH platform/migrations/ and
-- platform/supabase/migrations/ (2026-09-30: max in use anywhere is 1152;
-- no 1154 anywhere). `npm run guard:migration-numbers` green on this branch.
--
-- Amendment 2 (P1 #2): NO BEGIN/COMMIT — migrate.ts owns ONE transaction
-- around DDL + ledger insert (see the 1153 header). SET LOCAL is scoped to
-- the runner's transaction.
--
-- Amendment 3 (P1 #3) — references are real integrity constraints: the old
-- JSONB `prerequisites` / `soft_factors` columns (shape-checked only) are
-- GONE. prerequisites live in ka_gochara_rule_path_prerequisite with a real
-- composite FK to ka_gochara_predicate(predicate_id, rule_version) and an
-- ordinal preserving the contracted evaluation order (cheapest necessary
-- predicate first, §1.1/§2.1); soft_factors live in
-- ka_gochara_rule_path_soft_factor with a real composite FK to
-- ka_gochara_factor(factor_id, rule_version). A bare or dangling id cannot
-- be written. (ka_gochara_composite_refs_ok from round 1 is deliberately
-- NOT recreated — JSON reference lists are normalised away.)
--
-- Amendment 7 (P1 #7) — steward ruling (D-SPECS C2): NO factor numbers are
-- invented here. Enforced exactly: factor range ⊆ [0,1] (CHECK, unchanged);
-- calibration_status ∈ {uncalibrated_default, calibrated} NOT NULL;
-- calibrated rows CARRY a machine-readable category_mapping (jsonb object —
-- its content is B5.1 registry content, not invented at A5.1); uncalibrated
-- rows carry the doctrine ORDERING only (doctrine_ordering: jsonb array of
-- category strings, e.g. exaltation > own > … — content authored at B5.1)
-- and no mapping. score_rule is NOT NULL (every path row declares its
-- within-path algebra reference — NK-4; testimony-only paths name their
-- zero-weight rule explicitly at authoring time).
--
-- Amendment 9 (P2 #9) — typed frame/selector/operand domains:
--   * frame via immutable helper ka_gochara_frame_ok(frame_kind, frame_arg):
--     moon/lagna/dasha_lord ⇒ arg NULL; graha ⇒ arg ∈ the 9 grahas;
--     bhavat_bhavam ⇒ arg ∈ 1..12 (S:70-71, 94).
--   * agent_set: jsonb array of strings ⊆ the 9 grahas (§2.1 exhaustive
--     agent set — running MD/AD/PD lords appear in their period ROLE, not as
--     extra agent values).
--   * relation_set: jsonb array of strings ⊆ the 8 §1.1 relations.
--   * object_selector: jsonb array of (agent, relation, object_role) tuples
--     with each element validated against the closed vocabs (§2.1
--     qualification-driven enumeration, O-RP-8).
--   * predicate operands / factor operand_selector: jsonb OBJECT naming every
--     L1/L0 input (string or string-array values; scalars/null/prose fail —
--     S:160-162 excludes free prose).
-- Encoded as:
--   * CONSTRAINT: composite PKs (path_id, rule_version) / (predicate_id,
--     rule_version) / (factor_id, rule_version) (§2.1 amendment 1);
--     provenance ∈ {verse_cited, uncited_extension}, operator_role ∈ {scored,
--     testimony} (§0 S-04); ruling_ref REQUIRED when provenance =
--     'uncited_extension' — and never forbidden otherwise (amendment 9: the
--     frozen wording S:110 is "testimony UNDER A RULING"; the round-1
--     biconditional imposed a stronger reading and is aligned here);
--     predicate operator 7-enum; unknown_is_false pinned false (§2.2 inv 2);
--     factor direction 2-enum; units 4-enum; null_state ∈ {omit,
--     unqualified}; range codomain ⊆ [0,1].
--   * TRIGGER: all five tables are insert-only — a change is a new
--     rule_version row, never UPDATE/DELETE (§2.1 amendment 1).
--   * COMMENT ONLY: predicate evaluation states {true|false|unknown} are
--     evaluator semantics; the within-path product / cross-path max score
--     algebra and the shared-root evidence reduction (§2.1, NK-4/R2-S03,
--     R4-S01) are evaluator behaviour.
--
-- asset_registry: deliberately NOT registered (asset_registry.layer CHECK
-- has no 'L2' value; contract tables of the already-registered ka_gochara
-- writer family — same disposition as 1081).
--
-- Operational properties: pure CREATE TABLE / FUNCTION / TRIGGER + post-DDL
-- verification; no existing object or data touched; no business-data writes.
-- Execution outcomes (amendment 8): fresh apply = create + verify; repeat
-- execution = verified no-op; drifted same-named object = loud RAISE.
--
-- ROLLBACK (dependents first):
--   DROP TRIGGER IF EXISTS ka_gochara_rp_soft_factor_immutable ON ka_gochara_rule_path_soft_factor;
--   DROP TRIGGER IF EXISTS ka_gochara_rp_prereq_immutable       ON ka_gochara_rule_path_prerequisite;
--   DROP TRIGGER IF EXISTS ka_gochara_factor_immutable          ON ka_gochara_factor;
--   DROP TRIGGER IF EXISTS ka_gochara_predicate_immutable       ON ka_gochara_predicate;
--   DROP TRIGGER IF EXISTS ka_gochara_rule_path_immutable       ON ka_gochara_rule_path;
--   DROP FUNCTION IF EXISTS ka_gochara_membership_no_mutation();
--   DROP FUNCTION IF EXISTS ka_gochara_factor_no_mutation();
--   DROP FUNCTION IF EXISTS ka_gochara_predicate_no_mutation();
--   DROP FUNCTION IF EXISTS ka_gochara_rule_path_no_mutation();
--   DROP TABLE IF EXISTS ka_gochara_rule_path_soft_factor;
--   DROP TABLE IF EXISTS ka_gochara_rule_path_prerequisite;
--   DROP TABLE IF EXISTS ka_gochara_rule_path;
--   DROP TABLE IF EXISTS ka_gochara_factor;
--   DROP TABLE IF EXISTS ka_gochara_predicate;
--   DROP FUNCTION IF EXISTS ka_gochara_named_operands_ok(jsonb);
--   DROP FUNCTION IF EXISTS ka_gochara_object_selector_ok(jsonb);
--   DROP FUNCTION IF EXISTS ka_gochara_vocab_array_ok(jsonb, text[]);
--   DROP FUNCTION IF EXISTS ka_gochara_string_array_ok(jsonb);
--   DROP FUNCTION IF EXISTS ka_gochara_frame_ok(text, text);
-- ─────────────────────────────────────────────────────────────────────────────

SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '120s';

-- ── 0. Shared immutable helpers (no table access — safe in CHECKs) ────────

-- §0 typed frame rule (amendment 9): moon/lagna/dasha_lord carry no arg;
-- graha carries one of the 9 grahas; bhavat_bhavam carries a house 1..12.
CREATE OR REPLACE FUNCTION ka_gochara_frame_ok(frame_kind text, frame_arg text)
RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
  SELECT CASE frame_kind
    WHEN 'moon'        THEN frame_arg IS NULL
    WHEN 'lagna'       THEN frame_arg IS NULL
    WHEN 'dasha_lord'  THEN frame_arg IS NULL
    WHEN 'graha'       THEN frame_arg IN
      ('sun','moon','mars','mercury','jupiter','venus','saturn','rahu','ketu')
    WHEN 'bhavat_bhavam' THEN frame_arg ~ '^([1-9]|1[0-2])$'
    ELSE false
  END;
$$;

COMMENT ON FUNCTION ka_gochara_frame_ok(text, text) IS
  '§0 frame enum+arg rule (amendment 9): arg NULL exactly for moon/lagna/dasha_lord; '
  'graha arg ∈ 9 grahas; bhavat_bhavam arg ∈ 1..12. Counting is inclusive of the '
  'reference sign (§0). Used in CHECKs on rule_path and relationship_record.';

-- jsonb array whose every element is a non-empty string.
CREATE OR REPLACE FUNCTION ka_gochara_string_array_ok(j jsonb)
RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
  SELECT jsonb_typeof(j) = 'array'
     AND NOT EXISTS (
       SELECT 1 FROM jsonb_array_elements(j) el
       WHERE jsonb_typeof(el.value) <> 'string'
          OR btrim(el.value #>> '{}') = ''
     );
$$;

-- jsonb string array whose every element is inside a closed vocab.
CREATE OR REPLACE FUNCTION ka_gochara_vocab_array_ok(j jsonb, vocab text[])
RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
  SELECT ka_gochara_string_array_ok(j)
     AND NOT EXISTS (
       SELECT 1 FROM jsonb_array_elements_text(j) v
       WHERE v <> ALL (vocab)
     );
$$;

-- §2.1 object_selector: array of (agent, relation, object_role) tuples, each
-- element validated against the closed vocabs; a missing key fails.
CREATE OR REPLACE FUNCTION ka_gochara_object_selector_ok(j jsonb)
RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
  SELECT jsonb_typeof(j) = 'array'
     AND NOT EXISTS (
       SELECT 1 FROM jsonb_array_elements(j) el
       WHERE jsonb_typeof(el.value) <> 'object'
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

-- §2.1 named operands: a non-empty jsonb OBJECT naming every L1/L0 input;
-- values are strings or arrays of strings — scalars, nulls and free prose
-- fail (S:160-162).
CREATE OR REPLACE FUNCTION ka_gochara_named_operands_ok(j jsonb)
RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
  SELECT jsonb_typeof(j) = 'object'
     AND j <> '{}'::jsonb
     AND NOT EXISTS (
       SELECT 1 FROM jsonb_each(j) e
       WHERE jsonb_typeof(e.value) <> 'string'
          AND NOT ka_gochara_string_array_ok(e.value)
     );
$$;

-- ── 1. predicate (§2.1) ────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS ka_gochara_predicate (
  predicate_id      TEXT NOT NULL,
  rule_version      TEXT NOT NULL,
  operator          TEXT NOT NULL,
  operands          JSONB NOT NULL,              -- named selectors, typed (amendment 9)
  unknown_is_false  BOOLEAN NOT NULL DEFAULT false,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),

  PRIMARY KEY (predicate_id, rule_version),
  CONSTRAINT kgp_operator_ck CHECK (operator IN
    ('eq','in_set','within_orb','house_from','overlaps',
     'period_running_at','declaration_exists')),
  CONSTRAINT kgp_unknown_is_false_ck CHECK (unknown_is_false = false),
    -- §2.1/§2.2 inv 2: unknown ≠ false; an unknown necessary predicate makes
    -- admission unqualified, never excluded
  CONSTRAINT kgp_operands_typed_ck CHECK (ka_gochara_named_operands_ok(operands))
);

COMMENT ON TABLE ka_gochara_predicate IS
  'Predicate registry (GOCHARA_DESIGN_SPECS_v1_4 §2.1): composite (predicate_id, '
  'rule_version) PK; states {true|false|unknown} are evaluator semantics; '
  'unknown_is_false pinned false. Insert-only (trigger).';

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

-- ── 2. factor (§2.1) ───────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS ka_gochara_factor (
  factor_id         TEXT NOT NULL,
  rule_version      TEXT NOT NULL,
  operand_selector  JSONB NOT NULL,              -- named operand selector, typed
  direction         TEXT NOT NULL,
  function          TEXT NOT NULL,               -- numeric form name: 'step','linear',…
  range_lower       REAL NOT NULL,
  range_upper       REAL NOT NULL,
  units             TEXT NOT NULL,
  calibration_status TEXT NOT NULL DEFAULT 'uncalibrated_default',
  doctrine_ordering JSONB,                       -- uncalibrated rows: the doctrine's
                                                 --   stated category ORDERING (array of
                                                 --   strings; content authored at B5.1)
  category_mapping  JSONB,                       -- calibrated rows: the machine-readable
                                                 --   numeric mapping (object; content set
                                                 --   at L5 calibration — A5.1 invents NO
                                                 --   numbers, steward ruling / D-SPECS C2)
  null_state        TEXT NOT NULL,
  effect            TEXT NOT NULL,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),

  PRIMARY KEY (factor_id, rule_version),
  CONSTRAINT kgf_direction_ck CHECK (direction IN
    ('higher_stronger','lower_stronger')),
  CONSTRAINT kgf_units_ck CHECK (units IN
    ('degrees','days','count','unitless')),
  CONSTRAINT kgf_calibration_status_ck CHECK (calibration_status IN
    ('uncalibrated_default','calibrated')),
  CONSTRAINT kgf_null_state_ck CHECK (null_state IN ('omit','unqualified')),
  CONSTRAINT kgf_range_unit_interval_ck
    CHECK (range_lower >= 0 AND range_lower <= range_upper AND range_upper <= 1),
    -- §2.1 codomain: every scored factor's range ⊆ [0,1]; never negative
  CONSTRAINT kgf_operand_selector_typed_ck
    CHECK (ka_gochara_named_operands_ok(operand_selector)),
  CONSTRAINT kgf_mapping_discipline_ck CHECK (
    (calibration_status = 'calibrated'
       AND category_mapping IS NOT NULL
       AND jsonb_typeof(category_mapping) = 'object')
    OR
    (calibration_status = 'uncalibrated_default'
       AND category_mapping IS NULL
       AND doctrine_ordering IS NOT NULL
       AND ka_gochara_string_array_ok(doctrine_ordering))
  )
    -- steward ruling (amendment 7 / D-SPECS C2): calibrated rows CARRY a
    -- mapping; uncalibrated rows carry the doctrine ordering ONLY
);

COMMENT ON TABLE ka_gochara_factor IS
  'Soft-factor registry (GOCHARA_DESIGN_SPECS_v1_4 §2.1): composite (factor_id, '
  'rule_version) PK. Codomain ⊆ [0,1] (CHECK). Calibration discipline (steward ruling): '
  'no factor numbers are invented by this migration — calibrated ⇒ category_mapping '
  'present; uncalibrated_default ⇒ doctrine_ordering only, rank-only, no served claim '
  'of magnitude (D-RQ1). Insert-only (trigger).';

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

-- ── 3. rule_path (§2.1) ────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS ka_gochara_rule_path (
  path_id           TEXT NOT NULL,               -- 'P1'…'P6', 'P9' behind D-T2 (§1.1)
  rule_version      TEXT NOT NULL,
  frame_kind        TEXT NOT NULL,
  frame_arg         TEXT,                        -- typed by ka_gochara_frame_ok (§0)
  agent_set         JSONB NOT NULL,              -- ⊆ 9 grahas (typed, amendment 9)
  relation_set      JSONB NOT NULL,              -- ⊆ 8 §1.1 relations (typed)
  object_selector   JSONB NOT NULL,              -- [(agent, relation, object_role)] tuples
  provenance        TEXT NOT NULL,
  operator_role     TEXT NOT NULL,
  ruling_ref        TEXT,                        -- e.g. 'D-P4', 'D-PADMIT'
  score_rule        TEXT NOT NULL,               -- within-path algebra reference (NK-4);
                                                 --   amendment 7: declared on every row,
                                                 --   testimony-only paths included
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),

  PRIMARY KEY (path_id, rule_version),
  CONSTRAINT kgrp_frame_ck CHECK (ka_gochara_frame_ok(frame_kind, frame_arg)),
  CONSTRAINT kgrp_agent_set_ck CHECK (ka_gochara_vocab_array_ok(agent_set,
    ARRAY['sun','moon','mars','mercury','jupiter','venus','saturn','rahu','ketu'])),
  CONSTRAINT kgrp_relation_set_ck CHECK (ka_gochara_vocab_array_ok(relation_set,
    ARRAY['residence','aspect','conjunction','dispositorship',
          'association','ownership','occupancy','period_running'])),
  CONSTRAINT kgrp_object_selector_ck
    CHECK (ka_gochara_object_selector_ok(object_selector)),
  CONSTRAINT kgrp_provenance_ck CHECK (provenance IN
    ('verse_cited','uncited_extension')),
  CONSTRAINT kgrp_operator_role_ck CHECK (operator_role IN ('scored','testimony')),
  CONSTRAINT kgrp_ruling_ck
    CHECK (provenance <> 'uncited_extension' OR ruling_ref IS NOT NULL)
    -- §0/S:110 as frozen: uncited_extension REQUIRES a ruling_ref; a ruling
    -- ref is never forbidden otherwise (amendment 9 — the round-1
    -- biconditional was stronger than the frozen wording and is aligned here)
);

COMMENT ON TABLE ka_gochara_rule_path IS
  'Rule-path registry (GOCHARA_DESIGN_SPECS_v1_4 §2.1): composite (path_id, rule_version) '
  'PK; all FKs into this table are composite version-bound. prerequisites and '
  'soft_factors are NORMALISED into ka_gochara_rule_path_prerequisite / '
  'ka_gochara_rule_path_soft_factor with real composite FKs (amendment 3) — a bare or '
  'dangling id cannot be written. Admission per §0 (S-04). Insert-only (trigger).';

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

-- ── 4. Membership tables (amendment 3): ordered, version-bound, real FKs ───

CREATE TABLE IF NOT EXISTS ka_gochara_rule_path_prerequisite (
  path_id              TEXT NOT NULL,
  rule_version         TEXT NOT NULL,
  ordinal              INTEGER NOT NULL,         -- §1.1/§2.1: ordered, cheapest
                                                 --   necessary predicate first
  predicate_id         TEXT NOT NULL,
  predicate_rule_version TEXT NOT NULL,

  PRIMARY KEY (path_id, rule_version, ordinal),
  CONSTRAINT kgrpp_ordinal_ck CHECK (ordinal >= 1),
  CONSTRAINT kgrpp_path_fk FOREIGN KEY (path_id, rule_version)
    REFERENCES ka_gochara_rule_path (path_id, rule_version),
  CONSTRAINT kgrpp_predicate_fk FOREIGN KEY (predicate_id, predicate_rule_version)
    REFERENCES ka_gochara_predicate (predicate_id, rule_version),
  CONSTRAINT kgrpp_no_dup_uq
    UNIQUE (path_id, rule_version, predicate_id, predicate_rule_version)
);

CREATE TABLE IF NOT EXISTS ka_gochara_rule_path_soft_factor (
  path_id              TEXT NOT NULL,
  rule_version         TEXT NOT NULL,
  factor_id            TEXT NOT NULL,
  factor_rule_version  TEXT NOT NULL,

  PRIMARY KEY (path_id, rule_version, factor_id, factor_rule_version),
  CONSTRAINT kgrps_path_fk FOREIGN KEY (path_id, rule_version)
    REFERENCES ka_gochara_rule_path (path_id, rule_version),
  CONSTRAINT kgrps_factor_fk FOREIGN KEY (factor_id, factor_rule_version)
    REFERENCES ka_gochara_factor (factor_id, rule_version)
);

CREATE OR REPLACE FUNCTION ka_gochara_membership_no_mutation()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION '% is insert-only (GOCHARA_DESIGN_SPECS_v1_4 §2.1 amendment 1): % not permitted; a membership change rides a new rule_version row', TG_TABLE_NAME, TG_OP;
END;
$$;

DROP TRIGGER IF EXISTS ka_gochara_rp_prereq_immutable ON ka_gochara_rule_path_prerequisite;
CREATE TRIGGER ka_gochara_rp_prereq_immutable
  BEFORE UPDATE OR DELETE ON ka_gochara_rule_path_prerequisite
  FOR EACH ROW EXECUTE FUNCTION ka_gochara_membership_no_mutation();

DROP TRIGGER IF EXISTS ka_gochara_rp_soft_factor_immutable ON ka_gochara_rule_path_soft_factor;
CREATE TRIGGER ka_gochara_rp_soft_factor_immutable
  BEFORE UPDATE OR DELETE ON ka_gochara_rule_path_soft_factor
  FOR EACH ROW EXECUTE FUNCTION ka_gochara_membership_no_mutation();

-- ── 5. Post-DDL definition verification (amendment 8) ─────────────────────

DO $$
DECLARE missing text;
BEGIN
  WITH expected(tbl, col, typ, nn) AS (
    VALUES
      ('ka_gochara_predicate','predicate_id','text',true),
      ('ka_gochara_predicate','rule_version','text',true),
      ('ka_gochara_predicate','operator','text',true),
      ('ka_gochara_predicate','operands','jsonb',true),
      ('ka_gochara_predicate','unknown_is_false','boolean',true),
      ('ka_gochara_factor','factor_id','text',true),
      ('ka_gochara_factor','rule_version','text',true),
      ('ka_gochara_factor','operand_selector','jsonb',true),
      ('ka_gochara_factor','direction','text',true),
      ('ka_gochara_factor','function','text',true),
      ('ka_gochara_factor','range_lower','real',true),
      ('ka_gochara_factor','range_upper','real',true),
      ('ka_gochara_factor','units','text',true),
      ('ka_gochara_factor','calibration_status','text',true),
      ('ka_gochara_factor','doctrine_ordering','jsonb',false),
      ('ka_gochara_factor','category_mapping','jsonb',false),
      ('ka_gochara_factor','null_state','text',true),
      ('ka_gochara_factor','effect','text',true),
      ('ka_gochara_rule_path','path_id','text',true),
      ('ka_gochara_rule_path','rule_version','text',true),
      ('ka_gochara_rule_path','frame_kind','text',true),
      ('ka_gochara_rule_path','frame_arg','text',false),
      ('ka_gochara_rule_path','agent_set','jsonb',true),
      ('ka_gochara_rule_path','relation_set','jsonb',true),
      ('ka_gochara_rule_path','object_selector','jsonb',true),
      ('ka_gochara_rule_path','provenance','text',true),
      ('ka_gochara_rule_path','operator_role','text',true),
      ('ka_gochara_rule_path','ruling_ref','text',false),
      ('ka_gochara_rule_path','score_rule','text',true),
      ('ka_gochara_rule_path_prerequisite','path_id','text',true),
      ('ka_gochara_rule_path_prerequisite','rule_version','text',true),
      ('ka_gochara_rule_path_prerequisite','ordinal','integer',true),
      ('ka_gochara_rule_path_prerequisite','predicate_id','text',true),
      ('ka_gochara_rule_path_prerequisite','predicate_rule_version','text',true),
      ('ka_gochara_rule_path_soft_factor','path_id','text',true),
      ('ka_gochara_rule_path_soft_factor','rule_version','text',true),
      ('ka_gochara_rule_path_soft_factor','factor_id','text',true),
      ('ka_gochara_rule_path_soft_factor','factor_rule_version','text',true)
  )
  SELECT string_agg(e.tbl || '.' || e.col, ', ' ORDER BY e.tbl, e.col) INTO missing
  FROM expected e
  LEFT JOIN pg_attribute a
    ON a.attrelid = to_regclass('public.' || e.tbl)
   AND a.attname = e.col AND NOT a.attisdropped
  WHERE a.attname IS NULL
     OR format_type(a.atttypid, a.atttypmod) IS DISTINCT FROM e.typ
     OR a.attnotnull IS DISTINCT FROM e.nn;
  IF missing IS NOT NULL THEN
    RAISE EXCEPTION 'migration 1154 post-DDL verification failed (amendment 8): column drift: %', missing;
  END IF;

  WITH expected(conrelid, conname) AS (
    VALUES
      ('ka_gochara_predicate','kgp_operator_ck'),
      ('ka_gochara_predicate','kgp_unknown_is_false_ck'),
      ('ka_gochara_predicate','kgp_operands_typed_ck'),
      ('ka_gochara_factor','kgf_direction_ck'),
      ('ka_gochara_factor','kgf_units_ck'),
      ('ka_gochara_factor','kgf_calibration_status_ck'),
      ('ka_gochara_factor','kgf_null_state_ck'),
      ('ka_gochara_factor','kgf_range_unit_interval_ck'),
      ('ka_gochara_factor','kgf_operand_selector_typed_ck'),
      ('ka_gochara_factor','kgf_mapping_discipline_ck'),
      ('ka_gochara_rule_path','kgrp_frame_ck'),
      ('ka_gochara_rule_path','kgrp_agent_set_ck'),
      ('ka_gochara_rule_path','kgrp_relation_set_ck'),
      ('ka_gochara_rule_path','kgrp_object_selector_ck'),
      ('ka_gochara_rule_path','kgrp_provenance_ck'),
      ('ka_gochara_rule_path','kgrp_operator_role_ck'),
      ('ka_gochara_rule_path','kgrp_ruling_ck'),
      ('ka_gochara_rule_path_prerequisite','kgrpp_ordinal_ck'),
      ('ka_gochara_rule_path_prerequisite','kgrpp_path_fk'),
      ('ka_gochara_rule_path_prerequisite','kgrpp_predicate_fk'),
      ('ka_gochara_rule_path_prerequisite','kgrpp_no_dup_uq'),
      ('ka_gochara_rule_path_soft_factor','kgrps_path_fk'),
      ('ka_gochara_rule_path_soft_factor','kgrps_factor_fk')
  )
  SELECT string_agg(e.conrelid || '.' || e.conname, ', ' ORDER BY 1) INTO missing
  FROM expected e
  WHERE NOT EXISTS (
    SELECT 1 FROM pg_constraint c
    WHERE c.conrelid = to_regclass('public.' || e.conrelid) AND c.conname = e.conname
  );
  IF missing IS NOT NULL THEN
    RAISE EXCEPTION 'migration 1154 post-DDL verification failed (amendment 8): missing constraint: %', missing;
  END IF;

  WITH expected(tgrelid, tgname) AS (
    VALUES
      ('ka_gochara_predicate','ka_gochara_predicate_immutable'),
      ('ka_gochara_factor','ka_gochara_factor_immutable'),
      ('ka_gochara_rule_path','ka_gochara_rule_path_immutable'),
      ('ka_gochara_rule_path_prerequisite','ka_gochara_rp_prereq_immutable'),
      ('ka_gochara_rule_path_soft_factor','ka_gochara_rp_soft_factor_immutable')
  )
  SELECT string_agg(e.tgrelid || '.' || e.tgname, ', ' ORDER BY 1) INTO missing
  FROM expected e
  WHERE NOT EXISTS (
    SELECT 1 FROM pg_trigger t
    WHERE t.tgrelid = to_regclass('public.' || e.tgrelid)
      AND t.tgname = e.tgname AND NOT t.tgisinternal
  );
  IF missing IS NOT NULL THEN
    RAISE EXCEPTION 'migration 1154 post-DDL verification failed (amendment 8): missing trigger: %', missing;
  END IF;
END;
$$;
