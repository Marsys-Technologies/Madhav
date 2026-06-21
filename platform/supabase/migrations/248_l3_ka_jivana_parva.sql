-- Migration 248 — L3 ka_jivana_parva: life-arc biographical chapter artifact

CREATE TABLE IF NOT EXISTS kala_jivana_parva (
    id BIGSERIAL PRIMARY KEY,
    chart_id UUID NOT NULL REFERENCES charts(chart_id) ON DELETE CASCADE,

    -- Chapter ordering and span
    parva_index SMALLINT NOT NULL,
    start_year SMALLINT NOT NULL,
    end_year SMALLINT,  -- NULL = ongoing

    -- Dominant daśā planet for this span
    dasha_planet TEXT NOT NULL,

    -- Dominant signal class during this span
    dominant_signal_class TEXT CHECK (dominant_signal_class IN (
        'YOGA','DOSHA','DIGNITY','DISPOSITOR_RELATIONAL',
        'SENSITIVE_POINT','CONJUNCTION_ASPECT','SUBSYSTEM','CLASSIFY_RESIDUAL'
    )),

    -- Quality of the parva
    parva_quality TEXT NOT NULL CHECK (parva_quality IN (
        'building',
        'peak',
        'consolidating',
        'receding',
        'transitional'
    )),

    -- Theme keywords (array of 2-4 words)
    theme_keywords TEXT[] NOT NULL DEFAULT '{}',

    -- Narrative summary (1-2 sentence structured description)
    narrative JSONB NOT NULL DEFAULT '{}',

    -- Convergence density: count of high-score (>=0.5) windows in this span
    high_convergence_count SMALLINT NOT NULL DEFAULT 0,

    -- Average effective score across windows in this span
    avg_effective_score DOUBLE PRECISION,

    source_citation TEXT NOT NULL DEFAULT 'ka_jivana_parva:v1.0',
    computed_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_kala_jivana_parva_chart_index
    ON kala_jivana_parva (chart_id, parva_index);
CREATE INDEX IF NOT EXISTS idx_kala_jivana_parva_chart
    ON kala_jivana_parva (chart_id);
CREATE INDEX IF NOT EXISTS idx_kala_jivana_parva_quality
    ON kala_jivana_parva (chart_id, parva_quality);
