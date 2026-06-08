-- brahma_kala_obstruction.sql
-- BRAHMA-KA-3-3: kala.obstruction — obstruction overlaps + period snapshot
--
-- Contract:
--   table: kala_obstruction
--     chart_id         UUID  (FK → charts)
--     date             DATE  (representative date of the obstruction period)
--     obstruction_type TEXT  CHECK IN ('malefic_transit','adverse_dasha','double_affliction')
--     severity         FLOAT [0.0, 1.0]
--     factors          JSONB (indicator breakdown, transit positions, dasha context)
--     source_citation  TEXT  NOT NULL — always "PyJHora/SwissEph DE441 + Brahma-L1"
--
-- Algorithm (Python side, obstruction.py):
--   Scan kala_timeline / Vimshottari schedule for dates where ≥2 adverse
--   indicators coincide:
--     (i)  Sani/Rahu/Ketu transit through dusthana houses (1,4,7,8,12)
--     (ii) MD or AD lord is a natural malefic (Sani, Rahu, Ketu)
--   ≥2 indicators → severity 0.50 ; ≥3 → 0.75 ; ≥4+ → 0.90
--
-- Tool: period_snapshot(chart_id, date) via kala_period_snapshot.ts (MCP)
--
-- FORENSIC source: chart_facts (rendered via forensic_render.ts; FORENSIC v8.0 chart data, §5.1 — md archived at 99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md)
-- Native: Abhisek Mohanty, 1984-02-05, 10:43 IST, Bhubaneswar
--
-- ROLLBACK: DROP TABLE IF EXISTS kala_obstruction;
-- ─────────────────────────────────────────────────────────────────────────────

-- ── Table ─────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS kala_obstruction (
  id               BIGSERIAL   NOT NULL,
  chart_id         UUID        REFERENCES charts(chart_id) ON DELETE CASCADE,
  date             DATE        NOT NULL,
  obstruction_type TEXT        NOT NULL
                               CHECK (obstruction_type IN (
                                 'malefic_transit',
                                 'adverse_dasha',
                                 'double_affliction'
                               )),
  severity         FLOAT       NOT NULL
                               CHECK (severity >= 0.0 AND severity <= 1.0),
  factors          JSONB       NOT NULL DEFAULT '{}',
  source_citation  TEXT        NOT NULL,
  computed_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  CONSTRAINT kala_obstruction_pk PRIMARY KEY (id),
  CONSTRAINT kala_obstruction_uniq UNIQUE (chart_id, date, obstruction_type)
);

-- ── Indexes ───────────────────────────────────────────────────────────────────

-- Primary scan: all obstructions for a chart
CREATE INDEX IF NOT EXISTS idx_kala_obstruction_chart_id
  ON kala_obstruction (chart_id);

-- Date range scans
CREATE INDEX IF NOT EXISTS idx_kala_obstruction_date
  ON kala_obstruction (chart_id, date);

-- Severity threshold queries
CREATE INDEX IF NOT EXISTS idx_kala_obstruction_severity
  ON kala_obstruction (chart_id, severity DESC);

-- Type filter
CREATE INDEX IF NOT EXISTS idx_kala_obstruction_type
  ON kala_obstruction (chart_id, obstruction_type);

-- JSONB factors search (GIN for arbitrary factor key lookups)
CREATE INDEX IF NOT EXISTS idx_kala_obstruction_factors
  ON kala_obstruction USING GIN (factors);

-- ── Table comment ─────────────────────────────────────────────────────────────

COMMENT ON TABLE kala_obstruction IS
  'BRAHMA-KA-3-3: Temporal obstruction overlaps. '
  'Each row represents a period where ≥2 adverse indicators overlap: '
  'malefic planet (Sani/Rahu/Ketu) transit through dusthana house AND/OR '
  'active Vimshottari MD/AD ruled by a natural malefic. '
  'severity: 0.5 (2 indicators), 0.75 (3), 0.90 (4+). '
  'source_citation: "PyJHora/SwissEph DE441 + Brahma-L1" on all rows. '
  'Tool: period_snapshot via platform-mcp/src/tools/kala_period_snapshot.ts. '
  'Native: Abhisek Mohanty 1984-02-05; FORENSIC §5.1 Vimshottari schedule.';
