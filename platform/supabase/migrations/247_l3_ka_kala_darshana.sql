-- Migration 247 — L3 ka_kala_darshana: display-ready temporal view

CREATE TABLE IF NOT EXISTS kala_darshana (
    id BIGSERIAL PRIMARY KEY,
    chart_id UUID NOT NULL REFERENCES charts(chart_id) ON DELETE CASCADE,
    convergence_id BIGINT REFERENCES kala_convergence(convergence_id) ON DELETE CASCADE,
    signal_id UUID REFERENCES bodha_msr_signals(signal_id) ON DELETE SET NULL,

    -- Effective score after obstruction discount
    -- effective_score = convergence_score × (1 - max(override_score per convergence))
    effective_score DOUBLE PRECISION NOT NULL CHECK (effective_score >= 0 AND effective_score <= 1),

    -- Net label after obstruction adjustment
    net_label TEXT NOT NULL CHECK (net_label IN (
        'auspicious_strong',
        'auspicious_moderate',
        'auspicious_speculative',
        'obstructed',
        'obstructed_severe',
        'neutral'
    )),

    -- Peak date (copied from kala_convergence for serve-time convenience)
    peak_date DATE,
    window_start DATE,
    window_end DATE,

    -- Obstruction summary (JSON array of {type, severity, override_score})
    obstruction_summary JSONB NOT NULL DEFAULT '[]',

    -- Narrative: a structured description for display
    -- {headline: str, context: str, caution: str | null}
    narrative JSONB NOT NULL DEFAULT '{}',

    source_citation TEXT NOT NULL DEFAULT 'ka_kala_darshana:v1.0',
    computed_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_kala_darshana_convergence
    ON kala_darshana (convergence_id) WHERE convergence_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_kala_darshana_chart
    ON kala_darshana (chart_id);
CREATE INDEX IF NOT EXISTS idx_kala_darshana_effective
    ON kala_darshana (chart_id, effective_score DESC);
CREATE INDEX IF NOT EXISTS idx_kala_darshana_peak
    ON kala_darshana (chart_id, peak_date)
    WHERE peak_date IS NOT NULL;
