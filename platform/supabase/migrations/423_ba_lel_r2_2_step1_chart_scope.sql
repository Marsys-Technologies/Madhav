-- Migration 423: BA Phase-4 R2.2 Step 1 — chart-scope the LEL tables.
-- Created: 2026-07-07
--
-- CLAUDECODE_BRIEF_BA_LEL_CHART_SCOPING v1.1 Step 1. Makes life_events +
-- event_chart_state_index per-chart so LEL becomes a living per-chart asset
-- (availability-driven calibration), closes the MCP chart_id impedance mismatch,
-- and registers/​protects the tables.
--
-- STATE AT WRITE (verified 2026-07-07): both tables are EMPTY in prod (0 rows).
-- The 57 native events live in the canonical markdown (LIFE_EVENT_LOG_v1_2.md v1.7)
-- + the lel_intake.py LEL_CORPUS; they are intaken chart-scoped in Step 2. Because
-- the tables are empty, chart_id is added + SET NOT NULL with NO backfill (and thus
-- no native-chart literal here — the governance no-native-literal gate stays clean).
-- If any unexpected row exists, SET NOT NULL fails loudly (safe — surfaces the surprise).

BEGIN;

-- ── life_events: chart-scope + re-key + new columns ──────────────────────────
ALTER TABLE life_events ADD COLUMN IF NOT EXISTS chart_id uuid REFERENCES charts(id);
ALTER TABLE life_events ALTER COLUMN chart_id SET NOT NULL;

-- natural key becomes (chart_id, event_id); drop the global-unique on event_id
ALTER TABLE life_events DROP CONSTRAINT IF EXISTS life_events_event_id_key;
ALTER TABLE life_events DROP CONSTRAINT IF EXISTS life_events_chart_event_uq;
ALTER TABLE life_events ADD CONSTRAINT life_events_chart_event_uq UNIQUE (chart_id, event_id);
CREATE INDEX IF NOT EXISTS life_events_chart_id_idx ON life_events (chart_id);

-- occurrence vs recording separation. event_date already carries occurrence
-- semantics (verified) — recorded_at is the NEW column that drives the Step-5
-- leakage-routing discipline (training vs outcome by recorded_at vs snapshot).
COMMENT ON COLUMN life_events.event_date IS
  'Occurrence date of the event (occurred_at semantics). For year-approx events, proxy YYYY-07-01.';
ALTER TABLE life_events ADD COLUMN IF NOT EXISTS recorded_at timestamptz NOT NULL DEFAULT now();
COMMENT ON COLUMN life_events.recorded_at IS
  'When this row was recorded into the instrument (NOT when the event occurred). '
  'Step-5 leakage routing: recorded_at BEFORE a frozen prediction snapshot = training; '
  'AFTER = outcome evidence (two-key blind path). The 57 native rows use a pre_instrument '
  'sentinel at intake (their recording predates all predictions — pure training).';

-- cross-chart pooling (Step 6): capture consent now, consume gated later
ALTER TABLE life_events ADD COLUMN IF NOT EXISTS pool_consent boolean NOT NULL DEFAULT false;
ALTER TABLE life_events ADD COLUMN IF NOT EXISTS contributed_to_pool_at timestamptz;
COMMENT ON COLUMN life_events.pool_consent IS
  'Native opt-in for this chart contributing to the cross-chart calibration pool (default false).';

-- ── event_chart_state_index: chart-scope + re-key ────────────────────────────
ALTER TABLE event_chart_state_index ADD COLUMN IF NOT EXISTS chart_id uuid REFERENCES charts(id);
ALTER TABLE event_chart_state_index ALTER COLUMN chart_id SET NOT NULL;
ALTER TABLE event_chart_state_index DROP CONSTRAINT IF EXISTS eci_chart_event_uq;
ALTER TABLE event_chart_state_index ADD CONSTRAINT eci_chart_event_uq UNIQUE (chart_id, event_id);
CREATE INDEX IF NOT EXISTS eci_chart_id_idx ON event_chart_state_index (chart_id);

-- ── lel_query: chart-scoped signature (closes the MCP impedance mismatch) ─────
-- The old chart-less fn is dropped; the new fn REQUIRES p_chart_id and filters on it.
DROP FUNCTION IF EXISTS lel_query(TEXT, DATE, DATE, INT);

CREATE OR REPLACE FUNCTION lel_query(
    p_chart_id    uuid,
    p_domain      TEXT    DEFAULT NULL,
    p_date_start  DATE    DEFAULT NULL,
    p_date_end    DATE    DEFAULT NULL,
    p_limit       INT     DEFAULT 100
)
RETURNS JSONB
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_events      JSONB;
    v_total_count BIGINT;
    v_result      JSONB;
