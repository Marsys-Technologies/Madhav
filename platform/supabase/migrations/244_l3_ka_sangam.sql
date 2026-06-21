-- Migration 244 — L3 ka_sangam: extend kala_convergence with rigor stratum columns

ALTER TABLE kala_convergence ADD COLUMN IF NOT EXISTS signal_id UUID REFERENCES bodha_msr_signals(signal_id) ON DELETE SET NULL;
ALTER TABLE kala_convergence ADD COLUMN IF NOT EXISTS mode TEXT CHECK (mode IN ('A', 'B'));
ALTER TABLE kala_convergence ADD COLUMN IF NOT EXISTS peak_date DATE;
ALTER TABLE kala_convergence ADD COLUMN IF NOT EXISTS orb_strength DOUBLE PRECISION CHECK (orb_strength >= 0 AND orb_strength <= 1);
ALTER TABLE kala_convergence ADD COLUMN IF NOT EXISTS rarity_years DOUBLE PRECISION;
ALTER TABLE kala_convergence ADD COLUMN IF NOT EXISTS confidence_score DOUBLE PRECISION CHECK (confidence_score >= 0 AND confidence_score <= 1);
ALTER TABLE kala_convergence ADD COLUMN IF NOT EXISTS confidence_label TEXT CHECK (confidence_label IN ('high', 'moderate', 'speculative'));
ALTER TABLE kala_convergence ADD COLUMN IF NOT EXISTS independent_current_count SMALLINT;
ALTER TABLE kala_convergence ADD COLUMN IF NOT EXISTS is_off_dasha_discovery BOOLEAN DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS idx_kala_convergence_signal ON kala_convergence (signal_id) WHERE signal_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_kala_convergence_mode ON kala_convergence (chart_id, mode);
CREATE INDEX IF NOT EXISTS idx_kala_convergence_discovery ON kala_convergence (chart_id, is_off_dasha_discovery) WHERE is_off_dasha_discovery = TRUE;
