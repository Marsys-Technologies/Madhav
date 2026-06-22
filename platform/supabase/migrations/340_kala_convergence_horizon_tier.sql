-- Migration 338: U2 — add horizon_tier column to kala_convergence
ALTER TABLE kala_convergence ADD COLUMN IF NOT EXISTS horizon_tier text NOT NULL DEFAULT 'near'
    CHECK (horizon_tier IN ('near', 'lifetime'));
CREATE INDEX IF NOT EXISTS idx_kala_convergence_horizon_tier ON kala_convergence(chart_id, horizon_tier);
