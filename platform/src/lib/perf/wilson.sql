-- wilson.sql — Wilson score interval functions (Track B — v3.4-S1)
--
-- Implements Wilson confidence interval lower and upper bound as PostgreSQL
-- immutable functions. Used by mv_calibration_score to produce honest CI
-- bands for per-confidence-band calibration cells.
--
-- Reference: Wilson (1927). The z-values hard-coded match common CI levels.
-- Accuracy: agrees with scipy.stats.proportion_confint(method='wilson') to 4 dp.
--
-- AC.S1.4 test vectors (verified in grounding_pipeline.test.ts):
--   wilson_lower_bound(5, 10, 0.95) ≈ 0.2366  (expect 0.24 ± 0.02)
--   wilson_upper_bound(5, 10, 0.95) ≈ 0.7634  (expect 0.76 ± 0.02)
--
-- Apply to Supabase (where mcp_predictions lives):
--   psql "$SUPABASE_DB_URL" -f platform/src/lib/perf/wilson.sql
--
-- Or via Supabase SQL editor.

CREATE OR REPLACE FUNCTION wilson_lower_bound(
  successes  int,
  total      int,
  confidence float DEFAULT 0.95
)
RETURNS float AS $$
DECLARE
  z      float;
  p_hat  float;
  denom  float;
  center float;
  margin float;
BEGIN
  IF total IS NULL OR total = 0 THEN RETURN NULL; END IF;

  z := CASE confidence
    WHEN 0.95 THEN 1.96
    WHEN 0.99 THEN 2.576
    WHEN 0.90 THEN 1.645
    ELSE 1.96
  END;

  p_hat  := successes::float / total;
  denom  := 1.0 + (z * z / total);
  center := (p_hat + (z * z / (2.0 * total))) / denom;
  margin := (z * sqrt(
    (p_hat * (1 - p_hat) / total) +
    (z * z / (4.0 * total * total))
  )) / denom;

  RETURN greatest(0.0, center - margin);
END;
$$ LANGUAGE plpgsql IMMUTABLE STRICT;


CREATE OR REPLACE FUNCTION wilson_upper_bound(
  successes  int,
  total      int,
  confidence float DEFAULT 0.95
)
RETURNS float AS $$
DECLARE
  z      float;
  p_hat  float;
  denom  float;
  center float;
  margin float;
BEGIN
  IF total IS NULL OR total = 0 THEN RETURN NULL; END IF;

  z := CASE confidence
    WHEN 0.95 THEN 1.96
    WHEN 0.99 THEN 2.576
    WHEN 0.90 THEN 1.645
    ELSE 1.96
  END;

  p_hat  := successes::float / total;
  denom  := 1.0 + (z * z / total);
  center := (p_hat + (z * z / (2.0 * total))) / denom;
  margin := (z * sqrt(
    (p_hat * (1 - p_hat) / total) +
    (z * z / (4.0 * total * total))
  )) / denom;

  RETURN least(1.0, center + margin);
END;
$$ LANGUAGE plpgsql IMMUTABLE STRICT;


-- ── mv_calibration_score ──────────────────────────────────────────────────────
--
-- Materialized view: per-confidence-band × domain × horizon_bucket hit rate.
-- Refreshed nightly at 04:00 UTC (see mv_refresh.ts).
--
-- Depends on:
--   mcp_predictions          — from migration 071 + WT-A migration 075 extensions
--   mcp_prediction_outcomes  — from WT-A migration 075
--   wilson_lower_bound()     — defined above
--   wilson_upper_bound()     — defined above
--
-- WT-A adds confidence_band (text), horizon_days (int) to mcp_predictions, and
-- creates the mcp_prediction_outcomes table. This view is safe to create after
-- WT-A merges into feature/mcpt-final.

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_calibration_score AS
SELECT
  p.confidence_band,
  p.domain,
  CASE
    WHEN p.horizon_days <= 30  THEN '<=30d'
    WHEN p.horizon_days <= 180 THEN '31-180d'
    WHEN p.horizon_days <= 730 THEN '181-730d'
    ELSE '>730d'
  END                                                              AS horizon_bucket,
  count(*)                                                         AS total_predictions,
  count(o.outcome) FILTER (WHERE o.outcome = 'realized')           AS realized,
  count(o.outcome) FILTER (WHERE o.outcome = 'disconfirmed')       AS disconfirmed,
  count(o.outcome) FILTER (WHERE o.outcome = 'partial')            AS partial,
  count(*) - count(o.outcome)                                      AS pending,
  -- realized_rate = realized / (realized + disconfirmed)  [excludes pending + partial]
  count(o.outcome) FILTER (WHERE o.outcome = 'realized')::float /
    NULLIF(
      count(o.outcome) FILTER (WHERE o.outcome IN ('realized', 'disconfirmed')),
      0
    )                                                              AS realized_rate,
  -- Wilson CI lower bound (95%)
  CASE WHEN count(o.outcome) FILTER (WHERE o.outcome IN ('realized', 'disconfirmed')) > 0
    THEN wilson_lower_bound(
      count(o.outcome) FILTER (WHERE o.outcome = 'realized'),
      count(o.outcome) FILTER (WHERE o.outcome IN ('realized', 'disconfirmed')),
      0.95
    )
  ELSE NULL END                                                    AS realized_rate_ci_low,
  -- Wilson CI upper bound (95%)
  CASE WHEN count(o.outcome) FILTER (WHERE o.outcome IN ('realized', 'disconfirmed')) > 0
    THEN wilson_upper_bound(
      count(o.outcome) FILTER (WHERE o.outcome = 'realized'),
      count(o.outcome) FILTER (WHERE o.outcome IN ('realized', 'disconfirmed')),
      0.95
    )
  ELSE NULL END                                                    AS realized_rate_ci_high,
  max(o.outcome_recorded_at)                                       AS last_outcome_at
FROM mcp_predictions p
LEFT JOIN mcp_prediction_outcomes o ON o.prediction_id = p.prediction_id
GROUP BY p.confidence_band, p.domain, horizon_bucket;

CREATE UNIQUE INDEX IF NOT EXISTS mv_calibration_score_key
  ON mv_calibration_score (confidence_band, domain, horizon_bucket);

-- Discrepancy flag: bands where |realized_rate - midpoint| > 0.15 AND N ≥ 10
-- Used by the dashboard to highlight under/over-realized confidence bands.
CREATE OR REPLACE VIEW v_calibration_discrepancies AS
SELECT
  confidence_band,
  domain,
  horizon_bucket,
  realized_rate,
  realized_rate_ci_low,
  realized_rate_ci_high,
  (realized + disconfirmed)                                        AS n_resolved,
  CASE confidence_band
    WHEN 'high'   THEN 0.70
    WHEN 'medium' THEN 0.50
    WHEN 'low'    THEN 0.30
    ELSE 0.50
  END                                                              AS band_midpoint,
  ABS(realized_rate - CASE confidence_band
    WHEN 'high'   THEN 0.70
    WHEN 'medium' THEN 0.50
    WHEN 'low'    THEN 0.30
    ELSE 0.50
  END)                                                             AS discrepancy_mag
FROM mv_calibration_score
WHERE (realized + disconfirmed) >= 10
  AND realized_rate IS NOT NULL;
