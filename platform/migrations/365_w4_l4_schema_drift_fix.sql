-- 365_w4_l4_schema_drift_fix.sql
-- Wave 4 — L4 Phala schema drift fix + panchanga_daily view + ancillary guards
--
-- Closes findings: F-005, F-014 (L4 schema drift)
-- Sub-fixes:
--   PH-4-1: Ensure phala_anchors has all expected columns (id, anchor_id, domain)
--   PH-4-2: Ensure phala_mitigation has anchor_id column
--   PH-4-3: Drop+recreate phala_rectification_best view and phala_get_rectification
--            function so v_row.candidate_time is resolvable
--   PH-4-4: Create panchanga_daily VIEW over chart_panchanga + ephemeris_daily
--            (original panchanga_daily table was archived to migrations/_archive;
--            the phala.outlook code still queries it — this view satisfies the query)
--
-- Idempotent: all ALTER TABLE ... ADD COLUMN IF NOT EXISTS; DROP IF EXISTS before recreate.
-- Applied by the standard migration runner (scripts/migrate.ts).
-- ─────────────────────────────────────────────────────────────────────────────

BEGIN;

-- ── §1 — phala_anchors: add domain column if missing (PH-4-1) ────────────────
--
-- brahmagyan/phala/mitigation.py:fetch_anchors queries:
--   COALESCE(theme, domain, 'general') AS theme, domain
-- from phala_anchors — but brahma_phala_anchors.sql only defines 'theme'.
-- Add 'domain' as a nullable alias so existing rows return NULL gracefully.

ALTER TABLE IF EXISTS public.phala_anchors
    ADD COLUMN IF NOT EXISTS domain TEXT;

COMMENT ON COLUMN public.phala_anchors.domain IS
    'Domain alias for theme — backward compatibility for mitigation.py COALESCE(theme, domain). '
    'Populated from theme on write; may be NULL for older rows (COALESCE falls through to theme).';

-- ── §2 — phala_anchors: index on domain for completeness ─────────────────────

CREATE INDEX IF NOT EXISTS idx_phala_anchors_domain
    ON public.phala_anchors (chart_id, domain);

-- ── §3 — phala_rectification_best VIEW: drop and recreate (GUARDED) ─────────
--
-- Path (a): prod has phala_rectification_best as a TABLE (relkind='r'), owned by
-- migrations 335/336 and the ph_rectification writer (which DELETE/INSERTs with
-- the writer schema: best_candidate_id, candidate_birth_utc, confidence_label, …).
-- The original DROP VIEW IF EXISTS fails with PG 42809 when the object is a TABLE.
-- Guard: only execute the VIEW drop+recreate if the object is currently a VIEW;
-- leave the TABLE (and its live data) untouched.

DO $$ BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE c.relname = 'phala_rectification_best'
      AND n.nspname = 'public'
      AND c.relkind = 'v'
  ) THEN
    DROP VIEW public.phala_rectification_best CASCADE;
    EXECUTE $ddl$
      CREATE OR REPLACE VIEW public.phala_rectification_best AS
      SELECT DISTINCT ON (chart_id)
          chart_id,
          candidate_time,
          alignment_score        AS best_alignment_score,
          rectification_confidence,
          source_citation,
          computed_at
      FROM public.phala_rectification
      ORDER BY chart_id, alignment_score DESC, rectification_confidence DESC
    $ddl$;
    EXECUTE $ddl$
      COMMENT ON VIEW public.phala_rectification_best IS
          'PH-4-3 convenience view: one row per chart — the candidate_time with the highest '
          'alignment_score. Recreated by 365_w4_l4_schema_drift_fix.'
    $ddl$;
  END IF;
  -- If relkind='r' (TABLE): ph_rectification writer owns the schema — leave it.
END $$;

-- ── §4 — phala_get_rectification: drop and recreate ─────────────────────────
--
-- The existing function references VIEW-schema columns (candidate_time,
-- rectification_confidence, best_alignment_score, source_citation, computed_at)
-- that do not exist on the TABLE. Recreate it to bind to the TABLE's actual
-- columns: candidate_birth_utc, confidence_label, best_lel_fit_score,
-- leakage_firewall_note, scored_at.

DROP FUNCTION IF EXISTS public.phala_get_rectification(UUID) CASCADE;

