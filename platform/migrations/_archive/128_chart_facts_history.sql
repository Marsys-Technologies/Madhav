-- Migration 128: chart_facts_history — audit trail for chart_facts mutations
-- MARSYS-JIS Multi-Ayanamsha Build Orchestrator [BUILD-ORCH-B-05]

CREATE TABLE IF NOT EXISTS chart_facts_history (
    history_id     UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    fact_id        TEXT        NOT NULL,
    chart_id       UUID,
    ayanamsha_id   TEXT,
    change_type    TEXT        NOT NULL CHECK (change_type IN ('insert','update','delete')),
    changed_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    old_value      JSONB,
    new_value      JSONB,
    build_id       TEXT,
    engine_version TEXT
);

CREATE INDEX IF NOT EXISTS chart_facts_hist_fact_idx
    ON chart_facts_history(fact_id, changed_at DESC);
CREATE INDEX IF NOT EXISTS chart_facts_hist_chart_ayan_idx
    ON chart_facts_history(chart_id, ayanamsha_id, changed_at DESC)
    WHERE chart_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS chart_facts_hist_change_type_idx
    ON chart_facts_history(change_type, changed_at DESC);

-- Audit trigger function
CREATE OR REPLACE FUNCTION fn_chart_facts_audit()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO chart_facts_history (
            fact_id, chart_id, ayanamsha_id, change_type, new_value, build_id, engine_version
        ) VALUES (
            NEW.fact_id, NEW.chart_id, NEW.ayanamsha_id, 'insert',
            row_to_json(NEW)::jsonb, NEW.build_id::text, NEW.engine_version
        );
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO chart_facts_history (
            fact_id, chart_id, ayanamsha_id, change_type, old_value, new_value, build_id, engine_version
        ) VALUES (
            NEW.fact_id, NEW.chart_id, NEW.ayanamsha_id, 'update',
            row_to_json(OLD)::jsonb, row_to_json(NEW)::jsonb, NEW.build_id::text, NEW.engine_version
        );
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO chart_facts_history (
            fact_id, chart_id, ayanamsha_id, change_type, old_value, build_id
        ) VALUES (
            OLD.fact_id, OLD.chart_id, OLD.ayanamsha_id, 'delete',
            row_to_json(OLD)::jsonb, OLD.build_id::text
        );
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS trg_chart_facts_audit ON chart_facts;
CREATE TRIGGER trg_chart_facts_audit
    AFTER INSERT OR UPDATE OR DELETE ON chart_facts
    FOR EACH ROW EXECUTE FUNCTION fn_chart_facts_audit();

COMMENT ON TABLE chart_facts_history IS 'Immutable audit log of all chart_facts mutations. Populated by trg_chart_facts_audit.';
