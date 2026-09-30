-- Migration 1156: ka_gochara_eval_window — the §2.1 eval_window typed
--                 contract, with §3.1 valence fields. Depends on 1154
--                 (ka_gochara_rule_path) and 1081 (kala_gochara_publication).
-- Created: 2026-09-30. Author: pravaha/a5-migrations (Stream A, A5.1).
--
-- Numbering: 1156 sits inside this lane's granted block (1150–1159 per
-- ADK-0026 §4; 1150/1151/1152 are used). Verified free by a fresh scan of
-- every origin/* ref across BOTH platform/migrations/ and
-- platform/supabase/migrations/ (2026-09-30: max in use anywhere is 1152;
-- no 1156 anywhere). `npm run guard:migration-numbers` green on this branch.
--
-- Spec: GOCHARA_DESIGN_SPECS_v1_4 (FROZEN 2026-09-30). §2.1 eval_window
-- schema: {window_id PK, chart_id, event_class, generation, (path_id,
-- rule_version) FK, interval, peak_instant, score, evidence_for,
-- evidence_against, outcome_valence_for_native, severity, record_ids: [FK],
-- coverage_ref, null_states_used[]}. Encoded as:
--   * CONSTRAINT / COLUMN: window_id uuid PK; chart_id FK → charts(id);
--     event_class CHECK against the 27-class enumeration of
--     EVALUATION_PROTOCOL_v2_2 §2 (sole enumeration — §2.1 amendment 2);
--     generation NOT NULL; composite version-bound FK (path_id, rule_version)
--     → ka_gochara_rule_path (§2.1); interval tstzrange NOT NULL;
--     peak_instant timestamptz; score / evidence_for / evidence_against
--     real; outcome_valence_for_native 4-enum (§3.1); severity real;
--     record_ids uuid[] (array of ka_gochara_relationship_record.record_id
--     — see the COMMENT; Postgres cannot FK-constrain array elements);
--     coverage_ref uuid NOT NULL → kala_gochara_publication(manifest_id)
--     (same decision as 1155 — kala_gochara_coverage's PK is composite; see
--     the 1155 header); null_states_used text[] NOT NULL DEFAULT '{}'.
--   * COMMENT ONLY (evaluator behaviour): cross-path aggregation — a
--     class–instant's score is the MAX over admitted paths (union
--     semantics); conflicting evidence is never netted; the peak instant is
--     the argmax of min(activity_Jupiter, activity_Saturn) for P4, solved
--     for interior extrema, never endpoint-only (§2.2 P4, §7.2 inv 2);
--     score ranks and never admits or excludes (§2).
--   * DELIBERATELY NOT ENCODED: peak_instant ∈ interval CHECK — §7.2 inv 2
--     requires interior-extremum solving, but the spec does not state the
--     peak must lie inside the stored interval for every path form, and an
--     invented containment CHECK could reject a legitimate row; flagged in
--     the A5.1 report as an open question rather than guessed. score
--     ∈ [0,1] is NOT constrained: the within-path product lies in [0,1]
--     (§2.1), but the cross-path max preserves that only for scores —
--     evidence sums are unbounded and score nullability under 'unqualified'
--     propagation (NK-4) is evaluator semantics.
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
--   DROP TABLE IF EXISTS ka_gochara_eval_window;
-- ─────────────────────────────────────────────────────────────────────────────

BEGIN;

SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '120s';

CREATE TABLE IF NOT EXISTS ka_gochara_eval_window (
  window_id         UUID PRIMARY KEY,
  chart_id          UUID NOT NULL REFERENCES charts(id),
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
                    -- 27 classes, EVALUATION_PROTOCOL_v2_2 §2 (sole enumeration)
  generation        TEXT NOT NULL,               -- '4.1'/'5.0'…; generation-scoped
  path_id           TEXT,
  rule_version      TEXT,
  interval          TSTZRANGE NOT NULL,          -- the admitted window; era/month/day
                    -- are output resolutions produced by the paths at those grains,
                    -- never a clipped curve (§2.3 inv 4, #24)
  peak_instant      TIMESTAMPTZ,                 -- P4: argmax of min(activity_Jupiter,
                    -- activity_Saturn) over the overlap, interior extrema not
                    -- endpoints (§2.2 P4 peak definition, §7.2 inv 2, O-SM-4)
  score             REAL,                        -- ranks; never admits or excludes (§2);
                    -- within-path product of factor scores, cross-path max (§2.1
                    -- S-01); 'unqualified' propagates per NK-4 (evaluator semantics)
  evidence_for      REAL,                        -- §3.1: accumulates; never netted
  evidence_against  REAL,                        -- §3.1: accumulates; never netted
  outcome_valence_for_native TEXT CHECK (outcome_valence_for_native IN
                      ('favourable','adverse','mixed','unqualified')),   -- §3.1
  severity          REAL,                        -- §3.1: interpretive, rank-only
  record_ids        UUID[],                      -- FKs to
                    -- ka_gochara_relationship_record(record_id) — array elements
                    -- cannot be FK-constrained in Postgres; resolvability is
                    -- writer-checked (§2.1 record_ids: [FK])
  coverage_ref      UUID NOT NULL REFERENCES kala_gochara_publication(manifest_id),
                    -- §2.1 coverage_ref; §10.2 inv 3: every no-window answer carries
                    -- its coverage object. kala_gochara_coverage's PK is composite
                    -- (1081); the uuid-keyed manifest is kala_gochara_publication —
                    -- same disposition as 1155 (see its header).
  null_states_used  TEXT[] NOT NULL DEFAULT '{}',-- factor null_states exercised in
                    -- this evaluation (§2.1: omit / unqualified), never silent
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),

  FOREIGN KEY (path_id, rule_version)
    REFERENCES ka_gochara_rule_path (path_id, rule_version)
    -- §2.1: composite version-bound FK; unversioned references rejected
);

COMMENT ON TABLE ka_gochara_eval_window IS
  'Evaluated window (GOCHARA_DESIGN_SPECS_v1_4 §2.1 eval_window contract + §3.1 '
  'valence fields): one evaluated interval per (chart, event_class, generation, path). '
  'Occurrence evidence (evidence_for / evidence_against) answers "will this class of '
  'thing occur?"; outcome_valence_for_native answers "is that occurrence good for the '
  'native?" — the fields are independent, never netted, and contested occurrence is '
  'reported with both fields standing, never relabelled mixed (§3.1 S-03, §3.2). '
  'Writer contract: ka_gochara writer family, idempotent per-(chart_id × generation) '
  'delete-then-insert (§10.1).';

-- Serving shape: per-chart+generation windows of a class, time-ordered.
CREATE INDEX IF NOT EXISTS idx_kgew_chart_gen ON ka_gochara_eval_window
  (chart_id, generation, event_class, interval);
CREATE INDEX IF NOT EXISTS idx_kgew_path ON ka_gochara_eval_window
  (path_id, rule_version);

COMMIT;
