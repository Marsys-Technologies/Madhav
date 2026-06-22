-- Migration 340 — School consensus tables (U4 activation; formerly 057-060 archived schema)
-- L4 Phala Campaign, 2026-06-22.
-- Tables: school_signal_coverage, school_analysis_runs, convergence_scores, school_disagreements.
-- Key differences from archived 057-060: chart_id added everywhere; no 'abhisek_primary' default.
-- Idempotent: all CREATE TABLE / INDEX wrapped in IF NOT EXISTS.

-- ── school_signal_coverage ────────────────────────────────────────────────────
-- Records which of the 7 Jyotish schools covers each MSR signal (per chart).
-- 573 signals × 7 schools = 4,011 classifications at full population (native chart).
CREATE TABLE IF NOT EXISTS school_signal_coverage (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chart_id       TEXT NOT NULL,
  signal_id      TEXT NOT NULL,
  school         TEXT NOT NULL CHECK (
    school IN ('parashari','jaimini','tajika','kp','nadi','bnn','yogini')
  ),
  coverage_type  TEXT NOT NULL CHECK (
    coverage_type IN ('primary','secondary','silent')
  ),
  confidence     NUMERIC(4,3),
  attribution_chunk_id UUID,
  created_at     TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (chart_id, signal_id, school)
);

CREATE INDEX IF NOT EXISTS ssc_chart_id_idx       ON school_signal_coverage(chart_id);
CREATE INDEX IF NOT EXISTS ssc_signal_idx         ON school_signal_coverage(signal_id);
CREATE INDEX IF NOT EXISTS ssc_school_idx         ON school_signal_coverage(school);
CREATE INDEX IF NOT EXISTS ssc_coverage_type_idx  ON school_signal_coverage(coverage_type);
CREATE INDEX IF NOT EXISTS ssc_school_coverage_idx ON school_signal_coverage(school, coverage_type);
CREATE INDEX IF NOT EXISTS ssc_chart_school_type_idx ON school_signal_coverage(chart_id, school, coverage_type);

COMMENT ON TABLE school_signal_coverage IS
  'Per-signal per-school coverage classification for school consensus activation (U4). '
  '573 signals × 7 schools = 4,011 rows at full population. '
  'coverage_type: primary=school owns this signal; secondary=partial; silent=no coverage.';

-- ── school_analysis_runs ──────────────────────────────────────────────────────
-- Per-school per-domain analysis run results. 7 schools × 5 domains = 35 rows per full run.
CREATE TABLE IF NOT EXISTS school_analysis_runs (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_date       DATE NOT NULL DEFAULT CURRENT_DATE,
  chart_id       TEXT NOT NULL,
  school         TEXT NOT NULL CHECK (
    school IN ('parashari','jaimini','tajika','kp','nadi','bnn','yogini')
  ),
  chart_type     TEXT NOT NULL DEFAULT 'natal'
    CHECK (chart_type IN ('natal','varsha_kundali')),
  varsha_year    INTEGER,
  domain         TEXT NOT NULL CHECK (
    domain IN ('CAREER','HEALTH','RELATIONSHIP','SPIRITUAL','PSYCHOLOGICAL')
  ),
  domain_score   NUMERIC(5,3),
  direction      TEXT CHECK (direction IN ('positive','negative','neutral')),
  top_signals    JSONB,
  school_verdict TEXT,
  pending_flags  TEXT[],
  weighted_domain_score NUMERIC(5,3),
  domain_authority_weight NUMERIC(4,3),
  created_at     TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (chart_id, run_date, school, domain)
);

CREATE INDEX IF NOT EXISTS sar_chart_id_idx       ON school_analysis_runs(chart_id);
CREATE INDEX IF NOT EXISTS sar_school_domain_idx  ON school_analysis_runs(school, domain);
CREATE INDEX IF NOT EXISTS sar_run_date_idx       ON school_analysis_runs(run_date);
CREATE INDEX IF NOT EXISTS sar_chart_domain_idx   ON school_analysis_runs(chart_id, domain);

COMMENT ON TABLE school_analysis_runs IS
  'Per-school per-domain analysis results for U4 school consensus. '
  '35 rows per full run (7 schools × 5 domains). '
  'weighted_domain_score = domain_score × domain_authority_weight (per §2.5 E2 weighting).';

