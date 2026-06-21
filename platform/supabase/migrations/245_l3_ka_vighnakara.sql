-- Migration 245 — L3 ka_vighnakara: obstruction / counter-indicator table
-- Replaces the legacy BRAHMA-KA-3-3 stub (0 rows, incompatible schema) with
-- the full ka_vighnakara schema: convergence FK, 7 obstruction types,
-- severity_score + override_score columns.

-- Drop legacy stub (0 rows confirmed; no data loss)
DROP TABLE IF EXISTS kala_obstruction CASCADE;

CREATE TABLE kala_obstruction (
    id BIGSERIAL PRIMARY KEY,
    chart_id UUID NOT NULL REFERENCES charts(chart_id) ON DELETE CASCADE,
    convergence_id BIGINT REFERENCES kala_convergence(convergence_id) ON DELETE CASCADE,
    signal_id UUID REFERENCES bodha_msr_signals(signal_id) ON DELETE SET NULL,

    obstruction_type TEXT NOT NULL CHECK (obstruction_type IN (
        'malefic_transit',
        'dasha_lord_afflicted',
        'panchanga_obstruction',
        'rashi_dristi_conflict',
        'combustion',
        'gandanta',
        'papakartari'
    )),

    severity TEXT NOT NULL CHECK (severity IN ('mild', 'moderate', 'severe')),
    severity_score DOUBLE PRECISION NOT NULL CHECK (severity_score >= 0 AND severity_score <= 1),

    -- How much this obstruction reduces the convergence score
    -- convergence_effective = convergence_score * (1 - override_score)
    override_score DOUBLE PRECISION NOT NULL DEFAULT 0.0 CHECK (override_score >= 0 AND override_score <= 1),

    obstruction_detail JSONB NOT NULL DEFAULT '{}',
    source_citation TEXT NOT NULL DEFAULT 'ka_vighnakara:v1.0',
    computed_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_kala_obstruction_chart ON kala_obstruction (chart_id);
CREATE INDEX idx_kala_obstruction_convergence ON kala_obstruction (convergence_id) WHERE convergence_id IS NOT NULL;
CREATE INDEX idx_kala_obstruction_signal ON kala_obstruction (signal_id) WHERE signal_id IS NOT NULL;
CREATE INDEX idx_kala_obstruction_type ON kala_obstruction (chart_id, obstruction_type);
CREATE INDEX idx_kala_obstruction_severe ON kala_obstruction (chart_id, severity) WHERE severity = 'severe';
