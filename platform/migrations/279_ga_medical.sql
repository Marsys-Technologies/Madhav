-- 279_ga_medical.sql
-- =============================================================================
-- Medical/Ayurvedic Subsystem Gate-1 — ga_medical L1 per-chart table.
--
-- ga_medical: 9 grahas × 5 ayanamshas = 45 rows per chart.
-- Joined from ga_condition_composite + bg_medical_mappings.
-- condition_score → indication_strength: <0.4→'strong', 0.4-0.6→'moderate', >0.6→'mild'.
-- Moon row carries nakshatra_body_part from bg_nakshatra_medical.
--
-- MEDICAL DISCLAIMER (NON-NEGOTIABLE):
--   indication_tier = 'jyotish_indication' (NOT NULL, DEFAULT enforced)
--   not_diagnosis   = TRUE                 (NOT NULL, DEFAULT enforced)
--   This is a Jyotish indicator system ONLY — NOT a medical diagnosis.
--
-- Idempotency: L1 pattern — DELETE WHERE (chart_id, ayanamsha_id) then INSERT.
-- Natural key: UNIQUE (chart_id, ayanamsha_id, graha).
-- =============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS ga_medical (
    id                  SERIAL PRIMARY KEY,
    chart_id            UUID NOT NULL,
    ayanamsha_id        TEXT NOT NULL,
    graha               TEXT NOT NULL,
    natal_sign          TEXT,
    natal_nakshatra     TEXT,
    indication_strength TEXT,
    dosha_aggravated    TEXT[],
    organ_watch         TEXT[],
    body_part_watch     TEXT[],
    nakshatra_body_part TEXT,
    indication_tier     TEXT NOT NULL DEFAULT 'jyotish_indication',
    not_diagnosis       BOOLEAN NOT NULL DEFAULT TRUE,
    classical_citation  TEXT NOT NULL,
    computed_at         TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (chart_id, ayanamsha_id, graha)
);

CREATE INDEX IF NOT EXISTS ga_medical_chart_aya_idx
    ON ga_medical (chart_id, ayanamsha_id);

CREATE INDEX IF NOT EXISTS ga_medical_graha_idx
    ON ga_medical (graha);

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   DROP TABLE IF EXISTS ga_medical;
--   COMMIT;
-- =============================================================================
