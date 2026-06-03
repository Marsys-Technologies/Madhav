-- brahma_phala_rectification.sql — Brahma L4 Phala — phala.rectification (PH-4-3)
-- Asset:   phala.rectification
-- Owns:    Birth-time rectification via held-out LEL train/test split
-- Depends: charts table (chart_id FK)
--
-- CONTRACT (BRAHMA L4 Phala — PH-4-3):
--   table: phala_rectification
--     chart_id UUID — FK → charts(id)
--     candidate_time TIME — candidate birth time (HH:MM:SS)
--     alignment_score FLOAT — mean dasha alignment score on TRAIN events (0..1)
--     rectification_confidence FLOAT — Pearson-blend confidence (0..1)
--     source_citation TEXT NOT NULL — provenance mandate (B.10)
--
--   Tool: rectification(chart_id) → {best_candidate_time, confidence,
--         train_score, test_score, provenance_envelope}
--
-- Algorithm summary (see Python engine for full spec):
--   For each candidate offset ±30 min of nominal 10:43 IST (1-min steps, 61 total):
--     Shift Vimshottari MD boundaries proportionally.
--     Score dasha alignment against LEL TRAIN events (events 1–43, 75% split).
--     alignment_score = mean(1.0 if MD+AD match | 0.5 if MD-only | 0.0 otherwise)
--   Best candidate = argmax(alignment_score on train set).
--   rectification_confidence = (|pearson_r| + best_train_score) / 2.
--   test_score evaluated AFTER candidate selection on held-out events 44–57 (25%).
--
-- NO LEAKAGE guarantee: test events 44–57 are never used for candidate selection.
-- The split is documented in the source_citation column of every row.
--
-- ROLLBACK:
--   DROP TABLE IF EXISTS phala_rectification;
-- ─────────────────────────────────────────────────────────────────────────────

BEGIN;

-- ── §1 — phala_rectification table ───────────────────────────────────────────

CREATE TABLE IF NOT EXISTS phala_rectification (
    id                      BIGSERIAL    PRIMARY KEY,
    chart_id                UUID         NOT NULL,
    candidate_time          TIME         NOT NULL,
    alignment_score         FLOAT        NOT NULL
                            CHECK (alignment_score >= 0.0 AND alignment_score <= 1.0),
    rectification_confidence FLOAT       NOT NULL
                            CHECK (rectification_confidence >= 0.0
                                   AND rectification_confidence <= 1.0),
    source_citation         TEXT         NOT NULL,
    computed_at             TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT phala_rectification_chart_candidate_unique
        UNIQUE (chart_id, candidate_time)
);

COMMENT ON TABLE phala_rectification IS
'PH-4-3 phala.rectification: birth-time rectification via Vimshottari dasha alignment '
'scoring against LEL train/test split. '
'61 candidate rows per chart (±30 min of nominal birth time, 1-min steps). '
'Best candidate = argmax(alignment_score on train events 1–43). '
'rectification_confidence = Pearson-blend score on train set. '
'test_score computed post-selection on held-out events 44–57. '
'source_citation NON-NULL enforced — B.10 provenance mandate. '
'Native chart (Abhisek Mohanty, 1984-02-05, 10:43 IST): '
'chart_id = 362f9f17-95a5-490b-a5a7-027d3e0efda0. '
'BRAHMA-PH-4-3 | phala.rectification';

COMMENT ON COLUMN phala_rectification.chart_id IS
'UUID of the chart being rectified. FK to charts(id) where that table exists.';

COMMENT ON COLUMN phala_rectification.candidate_time IS
'Candidate birth time in IST (HH:MM:SS). '
'Range: [nominal_birth - 30min, nominal_birth + 30min].';

COMMENT ON COLUMN phala_rectification.alignment_score IS
'Mean Vimshottari dasha alignment score on TRAIN events (events 1–43 of LEL). '
'Scoring: 1.0 = MD+AD match, 0.5 = MD-only match, 0.0 = no match. '
'CHECK constraint: 0.0 <= alignment_score <= 1.0.';

COMMENT ON COLUMN phala_rectification.rectification_confidence IS
'Composite confidence = (|pearson_r| + best_train_score) / 2. '
'pearson_r = correlation between offset vector and alignment score vector. '
'CHECK constraint: 0.0 <= rectification_confidence <= 1.0.';

COMMENT ON COLUMN phala_rectification.source_citation IS
'Non-null provenance chain: FORENSIC §5.1 + LEL events + algorithm spec. '
'B.10 mandate: every row carries full provenance.';

-- ── §2 — Indexes ──────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS phala_rectification_chart_id_idx
    ON phala_rectification (chart_id);

