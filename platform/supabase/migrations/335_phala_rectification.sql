-- Migration 333: phala_rectification — Birth-time rectification candidates
-- Separate from 333_phala_sodhana (anomaly registry); both apply cleanly via migrate.ts filename keying.
-- Birth-time rectification: PyJHora ascendant scan (±90 min) scored against pre-2020 LEL events.
-- NO-AUTO-OVERRIDE (D43): canonical chart 482012f1 is NEVER auto-mutated by this build.
CREATE TABLE IF NOT EXISTS phala_rectification (
    id                      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    chart_id                uuid NOT NULL REFERENCES charts(id) ON DELETE CASCADE,
    candidate_birth_utc     timestamptz NOT NULL,
    offset_minutes          integer NOT NULL,  -- signed offset from recorded 10:43 IST
    ayanamsha_id            text NOT NULL,
    lagna_sign              text NOT NULL,
    lagna_longitude_deg     numeric(8,4) NOT NULL,
    lagna_degree_in_sign    numeric(8,4) NOT NULL,
    lel_fit_score           numeric(6,4),      -- normalized [0,1]; higher = better LEL fit
    lel_events_matched      integer,
    lel_events_tested       integer,
    lagna_stable            boolean NOT NULL DEFAULT true,  -- false if lagna shifts sign from the recorded-time reference
    scored_at               timestamptz NOT NULL DEFAULT NOW(),
    CONSTRAINT phala_rectification_chart_offset_ayan
        UNIQUE (chart_id, offset_minutes, ayanamsha_id)
);
CREATE INDEX IF NOT EXISTS idx_phala_rectification_chart_score
    ON phala_rectification(chart_id, lel_fit_score DESC NULLS LAST);
