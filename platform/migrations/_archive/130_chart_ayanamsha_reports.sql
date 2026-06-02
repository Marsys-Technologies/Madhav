-- Migration 130: chart_ayanamsha_reports — cross-ayanamsha divergence scoring
-- MARSYS-JIS Multi-Ayanamsha Build Orchestrator [BUILD-ORCH-B-07]

CREATE TABLE IF NOT EXISTS chart_ayanamsha_reports (
    report_id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    chart_id            UUID        NOT NULL,
    build_id            UUID        NOT NULL REFERENCES builds(build_id) ON DELETE CASCADE,
    ayanamsha_id_1      TEXT        NOT NULL,
    ayanamsha_id_2      TEXT        NOT NULL,
    divergence_score    FLOAT,
    max_position_delta_deg FLOAT,
    convergent_facts    INT         DEFAULT 0,
    divergent_facts     INT         DEFAULT 0,
    report_json         JSONB       NOT NULL DEFAULT '{}',
    generated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT car_different_ayanamshas CHECK (ayanamsha_id_1 != ayanamsha_id_2),
    CONSTRAINT car_unique_pair UNIQUE (chart_id, build_id, ayanamsha_id_1, ayanamsha_id_2)
);

CREATE INDEX IF NOT EXISTS car_chart_build_idx
    ON chart_ayanamsha_reports(chart_id, build_id);
CREATE INDEX IF NOT EXISTS car_divergence_idx
    ON chart_ayanamsha_reports(chart_id, divergence_score DESC)
    WHERE divergence_score IS NOT NULL;
CREATE INDEX IF NOT EXISTS car_report_json_gin
    ON chart_ayanamsha_reports USING gin(report_json);

-- View: latest cross-ayanamsha report per chart
CREATE OR REPLACE VIEW v_chart_latest_ayanamsha_reports AS
SELECT DISTINCT ON (car.chart_id, car.ayanamsha_id_1, car.ayanamsha_id_2)
    car.*
FROM chart_ayanamsha_reports car
JOIN builds b ON b.build_id = car.build_id
WHERE b.status = 'complete'
ORDER BY car.chart_id, car.ayanamsha_id_1, car.ayanamsha_id_2, car.generated_at DESC;

COMMENT ON TABLE chart_ayanamsha_reports IS 'Pairwise cross-ayanamsha divergence reports. Used by cross_ayanamsha_consensus retrieval tool to flag high-divergence chart regions.';