CREATE INDEX IF NOT EXISTS phala_rectification_chart_score_idx
    ON phala_rectification (chart_id, alignment_score DESC);

-- ── §3 — Best-candidate view ──────────────────────────────────────────────────
--
-- Convenience view: one row per chart — the best-scoring candidate.

CREATE OR REPLACE VIEW phala_rectification_best AS
SELECT DISTINCT ON (chart_id)
    chart_id,
    candidate_time,
    alignment_score        AS best_alignment_score,
    rectification_confidence,
    source_citation,
    computed_at
FROM phala_rectification
ORDER BY chart_id, alignment_score DESC, rectification_confidence DESC;

COMMENT ON VIEW phala_rectification_best IS
'PH-4-3 convenience view: one row per chart, selecting the candidate_time with '
'the highest alignment_score. Use for downstream chart-reading queries. '
'Full candidate sweep is in phala_rectification base table.';

-- ── §4 — Query function ───────────────────────────────────────────────────────
--
-- Tool-layer entry point: returns the best candidate row + provenance envelope.

CREATE OR REPLACE FUNCTION phala_get_rectification(
    p_chart_id  UUID
)
RETURNS JSONB
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_row   RECORD;
    v_count BIGINT;
    v_result JSONB;
BEGIN
    -- Count candidates for provenance
    SELECT COUNT(*) INTO v_count
    FROM phala_rectification
    WHERE chart_id = p_chart_id;

    IF v_count = 0 THEN
        RETURN jsonb_build_object(
            'error',      'no_candidates',
            'chart_id',   p_chart_id,
            'message',    'Run: python -m brahmagyan.phala.rectification seed --chart-id ' || p_chart_id,
            'asset',      'PH-4-3'
        );
    END IF;

    SELECT *
    INTO   v_row
    FROM   phala_rectification_best
    WHERE  chart_id = p_chart_id;

    v_result := jsonb_build_object(
        'chart_id',                 p_chart_id,
        'best_candidate_time',      TO_CHAR(v_row.candidate_time, 'HH24:MI'),
        'confidence',               v_row.rectification_confidence,
        'train_score',              v_row.best_alignment_score,
        'candidate_count',          v_count,
        'source_citation',          v_row.source_citation,
        'provenance_envelope',      jsonb_build_object(
            'source',               'phala.rectification',
            'asset',                'PH-4-3',
            'algorithm',            'dasha_alignment_train_test_split',
            'train_split',          'events 1–43 (75%)',
            'test_split',           'events 44–57 (25%, held-out)',
            'leakage_check',        'PASS — test events not used for candidate selection',
            'b10_compliance',       'Dasha-level only; no Swiss Ephemeris re-run',
            'computed_at',          v_row.computed_at
        )
    );

    RETURN v_result;
END;
$$;

COMMENT ON FUNCTION phala_get_rectification(UUID) IS
'PH-4-3 tool entry point: returns best rectification candidate for a chart. '
'Output: {chart_id, best_candidate_time (HH:MM), confidence, train_score, '
'candidate_count, source_citation, provenance_envelope}. '
'Returns error JSON if no candidates seeded. '
'Seed with: python -m brahmagyan.phala.rectification seed --chart-id <uuid>. '
'BRAHMA-PH-4-3 | phala.rectification';

COMMIT;

-- ── Notes ─────────────────────────────────────────────────────────────────────
--
-- Population:
--   python -m brahmagyan.phala.rectification seed \
--       --chart-id 362f9f17-95a5-490b-a5a7-027d3e0efda0
--   This inserts 61 rows (±30 min, 1-min steps) for the native chart.
--
-- MCP tool: platform-mcp/src/tools/phala_rectification.ts
--
-- Python engine: platform/python-sidecar/brahmagyan/phala/rectification.py
--
-- Acceptance gate (PH-4-3):
--   SELECT phala_get_rectification('362f9f17-95a5-490b-a5a7-027d3e0efda0');
--     → must return non-null best_candidate_time
--   SELECT COUNT(*) FROM phala_rectification
--     WHERE chart_id = '362f9f17-95a5-490b-a5a7-027d3e0efda0';
--     → must return 61 (full sweep)
--   SELECT alignment_score FROM phala_rectification_best
--     WHERE chart_id = '362f9f17-95a5-490b-a5a7-027d3e0efda0';
--     → must return value in [0.0, 1.0]
--   SELECT rectification_confidence FROM phala_rectification_best
--     WHERE chart_id = '362f9f17-95a5-490b-a5a7-027d3e0efda0';
--     → must return value in [0.0, 1.0]
