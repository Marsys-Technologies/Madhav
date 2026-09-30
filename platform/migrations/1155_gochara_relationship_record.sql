-- Migration 1155: ka_gochara_relationship_record — the §1.1 typed contract
--                 + §3.1 valence fields + admission persistence, with
--                 ownership-bound contact references (F1/F7), normalised
--                 prerequisite membership finalised at the atomic write
--                 boundary (F5), coverage APPLICABILITY (F7), sealed-generation
--                 immutability (F2) and sealed-rule-version references (F3).
--                 Depends on 1153 (identity/ledger/seal/bridge/helpers), 1154
--                 (registries, typed helpers, rule-version seal) and 1081/1087
--                 (kala_gochara_coverage). Round-3 rewrite per
--                 ASTRA_REVIEW_A5_1_MIGRATIONS v1_1 under the steward rulings.
--                 Never applied anywhere — in-place rewrite of the same number.
-- Created: 2026-09-30. Author: pravaha/a5-migrations (Stream A, A5.1).
--
-- Numbering: 1155 sits inside this lane's granted block (1150–1159 per
-- ADK-0026 §4). Verified free by a fresh scan of every origin/* ref across
-- BOTH migration directories (2026-09-30). `npm run guard:migration-numbers`
-- green.
--
-- Transaction ownership: NO BEGIN/COMMIT — migrate.ts owns ONE transaction
-- (see the 1153 header). Effective ordered gate: pinned schema → preflight
-- gate (byte-identical to preflight_1155_relationship_record.sql; requires
-- 1153 and 1154 recorded) → DDL → post-DDL definition verification.
--
-- ── F1/F7 — every contact reference is ownership-bound and relation-exact ─
-- Transit rows FK (chart_id, generation, contact_id, agent, relation,
-- object_id) → ka_gochara_contact (chart_id, generation, contact_id, body,
-- relation_kind, physical_object_id): a record can reference only a contact
-- OWNED by its own chart and generation, and its agent, physical relation and
-- object must agree with that ledger row (which in turn agrees with its
-- identity and physical object — 1153). Natal-fact rows carry contact_id NULL
-- (MATCH SIMPLE keeps them out of this FK; the transit/natal CHECK keeps
-- transit rows in it).
--
-- ── F7 — coverage APPLICABILITY, not mere existence ──────────────────────
-- The composite FK (chart_id, generation, partition_kind, partition_key) →
-- kala_gochara_coverage proves the partition exists in the record's own
-- scope. ka_gochara_record_coverage_guard (BEFORE INSERT OR UPDATE) proves it
-- APPLIES:
--   * partition_kind = 'event_class'  ⇒ partition_key = event_class
--     (1081: the key IS the class);
--   * partition_kind = 'body_target'  ⇒ the key's leading body = agent
--     (1081: 'saturn:karaka' form);
--   * transit rows: agent = 'moon' ⇔ partition_kind = 'moon_on_demand'
--     (§6.1 Moon-on-demand; O-SS-4); relation ∈ relations_searched; the
--     partition's LEGACY convention is bridged (ka_gochara_convention_bridge)
--     to the contact's sky convention; the contact's t_in lies inside
--     completed_horizon (C7: "a contact whose in-orb interval begins inside
--     the solved partition …"); the record's precision payload restates the
--     contact's method/uncertainties (CLAUDE.md §N.5 — no restated value may
--     disagree with the fact it cites);
--   * natal-fact rows never reference moon_on_demand coverage;
--   * every computed temporal_support interval lies inside completed_horizon.
--
-- ── F5 — total validators; contradictory qualification states rejected ───
-- ka_gochara_precision_ok returns a total boolean: a NULL/absent/non-string
-- solver_method, a negative or non-numeric uncertainty, an extra key, all
-- ⇒ FALSE. Every CHECK asks `… IS TRUE`. Qualification is finalised at the
-- ATOMIC WRITE BOUNDARY by DEFERRABLE INITIALLY DEFERRED constraint triggers
-- on the record and on its prerequisite membership (a record and its
-- membership are written in one transaction; the check runs at COMMIT over
-- the final state):
--   (i)  the record's prerequisite list (ordinal, predicate_id, version)
--        EQUALS its path version's declared prerequisite list (§1.2 inv 7:
--        exclusion only via a failed necessary predicate of the record's OWN
--        path; a record cannot evaluate a predicate its path does not
--        declare, nor skip one it does);
--   (ii) admission_state EQUALS the state derived from the results —
--        any 'false' ⇒ not_admitted; else any unknown/unevaluated ⇒
--        unqualified (§2.2 inv 2: unknown ≠ false, recorded as unqualified,
--        never admitted); else admitted.
-- Adding an 'unknown' prerequisite to an 'admitted' record therefore fails
-- at commit (the reviewer's F5 counterexample).
--
-- ── F2 — sealed-generation immutability ──────────────────────────────────
-- ka_gochara_sealed_generation_guard refuses UPDATE/DELETE of any row whose
-- (chart_id, generation) is sealed (1153's permanent predicate, serialized
-- with publication); TRUNCATE is refused unconditionally. INSERT stays
-- permitted (append — a partition extension adds records; published values
-- never change). Candidate generations remain writer-owned per-(chart_id ×
-- generation) delete-then-insert (§N.3).
--
-- ── F3 — only a sealed rule version produces records ─────────────────────
-- ka_gochara_require_sealed_rule_path (1154) runs BEFORE INSERT OR UPDATE.
--
-- ── F11 — lineage and numeric domains ────────────────────────────────────
-- source_fact_ids: typed non-empty whitespace-free string array, [] only on
-- fixture rows. RESOLVABILITY of those ids (L0/L1 chart_facts.fact_id or a
-- pinned extract row id) is a WRITER-BOUNDARY obligation stated here
-- explicitly: the spec admits extract-row ids and synthetic fixtures, so no
-- single table can be the FK target; the writer resolves every id it emits
-- (CLAUDE.md §N.5) and the A5.5 rehearsal asserts it. evidence/severity are
-- finite (evidence non-negative); no upper bound of one is imposed on
-- evidence (amendment 7).
--
-- asset_registry: deliberately NOT registered (same disposition as 1081).
--
-- ROLLBACK (dependents first; 1156/1157 before this):
--   DROP TABLE IF EXISTS ka_gochara_record_prerequisite;
--   DROP TABLE IF EXISTS ka_gochara_relationship_record;
--   DROP FUNCTION IF EXISTS ka_gochara_record_finalize_check();
--   DROP FUNCTION IF EXISTS ka_gochara_record_coverage_guard();
--   DROP FUNCTION IF EXISTS ka_gochara_sealed_generation_guard();
--   DROP FUNCTION IF EXISTS ka_gochara_intervals_ok(tstzrange[]);
--   DROP FUNCTION IF EXISTS ka_gochara_precision_ok(jsonb);
-- ─────────────────────────────────────────────────────────────────────────────

SET LOCAL search_path = public, pg_catalog;   -- pinned schema resolution (F9)
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '120s';

-- ── GATE (byte-identical to preflight_1155_relationship_record.sql) ────────
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
    SELECT 'no_references_privilege', p.t
    FROM (VALUES ('public.charts'), ('public.kala_gochara_coverage')) AS p(t)
    WHERE to_regclass(p.t) IS NOT NULL AND NOT has_table_privilege(p.t, 'REFERENCES')
    UNION ALL
    SELECT 'relation_already_exists', 'public.' || c.relname
    FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE NOT replay AND n.nspname = 'public'
      AND c.relname IN ('ka_gochara_relationship_record', 'ka_gochara_relationship_record_pkey',
                        'kgrr_identity_uq', 'kgrr_membership_uq',
                        'ka_gochara_record_prerequisite', 'ka_gochara_record_prerequisite_pkey',
                        'kgrpr_no_dup_uq',
                        'idx_kgrr_chart_gen', 'idx_kgrr_contact', 'idx_kgrr_object',
                        'idx_kgrr_path', 'idx_kgrr_coverage', 'idx_kgrpr_record')
    UNION ALL
    SELECT 'trigger_already_exists', 'public.' || c.relname || '.' || t.tgname
    FROM pg_trigger t
    JOIN pg_class c ON c.oid = t.tgrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE NOT replay AND n.nspname = 'public' AND NOT t.tgisinternal
      AND ( (c.relname = 'ka_gochara_relationship_record'
               AND t.tgname IN ('ka_gochara_rr_sealed_path_check', 'ka_gochara_rr_coverage_guard',
                                'ka_gochara_rr_sealed_generation_guard', 'ka_gochara_rr_finalize',
                                'ka_gochara_rr_no_truncate'))
         OR (c.relname = 'ka_gochara_record_prerequisite'
               AND t.tgname IN ('ka_gochara_rpr_sealed_generation_guard', 'ka_gochara_rpr_finalize',
                                'ka_gochara_rpr_no_truncate')) )
    UNION ALL
    -- function collisions by EXACT ARGUMENT TYPES (F8) — this file's own helpers
    SELECT 'function_already_exists',
           'public.' || p.proname || '(' || array_to_string(e.argtypes, ',') || ')'
    FROM (VALUES
            ('ka_gochara_precision_ok',            ARRAY['jsonb']),
            ('ka_gochara_intervals_ok',            ARRAY['tstzrange[]']),
            ('ka_gochara_sealed_generation_guard', ARRAY[]::text[]),
            ('ka_gochara_record_coverage_guard',   ARRAY[]::text[]),
            ('ka_gochara_record_finalize_check',   ARRAY[]::text[])
         ) AS e(fname, argtypes)
    JOIN pg_proc p ON p.proname = e.fname
    JOIN pg_namespace n ON n.oid = p.pronamespace AND n.nspname = 'public'
    WHERE NOT replay
      AND (SELECT COALESCE(array_agg(format_type(u.oid, NULL) ORDER BY u.ord), '{}')
           FROM unnest(p.proargtypes) WITH ORDINALITY AS u(oid, ord)) = e.argtypes
    UNION ALL
    -- (b1) parents exist
    SELECT 'parent_table_missing', p.t
    FROM (VALUES ('charts'), ('kala_gochara_coverage'), ('ka_gochara_contact'),
                 ('ka_gochara_physical_object'), ('ka_gochara_rule_path'),
                 ('ka_gochara_rule_path_seal'), ('ka_gochara_predicate'),
                 ('ka_gochara_convention_bridge'), ('ka_gochara_generation_seal')) AS p(t)
    WHERE to_regclass('public.' || p.t) IS NULL
    UNION ALL
    -- (b2) parent columns with expected types (the coverage columns the
    -- applicability guard reads are included)
    SELECT 'parent_column_missing_or_type',
           e.t || '.' || e.col || ' expected ' || e.typ
    FROM (VALUES ('charts',                     'id',                 'uuid'),
                 ('kala_gochara_coverage',      'chart_id',           'uuid'),
                 ('kala_gochara_coverage',      'generation',         'text'),
                 ('kala_gochara_coverage',      'partition_kind',     'text'),
                 ('kala_gochara_coverage',      'partition_key',      'text'),
                 ('kala_gochara_coverage',      'convention_id',      'text'),
                 ('kala_gochara_coverage',      'completed_horizon',  'tstzrange'),
                 ('kala_gochara_coverage',      'relations_searched', 'text[]'),
                 ('ka_gochara_contact',         'chart_id',           'uuid'),
                 ('ka_gochara_contact',         'generation',         'text'),
                 ('ka_gochara_contact',         'contact_id',         'uuid'),
                 ('ka_gochara_contact',         'body',               'text'),
                 ('ka_gochara_contact',         'relation_kind',      'text'),
                 ('ka_gochara_contact',         'physical_object_id', 'uuid'),
                 ('ka_gochara_contact',         'convention_id',      'text'),
                 ('ka_gochara_contact',         't_in',               'timestamp with time zone'),
                 ('ka_gochara_contact',         'solver_method',      'text'),
                 ('ka_gochara_contact',         'delta_lambda',       'real'),
                 ('ka_gochara_contact',         'delta_t',            'real'),
                 ('ka_gochara_physical_object', 'physical_object_id', 'uuid'),
                 ('ka_gochara_rule_path',       'path_id',            'text'),
                 ('ka_gochara_rule_path',       'rule_version',       'text'),
                 ('ka_gochara_predicate',       'predicate_id',       'text'),
                 ('ka_gochara_predicate',       'rule_version',       'text'),
                 ('ka_gochara_convention_bridge','kala_convention_id', 'text'),
                 ('ka_gochara_convention_bridge','sky_convention_id',  'text')) AS e(t, col, typ)
    LEFT JOIN pg_attribute a
      ON a.attrelid = to_regclass('public.' || e.t) AND a.attname = e.col AND NOT a.attisdropped
    WHERE a.attname IS NULL OR format_type(a.atttypid, a.atttypmod) IS DISTINCT FROM e.typ
    UNION ALL
    -- (b3) parent PK/UNIQUE definitions verified against pg_constraint
    SELECT 'parent_key_missing', e.t || ' must carry a PK/UNIQUE over ' || e.cols::text
    FROM (VALUES ('charts',                     ARRAY['id']),
                 ('kala_gochara_coverage',      ARRAY['chart_id','generation','partition_kind','partition_key']),
                 ('ka_gochara_contact',         ARRAY['chart_id','generation','contact_id','body','relation_kind','physical_object_id']),
                 ('ka_gochara_physical_object', ARRAY['physical_object_id']),
                 ('ka_gochara_rule_path',       ARRAY['path_id','rule_version']),
                 ('ka_gochara_rule_path_seal',  ARRAY['path_id','rule_version']),
                 ('ka_gochara_predicate',       ARRAY['predicate_id','rule_version']),
                 ('ka_gochara_convention_bridge', ARRAY['kala_convention_id'])) AS e(t, cols)
    WHERE to_regclass('public.' || e.t) IS NOT NULL
      AND NOT EXISTS (
        SELECT 1 FROM pg_constraint c
        WHERE c.conrelid = to_regclass('public.' || e.t) AND c.contype IN ('p','u')
          AND (SELECT array_agg(a.attname::text ORDER BY a.attname)
               FROM unnest(c.conkey) k JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = k)
              = (SELECT array_agg(x ORDER BY x) FROM unnest(e.cols) x))
    UNION ALL
    -- (b4) helper functions with exact signatures AND boolean return
    SELECT 'helper_function_missing', e.sig
    FROM (VALUES ('ka_gochara_frame_ok(text,text)'),
                 ('ka_gochara_string_array_ok(jsonb)'),
                 ('ka_gochara_finite_ok(double precision)'),
                 ('ka_gochara_finite_nonneg_ok(double precision)'),
                 ('ka_gochara_generation_is_sealed(uuid,text)')) AS e(sig)
    WHERE to_regprocedure('public.' || e.sig) IS NULL
       OR (SELECT format_type(p.prorettype, NULL) FROM pg_proc p
           WHERE p.oid = to_regprocedure('public.' || e.sig)) <> 'boolean'
    UNION ALL
    SELECT 'helper_function_missing', e.sig
    FROM (VALUES ('ka_gochara_refuse_truncate()'),
                 ('ka_gochara_require_sealed_rule_path()'),
                 ('ka_gochara_verify_definitions(text,jsonb)')) AS e(sig)
    WHERE to_regprocedure('public.' || e.sig) IS NULL
    UNION ALL
    -- (c1) ordered execution gate
    SELECT 'prerequisite_migration_not_applied', p.prefix
    FROM (VALUES ('1153_'), ('1154_')) AS p(prefix)
    WHERE to_regclass('public._migrations_applied') IS NOT NULL
      AND NOT EXISTS (SELECT 1 FROM _migrations_applied m WHERE starts_with(m.filename, p.prefix))
    UNION ALL
    SELECT 'migration_already_applied', m.filename
    FROM _migrations_applied m
    WHERE NOT replay AND to_regclass('public._migrations_applied') IS NOT NULL
      AND starts_with(m.filename, '1155_')
  )
  SELECT string_agg(f.failure || ' :: ' || f.detail, E'\n' ORDER BY f.failure, f.detail)
  INTO failures
  FROM f;
  IF failures IS NOT NULL THEN
    RAISE EXCEPTION 'preflight 1155 BLOCKED — migration 1155 must NOT be applied:% %', E'\n', failures;
  END IF;
  IF replay THEN
    RAISE NOTICE 'preflight 1155: deliberate replay — existence checks skipped; definitions are verified post-DDL';
  END IF;
  RAISE NOTICE 'preflight 1155: all checks passed';
END;
$$;

-- ── 0. Helpers — TOTAL booleans (F5) ──────────────────────────────────────

-- §7.1 typed precision payload: exactly {solver_method, delta_lambda,
-- delta_t}; solver_method a string in the 3-enum; uncertainties non-negative
-- numbers, or null exactly when the method is the clipped_truncated
-- placeholder. NULL/absent/non-string/extra keys ⇒ FALSE.
CREATE OR REPLACE FUNCTION public.ka_gochara_precision_ok(p jsonb)
RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
  SELECT p IS NOT NULL
     AND jsonb_typeof(p) = 'object'
     AND (p - 'solver_method' - 'delta_lambda' - 'delta_t') = '{}'::jsonb
     AND jsonb_typeof(p -> 'solver_method') = 'string'
     AND (p ->> 'solver_method') IN ('arc_index_bracket','swiss_refined','clipped_truncated')
     AND p ? 'delta_lambda' AND p ? 'delta_t'
     AND CASE WHEN (p ->> 'solver_method') = 'clipped_truncated'
              THEN jsonb_typeof(p -> 'delta_lambda') = 'null'
               AND jsonb_typeof(p -> 'delta_t') = 'null'
              ELSE jsonb_typeof(p -> 'delta_lambda') = 'number'
               AND jsonb_typeof(p -> 'delta_t') = 'number'
               AND (p ->> 'delta_lambda')::numeric >= 0
               AND (p ->> 'delta_t')::numeric >= 0
         END;
$$;

-- Interval arrays: non-NULL array, no NULL element, no empty range.
CREATE OR REPLACE FUNCTION public.ka_gochara_intervals_ok(iv tstzrange[])
RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
  SELECT iv IS NOT NULL
     AND NOT EXISTS (
       SELECT 1 FROM unnest(iv) r
       WHERE r IS NULL OR isempty(r)
     );
$$;

-- Sealed-generation immutability (F2): UPDATE/DELETE refused once the row's
-- (chart_id, generation) was ever published. Used by 1155 and 1156.
CREATE OR REPLACE FUNCTION public.ka_gochara_sealed_generation_guard()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
BEGIN
  IF public.ka_gochara_generation_is_sealed(OLD.chart_id, OLD.generation) THEN
    RAISE EXCEPTION '% is publication-immutable (GOCHARA_DESIGN_SPECS_v1_4 §10.1; F2): (chart_id %, generation %) is SEALED (was published) — % refused; a re-evaluation is a new generation',
      TG_TABLE_NAME, OLD.chart_id, OLD.generation, TG_OP;
  END IF;
  IF TG_OP = 'DELETE' THEN
    RETURN OLD;
  END IF;
  RETURN NEW;
END;
$$;

-- ── 1. relationship_record (§1.1 + §3.1 + admission persistence) ──────────

CREATE TABLE IF NOT EXISTS public.ka_gochara_relationship_record (
  record_id         UUID PRIMARY KEY,
  -- §1.1: deterministic hash of the natural key
  --   (chart_id, generation, event_class, affected_person, frame, agent,
  --    relation, object_id, object_role, contact_id, path_id, rule_version,
  --    prerequisites, source_text) — generation and contact_id are IN the key.
  -- The prerequisites component reads the ka_gochara_record_prerequisite
  -- membership rows; the hash is writer-computed, not re-implemented in SQL.
  chart_id          UUID NOT NULL REFERENCES public.charts(id),
  generation        TEXT NOT NULL,               -- '4.1'/'5.0'… (§1.1 NK-3)
  contact_id        UUID,                        -- NOT NULL on transit rows (CHECK);
                                                 --   ownership-bound FK below (F1/F7)
  event_class       TEXT NOT NULL,
  affected_person   TEXT NOT NULL,
  frame_kind        TEXT NOT NULL,
  frame_arg         TEXT,                        -- typed by ka_gochara_frame_ok (§0)
  agent             TEXT NOT NULL,               -- the transiting (or period) body
  relation          TEXT NOT NULL,
  object_id         UUID NOT NULL REFERENCES public.ka_gochara_physical_object(physical_object_id),
  object_kind       TEXT NOT NULL,
  object_role       TEXT NOT NULL,
  path_id           TEXT NOT NULL,               -- mandatory complete version-bound
  rule_version      TEXT NOT NULL,               --   reference (sealed version — F3)
  temporal_support_state TEXT NOT NULL,          -- §1.1 tagged states (typed)
  temporal_support_grain TEXT,                   -- evaluation grain; NULL iff uncomputed
  temporal_support_intervals TSTZRANGE[] NOT NULL DEFAULT '{}',
  coverage_partition_kind TEXT NOT NULL,         -- the coverage handle IS the 1081
  coverage_partition_key  TEXT NOT NULL,         --   partition, scope-bound + applicable
  precision         JSONB,                       -- {solver_method, delta_lambda, delta_t}
                                                 --   (§7.1); REQUIRED on transit rows,
                                                 --   restates the contact (guard)
  source_text       TEXT,
  source_page       TEXT,
  source_fact_ids   JSONB NOT NULL,              -- typed string array; [] only on fixtures
  fixture           BOOLEAN NOT NULL DEFAULT false,
  provenance        TEXT NOT NULL,
  operator_role     TEXT NOT NULL,
  ruling_ref        TEXT,
  admission_state   TEXT NOT NULL,               -- the persisted §2.2 inv 2 / S:103
                                                 --   result; finalised at commit (F5)
  house_from_frame  INTEGER,                     -- §1.2 inv 5: frame arithmetic, stored
                                                 --   at evaluation time
  evidence_for_occurrence     REAL,              -- §3.1: rank-only, never a gate; finite ≥ 0
  evidence_against_occurrence REAL,              -- §3.1: never netted; finite ≥ 0
  outcome_valence_for_native  TEXT NOT NULL,     -- §3.1: 'unqualified' is the declared
                                                 --   honest state — SQL NULL is not a valence
  severity          REAL,                        -- finite
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT kgrr_canonical_chart_ck
    CHECK (chart_id = '482012f1-710e-4a25-994a-93821f5871aa'::uuid),
    -- D-SCOPE disposition: canonical chart only (S:89).
  CONSTRAINT kgrr_event_class_ck CHECK (event_class IN (
    'achievement_recognition','bereavement','birth_anchor',
    'business_launch','career_advancement','career_change',
    'career_entry','career_setback','childbirth',
    'chronic_onset','education_milestone','exam_outcome',
    'financial_deception','foreign_settlement','illness_acute',
    'major_gain','major_loss','marriage','parental_event',
    'property_acquisition','psychological_arc','relocation',
    'romantic_start','separation','spiritual_turn','surgery',
    'travel_event')),
    -- the 27 classes of EVALUATION_PROTOCOL_v2_2 §2 — the sole enumeration
  CONSTRAINT kgrr_affected_person_ck CHECK (affected_person IN
    ('native','father','mother','spouse','child','sibling')),
  CONSTRAINT kgrr_frame_ck CHECK (public.ka_gochara_frame_ok(frame_kind, frame_arg) IS TRUE),
  CONSTRAINT kgrr_relative_frame_ck
    CHECK (affected_person = 'native' OR frame_kind <> 'moon'),
    -- §1.2 inv 6 / S:126-128: a relative's event never reads the native's
    -- Moon frame; bhavat_bhavam frames carry relatives
  CONSTRAINT kgrr_agent_ck CHECK (agent IN
    ('sun','moon','mars','mercury','jupiter','venus','saturn','rahu','ketu')),
  CONSTRAINT kgrr_relation_ck CHECK (relation IN
    ('residence','aspect','conjunction',
     'dispositorship','association','ownership','occupancy','period_running')),
  CONSTRAINT kgrr_object_kind_ck CHECK (object_kind IN
    ('degree_point','sign_span','star','derived_point',
     'varga_position','saham','house_span','house_lord')),
  CONSTRAINT kgrr_object_role_ck CHECK (object_role IN
    ('lord','occupant','karaka','dispositor','maraka_of_house',
     'period_lord','yoga_constituent','pada','signature_house')),
  CONSTRAINT kgrr_path_fk FOREIGN KEY (path_id, rule_version)
    REFERENCES public.ka_gochara_rule_path (path_id, rule_version),
  CONSTRAINT kgrr_contact_fk
    FOREIGN KEY (chart_id, generation, contact_id, agent, relation, object_id)
    REFERENCES public.ka_gochara_contact (chart_id, generation, contact_id, body, relation_kind, physical_object_id),
    -- F1/F7: the contact must be OWNED by this chart+generation and agree on
    -- agent, physical relation and object. MATCH SIMPLE + contact_id NULL on
    -- natal rows (CHECK below) keeps the natal branch out of this FK.
  CONSTRAINT kgrr_coverage_fk
    FOREIGN KEY (chart_id, generation, coverage_partition_kind, coverage_partition_key)
    REFERENCES public.kala_gochara_coverage (chart_id, generation, partition_kind, partition_key),
    -- existence in the record's own scope; APPLICABILITY is the guard (F7)
  CONSTRAINT kgrr_coverage_kind_ck CHECK (coverage_partition_kind IN
    ('body_target','event_class','moon_on_demand','bodies_on_demand')),
    -- the 1081+1087 partition-kind domain, mirrored
  CONSTRAINT kgrr_support_state_ck CHECK (temporal_support_state IN
    ('uncomputed','computed_empty','computed')),
  CONSTRAINT kgrr_support_cardinality_ck CHECK (
    (temporal_support_state = 'uncomputed'
       AND temporal_support_grain IS NULL
       AND COALESCE(array_length(temporal_support_intervals, 1), 0) = 0)
    OR (temporal_support_state = 'computed_empty'
       AND temporal_support_grain IS NOT NULL
       AND COALESCE(array_length(temporal_support_intervals, 1), 0) = 0)
    OR (temporal_support_state = 'computed'
       AND temporal_support_grain IS NOT NULL
       AND COALESCE(array_length(temporal_support_intervals, 1), 0) >= 1)
  ),
    -- §1.1/S:103: the three tagged states are never conflated
  CONSTRAINT kgrr_support_intervals_ck
    CHECK (public.ka_gochara_intervals_ok(temporal_support_intervals) IS TRUE),
  CONSTRAINT kgrr_house_from_frame_ck
    CHECK (house_from_frame IS NULL OR house_from_frame BETWEEN 1 AND 12),
  CONSTRAINT kgrr_evaluated_has_house_ck
    CHECK (temporal_support_state = 'uncomputed' OR house_from_frame IS NOT NULL),
    -- §1.2 inv 5: the frame arithmetic is stored at evaluation time — an
    -- evaluated row cannot omit it
  CONSTRAINT kgrr_precision_typed_ck
    CHECK (precision IS NULL OR public.ka_gochara_precision_ok(precision) IS TRUE),
  CONSTRAINT kgrr_transit_natal_ck CHECK (
    (relation IN ('residence','aspect','conjunction')
       AND contact_id IS NOT NULL AND precision IS NOT NULL)
    OR
    (relation IN ('dispositorship','association','ownership','occupancy',
                  'period_running')
       AND contact_id IS NULL AND precision IS NULL)
  ),
    -- §1.1/§7: transit rows carry a contact AND their precision payload;
    -- natal-fact rows carry neither; the two never mix (F6a)
  CONSTRAINT kgrr_source_fact_ids_ck
    CHECK (public.ka_gochara_string_array_ok(source_fact_ids) IS TRUE
           AND (jsonb_array_length(source_fact_ids) > 0 OR fixture)),
    -- §1.1 source-fact lineage: [null] / [123] / ["a b"] fail; [] only on
    -- synthetic-fixture rows (fixture = true); resolvability is the writer's
    -- boundary obligation (header)
  CONSTRAINT kgrr_provenance_ck CHECK (provenance IN
    ('verse_cited','uncited_extension')),
  CONSTRAINT kgrr_operator_role_ck CHECK (operator_role IN ('scored','testimony')),
  CONSTRAINT kgrr_ruling_ck
    CHECK (provenance <> 'uncited_extension' OR ruling_ref IS NOT NULL),
    -- S:110 as frozen: uncited_extension REQUIRES a ruling; never forbidden otherwise
  CONSTRAINT kgrr_citation_ck
    CHECK (provenance <> 'verse_cited'
           OR (source_text IS NOT NULL AND source_page IS NOT NULL)),
    -- S:62-64/106-108: a verse_cited row carries its citation
  CONSTRAINT kgrr_admission_state_ck CHECK (admission_state IN
    ('admitted','unqualified','not_admitted')),
  CONSTRAINT kgrr_evidence_finite_ck
    CHECK (public.ka_gochara_finite_nonneg_ok(evidence_for_occurrence) IS TRUE
           AND public.ka_gochara_finite_nonneg_ok(evidence_against_occurrence) IS TRUE),
    -- F11: finite and non-negative; no upper bound of one (amendment 7)
  CONSTRAINT kgrr_severity_finite_ck
    CHECK (public.ka_gochara_finite_ok(severity) IS TRUE),
  CONSTRAINT kgrr_valence_ck CHECK (outcome_valence_for_native IN
    ('favourable','adverse','mixed','unqualified')),
  -- FK targets: prerequisite membership (same chart/generation) and eval-window
  -- membership (same chart/generation/class/path — F7).
  CONSTRAINT kgrr_identity_uq UNIQUE (record_id, chart_id, generation),
  CONSTRAINT kgrr_membership_uq
    UNIQUE (record_id, chart_id, generation, event_class, path_id, rule_version)
);

COMMENT ON TABLE public.ka_gochara_relationship_record IS
  'Relationship record (GOCHARA_DESIGN_SPECS_v1_4 §1.1): one row per (event_class, '
  'affected_person, frame, agent, relation, object, role, path). Transit rows FK the '
  'OWNED contact ledger row with agent/relation/object consistency (F1/F7); coverage is '
  'an existing (chart, generation, partition) row proven APPLICABLE by trigger (F7). '
  'temporal_support is typed with state-dependent cardinality. admission_state + '
  'ka_gochara_record_prerequisite.result are finalised at COMMIT against the path''s '
  'declared prerequisites (F5). Only a sealed rule version may produce a row (F3). A '
  'sealed generation refuses UPDATE/DELETE (F2); TRUNCATE refused. Root key (§2.1 '
  'R4-S01): contact_id on transit rows, object_id on natal rows — derivable.';

-- Read shapes the evaluator and rehearsal actually use.
CREATE INDEX IF NOT EXISTS idx_kgrr_chart_gen ON public.ka_gochara_relationship_record
  (chart_id, generation, event_class);
CREATE INDEX IF NOT EXISTS idx_kgrr_contact ON public.ka_gochara_relationship_record
  (chart_id, generation, contact_id) WHERE contact_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_kgrr_object ON public.ka_gochara_relationship_record
  (object_id);
CREATE INDEX IF NOT EXISTS idx_kgrr_path ON public.ka_gochara_relationship_record
  (path_id, rule_version);
CREATE INDEX IF NOT EXISTS idx_kgrr_coverage ON public.ka_gochara_relationship_record
  (chart_id, generation, coverage_partition_kind, coverage_partition_key);

-- ── 2. Prerequisite membership + evaluated results ─────────────────────────

CREATE TABLE IF NOT EXISTS public.ka_gochara_record_prerequisite (
  record_id              UUID NOT NULL,
  chart_id               UUID NOT NULL,          -- ownership scope, bound to the record
  generation             TEXT NOT NULL,
  ordinal                INTEGER NOT NULL,       -- §1.1: ordered, cheapest necessary
                                                 --   predicate first
  predicate_id           TEXT NOT NULL,
  predicate_rule_version TEXT NOT NULL,
  result                 TEXT,                   -- evaluated state; NULL = not evaluated
                                                 --   (counts as unknown for admission)

  PRIMARY KEY (record_id, ordinal),
  CONSTRAINT kgrpr_ordinal_ck CHECK (ordinal >= 1),
  CONSTRAINT kgrpr_result_ck CHECK (result IS NULL OR result IN
    ('true','false','unknown')),
  CONSTRAINT kgrpr_record_fk FOREIGN KEY (record_id, chart_id, generation)
    REFERENCES public.ka_gochara_relationship_record (record_id, chart_id, generation)
    ON DELETE CASCADE,
    -- §N.3 lifecycle: a candidate rebuild removes a record's membership with
    -- it; a sealed generation's record refuses the DELETE before the cascade
  CONSTRAINT kgrpr_predicate_fk FOREIGN KEY (predicate_id, predicate_rule_version)
    REFERENCES public.ka_gochara_predicate (predicate_id, rule_version),
  CONSTRAINT kgrpr_no_dup_uq
    UNIQUE (record_id, predicate_id, predicate_rule_version)
);

COMMENT ON TABLE public.ka_gochara_record_prerequisite IS
  'Record prerequisite membership: ordered, version-bound composite references into '
  'ka_gochara_predicate with real FK enforcement, bound to the record''s own '
  '(chart_id, generation). result persists the per-prerequisite evaluated state '
  '{true,false,unknown} (NULL = not evaluated). At COMMIT the membership must equal the '
  'path version''s declared list and admission_state must equal the state derived from '
  'the results (F5; §2.2 inv 2, S:103).';

CREATE INDEX IF NOT EXISTS idx_kgrpr_record ON public.ka_gochara_record_prerequisite
  (chart_id, generation, record_id);

-- ── 3. Coverage applicability (F7) ────────────────────────────────────────

CREATE OR REPLACE FUNCTION public.ka_gochara_record_coverage_guard()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
DECLARE
  cov     record;
  ct      record;
  bridged text;
  iv      tstzrange;
BEGIN
  SELECT c.partition_kind, c.partition_key, c.convention_id, c.completed_horizon, c.relations_searched
    INTO cov
  FROM public.kala_gochara_coverage c
  WHERE c.chart_id = NEW.chart_id AND c.generation = NEW.generation
    AND c.partition_kind = NEW.coverage_partition_kind
    AND c.partition_key = NEW.coverage_partition_key;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'ka_gochara_relationship_record coverage unresolvable (§1.1 coverage_ref): no kala_gochara_coverage partition (%, %) for (chart %, generation %)',
      NEW.coverage_partition_kind, NEW.coverage_partition_key, NEW.chart_id, NEW.generation;
  END IF;

  IF cov.partition_kind = 'event_class' AND cov.partition_key <> NEW.event_class THEN
    RAISE EXCEPTION 'ka_gochara_relationship_record coverage not applicable (F7): event_class partition ''%'' does not cover class ''%''',
      cov.partition_key, NEW.event_class;
  END IF;
  IF cov.partition_kind = 'body_target'
     AND lower(split_part(cov.partition_key, ':', 1)) <> NEW.agent THEN
    RAISE EXCEPTION 'ka_gochara_relationship_record coverage not applicable (F7): body_target partition ''%'' does not cover agent ''%''',
      cov.partition_key, NEW.agent;
  END IF;

  IF NEW.contact_id IS NOT NULL THEN
    -- transit row
    IF (NEW.agent = 'moon') <> (cov.partition_kind = 'moon_on_demand') THEN
      RAISE EXCEPTION 'ka_gochara_relationship_record coverage not applicable (F7; §6.1 Moon-on-demand, O-SS-4): agent ''%'' with partition kind ''%'' — a Moon contact is covered only by a moon_on_demand partition, and vice versa',
        NEW.agent, cov.partition_kind;
    END IF;
    IF NOT (NEW.relation = ANY (COALESCE(cov.relations_searched, '{}'))) THEN
      RAISE EXCEPTION 'ka_gochara_relationship_record coverage not applicable (F7): relation ''%'' is not among the partition''s relations_searched %',
        NEW.relation, cov.relations_searched;
    END IF;
    SELECT k.t_in, k.convention_id, k.solver_method, k.delta_lambda, k.delta_t
      INTO ct
    FROM public.ka_gochara_contact k
    WHERE k.chart_id = NEW.chart_id AND k.generation = NEW.generation
      AND k.contact_id = NEW.contact_id;
    IF NOT FOUND THEN
      RAISE EXCEPTION 'ka_gochara_relationship_record contact % is not owned by (chart %, generation %) (F1)',
        NEW.contact_id, NEW.chart_id, NEW.generation;
    END IF;
    SELECT b.sky_convention_id INTO bridged
    FROM public.ka_gochara_convention_bridge b
    WHERE b.kala_convention_id = cov.convention_id;
    IF bridged IS DISTINCT FROM ct.convention_id THEN
      RAISE EXCEPTION 'ka_gochara_relationship_record coverage not applicable (F7): partition convention ''%'' is not bridged to the contact''s sky convention ''%'' (ka_gochara_convention_bridge)',
        cov.convention_id, ct.convention_id;
    END IF;
    IF NOT (cov.completed_horizon @> ct.t_in) THEN
      RAISE EXCEPTION 'ka_gochara_relationship_record coverage not applicable (F7; §6.1 C7): contact t_in % lies outside the partition''s completed_horizon %',
        ct.t_in, cov.completed_horizon;
    END IF;
    -- a malformed payload is the CHECK constraint's finding (kgrr_precision_typed_ck);
    -- only a well-formed payload is compared against the contact it restates
    IF public.ka_gochara_precision_ok(NEW.precision) IS TRUE
       AND ((NEW.precision ->> 'solver_method') IS DISTINCT FROM ct.solver_method
            OR ((NEW.precision ->> 'delta_lambda')::real) IS DISTINCT FROM ct.delta_lambda
            OR ((NEW.precision ->> 'delta_t')::real) IS DISTINCT FROM ct.delta_t) THEN
      RAISE EXCEPTION 'ka_gochara_relationship_record.precision % restates the contact''s solved precision (%, %, %) incorrectly (CLAUDE.md §N.5: a restated value never disagrees with the fact it cites)',
        NEW.precision, ct.solver_method, ct.delta_lambda, ct.delta_t;
    END IF;
  ELSE
    -- natal-fact row
    IF cov.partition_kind = 'moon_on_demand' THEN
      RAISE EXCEPTION 'ka_gochara_relationship_record coverage not applicable (F7): a natal-fact row never references a moon_on_demand partition';
    END IF;
  END IF;

  FOREACH iv IN ARRAY NEW.temporal_support_intervals LOOP
    IF NOT (cov.completed_horizon @> iv) THEN
      RAISE EXCEPTION 'ka_gochara_relationship_record coverage not applicable (F7): support interval % lies outside the partition''s completed_horizon %',
        iv, cov.completed_horizon;
    END IF;
  END LOOP;
  RETURN NEW;
END;
$$;

-- ── 4. Finalisation at the atomic write boundary (F5) ─────────────────────

CREATE OR REPLACE FUNCTION public.ka_gochara_record_finalize_check()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
DECLARE
  rid       uuid;
  rec       record;
  mismatch  integer;
  n_false   integer;
  n_unknown integer;
  derived   text;
BEGIN
  rid := CASE WHEN TG_OP = 'DELETE' THEN OLD.record_id ELSE NEW.record_id END;
  SELECT r.record_id, r.path_id, r.rule_version, r.admission_state INTO rec
  FROM public.ka_gochara_relationship_record r
  WHERE r.record_id = rid;
  IF NOT FOUND THEN
    RETURN NULL;   -- the record left with this transaction; nothing to finalise
  END IF;

  -- (i) membership equals the path version's declared prerequisites, in order
  SELECT count(*) INTO mismatch
  FROM (
    (SELECT p.ordinal, p.predicate_id, p.predicate_rule_version
     FROM public.ka_gochara_rule_path_prerequisite p
     WHERE p.path_id = rec.path_id AND p.rule_version = rec.rule_version
     EXCEPT
     SELECT m.ordinal, m.predicate_id, m.predicate_rule_version
     FROM public.ka_gochara_record_prerequisite m
     WHERE m.record_id = rid)
    UNION ALL
    (SELECT m.ordinal, m.predicate_id, m.predicate_rule_version
     FROM public.ka_gochara_record_prerequisite m
     WHERE m.record_id = rid
     EXCEPT
     SELECT p.ordinal, p.predicate_id, p.predicate_rule_version
     FROM public.ka_gochara_rule_path_prerequisite p
     WHERE p.path_id = rec.path_id AND p.rule_version = rec.rule_version)
  ) d;
  IF mismatch > 0 THEN
    RAISE EXCEPTION 'ka_gochara_relationship_record % finalisation failed (F5; §1.1/§1.2 inv 7): its prerequisite membership does not equal the declared prerequisites of rule version (%, %) — a record evaluates exactly its path''s necessary predicates, in order',
      rid, rec.path_id, rec.rule_version;
  END IF;

  -- (ii) admission_state is the state derived from the results
  SELECT count(*) FILTER (WHERE m.result = 'false'),
         count(*) FILTER (WHERE m.result IS DISTINCT FROM 'true' AND m.result IS DISTINCT FROM 'false')
    INTO n_false, n_unknown
  FROM public.ka_gochara_record_prerequisite m
  WHERE m.record_id = rid;
  derived := CASE WHEN n_false > 0 THEN 'not_admitted'
                  WHEN n_unknown > 0 THEN 'unqualified'
                  ELSE 'admitted' END;
  IF rec.admission_state <> derived THEN
    RAISE EXCEPTION 'ka_gochara_relationship_record % finalisation failed (F5; §2.2 inv 2, S:103): admission_state ''%'' contradicts its prerequisite results (derived ''%'': any false ⇒ not_admitted; else any unknown/unevaluated ⇒ unqualified; else admitted)',
      rid, rec.admission_state, derived;
  END IF;
  RETURN NULL;
END;
$$;

-- ── 5. Triggers ────────────────────────────────────────────────────────────

DROP TRIGGER IF EXISTS ka_gochara_rr_sealed_path_check ON public.ka_gochara_relationship_record;
CREATE TRIGGER ka_gochara_rr_sealed_path_check
  BEFORE INSERT OR UPDATE OF path_id, rule_version ON public.ka_gochara_relationship_record
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_require_sealed_rule_path();
DROP TRIGGER IF EXISTS ka_gochara_rr_coverage_guard ON public.ka_gochara_relationship_record;
CREATE TRIGGER ka_gochara_rr_coverage_guard
  BEFORE INSERT OR UPDATE ON public.ka_gochara_relationship_record
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_record_coverage_guard();
DROP TRIGGER IF EXISTS ka_gochara_rr_sealed_generation_guard ON public.ka_gochara_relationship_record;
CREATE TRIGGER ka_gochara_rr_sealed_generation_guard
  BEFORE UPDATE OR DELETE ON public.ka_gochara_relationship_record
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_sealed_generation_guard();
DROP TRIGGER IF EXISTS ka_gochara_rr_finalize ON public.ka_gochara_relationship_record;
CREATE CONSTRAINT TRIGGER ka_gochara_rr_finalize
  AFTER INSERT OR UPDATE ON public.ka_gochara_relationship_record
  DEFERRABLE INITIALLY DEFERRED
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_record_finalize_check();
DROP TRIGGER IF EXISTS ka_gochara_rr_no_truncate ON public.ka_gochara_relationship_record;
CREATE TRIGGER ka_gochara_rr_no_truncate
  BEFORE TRUNCATE ON public.ka_gochara_relationship_record
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_refuse_truncate();

DROP TRIGGER IF EXISTS ka_gochara_rpr_sealed_generation_guard ON public.ka_gochara_record_prerequisite;
CREATE TRIGGER ka_gochara_rpr_sealed_generation_guard
  BEFORE UPDATE OR DELETE ON public.ka_gochara_record_prerequisite
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_sealed_generation_guard();
DROP TRIGGER IF EXISTS ka_gochara_rpr_finalize ON public.ka_gochara_record_prerequisite;
CREATE CONSTRAINT TRIGGER ka_gochara_rpr_finalize
  AFTER INSERT OR UPDATE OR DELETE ON public.ka_gochara_record_prerequisite
  DEFERRABLE INITIALLY DEFERRED
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_record_finalize_check();
DROP TRIGGER IF EXISTS ka_gochara_rpr_no_truncate ON public.ka_gochara_record_prerequisite;
CREATE TRIGGER ka_gochara_rpr_no_truncate
  BEFORE TRUNCATE ON public.ka_gochara_record_prerequisite
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_refuse_truncate();

-- ── 6. Post-DDL verification (F9): helper self-tests, then definitions ────
DO $$
BEGIN
  IF NOT (public.ka_gochara_precision_ok(NULL) IS FALSE
          AND public.ka_gochara_precision_ok('{"solver_method":null,"delta_lambda":0.001,"delta_t":60}'::jsonb) IS FALSE
          AND public.ka_gochara_precision_ok('{"solver_method":"swiss_refined","delta_lambda":-0.001,"delta_t":60}'::jsonb) IS FALSE
          AND public.ka_gochara_precision_ok('{"solver_method":"swiss_refined","delta_lambda":0.001}'::jsonb) IS FALSE
          AND public.ka_gochara_precision_ok('{"solver_method":"swiss_refined","delta_lambda":0.001,"delta_t":60,"x":1}'::jsonb) IS FALSE
          AND public.ka_gochara_precision_ok('{"solver_method":"clipped_truncated","delta_lambda":0.001,"delta_t":60}'::jsonb) IS FALSE
          AND public.ka_gochara_precision_ok('{"solver_method":"clipped_truncated","delta_lambda":null,"delta_t":null}'::jsonb) IS TRUE
          AND public.ka_gochara_precision_ok('{"solver_method":"swiss_refined","delta_lambda":0.001,"delta_t":60}'::jsonb) IS TRUE
          AND public.ka_gochara_intervals_ok(NULL) IS FALSE
          AND public.ka_gochara_intervals_ok(ARRAY['empty'::tstzrange]) IS FALSE
          AND public.ka_gochara_intervals_ok(ARRAY[NULL::tstzrange]) IS FALSE
          AND public.ka_gochara_intervals_ok('{}'::tstzrange[]) IS TRUE) THEN
    RAISE EXCEPTION 'migration 1155 post-DDL verification failed (amendment 8): helper self-test failed';
  END IF;
END;
$$;

DO $$
BEGIN
  PERFORM public.ka_gochara_verify_definitions('1155', $expected$
{
  "functions": {
    "ka_gochara_intervals_ok(tstzrange[])": [
      "boolean",
      "i",
      "sql",
      false,
      "f"
    ],
    "ka_gochara_precision_ok(jsonb)": [
      "boolean",
      "i",
      "sql",
      false,
      "f"
    ],
    "ka_gochara_record_coverage_guard()": [
      "trigger",
      "v",
      "plpgsql",
      false,
      "f"
    ],
    "ka_gochara_record_finalize_check()": [
      "trigger",
      "v",
      "plpgsql",
      false,
      "f"
    ],
    "ka_gochara_sealed_generation_guard()": [
      "trigger",
      "v",
      "plpgsql",
      false,
      "f"
    ]
  },
  "tables": {
    "ka_gochara_record_prerequisite": {
      "columns": {
        "chart_id": [
          "uuid",
          true
        ],
        "generation": [
          "text",
          true
        ],
        "ordinal": [
          "integer",
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
        "record_id": [
          "uuid",
          true
        ],
        "result": [
          "text",
          false
        ]
      },
      "constraints": {
        "ka_gochara_record_prerequisite_pkey": [
          "p",
          "primarykeyrecord_id,ordinal",
          true
        ],
        "kgrpr_no_dup_uq": [
          "u",
          "uniquerecord_id,predicate_id,predicate_rule_version",
          true
        ],
        "kgrpr_ordinal_ck": [
          "c",
          "checkordinal>=1",
          true
        ],
        "kgrpr_predicate_fk": [
          "f",
          "foreignkeypredicate_id,predicate_rule_versionreferenceska_gochara_predicatepredicate_id,rule_version",
          true
        ],
        "kgrpr_record_fk": [
          "f",
          "foreignkeyrecord_id,chart_id,generationreferenceska_gochara_relationship_recordrecord_id,chart_id,generationondeletecascade",
          true
        ],
        "kgrpr_result_ck": [
          "c",
          "checkresultisnullorresult=anyarray['true','false','unknown']",
          true
        ]
      },
      "indexes": {
        "idx_kgrpr_record": "createindexidx_kgrpr_recordonka_gochara_record_prerequisiteusingbtreechart_id,generation,record_id",
        "ka_gochara_record_prerequisite_pkey": "createuniqueindexka_gochara_record_prerequisite_pkeyonka_gochara_record_prerequisiteusingbtreerecord_id,ordinal",
        "kgrpr_no_dup_uq": "createuniqueindexkgrpr_no_dup_uqonka_gochara_record_prerequisiteusingbtreerecord_id,predicate_id,predicate_rule_version"
      },
      "triggers": {
        "ka_gochara_rpr_finalize": [
          "createconstrainttriggerka_gochara_rpr_finalizeafterinsertordeleteorupdateonka_gochara_record_prerequisitedeferrableinitiallydeferredforeachrowexecutefunctionka_gochara_record_finalize_check",
          "O"
        ],
        "ka_gochara_rpr_no_truncate": [
          "createtriggerka_gochara_rpr_no_truncatebeforetruncateonka_gochara_record_prerequisiteforeachstatementexecutefunctionka_gochara_refuse_truncate",
          "O"
        ],
        "ka_gochara_rpr_sealed_generation_guard": [
          "createtriggerka_gochara_rpr_sealed_generation_guardbeforedeleteorupdateonka_gochara_record_prerequisiteforeachrowexecutefunctionka_gochara_sealed_generation_guard",
          "O"
        ]
      }
    },
    "ka_gochara_relationship_record": {
      "columns": {
        "admission_state": [
          "text",
          true
        ],
        "affected_person": [
          "text",
          true
        ],
        "agent": [
          "text",
          true
        ],
        "chart_id": [
          "uuid",
          true
        ],
        "contact_id": [
          "uuid",
          false
        ],
        "coverage_partition_key": [
          "text",
          true
        ],
        "coverage_partition_kind": [
          "text",
          true
        ],
        "created_at": [
          "timestamp with time zone",
          true
        ],
        "event_class": [
          "text",
          true
        ],
        "evidence_against_occurrence": [
          "real",
          false
        ],
        "evidence_for_occurrence": [
          "real",
          false
        ],
        "fixture": [
          "boolean",
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
        "generation": [
          "text",
          true
        ],
        "house_from_frame": [
          "integer",
          false
        ],
        "object_id": [
          "uuid",
          true
        ],
        "object_kind": [
          "text",
          true
        ],
        "object_role": [
          "text",
          true
        ],
        "operator_role": [
          "text",
          true
        ],
        "outcome_valence_for_native": [
          "text",
          true
        ],
        "path_id": [
          "text",
          true
        ],
        "precision": [
          "jsonb",
          false
        ],
        "provenance": [
          "text",
          true
        ],
        "record_id": [
          "uuid",
          true
        ],
        "relation": [
          "text",
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
        "severity": [
          "real",
          false
        ],
        "source_fact_ids": [
          "jsonb",
          true
        ],
        "source_page": [
          "text",
          false
        ],
        "source_text": [
          "text",
          false
        ],
        "temporal_support_grain": [
          "text",
          false
        ],
        "temporal_support_intervals": [
          "tstzrange[]",
          true
        ],
        "temporal_support_state": [
          "text",
          true
        ]
      },
      "constraints": {
        "ka_gochara_relationship_record_chart_id_fkey": [
          "f",
          "foreignkeychart_idreferenceschartsid",
          true
        ],
        "ka_gochara_relationship_record_object_id_fkey": [
          "f",
          "foreignkeyobject_idreferenceska_gochara_physical_objectphysical_object_id",
          true
        ],
        "ka_gochara_relationship_record_pkey": [
          "p",
          "primarykeyrecord_id",
          true
        ],
        "kgrr_admission_state_ck": [
          "c",
          "checkadmission_state=anyarray['admitted','unqualified','not_admitted']",
          true
        ],
        "kgrr_affected_person_ck": [
          "c",
          "checkaffected_person=anyarray['native','father','mother','spouse','child','sibling']",
          true
        ],
        "kgrr_agent_ck": [
          "c",
          "checkagent=anyarray['sun','moon','mars','mercury','jupiter','venus','saturn','rahu','ketu']",
          true
        ],
        "kgrr_canonical_chart_ck": [
          "c",
          "checkchart_id='482012f1-710e-4a25-994a-93821f5871aa'",
          true
        ],
        "kgrr_citation_ck": [
          "c",
          "checkprovenance<>'verse_cited'orsource_textisnotnullandsource_pageisnotnull",
          true
        ],
        "kgrr_contact_fk": [
          "f",
          "foreignkeychart_id,generation,contact_id,agent,relation,object_idreferenceska_gochara_contactchart_id,generation,contact_id,body,relation_kind,physical_object_id",
          true
        ],
        "kgrr_coverage_fk": [
          "f",
          "foreignkeychart_id,generation,coverage_partition_kind,coverage_partition_keyreferenceskala_gochara_coveragechart_id,generation,partition_kind,partition_key",
          true
        ],
        "kgrr_coverage_kind_ck": [
          "c",
          "checkcoverage_partition_kind=anyarray['body_target','event_class','moon_on_demand','bodies_on_demand']",
          true
        ],
        "kgrr_evaluated_has_house_ck": [
          "c",
          "checktemporal_support_state='uncomputed'orhouse_from_frameisnotnull",
          true
        ],
        "kgrr_event_class_ck": [
          "c",
          "checkevent_class=anyarray['achievement_recognition','bereavement','birth_anchor','business_launch','career_advancement','career_change','career_entry','career_setback','childbirth','chronic_onset','education_milestone','exam_outcome','financial_deception','foreign_settlement','illness_acute','major_gain','major_loss','marriage','parental_event','property_acquisition','psychological_arc','relocation','romantic_start','separation','spiritual_turn','surgery','travel_event']",
          true
        ],
        "kgrr_evidence_finite_ck": [
          "c",
          "checkka_gochara_finite_nonneg_okevidence_for_occurrenceistrueandka_gochara_finite_nonneg_okevidence_against_occurrenceistrue",
          true
        ],
        "kgrr_frame_ck": [
          "c",
          "checkka_gochara_frame_okframe_kind,frame_argistrue",
          true
        ],
        "kgrr_house_from_frame_ck": [
          "c",
          "checkhouse_from_frameisnullorhouse_from_frame>=1andhouse_from_frame<=12",
          true
        ],
        "kgrr_identity_uq": [
          "u",
          "uniquerecord_id,chart_id,generation",
          true
        ],
        "kgrr_membership_uq": [
          "u",
          "uniquerecord_id,chart_id,generation,event_class,path_id,rule_version",
          true
        ],
        "kgrr_object_kind_ck": [
          "c",
          "checkobject_kind=anyarray['degree_point','sign_span','star','derived_point','varga_position','saham','house_span','house_lord']",
          true
        ],
        "kgrr_object_role_ck": [
          "c",
          "checkobject_role=anyarray['lord','occupant','karaka','dispositor','maraka_of_house','period_lord','yoga_constituent','pada','signature_house']",
          true
        ],
        "kgrr_operator_role_ck": [
          "c",
          "checkoperator_role=anyarray['scored','testimony']",
          true
        ],
        "kgrr_path_fk": [
          "f",
          "foreignkeypath_id,rule_versionreferenceska_gochara_rule_pathpath_id,rule_version",
          true
        ],
        "kgrr_precision_typed_ck": [
          "c",
          "check\"precision\"isnullorka_gochara_precision_ok\"precision\"istrue",
          true
        ],
        "kgrr_provenance_ck": [
          "c",
          "checkprovenance=anyarray['verse_cited','uncited_extension']",
          true
        ],
        "kgrr_relation_ck": [
          "c",
          "checkrelation=anyarray['residence','aspect','conjunction','dispositorship','association','ownership','occupancy','period_running']",
          true
        ],
        "kgrr_relative_frame_ck": [
          "c",
          "checkaffected_person='native'orframe_kind<>'moon'",
          true
        ],
        "kgrr_ruling_ck": [
          "c",
          "checkprovenance<>'uncited_extension'orruling_refisnotnull",
          true
        ],
        "kgrr_severity_finite_ck": [
          "c",
          "checkka_gochara_finite_okseverityistrue",
          true
        ],
        "kgrr_source_fact_ids_ck": [
          "c",
          "checkka_gochara_string_array_oksource_fact_idsistrueandjsonb_array_lengthsource_fact_ids>0orfixture",
          true
        ],
        "kgrr_support_cardinality_ck": [
          "c",
          "checktemporal_support_state='uncomputed'andtemporal_support_grainisnullandcoalescearray_lengthtemporal_support_intervals,1,0=0ortemporal_support_state='computed_empty'andtemporal_support_grainisnotnullandcoalescearray_lengthtemporal_support_intervals,1,0=0ortemporal_support_state='computed'andtemporal_support_grainisnotnullandcoalescearray_lengthtemporal_support_intervals,1,0>=1",
          true
        ],
        "kgrr_support_intervals_ck": [
          "c",
          "checkka_gochara_intervals_oktemporal_support_intervalsistrue",
          true
        ],
        "kgrr_support_state_ck": [
          "c",
          "checktemporal_support_state=anyarray['uncomputed','computed_empty','computed']",
          true
        ],
        "kgrr_transit_natal_ck": [
          "c",
          "checkrelation=anyarray['residence','aspect','conjunction']andcontact_idisnotnulland\"precision\"isnotnullorrelation=anyarray['dispositorship','association','ownership','occupancy','period_running']andcontact_idisnulland\"precision\"isnull",
          true
        ],
        "kgrr_valence_ck": [
          "c",
          "checkoutcome_valence_for_native=anyarray['favourable','adverse','mixed','unqualified']",
          true
        ]
      },
      "indexes": {
        "idx_kgrr_chart_gen": "createindexidx_kgrr_chart_genonka_gochara_relationship_recordusingbtreechart_id,generation,event_class",
        "idx_kgrr_contact": "createindexidx_kgrr_contactonka_gochara_relationship_recordusingbtreechart_id,generation,contact_idwherecontact_idisnotnull",
        "idx_kgrr_coverage": "createindexidx_kgrr_coverageonka_gochara_relationship_recordusingbtreechart_id,generation,coverage_partition_kind,coverage_partition_key",
        "idx_kgrr_object": "createindexidx_kgrr_objectonka_gochara_relationship_recordusingbtreeobject_id",
        "idx_kgrr_path": "createindexidx_kgrr_pathonka_gochara_relationship_recordusingbtreepath_id,rule_version",
        "ka_gochara_relationship_record_pkey": "createuniqueindexka_gochara_relationship_record_pkeyonka_gochara_relationship_recordusingbtreerecord_id",
        "kgrr_identity_uq": "createuniqueindexkgrr_identity_uqonka_gochara_relationship_recordusingbtreerecord_id,chart_id,generation",
        "kgrr_membership_uq": "createuniqueindexkgrr_membership_uqonka_gochara_relationship_recordusingbtreerecord_id,chart_id,generation,event_class,path_id,rule_version"
      },
      "triggers": {
        "ka_gochara_rr_coverage_guard": [
          "createtriggerka_gochara_rr_coverage_guardbeforeinsertorupdateonka_gochara_relationship_recordforeachrowexecutefunctionka_gochara_record_coverage_guard",
          "O"
        ],
        "ka_gochara_rr_finalize": [
          "createconstrainttriggerka_gochara_rr_finalizeafterinsertorupdateonka_gochara_relationship_recorddeferrableinitiallydeferredforeachrowexecutefunctionka_gochara_record_finalize_check",
          "O"
        ],
        "ka_gochara_rr_no_truncate": [
          "createtriggerka_gochara_rr_no_truncatebeforetruncateonka_gochara_relationship_recordforeachstatementexecutefunctionka_gochara_refuse_truncate",
          "O"
        ],
        "ka_gochara_rr_sealed_generation_guard": [
          "createtriggerka_gochara_rr_sealed_generation_guardbeforedeleteorupdateonka_gochara_relationship_recordforeachrowexecutefunctionka_gochara_sealed_generation_guard",
          "O"
        ],
        "ka_gochara_rr_sealed_path_check": [
          "createtriggerka_gochara_rr_sealed_path_checkbeforeinsertorupdateofpath_id,rule_versiononka_gochara_relationship_recordforeachrowexecutefunctionka_gochara_require_sealed_rule_path",
          "O"
        ]
      }
    }
  }
}
$expected$::jsonb);
END;
$$;
