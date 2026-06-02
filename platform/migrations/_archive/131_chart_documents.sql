-- Migration 131: chart_documents — rendered per-chart artifacts storage
-- MARSYS-JIS Multi-Ayanamsha Build Orchestrator [BUILD-ORCH-B-08]

CREATE TABLE IF NOT EXISTS chart_documents (
    document_id   UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    chart_id      UUID        NOT NULL,
    ayanamsha_id  TEXT        NOT NULL,
    document_type TEXT        NOT NULL CHECK (document_type IN (
        'forensic_render',
        'ucn_digest',
        'msr_export',
        'cdlm_export',
        'cgm_export',
        'rm_export',
        'cross_ayanamsha_report'
    )),
    content_md    TEXT,
    content_json  JSONB,
    build_id      UUID        NOT NULL REFERENCES builds(build_id) ON DELETE CASCADE,
    rendered_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    gcs_uri       TEXT,
    byte_size     INT,
    chunk_count   INT,
    is_embedded   BOOLEAN     NOT NULL DEFAULT false,
    CONSTRAINT chart_docs_unique UNIQUE (chart_id, ayanamsha_id, document_type, build_id)
);

CREATE INDEX IF NOT EXISTS chart_docs_chart_ayan_idx
    ON chart_documents(chart_id, ayanamsha_id, document_type);
CREATE INDEX IF NOT EXISTS chart_docs_build_idx
    ON chart_documents(build_id);
CREATE INDEX IF NOT EXISTS chart_docs_embedding_pending_idx
    ON chart_documents(chart_id, ayanamsha_id)
    WHERE is_embedded = false;
CREATE INDEX IF NOT EXISTS chart_docs_content_json_gin
    ON chart_documents USING gin(content_json)
    WHERE content_json IS NOT NULL;

-- View: latest document per (chart, ayanamsha, type)
CREATE OR REPLACE VIEW v_chart_latest_documents AS
SELECT DISTINCT ON (cd.chart_id, cd.ayanamsha_id, cd.document_type)
    cd.*
FROM chart_documents cd
JOIN builds b ON b.build_id = cd.build_id
WHERE b.status = 'complete'
ORDER BY cd.chart_id, cd.ayanamsha_id, cd.document_type, cd.rendered_at DESC;

COMMENT ON TABLE chart_documents IS 'Rendered per-chart artifacts: FORENSIC.md, UCN digest, MSR/CDLM/CGM/RM exports. One row per (chart, ayanamsha, document_type, build). is_embedded tracks RAG chunking status.';
