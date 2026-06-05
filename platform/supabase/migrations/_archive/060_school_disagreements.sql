-- Migration 060 — school_disagreements
-- M9-A-S1 (2026-05-14): Records classified inter-school disagreements with worked examples
-- Built by build_disagreement_register.py in M9-E-S1; ≥10 rows required

CREATE TABLE school_disagreements (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  disagreement_id TEXT NOT NULL UNIQUE,     -- e.g. 'DIS.SCH.001'
  domain TEXT NOT NULL CHECK (
    domain IN ('CAREER','HEALTH','RELATIONSHIP','SPIRITUAL','PSYCHOLOGICAL')
  ),
  signal_id TEXT,
  schools_affirming TEXT[] NOT NULL,
  schools_denying TEXT[] NOT NULL,
  schools_silent TEXT[],
  disagreement_class TEXT NOT NULL CHECK (
    disagreement_class IN (
      'method_divergence',      -- schools use different methods to assess same domain
      'signal_gap',             -- some schools have no signal for this domain
      'tradition_specificity',  -- signal only exists in one tradition's framework
      'temporal_scope'          -- schools differ on WHEN, not WHETHER, an outcome manifests
    )
  ),
  resolution TEXT,
  resolution_verdict TEXT CHECK (
    resolution_verdict IN (
      'affirming_majority',     -- majority affirms; minority noted
      'denying_majority',       -- majority denies; minority noted
      'context_dependent',      -- both valid in different chart contexts
      'unresolved'              -- no resolution possible without more data
    )
  ),
  worked_example_narrative TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX sd_domain_idx ON school_disagreements(domain);
CREATE INDEX sd_disagreement_class_idx ON school_disagreements(disagreement_class);
CREATE INDEX sd_resolution_verdict_idx ON school_disagreements(resolution_verdict);

COMMENT ON TABLE school_disagreements IS 'Inter-school disagreement register for M9. ≥10 worked examples required for M9-E AC.M9E.1. Classified by method_divergence|signal_gap|tradition_specificity|temporal_scope. Resolution by Gemini Pro judge.';
