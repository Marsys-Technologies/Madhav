-- Migration 057 — school_signal_coverage
-- M9-A-S1 (2026-05-14): Multi-school triangulation infrastructure
-- Records which of the 7 Jyotish schools covers each MSR signal

CREATE TABLE school_signal_coverage (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  signal_id TEXT NOT NULL,
  school TEXT NOT NULL CHECK (
    school IN ('parashari','jaimini','tajika','kp','nadi','bnn','yogini')
  ),
  coverage_type TEXT NOT NULL CHECK (
    coverage_type IN ('primary','secondary','silent')
  ),
  -- primary   = signal belongs to this school's tradition
  -- secondary = school has partial/analogous coverage
  -- silent    = school does not address this signal
  confidence NUMERIC(4,3),
  attribution_chunk_id UUID REFERENCES classical_chunks(id),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (signal_id, school)
);

CREATE INDEX ssc_signal_idx ON school_signal_coverage(signal_id);
CREATE INDEX ssc_school_idx ON school_signal_coverage(school);
CREATE INDEX ssc_coverage_type_idx ON school_signal_coverage(coverage_type);
CREATE INDEX ssc_school_coverage_idx ON school_signal_coverage(school, coverage_type);

COMMENT ON TABLE school_signal_coverage IS 'Per-signal per-school coverage classification for M9 multi-school triangulation. 543 signals × 7 schools = 3801 rows at full population.';
COMMENT ON COLUMN school_signal_coverage.coverage_type IS 'primary=school owns this signal type; secondary=partial coverage; silent=no coverage';
