-- Migration 490: kala_field_clocks — Lane B, ṢAḌ-DARŚANA W2 ("the field as
-- science"). Per KALA_W2_FIELD_DESIGN_v1_0.md §4 (Lane B: Stage 3 clocks,
-- Law-1 applicability item 12, uncertainty-budget item 24-full) + §9.3's
-- reserved migration-table list (474-483 in this directory; 473 was the
-- confirmed live max immediately before this migration was written).
-- =============================================================================
-- Context: W2 is a ten-stage point-process pipeline built BESIDE the legacy
-- ka_gochara_sweep/ka_sangam/etc writers (strangler-fig; those keep serving,
-- untouched). It is built by five parallel lanes, each owning a disjoint set
-- of files and tables (design doc §0). Lane B owns Stage 3: for each daśā
-- system, Law-1 applicability evaluation (a graded (state, quality) pair, not
-- a boolean) and the uncertainty-budget / interval-propagation machinery
-- (birth-time + ayanamsha uncertainty propagated through the daśā ladder,
-- yielding an honest instant/interval/precision_unsupported posture per
-- boundary — "no claim is ever served at a precision the input uncertainty
-- cannot support").
--
-- TWO TABLES:
--   1. kala_field_clocks     — one row per (chart_id, system_id): the Law-1
--      applicability_state, competence_class, seniority_rank, and quality
--      (A_s, the system's own determination-robustness) that feed §5.1's
--      hazard formula's clock term C_e(t). A system with no chart_dashas
--      rows, or with no quality rule this builder is willing to invent
--      (B.10), is honestly `not_computed` here, never fabricated.
--   2. kala_field_boundaries — one row per (chart_id, system_id, level,
--      t_boundary): the propagated sigma_t, its [interval_lo, interval_hi],
--      and the resulting precision_state, for every chart_dashas boundary
--      this builder can support (levels MD/AD/PD/SD only — chart_dashas
--      never computes level 5 / Prāṇa; that absence is honest, not a gap).
--      Every row cites the exact chart_dashas row it inherits its
--      t_boundary from (`source_pk`) — this builder computes UNCERTAINTY
--      ABOUT the boundary, never the boundary itself (§N.5 / SS_N.5: L1 is
--      the authority over L2+ derivations).
--
-- Nirmāṇa build-tracker contract (brief §2.5 / design doc §9.2): NO new
-- asset_registry row lands here — ka_kshetra's single seed row (and its
-- depends_on array) is owned by Lane C and lands with migration 483 per the
-- design doc's own migration-table plan (§9.3), together with mi_bhara /
-- mi_sankalpa's rows. This migration creates ONLY the two tables Lane B owns.
--
-- Idempotency (§N.3 — L1+ per-chart tables: delete-then-insert scoped to
-- chart_id x natural key, never accretive). The writer (Lane C's forthcoming
-- `pipeline/orchestrator/writers/ka_kshetra.py`, per the FROZEN orchestrator
-- contract) deletes this chart's prior kala_* field-table rows ONCE in
-- plan_substeps before any substep of a fresh/replanned build runs. Lane B's
-- own writer helpers (`stage3_clocks.write_clock_rows` /
-- `write_boundary_rows`) additionally delete-then-insert scoped to
-- (chart_id x system_id) on every call, so they remain independently
-- idempotent even outside that orchestrator-level guarantee.
-- =============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS kala_field_clocks (
    id                    BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    chart_id              UUID        NOT NULL,
    system_id             TEXT        NOT NULL,
    applicability_state   TEXT        NOT NULL
        CHECK (applicability_state IN ('applicable', 'excluded_by_condition', 'not_computed')),
    exclusion_reason      TEXT,
    competence_class      TEXT        NOT NULL
        CHECK (competence_class IN ('fruition', 'arena', 'flavour', 'health', 'annual', 'life_stage')),
    seniority_rank        INT         NOT NULL,
    quality               DOUBLE PRECISION
        CHECK (quality IS NULL OR (quality >= 0 AND quality <= 1)),
    quality_basis         TEXT,
    is_predictive         BOOLEAN     NOT NULL,
    source_table          TEXT        NOT NULL DEFAULT 'chart_dashas',
    computed_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_kala_field_clocks UNIQUE (chart_id, system_id)
);

CREATE INDEX IF NOT EXISTS idx_kala_field_clocks_chart
    ON kala_field_clocks (chart_id);

COMMENT ON TABLE kala_field_clocks IS
  'ṢAḌ-DARŚANA W2 Lane B / Stage 3, item 12: one row per (chart, daśā system) '
  '— the Law-1 applicability evaluation (state + competence_class + quality, '
  'NOT a boolean gate) that feeds the §5.1 hazard formula''s clock term. A '
  'system absent from chart_dashas, or lacking a defined quality rule, is '
  'honestly not_computed here (quality NULL) — never fabricated (B.10). '
  'quality (A_s) is the system''s own determination-robustness at build '
  'time; it is NOT the fitted weight w_s (owned by mi_bhara/Lane E), which '
  'multiplies in the hazard exponent independently.';

CREATE TABLE IF NOT EXISTS kala_field_boundaries (
    id                          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    chart_id                    UUID        NOT NULL,
    system_id                   TEXT        NOT NULL,
    level                       TEXT        NOT NULL
        CHECK (level IN ('MD', 'AD', 'PD', 'SD', 'PrD')),
    lord                        TEXT        NOT NULL,
    parent_lords                TEXT[]      NOT NULL DEFAULT '{}',
    t_boundary                  DOUBLE PRECISION NOT NULL,
    period_days                 DOUBLE PRECISION NOT NULL CHECK (period_days > 0),
    sigma_t_days                DOUBLE PRECISION NOT NULL CHECK (sigma_t_days >= 0),
    interval_lo                 DOUBLE PRECISION NOT NULL,
    interval_hi                 DOUBLE PRECISION NOT NULL,
    precision_state             TEXT        NOT NULL
        CHECK (precision_state IN ('instant', 'interval', 'precision_unsupported')),
    dominant_uncertainty_source TEXT        NOT NULL
        CHECK (dominant_uncertainty_source IN ('birth_time', 'ayanamsha')),
    sigma_t_source              TEXT        NOT NULL,
    source_table                TEXT        NOT NULL DEFAULT 'chart_dashas',
    source_pk                   TEXT        NOT NULL,
    computed_at                 TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_kala_field_boundaries UNIQUE (chart_id, system_id, level, t_boundary)
);

CREATE INDEX IF NOT EXISTS idx_kala_field_boundaries_chart_system
    ON kala_field_boundaries (chart_id, system_id);
CREATE INDEX IF NOT EXISTS idx_kala_field_boundaries_precision
    ON kala_field_boundaries (chart_id, precision_state);
CREATE INDEX IF NOT EXISTS idx_kala_field_boundaries_source_pk
    ON kala_field_boundaries (source_pk);

COMMENT ON TABLE kala_field_boundaries IS
  'ṢAḌ-DARŚANA W2 Lane B / Stage 3, item 24-full: one row per (chart, '
  'system, level, t_boundary) — the propagated birth-time + ayanāṃśa '
  'uncertainty (sigma_t) around a chart_dashas boundary, its [interval_lo, '
  'interval_hi], and the honest precision_state this uncertainty supports '
  '(instant / interval / precision_unsupported — never a claim finer than '
  'the input uncertainty allows). t_boundary is INHERITED from the cited '
  'chart_dashas row (source_pk) to within 1e-6 days, never recomputed '
  '(§N.5 / SS_N.5). Levels MD/AD/PD/SD only — chart_dashas never persists '
  'level 5 (Prāṇa); that absence is honest, not a build gap.';

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   DROP TABLE IF EXISTS kala_field_boundaries;
--   DROP TABLE IF EXISTS kala_field_clocks;
--   COMMIT;
-- =============================================================================
