-- Migration 561: gochara_v3_calibration table — GOCHARA-UTKARSA W4.4
-- =============================================================================
-- GOCHARA-UTKARSHA campaign, wave W4.4 (cross-chart pooled weight fitting).
--
-- WHY: W4.4 fits per-mechanism weights for the 7 admitted Wave-2 scoring
-- mechanisms + 3 sub-components (10 total), using cross-chart partial pooling
-- across native (482012f1-...) and Abhinandan (1c826d5a-...) charts.
-- The fitted weights land here with provenance (fit_run_id, dataset_hash,
-- per-chart deltas, shrinkage parameters) so they are auditable and can be
-- versioned across calibration runs.
--
-- WHAT: Creates gochara_v3_calibration with UNIQUE (fit_run_id, toggle_key)
-- for idempotent re-runs. ON CONFLICT DO UPDATE on the primary key means a
-- re-run with the same fit_run_id + toggle_key overwrites rather than
-- accretes — intentional, since the harness generates a fresh UUID per run.
--
-- IDEMPOTENCY: CREATE TABLE IF NOT EXISTS + safe re-application.
--
-- SCOPE: New table only. No kala_gochara_windows or kala_gochara_windows_v2
-- rows are touched.
-- =============================================================================

CREATE TABLE IF NOT EXISTS gochara_v3_calibration (
    id                        BIGSERIAL PRIMARY KEY,
    fit_run_id                UUID       NOT NULL DEFAULT gen_random_uuid(),
    wave                      TEXT       NOT NULL DEFAULT 'W4.4',
    mechanism_id              TEXT       NOT NULL,
    toggle_key                TEXT       NOT NULL,
    weight_value              NUMERIC(10, 6) NOT NULL,
    pooled_delta_hit_rate     NUMERIC(10, 6),
    delta_native              NUMERIC(10, 6),
    delta_abhinandan          NUMERIC(10, 6),
    n_train_events_native     INTEGER,
    n_train_events_abhinandan INTEGER,
    per_chart_hit_rates       JSONB,
    fit_provenance            JSONB,
    fitted_at                 TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (fit_run_id, toggle_key)
);

COMMENT ON TABLE gochara_v3_calibration IS
  'GOCHARA-UTKARSA W4.4 fitted weights. Each row is one mechanism weight '
  'computed by cross-chart partial pooling (native + Abhinandan). '
  'fit_run_id groups all weights from a single harness run. '
  'The UNIQUE (fit_run_id, toggle_key) constraint makes ON CONFLICT DO UPDATE '
  'idempotent: re-running with the same UUID overwrites, not accretes. '
  'fit_provenance JSONB carries dataset_hash, shrinkage_prior_k, and '
  'ablation_method for full reproducibility audit.';

COMMENT ON COLUMN gochara_v3_calibration.fit_run_id IS
  'UUID generated once per harness run (w44_weight_fitting.py:build_weight_fitting_report). '
  'Groups all 10 mechanism weights from the same run.';

COMMENT ON COLUMN gochara_v3_calibration.weight_value IS
  'Final fitted weight = max(0.0, pooled_delta_shrunk). Non-negative: '
  'a mechanism that does not help the pooled score gets 0, never negative.';

COMMENT ON COLUMN gochara_v3_calibration.pooled_delta_hit_rate IS
  'Pre-shrinkage pooled delta: (n_native * delta_native + n_abhinandan * delta_abhinandan) '
  '/ (n_native + n_abhinandan). Stored for audit; weight_value = max(0, pooled * shrinkage).';

COMMENT ON COLUMN gochara_v3_calibration.fit_provenance IS
  'JSON provenance: dataset_hash (MD5 of sorted train event_ids), '
  'shrinkage_prior_k, proxy_ablation_fraction, ablation_method, '
  'hit_rate_full_native, hit_rate_full_abhinandan, and window counts.';

-- Index for fast lookup by toggle_key across all runs (e.g. retrieve latest weight)
CREATE INDEX IF NOT EXISTS gochara_v3_calibration_toggle_key_idx
    ON gochara_v3_calibration (toggle_key);

-- Index for lookup by fit_run_id (retrieve all weights from one run)
CREATE INDEX IF NOT EXISTS gochara_v3_calibration_fit_run_id_idx
    ON gochara_v3_calibration (fit_run_id);

-- Index to find the most-recent run per mechanism (fitted_at DESC)
CREATE INDEX IF NOT EXISTS gochara_v3_calibration_mechanism_fitted_idx
    ON gochara_v3_calibration (mechanism_id, fitted_at DESC);

-- =============================================================================
-- Rollback (manual — no automated down path):
--   DROP TABLE IF EXISTS gochara_v3_calibration;
-- Only safe AFTER w44_weight_fitting.py is fully decommissioned.
-- =============================================================================
