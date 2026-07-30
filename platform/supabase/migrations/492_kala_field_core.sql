-- migration 492: kala_field + kala_field_windows + kala_field_snapshots
-- =============================================================================
-- ṢAḌ-DARŚANA campaign · Wave W2 ("the field as science") · Lane C.
-- Build spec: KALA_W2_FIELD_DESIGN_v1_0.md §5.2 (segment representation + exact
-- analytic integration), §5.3 (these two tables verbatim), §9.3 row 478, §9.4
-- (kala_field_snapshots / freshness).
--
-- ── WHAT `kala_field` STORES, AND WHY LOG-LINEAR SEGMENTS (§5.2) ─────────────
-- λ_e(t) is the point-process HAZARD RATE of event class e at time t for this
-- chart, in events/day, STRICTLY POSITIVE everywhere by construction (§5.1). On
-- each segment [t_i, t_{i+1}] the field is stored as
--       ln λ_e(t) = alpha_i + gamma_i · (t − t_i)
-- This is a DEFINITION OF THE STORED FIELD, not an approximation claim: every
-- downstream consumer — serving, integration, the stage-5 null, the stage-9
-- fitter — reads THAT. Two properties follow and both are load-bearing:
--   (a) Λ_e(a,b) = ∫λ is available in CLOSED FORM (integrator.py), so the
--       fitter's Poisson log-likelihood and the served expected_count are the
--       SAME arithmetic — if they diverged, the published skill score would be
--       measuring a model the product does not serve;
--   (b) ln λ is MONOTONE on each segment, so a window's peak is ALWAYS a
--       breakpoint and needs no interior optimizer. §5.2 states explicitly that
--       this "must not be 'improved' into one — the closed-form property is what
--       makes the field hash-replayable."
--
-- ── THE TWO SNAPSHOT IDENTITIES (a deliberate, documented resolution) ────────
-- §7.4 defines `field_snapshot_id` as a hash whose inputs INCLUDE "canonical
-- serialization of every stage 0–8 row for this chart". But §5.3 also makes
-- `field_snapshot_id` a NOT NULL column ON those very rows. A value cannot both
-- be an input to writing a row and a digest of it. This migration therefore
-- carries the two identities under two distinct names:
--   • `field_snapshot_id` (on every row here) = the PIN IDENTITY,
--       'kfs_' + sha256(canonical_json({chart_id, corpus_pin, config_pin,
--                                       weights_version, cohort_version}))[:32]
--     — known at plan time, resolved EXACTLY ONCE in plan_substeps, identical on
--     every row of one build. This is what makes "all rows of one snapshot share
--     one weights_version" checkable (§7.5 sub-rule 5).
--   • `kala_field_snapshots.field_content_hash` = the FULL §7.4 hash, INCLUDING
--     the row serialization, computed in the terminal snapshot substep after all
--     rows are committed. THIS is the value the hash-replay CI compares and the
--     value the CIRCULARITY GUARD's CG-1 invariant is stated over (§8.3).
-- Anything asserting "the field did not move" must compare `field_content_hash`;
-- comparing the pin identity alone would be a signal with no detector (§N.8).
--
-- ── IDEMPOTENCY (§N.3) ──────────────────────────────────────────────────────
-- Per-chart delete-then-insert scoped to (chart_id × natural key), performed
-- EXACTLY ONCE in `plan_substeps` — never per-substep (the ka_gochara_sweep
-- D-5 RED-C lesson: a per-substep delete silently wipes sibling substeps' rows).
-- =============================================================================

BEGIN;

-- ── kala_field — the segment representation ──────────────────────────────────

CREATE TABLE IF NOT EXISTS kala_field (
  id                        BIGSERIAL PRIMARY KEY,
  chart_id                  UUID NOT NULL,
  event_class               TEXT NOT NULL,
  segment_index             INT  NOT NULL,               -- ascending within (chart, event_class)
  t_start                   DOUBLE PRECISION NOT NULL,   -- days since birth
  t_end                     DOUBLE PRECISION NOT NULL,
  alpha                     DOUBLE PRECISION NOT NULL,   -- ln λ at t_start⁺
  gamma                     DOUBLE PRECISION NOT NULL,   -- d(ln λ)/dt on the segment
  lambda_start              DOUBLE PRECISION NOT NULL,   -- exp(alpha)      (denormalized read path)
  lambda_end                DOUBLE PRECISION NOT NULL,
  integral_days             DOUBLE PRECISION NOT NULL,   -- Λ over this segment (denormalized, ADDITIVE)
  promise_term              DOUBLE PRECISION NOT NULL,   -- P̃_e (constant in t)
  clock_term_start          DOUBLE PRECISION NOT NULL,   -- C_e(t_start)
  modifier_term_start       DOUBLE PRECISION NOT NULL,   -- M_e(t_start)
  suppression_term_start    DOUBLE PRECISION NOT NULL,   -- S_e(t_start) ∈ (0,1]
  signed_obstruction_start  DOUBLE PRECISION NOT NULL,   -- −(1 − S)  SERVING RENDERING ONLY
  refinement_depth          SMALLINT NOT NULL DEFAULT 0,
  refinement_exhausted      BOOLEAN  NOT NULL DEFAULT FALSE,
  refinement_residual       DOUBLE PRECISION,            -- |ln λ(t_m) − stored| at exhaustion (nats)
  weights_version           TEXT NOT NULL,
  x_schema_version          TEXT NOT NULL,
  field_snapshot_id         TEXT NOT NULL,               -- PIN identity (see header)
  computed_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT kala_field_segment_order_ck CHECK (t_end > t_start),
  CONSTRAINT kala_field_suppression_range_ck
    CHECK (suppression_term_start > 0 AND suppression_term_start <= 1),
  CONSTRAINT kala_field_natural_key UNIQUE (chart_id, event_class, segment_index)
);

CREATE INDEX IF NOT EXISTS idx_kala_field_lookup
  ON kala_field (chart_id, event_class, t_start, t_end);
CREATE INDEX IF NOT EXISTS idx_kala_field_snapshot
  ON kala_field (chart_id, field_snapshot_id);

COMMENT ON TABLE kala_field IS
  'ṢAḌ-DARŚANA W2 §5.2/§5.3: the log-linearly segmented point-process hazard '
  'λ_e(t) for one chart. ln λ = alpha + gamma·(t − t_start) on each segment — a '
  'DEFINITION of the stored field, not an approximation claim. Exactly '
  'integrable in closed form (services/ka_kshetra/integrator.py), which is what '
  'lets the stage-9 fitter and the serving layer share one arithmetic.';

COMMENT ON COLUMN kala_field.signed_obstruction_start IS
  'SERVING RENDERING ONLY (§5.1 C-6). −(1 − S_e) is what a reader sees as a '
  '"negative"; it is NEVER fed back into the hazard math. Suppression is '
  'MULTIPLICATIVE THINNING (S = Π(1 − ρ·u), ρ ≤ 0.95), never subtraction — '
  'which is exactly what keeps λ strictly positive by construction.';

COMMENT ON COLUMN kala_field.refinement_exhausted IS
  'TRUE when adaptive refinement hit depth 6 with the midpoint residual still '
  'above τ = 0.02 nats. The row is still served, with refinement_residual '
  'recorded — visible, never silent (LAW ZERO).';

-- ── kala_field_windows ───────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS kala_field_windows (
  id                  BIGSERIAL PRIMARY KEY,
  chart_id            UUID NOT NULL,
  window_id           TEXT NOT NULL,               -- THE item-44 authority_basis value (§5.2)
  event_class         TEXT NOT NULL,
  t_start             DOUBLE PRECISION NOT NULL,
  t_end               DOUBLE PRECISION NOT NULL,
  window_start        DATE NOT NULL,
  window_end          DATE NOT NULL,
  peak_date           DATE NOT NULL,
  t_peak              DOUBLE PRECISION NOT NULL,
  lambda_peak         DOUBLE PRECISION NOT NULL,
  expected_count      DOUBLE PRECISION NOT NULL,   -- Λ over the window
  duration_days       DOUBLE PRECISION NOT NULL,
  promise_state       TEXT NOT NULL CHECK (promise_state IN ('strong','moderate','weak','absent')),
  temporal_shape      TEXT NOT NULL CHECK (temporal_shape IN ('point','interval','chain')),
  precision_regime    TEXT NOT NULL DEFAULT 'day_grade'
                        CHECK (precision_regime IN ('day_grade','sub_day')),
  -- ── stage 5 columns (same lane, written in the stage-5 finalize substep) ──
  null_p              DOUBLE PRECISION,
  null_R              INT,
  null_resolution     DOUBLE PRECISION,
  null_exceeding      BOOLEAN,
  robustness          JSONB,
  confidence_tier     TEXT,
  weakest_link        TEXT,
  adrishta_residual   DOUBLE PRECISION,
  weights_version     TEXT NOT NULL,
  x_schema_version    TEXT NOT NULL,
  field_snapshot_id   TEXT NOT NULL,
  computed_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT kala_field_windows_span_ck CHECK (t_end >= t_start),
  CONSTRAINT kala_field_windows_peak_in_span_ck CHECK (t_peak >= t_start AND t_peak <= t_end),
  CONSTRAINT kala_field_windows_natural_key UNIQUE (chart_id, window_id)
);

CREATE INDEX IF NOT EXISTS idx_kala_field_windows_lookup
  ON kala_field_windows (chart_id, event_class, t_start, t_end);
CREATE INDEX IF NOT EXISTS idx_kala_field_windows_snapshot
  ON kala_field_windows (chart_id, field_snapshot_id);

COMMENT ON TABLE kala_field_windows IS
  'ṢAḌ-DARŚANA W2 §5.2/§5.3. A window is a MAXIMAL interval where λ_e(t) ≥ q_e, '
  'with q_e the 95th percentile of the chart''s OWN circular-shifted null (§5.5) '
  '— so "a window" means "a stretch where this chart''s hazard exceeds what its '
  'own shifted sky would produce 95% of the time". A definition, not a tuning '
  'knob. window_id is the SINGLE TEMPORAL AUTHORITY value (item 44): every '
  'temporal claim product-wide cites it via authority_basis, and a serving path '
  'that computes its own window is a build error, not a divergence to classify.';

COMMENT ON COLUMN kala_field_windows.window_id IS
  'kfw_ + sha256(chart_id|event_class|round(t_start,6)|round(t_end,6)|'
  'weights_version|x_schema_version)[:24]. Deterministic and stable: the same '
  'field replayed yields the same ids, which is what makes EXPLAIN drill-ids '
  '1:1 with timeline-spec interval ids.';

COMMENT ON COLUMN kala_field_windows.null_resolution IS
  '1/(R+1). Served ALONGSIDE null_p so a consumer can never mistake p = 0.0039 '
  'for p = 0 (LAW ZERO: never report a precision the replicate count cannot '
  'support).';

COMMENT ON COLUMN kala_field_windows.expected_count IS
  'Λ_e over the window — the exact analytic integral of the stored segments. '
  'This is what makes PRIORITIZE''s imminence and intensity axes dimensionally '
  'honest: it is an expected NUMBER OF EVENTS, not a unitless score.';

-- ── kala_field_snapshots (§9.4 freshness + §7.4 content hash) ────────────────

CREATE TABLE IF NOT EXISTS kala_field_snapshots (
  id                   BIGSERIAL PRIMARY KEY,
  chart_id             UUID NOT NULL,
  field_snapshot_id    TEXT NOT NULL,              -- the PIN identity (see header)
  field_content_hash   TEXT,                       -- the FULL §7.4 row-inclusive hash; NULL until finalized
  weights_version      TEXT NOT NULL,
  x_schema_version     TEXT NOT NULL,
  corpus_pin           TEXT NOT NULL,
  config_pin           JSONB NOT NULL,             -- ephemeris version, ayanamsha, H, P_floor, τ, ρ_max, …
  cohort_version       TEXT,                       -- NULL ⇒ rarity not computable this build (honest)
  substrate_build_ids  JSONB NOT NULL DEFAULT '{}'::jsonb,  -- {asset_id: build_id} actually consumed
  hashed_tables        TEXT[] NOT NULL DEFAULT '{}',        -- which stage 0–8 tables the hash covered
  event_classes        TEXT[] NOT NULL DEFAULT '{}',
  skipped_classes      JSONB NOT NULL DEFAULT '[]'::jsonb,  -- [{event_class, reason}] — LAW ZERO
  horizon_days         DOUBLE PRECISION NOT NULL,
  built_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT kala_field_snapshots_natural_key UNIQUE (chart_id, field_snapshot_id)
);

CREATE INDEX IF NOT EXISTS idx_kala_field_snapshots_chart
  ON kala_field_snapshots (chart_id, built_at DESC);

COMMENT ON TABLE kala_field_snapshots IS
  'ṢAḌ-DARŚANA W2 §9.4: what kala_envelope.ts::buildKalaFreshness reads to fill '
  '{ephemeris_version, sweep_build_date, field_hash}, and where §7.4''s FULL '
  'row-inclusive content hash lives (field_content_hash). buildFieldSnapshotIdStub '
  'is replaced by a lookup against this table at W2 — per its own TODO, that '
  'function''s BODY is the only thing that changes; no caller in the eight '
  'facades is touched.';

COMMENT ON COLUMN kala_field_snapshots.skipped_classes IS
  'LAW ZERO / honest-empty: every event class the build did NOT write field rows '
  'for, WITH its reason (e.g. no bg_class_priors lifetime-count row ⇒ '
  'not_computed, §5.1 C-1 — "never given a made-up baseline"). An empty array '
  'here is a claim that nothing was skipped, and is checkable.';

COMMENT ON COLUMN kala_field_snapshots.field_content_hash IS
  'The §7.4 hash INCLUDING the canonical row serialization. This — not '
  'field_snapshot_id — is the value the hash-replay CI compares and the value '
  'CIRCULARITY GUARD CG-1 (§8.3) is stated over. NULL means the finalize substep '
  'has not run: an honest "not computed", never a stand-in.';

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   DROP TABLE IF EXISTS kala_field_snapshots;
--   DROP TABLE IF EXISTS kala_field_windows;
--   DROP TABLE IF EXISTS kala_field;
--   COMMIT;
-- =============================================================================
