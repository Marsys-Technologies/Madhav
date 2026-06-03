-- brahma_bodha_bo24.sql
-- BRAHMA Layer 2 — BO-2-4: bodha.resonance table
--
-- Asset contract: owns bodha.resonance (RM resonance elements).
-- Source data: 025_HOLISTIC_SYNTHESIS/RM_v2_0.md (canonical_id: RM, v2.2).
-- Writer: platform/python-sidecar/brahmagyan/bodha/bo24.py
-- Tool:   rm_walk (platform-mcp/src/tools/bodha_bo24.ts)
--
-- Keyed by (chart_id, ayanamsha_id, element_id) — supports multi-ayanamsha
-- deterministic builds per the Multi-Ayanamsha Deterministic Build architecture
-- (MULTI_AYANAMSHA_BUILD_CLOSE_v1_0.md).
--
-- Acceptance gate:
--   - Table exists with all required columns
--   - source_citation NOT NULL constraint enforced
--   - ≥30 rows present per (chart_id, ayanamsha_id) after build
--   - rm_walk tool returns provenance (source_citation, constituents non-null)
--
-- ROLLBACK: see end of file.

BEGIN;

CREATE TABLE IF NOT EXISTS bodha_resonance (
    -- Primary key: chart + ayanamsha + resonance element ID
    chart_id        UUID        NOT NULL REFERENCES charts(chart_id) ON DELETE CASCADE,
    ayanamsha_id    TEXT        NOT NULL DEFAULT 'jh_true_chitra',
    element_id      TEXT        NOT NULL,   -- e.g. 'RM.01', 'RM.21A', 'RM.35'

    -- Element classification
    -- Gate-1 contract enum: yoga | stellium | mutual_aspect | exchange | parivartana
    -- (RM resonance elements describe yoga/stellium/aspect/exchange/parivartana patterns,
    --  not raw planetary categories; 'other' kept as safe fallback for future types)
    element_type    TEXT        NOT NULL
                    CHECK (element_type IN (
                        'yoga',           -- yoga stacks (RM.28 Saraswati-Lakshmi-Raja, RM.29, …)
                        'stellium',       -- multi-planet conjunctions in one house/sign
                        'mutual_aspect',  -- reciprocal drishti between two planets
                        'exchange',       -- nakshatra/house exchange (parivartana variant)
                        'parivartana',    -- sign-lord exchange (rashi parivartana yoga)
                        'other'           -- fallback for unclassified resonance types
                    )),

    -- Resonance metrics
    -- strength: 0.0–1.0 float derived from net_resonance or explicit field.
    -- 0.90 = STRONGLY AMPLIFIED, 0.75 = TENSION-BEARING,
    -- 0.60 = MIXED/COMPENSATED, 0.50 = default.
    strength        DOUBLE PRECISION NOT NULL DEFAULT 0.50
                    CHECK (strength >= 0.0 AND strength <= 1.0),

    -- Signal/anchor provenance (JSON array of MSR/CDLM anchor IDs)
    -- e.g. ["MSR.413", "MSR.190", "D8.D8=0.95"]
    constituents    JSONB       NOT NULL DEFAULT '[]'::jsonb,

    -- Primary Jyotish domains (JSON array of domain strings)
    -- e.g. ["D1", "D2", "D3"] or ["career", "wealth", "mind"]
    domains_primary JSONB       NOT NULL DEFAULT '[]'::jsonb,

    -- Human-readable net resonance summary (from the RM YAML 'net_resonance' field)
    net_resonance   TEXT,

    -- Provenance: non-null, identifies exact element in the canonical RM artifact
    -- Format: "025_HOLISTIC_SYNTHESIS/RM_v2_0.md#RM.NN"
    source_citation TEXT        NOT NULL,

    -- Full raw YAML block for forensic provenance (the exact text from RM_v2_0.md)
    raw_yaml        TEXT,

    -- Audit timestamps
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Compound primary key
    PRIMARY KEY (chart_id, ayanamsha_id, element_id)
);

