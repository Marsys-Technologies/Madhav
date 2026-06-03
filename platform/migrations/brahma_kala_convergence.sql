-- brahma_kala_convergence.sql
-- BRAHMA-KA-3-2: kala.convergence — measured convergence windows (≥3 factors align simultaneously)
--
-- Contract (BRAHMA_L1_L5_REGISTRY_SEED §D):
--   table:   kala_convergence (chart_id UUID, window_start DATE, window_end DATE,
--            convergence_score FLOAT, constituent_factors JSONB, source_citation TEXT NOT NULL)
--   tool:    convergence_window(chart_id, date_range, min_score?) → windows with provenance_envelope
--   gate:    convergence windows surfaced; score in [0.0, 1.0]; provenance_envelope on response
--   FORENSIC: native's 2002-07 (Saturn-Moon AD start) and 2017-09 (Mercury Sun→Moon AD)
--             must produce ≥1 convergence window that overlaps those dates.
--
-- Algorithm:
--   Scan kala_timeline for date clusters where ≥3 of:
--   dasha_transition, transit_conjunction, signal_activation, MD/AD alignment coincide
--   within a 45-day neighbourhood.
--   convergence_score = Σ(factor_weight_i) / (factor_count × 1.0), capped at 1.0
--
-- Source: FORENSIC_ASTROLOGICAL_DATA §5.1 Vimshottari Dasha table + §22 Sade Sati cycles
-- Source citation (all rows): "PyJHora/SwissEph DE441 + Brahma-L1"
--
-- ROLLBACK: DROP TABLE IF EXISTS kala_convergence; DROP TABLE IF EXISTS kala_convergence_staging;
-- ─────────────────────────────────────────────────────────────────────────────────────────────

-- ── Table ─────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS kala_convergence (
  convergence_id      BIGSERIAL   NOT NULL,
  chart_id            UUID        REFERENCES charts(chart_id),
  window_start        DATE        NOT NULL,
  window_end          DATE        NOT NULL,
  convergence_score   FLOAT       NOT NULL
                                  CHECK (convergence_score >= 0.0 AND convergence_score <= 1.0),
  constituent_factors JSONB       NOT NULL DEFAULT '[]',
  source_citation     TEXT        NOT NULL
                                  CHECK (char_length(source_citation) > 0),
  computed_at         TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT kala_convergence_pk        PRIMARY KEY (convergence_id),
  CONSTRAINT kala_convergence_valid_range CHECK (window_end >= window_start)
);

-- ── Indexes ───────────────────────────────────────────────────────────────────

-- Primary lookup: all windows for a chart
CREATE INDEX IF NOT EXISTS idx_kala_convergence_chart_id
  ON kala_convergence (chart_id);

-- Date range queries: windows overlapping a given interval
CREATE INDEX IF NOT EXISTS idx_kala_convergence_window
  ON kala_convergence (chart_id, window_start, window_end);

-- Score filter: find high-convergence periods
CREATE INDEX IF NOT EXISTS idx_kala_convergence_score
  ON kala_convergence (chart_id, convergence_score DESC);

-- ── Staging mirror (idempotent swap pattern) ──────────────────────────────────

CREATE TABLE IF NOT EXISTS kala_convergence_staging
  (LIKE kala_convergence INCLUDING ALL);

-- ── Comment ───────────────────────────────────────────────────────────────────

COMMENT ON TABLE kala_convergence IS
  'BRAHMA-KA-3-2: kala.convergence — measured convergence windows where ≥3 temporal '
  'factors (dasha_transition, transit_conjunction, signal_activation, md_ad_alignment) '
  'align within a 30-day neighbourhood. convergence_score = Σweights/(count×1.0). '
  'source_citation is non-null on all rows: PyJHora/SwissEph DE441 + Brahma-L1. '
  'Seeded by brahmagyan.kala.convergence; queried by kala_convergence.ts MCP tool.';

COMMENT ON COLUMN kala_convergence.convergence_score IS
  'Weighted factor alignment score in [0.0, 1.0]. '
  'convergence_score = Σ(factor_weight_i) / (factor_count × 1.0). '
  'Higher = more factors aligned with higher individual weights.';

COMMENT ON COLUMN kala_convergence.constituent_factors IS
  'JSONB array of factor objects: {label, date, weight, factor_type}. '
  'factor_type ∈ {dasha_transition, transit_conjunction, signal_activation, md_ad_alignment}.';

COMMENT ON COLUMN kala_convergence.source_citation IS
  'Non-null provenance string. Required: "PyJHora/SwissEph DE441 + Brahma-L1".';
