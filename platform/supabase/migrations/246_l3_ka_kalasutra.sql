-- Migration 246 — L3 ka_kalasutra: bounded activation artifact (replaces row-per-day kala_timeline)

CREATE TABLE IF NOT EXISTS kala_activation (
    id BIGSERIAL PRIMARY KEY,
    chart_id UUID NOT NULL REFERENCES charts(chart_id) ON DELETE CASCADE,
    signal_id UUID NOT NULL REFERENCES bodha_msr_signals(signal_id) ON DELETE CASCADE,
    ayanamsha_id TEXT NOT NULL DEFAULT 'true_chitra',
    
    -- Signature classification (mirrors ka_yojaka's kala_activation_predicates)
    signature_class TEXT NOT NULL CHECK (signature_class IN (
        'YOGA','DOSHA','DIGNITY','DISPOSITOR_RELATIONAL',
        'SENSITIVE_POINT','CONJUNCTION_ASPECT','SUBSYSTEM','CLASSIFY_RESIDUAL'
    )),
    
    -- L2 NULL hooks: filled HERE at L3 (never by writing bodha_msr_signals)
    -- These correspond to columns that L2 left null for L3 to populate
    active_dasha_periods_jsonb JSONB NOT NULL DEFAULT '[]',
    activation_predicted_dates_jsonb JSONB NOT NULL DEFAULT '[]',
    dasha_activation_proximity_score DOUBLE PRECISION CHECK (dasha_activation_proximity_score >= 0 AND dasha_activation_proximity_score <= 1),
    
    -- Bounded activation window
    activation_start DATE,
    activation_end DATE,
    activation_peak_date DATE,
    
    -- Rigor fields (computed, not copied from L2)
    orb_strength DOUBLE PRECISION CHECK (orb_strength >= 0 AND orb_strength <= 1),
    convergence_score DOUBLE PRECISION CHECK (convergence_score >= 0 AND convergence_score <= 1),
    
    -- Source/audit
    source_citation TEXT NOT NULL DEFAULT 'ka_kalasutra:v1.0',
    computed_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_kala_activation_chart_signal_ayan 
    ON kala_activation (chart_id, signal_id, ayanamsha_id);
CREATE INDEX IF NOT EXISTS idx_kala_activation_chart 
    ON kala_activation (chart_id);
CREATE INDEX IF NOT EXISTS idx_kala_activation_class 
    ON kala_activation (chart_id, signature_class);
CREATE INDEX IF NOT EXISTS idx_kala_activation_window 
    ON kala_activation (chart_id, activation_start, activation_end) 
    WHERE activation_start IS NOT NULL;

-- Mark kala_timeline deprecated (do not drop — downstream K5/K6 still read it)
COMMENT ON TABLE kala_timeline IS 'DEPRECATED by migration 246 (L3 ka_kalasutra). Use kala_activation instead. This table will be dropped in L4 migration.';
