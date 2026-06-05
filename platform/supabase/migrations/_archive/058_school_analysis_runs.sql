-- Migration 058 — school_analysis_runs
-- M9-A-S1 (2026-05-14): Records each school engine's analysis per domain
-- 7 schools × 5 domains = 35 rows per analysis run

CREATE TABLE school_analysis_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_date DATE NOT NULL DEFAULT CURRENT_DATE,
  school TEXT NOT NULL CHECK (
    school IN ('parashari','jaimini','tajika','kp','nadi','bnn','yogini')
  ),
  chart_id TEXT NOT NULL DEFAULT 'abhisek_primary',
  chart_type TEXT NOT NULL DEFAULT 'natal'
    CHECK (chart_type IN ('natal','varsha_kundali')),
  varsha_year INTEGER,                 -- NULL for natal; year for Tajika Varsha Kundali
  domain TEXT NOT NULL CHECK (
    domain IN ('CAREER','HEALTH','RELATIONSHIP','SPIRITUAL','PSYCHOLOGICAL')
  ),
  domain_score NUMERIC(5,3),          -- 0.000–5.000 composite
  direction TEXT CHECK (direction IN ('positive','negative','neutral')),
  top_signals JSONB,                   -- [{signal_id, score, weight, attribution_ref}]
  school_verdict TEXT,
  pending_flags TEXT[],                -- e.g. ['VARSHA_KUNDALI_PENDING', 'TRANSIT_DATA_PENDING']
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX sar_school_domain_idx ON school_analysis_runs(school, domain);
CREATE INDEX sar_chart_id_idx ON school_analysis_runs(chart_id);
CREATE INDEX sar_run_date_idx ON school_analysis_runs(run_date);
CREATE INDEX sar_school_idx ON school_analysis_runs(school);

COMMENT ON TABLE school_analysis_runs IS 'Per-school per-domain analysis runs for M9 multi-school triangulation. 35 rows per full run (7 schools × 5 domains). Tajika uses chart_type=varsha_kundali; BNN may carry TRANSIT_DATA_PENDING flag.';
COMMENT ON COLUMN school_analysis_runs.pending_flags IS 'Flags for missing external computation: VARSHA_KUNDALI_PENDING (Tajika), TRANSIT_DATA_PENDING (BNN)';
