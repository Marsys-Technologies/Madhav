-- Migration 425: BA Phase-4 R2.2 Step 6 — cross-chart pool contribution capture table.
-- Created: 2026-07-08
--
-- Feature E-pool (Step 6: capture-now, consume-gated). Per-chart, provenance-tagged
-- capture table for cross-chart calibration-pool contributions. A chart's contribution
-- is CAPTURED here as soon as its calibration produces one — EVEN WHEN the cross-chart
-- pool flag (MIMAMSA_CROSS_CHART_POOL) is OFF. The row records the chart's consent
-- (pool_consent) at capture time; whether the contribution is ever CONSUMED into the
-- blended cross-chart priors is a separate, gated decision made downstream via
-- lel_calibration.may_consume_into_pool(pool_consent, override) — which requires BOTH
-- per-chart consent AND the global flag on. Nothing reads this table to serve pooled
-- values while the flag is off; it is capture-only for now.
--
-- Surgical, transactional, idempotent. No native chart literal (no backfill).

BEGIN;

CREATE TABLE IF NOT EXISTS mimamsa_pool_contributions (
    id             uuid        NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    chart_id       uuid        NOT NULL REFERENCES charts(id),
    event_classes  text[]      NOT NULL,
    weights        jsonb,
    priors_version text,
    pool_consent   boolean     NOT NULL DEFAULT false,
    contributed_at timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE mimamsa_pool_contributions IS
  'BA-LEL R2.2 Step 6: per-chart provenance-tagged capture of cross-chart calibration '
  'pool contributions. CAPTURE-NOW: a row is written whenever a chart calibrates, even '
  'while the pool flag is OFF. CONSUME-GATED: pooled values are only ever blended when '
  'may_consume_into_pool(pool_consent, MIMAMSA_CROSS_CHART_POOL) is true. Capture-only '
  'for now — no serving path reads this table while the flag is off.';
COMMENT ON COLUMN mimamsa_pool_contributions.event_classes IS
  'Event-class ids this contribution covers (from brahma_event_ontology).';
COMMENT ON COLUMN mimamsa_pool_contributions.weights IS
  'Optional per-class contribution weights (jsonb), if the calibration produced them.';
COMMENT ON COLUMN mimamsa_pool_contributions.priors_version IS
  'Version tag of the priors the contribution was computed against (provenance).';
COMMENT ON COLUMN mimamsa_pool_contributions.pool_consent IS
  'Chart consent captured at contribution time. NECESSARY but NOT SUFFICIENT to consume '
  'into the pool — the global MIMAMSA_CROSS_CHART_POOL flag must also be on.';

CREATE INDEX IF NOT EXISTS mimamsa_pool_contributions_chart_id_idx
    ON mimamsa_pool_contributions (chart_id);

COMMIT;

-- DOWN:
-- DROP INDEX IF EXISTS mimamsa_pool_contributions_chart_id_idx;
-- DROP TABLE IF EXISTS mimamsa_pool_contributions;