-- ── convergence_scores ────────────────────────────────────────────────────────
-- Per-domain inter-school convergence metrics. 5 rows per compute run (one per domain).
CREATE TABLE IF NOT EXISTS convergence_scores (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chart_id              TEXT NOT NULL,
  computed_at           TIMESTAMPTZ DEFAULT NOW(),
  domain                TEXT NOT NULL CHECK (
    domain IN ('CAREER','HEALTH','RELATIONSHIP','SPIRITUAL','PSYCHOLOGICAL')
  ),
  schools_agreeing      INTEGER NOT NULL,
  schools_total         INTEGER NOT NULL DEFAULT 7,
  convergence_level     TEXT GENERATED ALWAYS AS (
    CASE
      WHEN schools_agreeing >= 5 THEN 'HIGH'
      WHEN schools_agreeing >= 4 THEN 'MEDIUM'
      ELSE 'LOW'
    END
  ) STORED,
  mean_domain_score     NUMERIC(5,3),
  std_domain_score      NUMERIC(5,3),
  weighted_mean_score   NUMERIC(5,3),
  direction             TEXT CHECK (direction IN ('positive','negative','neutral','mixed')),
  per_school_scores     JSONB,
  per_school_weighted   JSONB,
  convergence_narrative TEXT,
  UNIQUE (chart_id, domain)
);

CREATE INDEX IF NOT EXISTS cs_chart_id_idx        ON convergence_scores(chart_id);
CREATE INDEX IF NOT EXISTS cs_domain_idx          ON convergence_scores(domain);
CREATE INDEX IF NOT EXISTS cs_convergence_level_idx ON convergence_scores(convergence_level);
CREATE INDEX IF NOT EXISTS cs_chart_domain_idx    ON convergence_scores(chart_id, domain);

COMMENT ON TABLE convergence_scores IS
  'Inter-school convergence metrics for U4. 5 domain rows per chart. '
  'convergence_level GENERATED: HIGH(>=5), MEDIUM(4), LOW(<4). '
  'per_school_weighted carries E2 authority-weighted scores.';

-- ── school_disagreements ──────────────────────────────────────────────────────
-- Classified inter-school disagreements (≥10 rows required for seal acceptance).
CREATE TABLE IF NOT EXISTS school_disagreements (
  id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chart_id                  TEXT NOT NULL,
  disagreement_id           TEXT NOT NULL,
  domain                    TEXT NOT NULL CHECK (
    domain IN ('CAREER','HEALTH','RELATIONSHIP','SPIRITUAL','PSYCHOLOGICAL')
  ),
  signal_id                 TEXT,
  schools_affirming         TEXT[] NOT NULL,
  schools_denying           TEXT[] NOT NULL,
  schools_silent            TEXT[],
  disagreement_class        TEXT NOT NULL CHECK (
    disagreement_class IN (
      'method_divergence',
      'signal_gap',
      'tradition_specificity',
      'temporal_scope'
    )
  ),
  resolution                TEXT,
  resolution_verdict        TEXT CHECK (
    resolution_verdict IN (
      'affirming_majority',
      'denying_majority',
      'context_dependent',
      'unresolved'
    )
  ),
  -- temporal_scope: schools agree on WHAT but not WHEN
  -- ph_nimitta treats this as timing-refinement (NOT low confidence)
  is_timing_refinement_signal BOOLEAN GENERATED ALWAYS AS (
    disagreement_class = 'temporal_scope'
  ) STORED,
  worked_example_narrative  TEXT,
  created_at                TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (chart_id, disagreement_id)
);

CREATE INDEX IF NOT EXISTS sd_chart_id_idx            ON school_disagreements(chart_id);
CREATE INDEX IF NOT EXISTS sd_domain_idx              ON school_disagreements(domain);
CREATE INDEX IF NOT EXISTS sd_disagreement_class_idx  ON school_disagreements(disagreement_class);
CREATE INDEX IF NOT EXISTS sd_resolution_verdict_idx  ON school_disagreements(resolution_verdict);
CREATE INDEX IF NOT EXISTS sd_timing_refinement_idx   ON school_disagreements(is_timing_refinement_signal);

COMMENT ON TABLE school_disagreements IS
  'Inter-school disagreement register for U4. '
  'disagreement_class: method_divergence|signal_gap|tradition_specificity|temporal_scope. '
  'is_timing_refinement_signal=true when temporal_scope — ph_nimitta reads this as timing '
  'uncertainty (outcome agreed, window wider), NOT low confidence.';