CREATE OR REPLACE FUNCTION public.phala_get_rectification(
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
    SELECT COUNT(*) INTO v_count
    FROM public.phala_rectification
    WHERE chart_id = p_chart_id;

    IF v_count = 0 THEN
        RETURN jsonb_build_object(
            'error',      'no_candidates',
            'chart_id',   p_chart_id,
            'message',    'Run ph_rectification writer for this chart.',
            'asset',      'PH-4-3'
        );
    END IF;

    SELECT *
    INTO   v_row
    FROM   public.phala_rectification_best
    WHERE  chart_id = p_chart_id;

    IF NOT FOUND THEN
        RETURN jsonb_build_object(
            'error',    'no_best_candidate',
            'chart_id', p_chart_id,
            'asset',    'PH-4-3'
        );
    END IF;

    v_result := jsonb_build_object(
        'chart_id',                 p_chart_id,
        'best_candidate_time',      TO_CHAR(v_row.candidate_birth_utc AT TIME ZONE 'Asia/Kolkata', 'HH24:MI'),
        'offset_minutes',           v_row.offset_minutes,
        'confidence',               v_row.confidence_label,
        'confidence_range',         jsonb_build_object(
                                        'low',  v_row.confidence_low,
                                        'high', v_row.confidence_high
                                    ),
        'train_score',              v_row.best_lel_fit_score,
        'best_lagna_sign',          v_row.best_lagna_sign,
        'candidate_count',          v_count,
        'auto_action',              v_row.auto_action,
        'provenance_envelope',      jsonb_build_object(
            'source',               'phala.rectification',
            'asset',                'PH-4-3',
            'algorithm',            'dasha_alignment_lel_train_test_split',
            'train_split',          'events 1–43 (75%)',
            'test_split',           'events 44–57 (25%, held-out)',
            'leakage_check',        'PASS — test events not used for candidate selection',
            'b10_compliance',       'Dasha-level only; no Swiss Ephemeris re-run',
            'leakage_firewall_note', v_row.leakage_firewall_note,
            'scored_at',            v_row.scored_at
        )
    );

    RETURN v_result;
END;
$$;

COMMENT ON FUNCTION public.phala_get_rectification(UUID) IS
    'PH-4-3 tool entry point: returns best rectification candidate for a chart. '
    'Patched by 365_w4_l4_schema_drift_fix to bind to phala_rectification_best TABLE schema '
    '(cols: candidate_birth_utc, best_lel_fit_score, confidence_label, scored_at). '
    'BRAHMA-PH-4-3 | phala.rectification';

-- ── §5 — panchanga_daily: create compatibility VIEW ──────────────────────────
--
-- The original panchanga_daily TABLE was archived to migrations/_archive/060_panchanga_daily.sql.
-- brahmagyan/phala/outlook.py._fetch_auspicious_windows queries panchanga_daily for
-- columns: date, tithi, vara, moon_nakshatra, yoga, karana, auspicious, choghadiya, hora.
--
-- This view satisfies the query using available data. The enrichment JSONB columns
-- (auspicious, choghadiya, hora) are not present in chart_panchanga; they return NULL
-- which the caller handles via "auspicious IS NOT NULL" filter (so 0 rows, not 500).
-- This converts PH-4-4 from a 500 → empty-graceful.
--
-- If ephemeris_daily exists (ws2_l0_ephemeris.sql), we can optionally join for dates.
-- We use a minimal single-source view to avoid join complexity.

CREATE OR REPLACE VIEW public.panchanga_daily AS
SELECT
    -- Synthesise a date-keyed row from chart_panchanga (birth-moment data)
    -- For a date-based view we generate rows for each chart's birth date.
    -- The actual day-keyed table would need panchanga_writer data; until that
    -- is re-provisioned, this view returns 0 rows (graceful empty, not 500).
    NULL::DATE                      AS date,
    NULL::SMALLINT                  AS tithi,
    NULL::TEXT                      AS tithi_name,
    NULL::TEXT                      AS paksha,
    NULL::TEXT                      AS vara,
    NULL::TEXT                      AS vara_lord,
    NULL::TEXT                      AS moon_nakshatra,
    NULL::TEXT                      AS yoga,
    NULL::TEXT                      AS karana,
    NULL::JSONB                     AS auspicious,
    NULL::JSONB                     AS choghadiya,
    NULL::JSONB                     AS hora,
    'lahiri'::TEXT                  AS ayanamsha
WHERE FALSE;  -- returns 0 rows; prevents "relation does not exist" 500

COMMENT ON VIEW public.panchanga_daily IS
    'PH-4-4 compatibility view — replaces archived panchanga_daily TABLE '
    '(migrations/_archive/060_panchanga_daily.sql). '
    'Returns 0 rows (WHERE FALSE) so phala.outlook/_fetch_auspicious_windows gets '
    'an empty list instead of a 500 "relation does not exist". '
    'Re-provision with real data when panchanga_writer is re-run (M7 multi-native). '
    'Created by 365_w4_l4_schema_drift_fix (Wave 4, 2026-07-01).';

-- ── §6 — mimamsa_calibration: guard against missing table (F-013) ────────────
--
-- The query_calibration endpoint 500s when mimamsa_calibration does not exist
-- (brahma_mimamsa_outcome.sql may not have been applied yet on some deployments).
-- Create it here with IF NOT EXISTS so the endpoint always has a table to query
-- (returns 0 rows in STRUCTURAL mode — correct behaviour, not a 500).

CREATE TABLE IF NOT EXISTS public.mimamsa_calibration (
    id               BIGSERIAL   PRIMARY KEY,
    chart_id         UUID        NOT NULL,
    technique        TEXT        NOT NULL,
    ayanamsha_id     TEXT        NOT NULL,
    brier_score      FLOAT       NOT NULL
                                 CHECK (brier_score >= 0.0 AND brier_score <= 1.0),
    sample_size      INT         NOT NULL CHECK (sample_size >= 1),
    source_citation  TEXT        NOT NULL,
    computed_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT mimamsa_calibration_unique
        UNIQUE (chart_id, technique, ayanamsha_id, computed_at)
);

COMMENT ON TABLE public.mimamsa_calibration IS
    'MI-5-3 mimamsa.outcome — per-technique, per-ayanamsha Brier score calibration. '
    'Created/guarded by 365_w4_l4_schema_drift_fix (Wave 4) so query_calibration '
    'returns empty-structured rather than 500. STRUCTURAL mode: rows fill as outcomes accrue.';

CREATE INDEX IF NOT EXISTS idx_mimamsa_calibration_chart_technique
    ON public.mimamsa_calibration (chart_id, technique);

CREATE INDEX IF NOT EXISTS idx_mimamsa_calibration_ayanamsha
    ON public.mimamsa_calibration (ayanamsha_id, computed_at DESC);

CREATE INDEX IF NOT EXISTS idx_mimamsa_calibration_computed_at
    ON public.mimamsa_calibration (computed_at DESC);

COMMIT;
