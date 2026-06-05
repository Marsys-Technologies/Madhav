-- Migration 059 — convergence_scores
-- M9-A-S1 (2026-05-14): Per-domain inter-school convergence metrics
-- Deterministic computation from school_analysis_runs directions

CREATE TABLE convergence_scores (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  computed_at TIMESTAMPTZ DEFAULT NOW(),
  domain TEXT NOT NULL CHECK (
    domain IN ('CAREER','HEALTH','RELATIONSHIP','SPIRITUAL','PSYCHOLOGICAL')
  ),
  schools_agreeing INTEGER NOT NULL,
  schools_total INTEGER NOT NULL DEFAULT 7,
  convergence_level TEXT GENERATED ALWAYS AS (
    CASE
      WHEN schools_agreeing >= 5 THEN 'HIGH'
      WHEN schools_agreeing >= 4 THEN 'MEDIUM'
      ELSE 'LOW'
    END
  ) STORED,
  mean_domain_score NUMERIC(5,3),
  std_domain_score NUMERIC(5,3),
  direction TEXT CHECK (direction IN ('positive','negative','neutral','mixed')),
  per_school_scores JSONB,             -- {"parashari": 3.2, "jaimini": 2.8, ...}
  convergence_narrative TEXT,
  UNIQUE (computed_at, domain)
);

CREATE INDEX cs_domain_idx ON convergence_scores(domain);
CREATE INDEX cs_convergence_level_idx ON convergence_scores(convergence_level);
CREATE INDEX cs_computed_at_idx ON convergence_scores(computed_at);

COMMENT ON TABLE convergence_scores IS 'Inter-school convergence metrics for M9. 5 domain rows per compute run. convergence_level AUTO-GENERATED: HIGH=5+/7, MEDIUM=4/7, LOW<4/7. schools_total=6 when Tajika excluded (VARSHA_KUNDALI_PENDING).';
COMMENT ON COLUMN convergence_scores.convergence_level IS 'GENERATED ALWAYS AS: HIGH (>=5 schools agree), MEDIUM (4 schools), LOW (<4 schools)';
COMMENT ON COLUMN convergence_scores.per_school_scores IS 'JSONB keyed by school name: {"parashari": 3.2, "jaimini": 2.8, "tajika": 0.0, "kp": 3.5, "nadi": 3.1, "bnn": 2.9, "yogini": 3.3}';
