-- Migration 1156: ka_gochara_eval_window — the §2.1 eval_window typed
--                 contract + §3.1 valence fields, with NORMALISED record
--                 membership scoped to chart+generation (amendments 3/4) and
--                 the completed score/interval contract (amendment 7).
--                 Depends on 1154 (ka_gochara_rule_path), 1155
--                 (ka_gochara_relationship_record) and 1081
--                 (kala_gochara_coverage). Rewritten at A5.1 round 2 per
--                 ASTRA_REVIEW_A5_1_MIGRATIONS v1_0 and the steward rulings.
--                 Never applied anywhere — in-place rewrite.
-- Created: 2026-09-30. Author: pravaha/a5-migrations (Stream A, A5.1).
--
-- Numbering: 1156 sits inside this lane's granted block (1150–1159 per
-- ADK-0026 §4; 1150/1151/1152 are used). Verified free by a fresh scan of
-- every origin/* ref across BOTH platform/migrations/ and
-- platform/supabase/migrations/ (2026-09-30: max in use anywhere is 1152;
-- no 1156 anywhere). `npm run guard:migration-numbers` green on this branch.
--
-- Amendment 2 (P1 #2): NO BEGIN/COMMIT — migrate.ts owns ONE transaction
-- around DDL + ledger insert (see the 1153 header). SET LOCAL is scoped to
-- the runner's transaction.
--
-- Amendment 3 (P1 #3): path_id/rule_version are NOT NULL — a mandatory,
-- complete composite version-bound reference (S:156-158). record_ids is
-- NORMALISED into ka_gochara_eval_window_record with real FKs (S:185's
-- `[FK]` made structural): the membership row carries (chart_id, generation)
-- and binds BOTH ends to the same chart and generation — a window can never
-- reference another chart's or generation's record. ON DELETE CASCADE on
-- both ends matches the prescribed per-(chart_id × generation)
-- delete-then-insert rebuild ordering (§N.3): membership never blocks or
-- orphans a rebuild.
--
-- Amendment 4 (P1 #4): the coverage handle is the 1081 coverage PARTITION,
-- bound by composite FK to the window's own chart and generation (same
-- disposition as 1155).
--
-- Amendment 7 (P1 #7): score carries the conditional [0,1] CHECK — the
-- within-path product lies in [0,1] and the cross-path max preserves it
-- (S:167-170, 187-188, 209-213); NULL is preserved for explicitly
-- unqualified scores (NK-4). evidence_for / evidence_against are CHECKed
-- nonnegative — they accumulate unbounded and never receive the score's
-- upper bound. Empty evaluated intervals are rejected (NOT isempty). A
-- computed peak_instant must lie inside the window's own interval — P4's
-- peak is the argmax of min(activity_Jupiter, activity_Saturn) over the
-- overlap (S:321-323, §7.2 inv 2).
--
-- Amendment 5 (P1 #5): outcome_valence_for_native is NOT NULL —
-- 'unqualified' is the declared honest state (§3.2 inv 3).
--
-- Amendment 9 (P2 #9): the S:89 canonical-chart restriction is enforced as
-- a CHECK (D-SCOPE disposition); null_states_used elements are constrained
-- to the declared {omit, unqualified} vocabulary.
--
-- asset_registry: deliberately NOT registered (asset_registry.layer CHECK
-- has no 'L2' value; contract table of the already-registered ka_gochara
-- writer family — same disposition as 1081).
--
-- Operational properties: pure CREATE TABLE / INDEX + post-DDL verification;
-- no existing object or data touched; no business-data writes. Execution
-- outcomes (amendment 8): fresh apply = create + verify; repeat execution =
-- verified no-op; drifted same-named object = loud RAISE.
--
-- ROLLBACK:
--   DROP TABLE IF EXISTS ka_gochara_eval_window_record;
--   DROP TABLE IF EXISTS ka_gochara_eval_window;
-- ─────────────────────────────────────────────────────────────────────────────

SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '120s';

CREATE TABLE IF NOT EXISTS ka_gochara_eval_window (
  window_id         UUID PRIMARY KEY,
  chart_id          UUID NOT NULL REFERENCES charts(id),
  event_class       TEXT NOT NULL,
  generation        TEXT NOT NULL,               -- '4.1'/'5.0'…; generation-scoped
  path_id           TEXT NOT NULL,               -- amendment 3: mandatory complete
  rule_version      TEXT NOT NULL,               --   version-bound reference
  interval          TSTZRANGE NOT NULL,          -- the admitted window; never empty
  peak_instant      TIMESTAMPTZ,                 -- P4: argmax of min(activity_Jupiter,
                                                 --   activity_Saturn) over the overlap,
                                                 --   interior extrema (S:321-323, §7.2
                                                 --   inv 2, O-SM-4); ∈ interval when set
  score             REAL,                        -- ranks; never admits or excludes (§2);
                                                 --   NULL = explicitly unqualified (NK-4)
  evidence_for      REAL,                        -- §3.1: accumulates; never netted; ≥ 0
  evidence_against  REAL,                        -- §3.1: accumulates; never netted; ≥ 0
  outcome_valence_for_native TEXT NOT NULL,      -- §3.1: 'unqualified' is the declared
                                                 --   honest state — SQL NULL is not a valence
  severity          REAL,                        -- §3.1: interpretive, rank-only
  coverage_partition_kind TEXT NOT NULL,         -- amendment 4: coverage partition handle
  coverage_partition_key  TEXT NOT NULL,
  null_states_used  TEXT[] NOT NULL DEFAULT '{}',-- factor null_states exercised (§2.1),
                                                 --   never silent; ⊆ {omit, unqualified}
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT kgew_canonical_chart_ck
    CHECK (chart_id = '482012f1-710e-4a25-994a-93821f5871aa'::uuid),
    -- D-SCOPE disposition (amendment 9): canonical chart only (S:89).
  CONSTRAINT kgew_event_class_ck CHECK (event_class IN (
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
  CONSTRAINT kgew_path_fk FOREIGN KEY (path_id, rule_version)
    REFERENCES ka_gochara_rule_path (path_id, rule_version),
  CONSTRAINT kgew_interval_nonempty_ck CHECK (NOT isempty(interval)),
    -- amendment 7: an empty evaluated interval is rejected
  CONSTRAINT kgew_peak_in_interval_ck
    CHECK (peak_instant IS NULL OR peak_instant <@ interval),
    -- amendment 7 / S:321-323: a computed peak lies inside its own overlap
  CONSTRAINT kgew_score_unit_interval_ck
    CHECK (score IS NULL OR (score >= 0 AND score <= 1)),
    -- amendment 7 / S:167-170, 209-213: product then max preserve [0,1];
    -- NULL preserved for explicitly unqualified scores
  CONSTRAINT kgew_evidence_for_nn_ck
    CHECK (evidence_for IS NULL OR evidence_for >= 0),
  CONSTRAINT kgew_evidence_against_nn_ck
    CHECK (evidence_against IS NULL OR evidence_against >= 0),
  CONSTRAINT kgew_valence_ck CHECK (outcome_valence_for_native IN
    ('favourable','adverse','mixed','unqualified')),
  CONSTRAINT kgew_coverage_kind_ck CHECK (coverage_partition_kind IN
    ('body_target','event_class','moon_on_demand')),
  CONSTRAINT kgew_coverage_fk
    FOREIGN KEY (chart_id, generation, coverage_partition_kind, coverage_partition_key)
    REFERENCES kala_gochara_coverage (chart_id, generation, partition_kind, partition_key),
  CONSTRAINT kgew_null_states_ck
    CHECK (null_states_used <@ ARRAY['omit','unqualified']::text[]),
  -- FK target for the scoped membership table (amendment 3).
  CONSTRAINT kgew_identity_uq UNIQUE (window_id, chart_id, generation)
);

COMMENT ON TABLE ka_gochara_eval_window IS
  'Evaluated window (GOCHARA_DESIGN_SPECS_v1_4 §2.1 eval_window contract + §3.1 valence '
  'fields): one evaluated interval per (chart, event_class, generation, path). Record '
  'membership is normalised into ka_gochara_eval_window_record, scoped to the window''s '
  'own chart and generation (amendment 3). score ∈ [0,1] when computed, NULL when '
  'unqualified; evidence accumulates nonnegatively, never netted (§3.1 S-03, §3.2). '
  'Writer contract: ka_gochara family, idempotent per-(chart_id × generation) '
  'delete-then-insert (§10.1, §N.3).';

-- Serving shape: per-chart+generation windows of a class, time-ordered.
CREATE INDEX IF NOT EXISTS idx_kgew_chart_gen ON ka_gochara_eval_window
  (chart_id, generation, event_class, interval);
CREATE INDEX IF NOT EXISTS idx_kgew_path ON ka_gochara_eval_window
  (path_id, rule_version);
CREATE INDEX IF NOT EXISTS idx_kgew_coverage ON ka_gochara_eval_window
  (chart_id, generation, coverage_partition_kind, coverage_partition_key);

-- ── Record membership (amendment 3): real FKs, same-chart/generation scope ─

CREATE TABLE IF NOT EXISTS ka_gochara_eval_window_record (
  window_id         UUID NOT NULL,
  record_id         UUID NOT NULL,
  chart_id          UUID NOT NULL,
  generation        TEXT NOT NULL,

  PRIMARY KEY (window_id, record_id),
  CONSTRAINT kgewr_window_fk
    FOREIGN KEY (window_id, chart_id, generation)
    REFERENCES ka_gochara_eval_window (window_id, chart_id, generation)
    ON DELETE CASCADE,
  CONSTRAINT kgewr_record_fk
    FOREIGN KEY (record_id, chart_id, generation)
    REFERENCES ka_gochara_relationship_record (record_id, chart_id, generation)
    ON DELETE CASCADE
    -- amendment 3: window membership can never cross chart or generation;
    -- cascades match the prescribed §N.3 delete-then-insert rebuild ordering
);

COMMENT ON TABLE ka_gochara_eval_window_record IS
  'Eval-window record membership (amendment 3; S:185 record_ids [FK] made structural): '
  'one row per (window, contributing record), bound on both ends to the SAME '
  '(chart_id, generation) — cross-chart or cross-generation membership is impossible. '
  'ON DELETE CASCADE on both ends matches the per-(chart × generation) rebuild '
  'ordering: a rebuild never dangles and never blocks.';

CREATE INDEX IF NOT EXISTS idx_kgewr_record ON ka_gochara_eval_window_record
  (record_id);

-- ── Post-DDL definition verification (amendment 8) ────────────────────────

DO $$
DECLARE missing text;
BEGIN
  WITH expected(tbl, col, typ, nn) AS (
    VALUES
      ('ka_gochara_eval_window','window_id','uuid',true),
      ('ka_gochara_eval_window','chart_id','uuid',true),
      ('ka_gochara_eval_window','event_class','text',true),
      ('ka_gochara_eval_window','generation','text',true),
      ('ka_gochara_eval_window','path_id','text',true),
      ('ka_gochara_eval_window','rule_version','text',true),
      ('ka_gochara_eval_window','interval','tstzrange',true),
      ('ka_gochara_eval_window','peak_instant','timestamp with time zone',false),
      ('ka_gochara_eval_window','score','real',false),
      ('ka_gochara_eval_window','evidence_for','real',false),
      ('ka_gochara_eval_window','evidence_against','real',false),
      ('ka_gochara_eval_window','outcome_valence_for_native','text',true),
      ('ka_gochara_eval_window','severity','real',false),
      ('ka_gochara_eval_window','coverage_partition_kind','text',true),
      ('ka_gochara_eval_window','coverage_partition_key','text',true),
      ('ka_gochara_eval_window','null_states_used','text[]',true),
      ('ka_gochara_eval_window_record','window_id','uuid',true),
      ('ka_gochara_eval_window_record','record_id','uuid',true),
      ('ka_gochara_eval_window_record','chart_id','uuid',true),
      ('ka_gochara_eval_window_record','generation','text',true)
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
    RAISE EXCEPTION 'migration 1156 post-DDL verification failed (amendment 8): column drift: %', missing;
  END IF;

  WITH expected(conrelid, conname) AS (
    VALUES
      ('ka_gochara_eval_window','kgew_canonical_chart_ck'),
      ('ka_gochara_eval_window','kgew_event_class_ck'),
      ('ka_gochara_eval_window','kgew_path_fk'),
      ('ka_gochara_eval_window','kgew_interval_nonempty_ck'),
      ('ka_gochara_eval_window','kgew_peak_in_interval_ck'),
      ('ka_gochara_eval_window','kgew_score_unit_interval_ck'),
      ('ka_gochara_eval_window','kgew_evidence_for_nn_ck'),
      ('ka_gochara_eval_window','kgew_evidence_against_nn_ck'),
      ('ka_gochara_eval_window','kgew_valence_ck'),
      ('ka_gochara_eval_window','kgew_coverage_kind_ck'),
      ('ka_gochara_eval_window','kgew_coverage_fk'),
      ('ka_gochara_eval_window','kgew_null_states_ck'),
      ('ka_gochara_eval_window','kgew_identity_uq'),
      ('ka_gochara_eval_window_record','kgewr_window_fk'),
      ('ka_gochara_eval_window_record','kgewr_record_fk')
  )
  SELECT string_agg(e.conrelid || '.' || e.conname, ', ' ORDER BY 1) INTO missing
  FROM expected e
  WHERE NOT EXISTS (
    SELECT 1 FROM pg_constraint c
    WHERE c.conrelid = to_regclass('public.' || e.conrelid) AND c.conname = e.conname
  );
  IF missing IS NOT NULL THEN
    RAISE EXCEPTION 'migration 1156 post-DDL verification failed (amendment 8): missing constraint: %', missing;
  END IF;
END;
$$;