BEGIN
    SELECT COUNT(*)
    INTO   v_total_count
    FROM   life_events le
    WHERE  le.chart_id = p_chart_id
      AND  (p_domain IS NULL OR le.domain ILIKE '%' || p_domain || '%' OR le.category ILIKE '%' || p_domain || '%' OR le.event_type ILIKE '%' || p_domain || '%')
      AND  (p_date_start IS NULL OR le.event_date >= p_date_start)
      AND  (p_date_end   IS NULL OR le.event_date <= p_date_end);

    SELECT jsonb_agg(
        jsonb_build_object(
            'event_id',          le.event_id,
            'event_date',        le.event_date,
            'category',          le.category,
            'event_type',        le.event_type,
            'description',       le.description,
            'domain',            le.domain,
            'significance',      le.significance,
            'outcome_observed',  le.outcome_observed,
            'dasha_active',      cs.dasha_active,
            'antardasha_active', cs.antardasha_active,
            'key_transits',      cs.key_transits,
            'convergence_score', cs.convergence_score,
            'source_citation',   le.source_citation
        )
        ORDER BY le.event_date
    )
    INTO v_events
    FROM life_events le
    LEFT JOIN event_chart_state_index cs
           ON cs.event_id = le.event_id AND cs.chart_id = le.chart_id
    WHERE le.chart_id = p_chart_id
      AND (p_domain IS NULL OR le.domain ILIKE '%' || p_domain || '%' OR le.category ILIKE '%' || p_domain || '%' OR le.event_type ILIKE '%' || p_domain || '%')
      AND (p_date_start IS NULL OR le.event_date >= p_date_start)
      AND (p_date_end   IS NULL OR le.event_date <= p_date_end)
    LIMIT p_limit;

    v_result := jsonb_build_object(
        'events',         COALESCE(v_events, '[]'::JSONB),
        'total_count',    v_total_count,
        'chart_id',       p_chart_id,
        'filter_applied', jsonb_build_object(
            'chart_id',   p_chart_id,
            'domain',     p_domain,
            'date_start', p_date_start,
            'date_end',   p_date_end,
            'limit',      p_limit
        ),
        'provenance_envelope', jsonb_build_object(
            'source',          'mimamsa.lel_intake',
            'asset',           'lel_events',
            'scope',           'per_chart',
            'no_leakage_note', 'life_events is a calibration corpus only — must not feed prediction generation',
            'b3_compliant',    true,
            'empty_reason',    CASE WHEN COALESCE(v_events,'[]'::JSONB) = '[]'::JSONB
                                    THEN 'no LEL events recorded for this chart (structural/no-lel)'
                                    ELSE NULL END
        )
    );

    RETURN v_result;
END;
$$;

COMMENT ON FUNCTION lel_query(uuid, TEXT, DATE, DATE, INT) IS
  'Chart-scoped LEL query (BA-LEL R2.2 Step 1): REQUIRES p_chart_id; returns that '
  'chart''s life events only, with an honest empty-with-reason envelope. NO LEAKAGE: '
  'life_events is a calibration corpus, never a prediction-generation source.';

-- ── asset_registry: register lel_events (user-authored source data, NOT a built asset)
INSERT INTO asset_registry
    (asset_id, layer, scope, has_writer, sanskrit_name, english_name, english_description,
     storage_type, sort_order, count_sql, target_floor, is_active)
VALUES (
    'lel_events',
    'mimamsa',
    'per_chart',
    false,
    'Jīvanaghaṭanā Mūla',
    'Life Event Log (user-authored source data)',
    'Per-chart user-authored life-event corpus (occurrence + recording dates, chart-state index). '
        || 'Source data, NOT a built asset (has_writer=false); intaken via the LEL save API. '
        || 'Availability-driven calibration input; never a prediction-generation source (no-leakage).',
    'postgres_table',
    0,
    'SELECT count(*) FROM life_events WHERE chart_id = $1',
    0,
    true
)
ON CONFLICT (asset_id) DO UPDATE
  SET scope        = EXCLUDED.scope,
      has_writer   = EXCLUDED.has_writer,
      count_sql    = EXCLUDED.count_sql;

COMMIT;

-- DOWN:
-- ALTER TABLE event_chart_state_index DROP CONSTRAINT IF EXISTS eci_chart_event_uq;
-- DROP INDEX IF EXISTS eci_chart_id_idx;
-- ALTER TABLE event_chart_state_index DROP COLUMN IF EXISTS chart_id;
-- ALTER TABLE life_events DROP CONSTRAINT IF EXISTS life_events_chart_event_uq;
-- ALTER TABLE life_events ADD CONSTRAINT life_events_event_id_key UNIQUE (event_id);
-- DROP INDEX IF EXISTS life_events_chart_id_idx;
-- ALTER TABLE life_events DROP COLUMN IF EXISTS chart_id, DROP COLUMN IF EXISTS recorded_at,
--   DROP COLUMN IF EXISTS pool_consent, DROP COLUMN IF EXISTS contributed_to_pool_at;
-- DROP FUNCTION IF EXISTS lel_query(uuid, TEXT, DATE, DATE, INT);
-- DELETE FROM asset_registry WHERE asset_id = 'lel_events';
-- (old chart-less lel_query(TEXT,DATE,DATE,INT) would be recreated from brahma_mimamsa_lel_intake.sql)
