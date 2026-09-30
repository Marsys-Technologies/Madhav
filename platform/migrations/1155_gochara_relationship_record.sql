-- Migration 1155: ka_gochara_relationship_record — the §1.1 typed contract
--                 + §3.1 valence fields + admission persistence, with
--                 NORMALISED prerequisite membership (amendment 3) and a
--                 chart/generation/partition-bound coverage handle
--                 (amendment 4). Depends on 1153 (ka_gochara_contact,
--                 ka_gochara_physical_object), 1154 (rule_path, predicate,
--                 typed helpers) and 1081 (kala_gochara_coverage).
--                 Rewritten at A5.1 round 2 per ASTRA_REVIEW_A5_1_MIGRATIONS
--                 v1_0 amendments 1–9 and the steward rulings. Never applied
--                 anywhere — in-place rewrite of the same number.
-- Created: 2026-09-30. Author: pravaha/a5-migrations (Stream A, A5.1).
--
-- Numbering: 1155 sits inside this lane's granted block (1150–1159 per
-- ADK-0026 §4; 1150/1151/1152 are used). Verified free by a fresh scan of
-- every origin/* ref across BOTH platform/migrations/ and
-- platform/supabase/migrations/ (2026-09-30: max in use anywhere is 1152;
-- no 1155 anywhere). `npm run guard:migration-numbers` green on this branch.
--
-- Amendment 2 (P1 #2): NO BEGIN/COMMIT — migrate.ts owns ONE transaction
-- around DDL + ledger insert (see the 1153 header). SET LOCAL is scoped to
-- the runner's transaction.
--
-- Amendment 1 (P1 #1): transit rows FK ka_gochara_CONTACT (the §6.1 contact
-- identity with relation kind, occurrence ordinal and t_in/t_out/t_exact),
-- never the boundary-only sky event.
--
-- Amendment 3 (P1 #3): path_id/rule_version are NOT NULL and the composite
-- FK is a complete, mandatory reference (no NULL-pair bypass of MATCH
-- SIMPLE — S:156-158). prerequisites are NORMALISED into
-- ka_gochara_record_prerequisite with a real composite FK to
-- ka_gochara_predicate and an ordinal preserving evaluation order; the old
-- shape-only JSONB column is gone.
--
-- Amendment 4 (P1 #4): the coverage handle is the 1081 coverage PARTITION
-- itself: (coverage_partition_kind, coverage_partition_key) plus the
-- composite FK (chart_id, generation, coverage_partition_kind,
-- coverage_partition_key) → kala_gochara_coverage binds every record to an
-- EXISTING coverage partition of its OWN chart and generation (S:104 — a
-- resolvable coverage manifest, scope-bound; a generation-5.0 row can never
-- point at another chart's or generation's manifest). The composite
-- consistency FK (contact_id, agent, object_id) → ka_gochara_contact
-- (contact_id, body, physical_object_id) makes a transit record's agent and
-- object physically agree with its referenced contact.
--
-- Amendment 5 (P1 #5): temporal_support is TYPED — state/grain/intervals
-- columns with state-dependent cardinality (uncomputed ⇒ no grain, no
-- intervals; computed_empty ⇒ grain, no intervals; computed ⇒ grain, ≥1
-- interval; S:103). Transit rows REQUIRE precision (with a typed
-- {solver_method, delta_lambda, delta_t} payload, §7). Valence is NOT NULL —
-- 'unqualified' is the declared honest state (S:113, §3.2 inv 3), SQL NULL
-- is not a valence. Admission is PERSISTED: admission_state ∈ {admitted,
-- unqualified, not_admitted} records the §2.2 inv 2 / S:103 outcome (an
-- unknown necessary prerequisite ⇒ 'unqualified' recorded here, never
-- folded into valence); the per-prerequisite evaluated states ride
-- ka_gochara_record_prerequisite.result ∈ {true,false,unknown}; the §1.2
-- inv 5 frame arithmetic is stored in house_from_frame (1..12, filled at
-- evaluation time). A5.3 invents no JSON keys.
--
-- Amendment 9 (P2 #9): frame_arg typed domains via ka_gochara_frame_ok;
-- the relative-person frame invariant is enforced (a relative's event never
-- reads the native's Moon frame — S:126-128); source_fact_ids is a typed
-- string array ([] only on fixture rows); provenance='verse_cited' REQUIRES
-- source_text AND source_page (S:62-64, 106-108); the ruling CHECK matches
-- the frozen wording (uncited_extension ⇒ ruling_ref, never forbidden
-- otherwise); the S:89 canonical-chart restriction is enforced as a CHECK
-- (D-SCOPE disposition — widening requires a migration).
--
-- DELIBERATELY NOT ENCODED: no immutability trigger — records are
-- writer-owned per (chart_id × generation) delete-then-insert under the
-- WriterBase contract (§10.1, §N.3); contact publication immutability is
-- enforced at ka_gochara_contact (1153). root_id (§2.1 R4-S01) stays
-- derivable: contact_id on transit rows, object_id on natal-fact rows.
--
-- asset_registry: deliberately NOT registered (asset_registry.layer CHECK
-- has no 'L2' value; contract table of the already-registered ka_gochara
-- writer family — same disposition as 1081).
--
-- Operational properties: pure CREATE TABLE / FUNCTION / INDEX + post-DDL
-- verification; no existing object or data touched; no business-data writes.
-- Execution outcomes (amendment 8): fresh apply = create + verify; repeat
-- execution = verified no-op; drifted same-named object = loud RAISE.
--
-- ROLLBACK:
--   DROP TABLE IF EXISTS ka_gochara_record_prerequisite;
--   DROP TABLE IF EXISTS ka_gochara_relationship_record;
--   DROP FUNCTION IF EXISTS ka_gochara_intervals_ok(tstzrange[]);
--   DROP FUNCTION IF EXISTS ka_gochara_precision_ok(jsonb);
-- ─────────────────────────────────────────────────────────────────────────────

SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '120s';

-- ── 0. Helpers (immutable — safe in CHECKs) ───────────────────────────────

-- §7.1 typed precision payload: {solver_method, delta_lambda, delta_t}.
CREATE OR REPLACE FUNCTION ka_gochara_precision_ok(p jsonb)
RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
  SELECT jsonb_typeof(p) = 'object'
     AND p ? 'solver_method' AND p ? 'delta_lambda' AND p ? 'delta_t'
     AND p ->> 'solver_method' IN
           ('arc_index_bracket','swiss_refined','clipped_truncated')
     AND jsonb_typeof(p -> 'delta_lambda') = 'number'
     AND jsonb_typeof(p -> 'delta_t')      = 'number';
$$;

-- Interval arrays: no NULL element, no empty range.
CREATE OR REPLACE FUNCTION ka_gochara_intervals_ok(iv tstzrange[])
RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
  SELECT NOT EXISTS (
    SELECT 1 FROM unnest(iv) r
    WHERE r IS NULL OR isempty(r)
  );
$$;

-- ── 1. relationship_record (§1.1 + §3.1 + admission persistence) ──────────

CREATE TABLE IF NOT EXISTS ka_gochara_relationship_record (
  record_id         UUID PRIMARY KEY,
  -- §1.1: deterministic hash of the natural key
  --   (chart_id, generation, event_class, affected_person, frame, agent,
  --    relation, object_id, object_role, contact_id, path_id, rule_version,
  --    prerequisites, source_text)
  -- — generation and contact_id are IN the key (R3/amendment 1). The
  -- prerequisites component reads the ka_gochara_record_prerequisite
  -- membership rows (amendment 3); the hash is writer-computed, not
  -- re-implemented in SQL.
  chart_id          UUID NOT NULL REFERENCES charts(id),
  generation        TEXT NOT NULL,               -- '4.1'/'5.0'… (§1.1 NK-3)
  contact_id        UUID,                        -- NOT NULL on transit rows (CHECK);
                                                 --   FK + consistency below (amendments 1/4)
  event_class       TEXT NOT NULL,
  affected_person   TEXT NOT NULL,
  frame_kind        TEXT NOT NULL,
  frame_arg         TEXT,                        -- typed by ka_gochara_frame_ok (§0)
  agent             TEXT NOT NULL,               -- the transiting (or period) body
  relation          TEXT NOT NULL,
  object_id         UUID NOT NULL REFERENCES ka_gochara_physical_object(physical_object_id),
  object_kind       TEXT NOT NULL,
  object_role       TEXT NOT NULL,
  path_id           TEXT NOT NULL,               -- amendment 3: mandatory complete
  rule_version      TEXT NOT NULL,               --   version-bound reference
  temporal_support_state TEXT NOT NULL,          -- §1.1 tagged states (typed, amendment 5)
  temporal_support_grain TEXT,                   -- evaluation grain; NULL iff uncomputed
  temporal_support_intervals TSTZRANGE[] NOT NULL DEFAULT '{}',
  coverage_partition_kind TEXT NOT NULL,         -- amendment 4: the coverage handle IS
  coverage_partition_key  TEXT NOT NULL,         --   the 1081 partition, scope-bound below
  precision         JSONB,                       -- {solver_method, delta_lambda, delta_t}
                                                 --   (§7.1); REQUIRED on transit rows
  source_text       TEXT,
  source_page       TEXT,
  source_fact_ids   JSONB NOT NULL,              -- typed string array; [] only on fixtures
  fixture           BOOLEAN NOT NULL DEFAULT false,
  provenance        TEXT NOT NULL,
  operator_role     TEXT NOT NULL,
  ruling_ref        TEXT,
  admission_state   TEXT NOT NULL,               -- amendment 5: the persisted §2.2 inv 2 /
                                                 --   S:103 admission result
  house_from_frame  INTEGER,                     -- §1.2 inv 5: frame arithmetic, stored
                                                 --   at evaluation time; NULL until then
  evidence_for_occurrence    REAL,               -- §3.1: rank-only, never a gate; ≥ 0
  evidence_against_occurrence REAL,              -- §3.1: never netted; ≥ 0
  outcome_valence_for_native TEXT NOT NULL,      -- §3.1: 'unqualified' is the declared
                                                 --   honest state — SQL NULL is not a valence
  severity          REAL,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT kgrr_canonical_chart_ck
    CHECK (chart_id = '482012f1-710e-4a25-994a-93821f5871aa'::uuid),
    -- D-SCOPE disposition (amendment 9): canonical chart only (S:89).
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
  CONSTRAINT kgrr_frame_ck CHECK (ka_gochara_frame_ok(frame_kind, frame_arg)),
  CONSTRAINT kgrr_relative_frame_ck
    CHECK (affected_person = 'native' OR frame_kind <> 'moon'),
    -- §1.2 inv 6 / S:126-128 (amendment 9): a relative's event never reads
    -- the native's Moon frame; bhavat_bhavam frames carry relatives
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
    REFERENCES ka_gochara_rule_path (path_id, rule_version),
  CONSTRAINT kgrr_contact_fk FOREIGN KEY (contact_id, agent, object_id)
    REFERENCES ka_gochara_contact (contact_id, body, physical_object_id),
    -- amendments 1/4: transit rows reference the CONTACT; agent/object must
    -- physically agree with it. MATCH SIMPLE + contact_id NULL on natal rows
    -- (enforced below) keeps the natal branch out of this FK.
  CONSTRAINT kgrr_coverage_fk
    FOREIGN KEY (chart_id, generation, coverage_partition_kind, coverage_partition_key)
    REFERENCES kala_gochara_coverage (chart_id, generation, partition_kind, partition_key),
    -- amendment 4: the coverage handle is bound to an EXISTING coverage
    -- partition of the record's own chart and generation (S:104).
  CONSTRAINT kgrr_coverage_kind_ck CHECK (coverage_partition_kind IN
    ('body_target','event_class','moon_on_demand')),
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
    -- §1.1/S:103 (amendment 5): the three tagged states are never conflated;
    -- 'computed' requires ≥1 interval, the others require none
  CONSTRAINT kgrr_support_intervals_ck
    CHECK (ka_gochara_intervals_ok(temporal_support_intervals)),
  CONSTRAINT kgrr_precision_typed_ck
    CHECK (precision IS NULL OR ka_gochara_precision_ok(precision)),
  CONSTRAINT kgrr_transit_natal_ck CHECK (
    (relation IN ('residence','aspect','conjunction')
       AND contact_id IS NOT NULL AND precision IS NOT NULL)
    OR
    (relation IN ('dispositorship','association','ownership','occupancy',
                  'period_running')
       AND contact_id IS NULL AND precision IS NULL)
  ),
    -- §1.1/§7 (amendment 5): transit rows carry a contact AND their precision
    -- payload; natal-fact rows carry neither; the two never mix (F6a)
  CONSTRAINT kgrr_source_fact_ids_ck
    CHECK (ka_gochara_string_array_ok(source_fact_ids)
           AND (jsonb_array_length(source_fact_ids) > 0 OR fixture)),
    -- §1.1 amendment 1 (typed, amendment 9): [null] / [123] fail the element
    -- check; [] only on synthetic-fixture rows (fixture = true)
  CONSTRAINT kgrr_provenance_ck CHECK (provenance IN
    ('verse_cited','uncited_extension')),
  CONSTRAINT kgrr_operator_role_ck CHECK (operator_role IN ('scored','testimony')),
  CONSTRAINT kgrr_ruling_ck
    CHECK (provenance <> 'uncited_extension' OR ruling_ref IS NOT NULL),
    -- S:110 as frozen (amendment 9): uncited_extension REQUIRES a ruling;
    -- a ruling ref is never forbidden otherwise
  CONSTRAINT kgrr_citation_ck
    CHECK (provenance <> 'verse_cited'
           OR (source_text IS NOT NULL AND source_page IS NOT NULL)),
    -- S:62-64/106-108 (amendment 9): a verse_cited row carries its citation
  CONSTRAINT kgrr_admission_state_ck CHECK (admission_state IN
    ('admitted','unqualified','not_admitted')),
    -- amendment 5 / S:103 / §2.2 inv 2: unknown necessary prerequisite ⇒
    -- 'unqualified' RECORDED here — never folded into valence, never false
  CONSTRAINT kgrr_house_from_frame_ck
    CHECK (house_from_frame IS NULL OR house_from_frame BETWEEN 1 AND 12),
  CONSTRAINT kgrr_evidence_for_nn_ck
    CHECK (evidence_for_occurrence IS NULL OR evidence_for_occurrence >= 0),
  CONSTRAINT kgrr_evidence_against_nn_ck
    CHECK (evidence_against_occurrence IS NULL OR evidence_against_occurrence >= 0),
    -- amendment 7: evidence accumulates nonnegatively; it never receives the
    -- score's [0,1] bound
  CONSTRAINT kgrr_valence_ck CHECK (outcome_valence_for_native IN
    ('favourable','adverse','mixed','unqualified')),
  -- FK target for eval-window membership (amendment 3): membership is scoped
  -- to the window's own chart and generation.
  CONSTRAINT kgrr_identity_uq UNIQUE (record_id, chart_id, generation)
);

COMMENT ON TABLE ka_gochara_relationship_record IS
  'Relationship record (GOCHARA_DESIGN_SPECS_v1_4 §1.1): one row per (event_class, '
  'affected_person, frame, agent, relation, object, role, path). Transit rows FK '
  'ka_gochara_contact (amendment 1) with composite agent/object consistency '
  '(amendment 4); coverage is bound to an existing (chart, generation, partition) '
  'coverage row (amendment 4). temporal_support is typed with state-dependent '
  'cardinality (amendment 5). admission_state + ka_gochara_record_prerequisite.result '
  'persist the §2.2 inv 2 qualification states (unknown ⇒ unqualified, recorded). '
  'Root key (§2.1 R4-S01): contact_id on transit rows, object_id on natal rows — '
  'derivable, deliberately not duplicated. Writer contract: ka_gochara family, '
  'idempotent per-(chart_id × generation) delete-then-insert (§10.1, §N.3).';

-- Read shapes the evaluator and rehearsal actually use.
CREATE INDEX IF NOT EXISTS idx_kgrr_chart_gen ON ka_gochara_relationship_record
  (chart_id, generation, event_class);
CREATE INDEX IF NOT EXISTS idx_kgrr_contact ON ka_gochara_relationship_record
  (contact_id) WHERE contact_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_kgrr_object ON ka_gochara_relationship_record
  (object_id);
CREATE INDEX IF NOT EXISTS idx_kgrr_path ON ka_gochara_relationship_record
  (path_id, rule_version);
-- Review minor item: the coverage handle is indexed on both consuming tables.
CREATE INDEX IF NOT EXISTS idx_kgrr_coverage ON ka_gochara_relationship_record
  (chart_id, generation, coverage_partition_kind, coverage_partition_key);

-- ── 2. Prerequisite membership (amendment 3) + evaluated results (amendment 5)

CREATE TABLE IF NOT EXISTS ka_gochara_record_prerequisite (
  record_id            UUID NOT NULL,
  ordinal              INTEGER NOT NULL,         -- §1.1: ordered, cheapest necessary
                                                 --   predicate first
  predicate_id         TEXT NOT NULL,
  predicate_rule_version TEXT NOT NULL,
  result               TEXT,                     -- evaluated state; NULL until evaluation
                                                 --   (amendment 5: the persisted §2.2
                                                 --   inv 2 per-prerequisite states)

  PRIMARY KEY (record_id, ordinal),
  CONSTRAINT kgrpr_ordinal_ck CHECK (ordinal >= 1),
  CONSTRAINT kgrpr_result_ck CHECK (result IS NULL OR result IN
    ('true','false','unknown')),
  CONSTRAINT kgrpr_record_fk FOREIGN KEY (record_id)
    REFERENCES ka_gochara_relationship_record (record_id) ON DELETE CASCADE,
    -- §N.3 lifecycle: per-chart delete-then-insert rebuild removes a
    -- record's membership with it (the prescribed rebuild ordering).
  CONSTRAINT kgrpr_predicate_fk FOREIGN KEY (predicate_id, predicate_rule_version)
    REFERENCES ka_gochara_predicate (predicate_id, rule_version),
  CONSTRAINT kgrpr_no_dup_uq
    UNIQUE (record_id, predicate_id, predicate_rule_version)
);

COMMENT ON TABLE ka_gochara_record_prerequisite IS
  'Record prerequisite membership (amendment 3): ordered, version-bound composite '
  'references into ka_gochara_predicate with real FK enforcement — a bare or dangling '
  'id cannot be written. result persists the per-prerequisite evaluated state '
  '{true,false,unknown}; an unknown necessary prerequisite makes the record '
  'admission_state = unqualified (§2.2 inv 2, S:103), recorded on the record.';

-- ── 3. Post-DDL definition verification (amendment 8) ─────────────────────

DO $$
DECLARE missing text;
BEGIN
  WITH expected(tbl, col, typ, nn) AS (
    VALUES
      ('ka_gochara_relationship_record','record_id','uuid',true),
      ('ka_gochara_relationship_record','chart_id','uuid',true),
      ('ka_gochara_relationship_record','generation','text',true),
      ('ka_gochara_relationship_record','contact_id','uuid',false),
      ('ka_gochara_relationship_record','event_class','text',true),
      ('ka_gochara_relationship_record','affected_person','text',true),
      ('ka_gochara_relationship_record','frame_kind','text',true),
      ('ka_gochara_relationship_record','frame_arg','text',false),
      ('ka_gochara_relationship_record','agent','text',true),
      ('ka_gochara_relationship_record','relation','text',true),
      ('ka_gochara_relationship_record','object_id','uuid',true),
      ('ka_gochara_relationship_record','object_kind','text',true),
      ('ka_gochara_relationship_record','object_role','text',true),
      ('ka_gochara_relationship_record','path_id','text',true),
      ('ka_gochara_relationship_record','rule_version','text',true),
      ('ka_gochara_relationship_record','temporal_support_state','text',true),
      ('ka_gochara_relationship_record','temporal_support_grain','text',false),
      ('ka_gochara_relationship_record','temporal_support_intervals','tstzrange[]',true),
      ('ka_gochara_relationship_record','coverage_partition_kind','text',true),
      ('ka_gochara_relationship_record','coverage_partition_key','text',true),
      ('ka_gochara_relationship_record','precision','jsonb',false),
      ('ka_gochara_relationship_record','source_text','text',false),
      ('ka_gochara_relationship_record','source_page','text',false),
      ('ka_gochara_relationship_record','source_fact_ids','jsonb',true),
      ('ka_gochara_relationship_record','fixture','boolean',true),
      ('ka_gochara_relationship_record','provenance','text',true),
      ('ka_gochara_relationship_record','operator_role','text',true),
      ('ka_gochara_relationship_record','ruling_ref','text',false),
      ('ka_gochara_relationship_record','admission_state','text',true),
      ('ka_gochara_relationship_record','house_from_frame','integer',false),
      ('ka_gochara_relationship_record','evidence_for_occurrence','real',false),
      ('ka_gochara_relationship_record','evidence_against_occurrence','real',false),
      ('ka_gochara_relationship_record','outcome_valence_for_native','text',true),
      ('ka_gochara_relationship_record','severity','real',false),
      ('ka_gochara_record_prerequisite','record_id','uuid',true),
      ('ka_gochara_record_prerequisite','ordinal','integer',true),
      ('ka_gochara_record_prerequisite','predicate_id','text',true),
      ('ka_gochara_record_prerequisite','predicate_rule_version','text',true),
      ('ka_gochara_record_prerequisite','result','text',false)
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
    RAISE EXCEPTION 'migration 1155 post-DDL verification failed (amendment 8): column drift: %', missing;
  END IF;

  WITH expected(conrelid, conname) AS (
    VALUES
      ('ka_gochara_relationship_record','kgrr_canonical_chart_ck'),
      ('ka_gochara_relationship_record','kgrr_event_class_ck'),
      ('ka_gochara_relationship_record','kgrr_affected_person_ck'),
      ('ka_gochara_relationship_record','kgrr_frame_ck'),
      ('ka_gochara_relationship_record','kgrr_relative_frame_ck'),
      ('ka_gochara_relationship_record','kgrr_agent_ck'),
      ('ka_gochara_relationship_record','kgrr_relation_ck'),
      ('ka_gochara_relationship_record','kgrr_object_kind_ck'),
      ('ka_gochara_relationship_record','kgrr_object_role_ck'),
      ('ka_gochara_relationship_record','kgrr_path_fk'),
      ('ka_gochara_relationship_record','kgrr_contact_fk'),
      ('ka_gochara_relationship_record','kgrr_coverage_fk'),
      ('ka_gochara_relationship_record','kgrr_coverage_kind_ck'),
      ('ka_gochara_relationship_record','kgrr_support_state_ck'),
      ('ka_gochara_relationship_record','kgrr_support_cardinality_ck'),
      ('ka_gochara_relationship_record','kgrr_support_intervals_ck'),
      ('ka_gochara_relationship_record','kgrr_precision_typed_ck'),
      ('ka_gochara_relationship_record','kgrr_transit_natal_ck'),
      ('ka_gochara_relationship_record','kgrr_source_fact_ids_ck'),
      ('ka_gochara_relationship_record','kgrr_provenance_ck'),
      ('ka_gochara_relationship_record','kgrr_operator_role_ck'),
      ('ka_gochara_relationship_record','kgrr_ruling_ck'),
      ('ka_gochara_relationship_record','kgrr_citation_ck'),
      ('ka_gochara_relationship_record','kgrr_admission_state_ck'),
      ('ka_gochara_relationship_record','kgrr_house_from_frame_ck'),
      ('ka_gochara_relationship_record','kgrr_evidence_for_nn_ck'),
      ('ka_gochara_relationship_record','kgrr_evidence_against_nn_ck'),
      ('ka_gochara_relationship_record','kgrr_valence_ck'),
      ('ka_gochara_relationship_record','kgrr_identity_uq'),
      ('ka_gochara_record_prerequisite','kgrpr_ordinal_ck'),
      ('ka_gochara_record_prerequisite','kgrpr_result_ck'),
      ('ka_gochara_record_prerequisite','kgrpr_record_fk'),
      ('ka_gochara_record_prerequisite','kgrpr_predicate_fk'),
      ('ka_gochara_record_prerequisite','kgrpr_no_dup_uq')
  )
  SELECT string_agg(e.conrelid || '.' || e.conname, ', ' ORDER BY 1) INTO missing
  FROM expected e
  WHERE NOT EXISTS (
    SELECT 1 FROM pg_constraint c
    WHERE c.conrelid = to_regclass('public.' || e.conrelid) AND c.conname = e.conname
  );
  IF missing IS NOT NULL THEN
    RAISE EXCEPTION 'migration 1155 post-DDL verification failed (amendment 8): missing constraint: %', missing;
  END IF;
END;
$$;