COMMENT ON TABLE bodha_resonance IS
    'BRAHMA L2 BO-2-4 — bodha.resonance: one row per RM element per (chart, ayanamsha). '
    'Populated by brahmagyan/bodha/bo24.py from 025_HOLISTIC_SYNTHESIS/RM_v2_0.md. '
    'source_citation is always non-null (acceptance gate). '
    'Queried by rm_walk MCP tool (platform-mcp/src/tools/bodha_bo24.ts).';

COMMENT ON COLUMN bodha_resonance.element_id IS
    'Canonical RM element identifier, e.g. RM.01, RM.21A, RM.35. '
    'Matches the ### RM.NN heading in RM_v2_0.md.';

COMMENT ON COLUMN bodha_resonance.strength IS
    '0.0–1.0 resonance strength: 0.90=STRONGLY AMPLIFIED, 0.75=TENSION-BEARING, '
    '0.60=MIXED/COMPENSATED, 0.50=default. Explicit override from YAML ''strength'' field '
    'where present (RM.31–RM.35).';

COMMENT ON COLUMN bodha_resonance.source_citation IS
    'Non-null provenance pointer. Format: 025_HOLISTIC_SYNTHESIS/RM_v2_0.md#RM.NN. '
    'Acceptance gate: every row must carry a non-null, non-empty source_citation.';

COMMENT ON COLUMN bodha_resonance.constituents IS
    'JSON array of MSR/CDLM anchor IDs referenced in the element block. '
    'e.g. ["MSR.413", "MSR.190", "D8.D8=0.95 self-amp"]. Provenance for B.3 compliance.';

-- ── Indexes ───────────────────────────────────────────────────────────────────

-- Primary lookup: chart + ayanamsha → all elements (rm_walk without element filter)
CREATE INDEX IF NOT EXISTS idx_bodha_resonance_chart_ayan
    ON bodha_resonance (chart_id, ayanamsha_id);

-- Element type filter (e.g. 'planet', 'dasha')
CREATE INDEX IF NOT EXISTS idx_bodha_resonance_element_type
    ON bodha_resonance (chart_id, ayanamsha_id, element_type);

-- Strength-ranked queries (e.g. top-N strongest resonances)
CREATE INDEX IF NOT EXISTS idx_bodha_resonance_strength
    ON bodha_resonance (chart_id, ayanamsha_id, strength DESC);

-- GIN index for JSONB constituent lookups (e.g. "which elements reference MSR.413?")
CREATE INDEX IF NOT EXISTS idx_bodha_resonance_constituents_gin
    ON bodha_resonance USING GIN (constituents);

-- GIN index for domain filtering
CREATE INDEX IF NOT EXISTS idx_bodha_resonance_domains_gin
    ON bodha_resonance USING GIN (domains_primary);

-- ── Data source floor (acceptance gate row) ───────────────────────────────────
-- Register the minimum row count expectation in data_source_expected (if present).

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_name = 'data_source_expected'
    ) THEN
        INSERT INTO data_source_expected (category, min_row_count, notes)
        VALUES (
            'bodha_resonance',
            30,
            'BRAHMA BO-2-4: ≥30 RM resonance elements per (chart_id, ayanamsha_id). '
            'RM_v2_0.md has 37 elements (v2.2). '
            'Writer: brahmagyan/bodha/bo24.py. Tool: rm_walk.'
        )
        ON CONFLICT (category) DO NOTHING;
    ELSE
        RAISE NOTICE 'data_source_expected table absent — skipping floor seed.';
    END IF;
END $$;

COMMIT;

-- ── ROLLBACK ──────────────────────────────────────────────────────────────────
-- To undo this migration:
--
-- BEGIN;
-- DROP TABLE IF EXISTS bodha_resonance;
-- DELETE FROM data_source_expected WHERE category = 'bodha_resonance';
-- COMMIT;
