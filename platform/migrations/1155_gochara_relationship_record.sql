-- Migration 1155: ka_gochara_relationship_record — the §1.1 typed contract
--                 (every field of the schema table) + §3.1 valence fields.
--                 Depends on 1153 (ka_gochara_sky_event,
--                 ka_gochara_physical_object) and 1154 (ka_gochara_rule_path,
--                 ka_gochara_composite_refs_ok).
-- Created: 2026-09-30. Author: pravaha/a5-migrations (Stream A, A5.1).
--
-- Numbering: 1155 sits inside this lane's granted block (1150–1159 per
-- ADK-0026 §4; 1150/1151/1152 are used). Verified free by a fresh scan of
-- every origin/* ref across BOTH platform/migrations/ and
-- platform/supabase/migrations/ (2026-09-30: max in use anywhere is 1152;
-- no 1155 anywhere). `npm run guard:migration-numbers` green on this branch.
--
-- Spec: GOCHARA_DESIGN_SPECS_v1_4 (FROZEN 2026-09-30). Encoded as:
--   * CONSTRAINT / COLUMN: every §1.1 field present. record_id uuid PK
--     (deterministic hash of the natural key, writer-computed — the exact
--     tuple is in the COMMENT below); chart_id FK → charts(id) (uuid PK per
--     001_baseline.sql §3); generation NOT NULL (§1.1 NK-3); contact_id
--     NULL-able FK → ka_gochara_sky_event(event_id); event_class CHECK
--     against the 27-class enumeration of EVALUATION_PROTOCOL_v2_2 §2 (the
--     sole enumeration — §2.1 amendment 2 instructs A5.1 to CHECK-constrain
--     event_class to it); affected_person 6-enum (§1.1); frame as
--     frame_kind/frame_arg with the §0 arg rule (arg NULL exactly for
--     moon/lagna/dasha_lord; graha:<X> and bhavat_bhavam:<house> carry the
--     arg) and frame NOT NULL on every row (§1.2 inv 1); agent 9-graha CHECK
--     (§2.1 exhaustive agent set — the period-lord roles are roles OF these
--     grahas, not additional agents); relation 8-enum (§1.1: transit vs
--     natal-fact relations never mix, F6a); object_id FK →
--     ka_gochara_physical_object (§1.2 inv 4 — natal objects are physical
--     objects too; relation_kind distinguishes); object_kind 8-enum (§1.1);
--     object_role 9-enum (§1.1, authoritative for the interpretive role —
--     F6c); composite FK (path_id, rule_version) → ka_gochara_rule_path
--     (§2.1: version-bound references only); prerequisites composite-ref
--     shape via ka_gochara_composite_refs_ok (§1.1/§2.1); temporal_support
--     tagged-state CHECK — state ∈ {uncomputed, computed_empty, computed}
--     inside the jsonb (§1.1 amendment 1); source_fact_ids jsonb array,
--     empty array only when fixture = true (§1.1 amendment 1); provenance /
--     operator_role enums + ruling_ref biconditional (§0, same rule as
--     ka_gochara_rule_path); §3.1 valence fields evidence_for_occurrence /
--     evidence_against_occurrence / outcome_valence_for_native (4-enum) /
--     severity — rank-only, never a gate (§1.1 F6b, §3.1).
--   * CROSS-FIELD CHECK: transit relations (residence/aspect/conjunction) ⇒
--     contact_id IS NOT NULL; natal-fact relations (dispositorship/
--     association/ownership/occupancy/period_running) ⇒ contact_id IS NULL
--     AND precision IS NULL (§1.1 "the same rule", §7).
--   * COMMENT ONLY (writer behaviour): the deterministic record_id hash
--     recipe; root_id := contact_id on transit rows / object_id on
--     natal-fact rows (§2.1 R4-S01) — derivable from the stored columns, no
--     extra column added; role-alias single-contact_id invariant (§1.2 inv
--     3) is structural via the shared FK, its cross-row uniqueness is writer
--     behaviour; temporal_support grain/intervals payload shape beyond the
--     state tag; precision payload {solver_method, delta_lambda, delta_t}
--     keys (§7); unknown-admission ⇒ outcome 'unqualified' (§2.2 inv 2).
--   * DELIBERATELY NOT ENCODED: no trigger immutability — §1 does not
--     declare relationship_record insert-only (records are writer-owned per
--     (chart_id × generation) delete-then-insert under the WriterBase
--     contract, §10.1); inventing an immutability trigger would contradict
--     the writer contract.
--
-- coverage_ref decision (A5.1 brief required verification): §1.1 says
-- "coverage_ref uuid FK → coverage manifest; always resolvable". The 1081
-- kala_gochara_coverage table has a COMPOSITE primary key (chart_id,
-- generation, partition_kind, partition_key) — it has no uuid column to
-- reference. The only uuid-keyed manifest is kala_gochara_publication
-- (manifest_id, N-10). coverage_ref therefore REFERENCES
-- kala_gochara_publication(manifest_id) — the generation manifest under
-- which the row's coverage partitions live; per-partition coverage rows are
-- reachable through (chart_id, generation) of that manifest. This is the
-- one place the spec's "coverage manifest" wording is ambiguous; flagged in
-- the A5.1 report, not silently resolved.
--
-- asset_registry: deliberately NOT registered (asset_registry.layer CHECK
-- has no 'L2' value; contract table of the already-registered ka_gochara
-- writer family — same disposition as 1081).
--
-- Operational properties: pure CREATE TABLE; no existing object or data
-- touched; no production data writes; ONE TRANSACTION (BEGIN/COMMIT, 1081
-- style); replay-idempotent by construction (IF NOT EXISTS everywhere),
-- though migrate.ts never replays; SET LOCAL bounds stated honestly.
--
-- ROLLBACK:
--   DROP TABLE IF EXISTS ka_gochara_relationship_record;
-- ─────────────────────────────────────────────────────────────────────────────

BEGIN;

SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '120s';

CREATE TABLE IF NOT EXISTS ka_gochara_relationship_record (
  record_id         UUID PRIMARY KEY,
  -- §1.1: deterministic hash of the natural key
  --   (chart_id, generation, event_class, affected_person, frame, agent,
  --    relation, object_id, object_role, contact_id, path_id, rule_version,
  --    prerequisites, source_text)
  -- — generation and contact_id are IN the key (R3/amendment 1): two
  -- otherwise identical episode records under different generations or
  -- different contact episodes never collide; a predicate-list or citation
  -- change re-keys the record instead of silently mutating it. The hash is
  -- computed by the writer; it is NOT re-implemented in SQL.
  chart_id          UUID NOT NULL REFERENCES charts(id),   -- §1.1; D-SCOPE:
                    -- 482012f1-710e-4a25-994a-93821f5871aa only
  generation        TEXT NOT NULL,               -- '4.1'/'5.0'…; records are
                    -- generation-scoped, never shared (§1.1 NK-3, R2-S01)
  contact_id        UUID REFERENCES ka_gochara_sky_event(event_id),
                    -- §1.1: NOT NULL on transit-relation rows; NULL only on
                    -- natal-fact rows (which carry precision = NULL by the
                    -- same rule). Role aliases of one physical contact share
                    -- ONE contact_id (§1.2 inv 3) — this column is that
                    -- declaration, made structural.
  event_class       TEXT NOT NULL CHECK (event_class IN (
                      'achievement_recognition','bereavement','birth_anchor',
                      'business_launch','career_advancement','career_change',
                      'career_entry','career_setback','childbirth',
                      'chronic_onset','education_milestone','exam_outcome',
                      'financial_deception','foreign_settlement','illness_acute',
                      'major_gain','major_loss','marriage','parental_event',
                      'property_acquisition','psychological_arc','relocation',
                      'romantic_start','separation','spiritual_turn','surgery',
                      'travel_event')),
                    -- the 27 classes of EVALUATION_PROTOCOL_v2_2 §2 — the sole
                    -- enumeration (§2.1 amendment 2); adverse classes first-class
  affected_person   TEXT NOT NULL CHECK (affected_person IN
                      ('native','father','mother','spouse','child','sibling')),
                    -- §1.1 closed enum; extension requires a migration and a
                    -- rule_version bump
  frame_kind        TEXT NOT NULL CHECK (frame_kind IN
                      ('moon','lagna','graha','dasha_lord','bhavat_bhavam')),
                    -- §0 frame enum; present on EVERY row (§1.2 inv 1)
  frame_arg         TEXT,                        -- graha:<X> / bhavat_bhavam:<house>;
                    -- NULL allowed only for moon/lagna/dasha_lord (CHECK below);
                    -- counting is inclusive of the reference sign (§0)
  agent             TEXT NOT NULL CHECK (agent IN
                      ('sun','moon','mars','mercury','jupiter','venus','saturn',
                       'rahu','ketu')),
                    -- §2.1 exhaustive agent set: the seven grahas + Rāhu/Ketu;
                    -- the running MD/AD/PD lords appear in their period role
                    -- (object_role = period_lord), not as additional agent values
  relation          TEXT NOT NULL CHECK (relation IN
                      ('residence','aspect','conjunction',
                       'dispositorship','association','ownership','occupancy',
                       'period_running')),
                    -- §1.1: transit relations (residence/aspect/conjunction) vs
                    -- natal-fact relations; the two never mix on one row (F6a);
                    -- relation is authoritative for the physical relation (F6c)
  object_id         UUID NOT NULL REFERENCES ka_gochara_physical_object(physical_object_id),
                    -- §1.1/§1.2 inv 4: §6 physical identity, never a label-only
                    -- ref. Natal-fact rows reference the NATAL object (natal
                    -- objects are physical objects too; relation_kind
                    -- distinguishes). Sensitive-degree negative checks
                    -- (not_gandanta/not_pushkara/not_fired/none) are NOT objects
                    -- (§1.2 inv 4, E3).
  object_kind       TEXT NOT NULL CHECK (object_kind IN
                      ('degree_point','sign_span','star','derived_point',
                       'varga_position','saham','house_span','house_lord')), -- §1.1
  object_role       TEXT NOT NULL CHECK (object_role IN
                      ('lord','occupant','karaka','dispositor','maraka_of_house',
                       'period_lord','yoga_constituent','pada','signature_house')),
                    -- §1.1: authoritative for the interpretive role (F6c);
                    -- signature_house marks a class's signature house (§2.2 truth
                    -- table) so role-based selection never re-derives it (R2-S01)
  path_id           TEXT,
  rule_version      TEXT,                        -- a path change re-keys records (§1.1)
  prerequisites     JSONB NOT NULL,              -- ordered [(predicate_id, rule_version)]
                    -- composite refs, cheapest necessary predicate first; a bare id
                    -- is rejected at write time (§1.1, same rule as path FKs)
  temporal_support  JSONB NOT NULL,              -- §1.1 tagged states (amendment 1):
                    -- {state ∈ {uncomputed, computed_empty, computed}, grain,
                    -- intervals[]}; the three states are never conflated; a
                    -- prerequisite in state unknown makes admission unqualified,
                    -- never false (§2.2 inv 2)
  coverage_ref      UUID NOT NULL REFERENCES kala_gochara_publication(manifest_id),
                    -- §1.1 "FK → coverage manifest; always resolvable". See the
                    -- header: kala_gochara_coverage's PK is composite (1081), so
                    -- the reference is to the uuid-keyed publication manifest
                    -- whose (chart_id, generation) scopes the coverage partitions.
  precision         JSONB,                       -- {solver_method, delta_lambda,
                    -- delta_t} (§7.1); NULL only on natal-fact rows (§1.1) —
                    -- enforced by the relation-class CHECK below
  source_text       TEXT,                        -- e.g. 'Phaladīpikā' (§1.1)
  source_page       TEXT,                        -- e.g. 'PG249-250 (XX.34-38)' (§1.1)
  source_fact_ids   JSONB NOT NULL,              -- §1.1 source-fact lineage
                    -- (amendment 1): ordered list of L0/L1 fact ids (or extract row
                    -- fact_ids) the record's operands came from; [] only on
                    -- synthetic-fixture rows, which must carry fixture = true
  fixture           BOOLEAN NOT NULL DEFAULT false,
  provenance        TEXT NOT NULL CHECK (provenance IN
                      ('verse_cited','uncited_extension')),       -- §0 (S-04)
  operator_role     TEXT NOT NULL CHECK (operator_role IN
                      ('scored','testimony')),                    -- §0 (S-04); a
                    -- testimony row contributes zero to any score, weight, or gate
                    -- (§1.2 inv 2, O-RR-7 — evaluator-checked)
  ruling_ref        TEXT,                        -- e.g. 'D-P4', 'D-PADMIT' (§1.1)
  evidence_for_occurrence    REAL,               -- §3.1: rank-only; scale set at
                    -- calibration (L5); never a gate (§1.1 F6b)
  evidence_against_occurrence REAL,              -- §3.1: same; never netted against
                    -- evidence_for (§3.1 S-03, §3.2 inv 1)
  outcome_valence_for_native TEXT CHECK (outcome_valence_for_native IN
                      ('favourable','adverse','mixed','unqualified')),
                    -- §3.1: the native's interest; 'mixed' is a valence verdict,
                    -- never contested occurrence evidence; 'unqualified' is the
                    -- honest state when operands are unresolved (§3.2 inv 3)
  severity          REAL,                        -- §3.1: interpretive, rank-only,
                    -- never a gate
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),

  FOREIGN KEY (path_id, rule_version)
    REFERENCES ka_gochara_rule_path (path_id, rule_version),
    -- §2.1: composite version-bound FK; an unversioned reference is rejected at
    -- write time (NULL pair allowed only where no path produced the row)

  CHECK ((frame_arg IS NULL) = (frame_kind IN ('moon','lagna','dasha_lord'))),
    -- §0 frame arg rule

  CHECK (ka_gochara_composite_refs_ok(prerequisites, 'predicate_id')),
    -- §1.1/§2.1: composite references only; bare ids rejected

  CHECK (jsonb_typeof(temporal_support) = 'object'
         AND (temporal_support ->> 'state') IN
             ('uncomputed','computed_empty','computed')),
    -- §1.1 amendment 1: the three tagged states, never conflated

  CHECK (jsonb_typeof(source_fact_ids) = 'array'
         AND (jsonb_array_length(source_fact_ids) > 0 OR fixture)),
    -- §1.1 amendment 1: [] only on synthetic-fixture rows (fixture = true)

  CHECK ((ruling_ref IS NOT NULL)
         = (provenance = 'uncited_extension' OR operator_role = 'testimony')),
    -- §0/§1.1: ruling_ref required iff uncited_extension OR testimony

  CHECK (
    (relation IN ('residence','aspect','conjunction') AND contact_id IS NOT NULL)
    OR
    (relation IN ('dispositorship','association','ownership','occupancy',
                  'period_running')
     AND contact_id IS NULL AND precision IS NULL)
  )
    -- §1.1/§7: transit-relation rows carry a contact; natal-fact rows carry no
    -- contact and no precision (the same rule); the two never mix (F6a)
);

COMMENT ON TABLE ka_gochara_relationship_record IS
  'Relationship record (GOCHARA_DESIGN_SPECS_v1_4 §1.1): one row per (event_class, '
  'affected_person, frame, agent, relation, object, role, path) — the object that '
  'replaces the flat target list. Root key (§2.1 R4-S01): root_id := contact_id on '
  'transit-relation rows, root_id := object_id on natal-fact rows — derivable from '
  'stored columns, deliberately not duplicated. House counts are computed from the '
  'row''s own frame, arithmetic stored at evaluation time (§1.2 inv 5). Affliction is a '
  'predicate, not a label (§1.2 inv 8, #23). No soft factor field may zero an admitted '
  'window (§1.2 inv 7). Writer contract: registered-writer family ka_gochara, '
  'idempotent per-(chart_id × generation) delete-then-insert (§10.1) — no immutability '
  'trigger by design.';

-- Read shapes the evaluator and rehearsal actually use.
CREATE INDEX IF NOT EXISTS idx_kgrr_chart_gen ON ka_gochara_relationship_record
  (chart_id, generation, event_class);
CREATE INDEX IF NOT EXISTS idx_kgrr_contact ON ka_gochara_relationship_record
  (contact_id) WHERE contact_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_kgrr_object ON ka_gochara_relationship_record
  (object_id);
CREATE INDEX IF NOT EXISTS idx_kgrr_path ON ka_gochara_relationship_record
  (path_id, rule_version);

COMMIT;
