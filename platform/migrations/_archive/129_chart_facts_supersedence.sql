-- Migration 129: chart_facts_supersedence — tracks when a new build supersedes an old one
-- MARSYS-JIS Multi-Ayanamsha Build Orchestrator [BUILD-ORCH-B-06]

CREATE TABLE IF NOT EXISTS chart_facts_supersedence (
    supersedence_id   UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    chart_id          UUID        NOT NULL,
    ayanamsha_id      TEXT        NOT NULL,
    superseded_build_id UUID      NOT NULL REFERENCES builds(build_id) ON DELETE CASCADE,
    current_build_id  UUID        NOT NULL REFERENCES builds(build_id) ON DELETE CASCADE,
    superseded_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reason            TEXT        NOT NULL DEFAULT 'new_build',
    fact_count        INT,
    CONSTRAINT cfs_different_builds CHECK (superseded_build_id != current_build_id)
);

CREATE INDEX IF NOT EXISTS cfs_chart_ayan_idx
    ON chart_facts_supersedence(chart_id, ayanamsha_id, superseded_at DESC);
CREATE INDEX IF NOT EXISTS cfs_superseded_build_idx
    ON chart_facts_supersedence(superseded_build_id);
CREATE INDEX IF NOT EXISTS cfs_current_build_idx
    ON chart_facts_supersedence(current_build_id);

-- Function to record supersedence when a new build replaces an old one
CREATE OR REPLACE FUNCTION fn_supersede_build(
    p_chart_id     UUID,
    p_ayanamsha_id TEXT,
    p_old_build_id UUID,
    p_new_build_id UUID,
    p_reason       TEXT DEFAULT 'new_build'
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_fact_count INT;
BEGIN
    -- Count how many facts are being superseded
    SELECT COUNT(*) INTO v_fact_count
    FROM chart_facts
    WHERE chart_id = p_chart_id
      AND ayanamsha_id = p_ayanamsha_id
      AND build_id = p_old_build_id::text;

    -- Record the supersedence event
    INSERT INTO chart_facts_supersedence (
        chart_id, ayanamsha_id, superseded_build_id, current_build_id, reason, fact_count
    ) VALUES (
        p_chart_id, p_ayanamsha_id, p_old_build_id, p_new_build_id, p_reason, v_fact_count
    );

    -- Mark old build's chart_facts as stale
    UPDATE chart_facts
    SET is_stale = true
    WHERE chart_id = p_chart_id
      AND ayanamsha_id = p_ayanamsha_id
      AND build_id = p_old_build_id::text;
END;
$$;

COMMENT ON TABLE chart_facts_supersedence IS 'Tracks when a new build supersedes an older build for a chart+ayanamsha pair. fn_supersede_build() marks old facts stale.';
COMMENT ON FUNCTION fn_supersede_build IS 'Records supersedence event and marks old chart_facts rows as is_stale=true.';
