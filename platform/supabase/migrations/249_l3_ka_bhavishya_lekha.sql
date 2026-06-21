-- Migration 249 — L3 ka_bhavishya_lekha: forward projection / probabilistic forecast

CREATE TABLE IF NOT EXISTS kala_bhavishya (
    id BIGSERIAL PRIMARY KEY,
    chart_id UUID NOT NULL REFERENCES charts(chart_id) ON DELETE CASCADE,

    -- Projection ranking within this build (1 = highest priority)
    projection_rank SMALLINT NOT NULL,

    -- Probability tier (calibrated, discrete)
    probability_tier TEXT NOT NULL CHECK (probability_tier IN (
        'tier_1_high',       -- convergence >= 0.70, no severe obstruction
        'tier_2_moderate',   -- convergence >= 0.45
        'tier_3_speculative' -- convergence < 0.45 or obstructed
    )),

    -- Domain of manifestation
    domain TEXT NOT NULL CHECK (domain IN (
        'career', 'health', 'relationship', 'finance', 'spiritual', 'education', 'general'
    )),

    -- Peak window
    peak_date DATE,
    window_start DATE,
    window_end DATE,

    -- Source convergence window
    convergence_id BIGINT REFERENCES kala_convergence(convergence_id) ON DELETE SET NULL,
    signal_id UUID REFERENCES bodha_msr_signals(signal_id) ON DELETE SET NULL,

    -- Effective score (from kala_darshana or kala_convergence)
    effective_score DOUBLE PRECISION CHECK (effective_score >= 0 AND effective_score <= 1),

    -- Falsifiability hook: what observable outcome would confirm/deny this projection
    -- {confirm_observable: str, deny_observable: str, evaluation_date: str}
    falsifiability JSONB NOT NULL DEFAULT '{}',

    -- Source chain: which convergence/darshana IDs drove this
    source_chain JSONB NOT NULL DEFAULT '[]',

    -- Narrative
    -- {headline: str, probability_statement: str, domain_context: str, caveat: str}
    narrative JSONB NOT NULL DEFAULT '{}',

    -- Calibration record (for future outcome comparison)
    outcome_recorded BOOLEAN NOT NULL DEFAULT FALSE,
    outcome_notes TEXT,

    source_citation TEXT NOT NULL DEFAULT 'ka_bhavishya_lekha:v1.0',
    computed_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_kala_bhavishya_chart
    ON kala_bhavishya (chart_id);
CREATE INDEX IF NOT EXISTS idx_kala_bhavishya_rank
    ON kala_bhavishya (chart_id, projection_rank);
CREATE INDEX IF NOT EXISTS idx_kala_bhavishya_peak
    ON kala_bhavishya (chart_id, peak_date)
    WHERE peak_date IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_kala_bhavishya_tier
    ON kala_bhavishya (chart_id, probability_tier);
CREATE INDEX IF NOT EXISTS idx_kala_bhavishya_domain
    ON kala_bhavishya (chart_id, domain);
CREATE INDEX IF NOT EXISTS idx_kala_bhavishya_unverified
    ON kala_bhavishya (chart_id) WHERE outcome_recorded = FALSE;
