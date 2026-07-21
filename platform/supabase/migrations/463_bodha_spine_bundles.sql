-- Migration 463: bodha_spine_bundles — Retrieval Plane Elevation W5 Lane L5
-- Created: 2026-07-21
--
-- Context: RETRIEVAL_IMPLEMENTATION_MASTER_BRIEF_v1_0.md §E W5 standing scope line
-- "spine bundles as post-build materialized views" / RETRIEVAL_PLANE_ELEVATION_PLAN_v1_0.md
-- §8 item 11 / RETRIEVAL_STRATEGY_v1_0.md §S-5 + §5.1: a "spine bundle" is the pre-joined
-- cross-layer chain `signal (bodha_msr_signals) → its activation windows (kala_activation)
-- → its phala anchors (phala_anchors) → its calibration (mimamsa_calibration /
-- mimamsa_multipliers)`, served per (chart, ayanamsha, domain) as ONE capability instead of
-- the 3-5 manual calls the census found the LLM must make today (only one real cross-layer
-- join — bodha_msr_signals ↔ kala_activation — exists before this lane).
--
-- This table is the persisted "materialized view" half of that mechanism: after a chart's
-- L2-L5 assets build, the join is computed once (platform/src/lib/retrieval/spine/
-- compute_spine_bundle.ts, itself composed from the existing, independently-tested L2/L3/L4/L5
-- query capabilities — not a re-derivation of their SQL) and persisted here so a subsequent
-- read is a single-row SELECT instead of a 4-capability fan-out. Not a genuine Postgres
-- `CREATE MATERIALIZED VIEW`: those are refreshed in full (see mv_tool_metrics_24h /
-- mv_calibration_score, migration 073 / wilson.sql) which does not fit a per-chart,
-- per-domain incremental refresh — this table instead follows the CLAUDE.md §N.3 L1+
-- idempotency standard (per-chart delete-then-insert scoped to a natural key), which is
-- the idiomatic "replace, never accrete" materialization pattern for chart-scoped data in
-- this codebase.
--
-- source_asset_marker carries MAX(asset_throughput.last_built_at) across the four
-- constituent source assets (bo_laksana, ka_kalasutra, ph_nimitta, mi_pramana) at the moment
-- this row was computed — the staleness check a reader uses to decide whether a persisted
-- row is still trustworthy or must be recomputed (no silent staleness, per B.10/B.11
-- honesty discipline).
--
-- Idempotency: per §N.4 "surgical migrations only" — CREATE TABLE IF NOT EXISTS,
-- CREATE INDEX IF NOT EXISTS throughout. Safe to re-run.

BEGIN;

CREATE TABLE IF NOT EXISTS bodha_spine_bundles (
  id                    bigserial PRIMARY KEY,
  -- FK'd to charts(id), matching the majority pattern for chart-scoped L2+ tables
  -- (e.g. migrations 166/170/335/336) — a chart delete cascades its spine bundles too.
  chart_id              uuid NOT NULL REFERENCES charts(id) ON DELETE CASCADE,
  ayanamsha_id          text NOT NULL DEFAULT 'lahiri_chitrapaksha',
  domain                text NOT NULL,
  top_k                 integer NOT NULL,
  signal_count          integer NOT NULL DEFAULT 0,
  bundle_jsonb          jsonb NOT NULL,
  source_asset_marker   timestamptz,
  computed_at           timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT bodha_spine_bundles_chart_ayanamsha_domain_uq
    UNIQUE (chart_id, ayanamsha_id, domain)
);

CREATE INDEX IF NOT EXISTS idx_bodha_spine_bundles_chart_domain
  ON bodha_spine_bundles(chart_id, domain);

COMMENT ON TABLE bodha_spine_bundles IS
  'W5 Lane L5 (RETRIEVAL_IMPLEMENTATION_MASTER_BRIEF §E W5 / RETRIEVAL_PLANE_ELEVATION_PLAN '
  '§8 item 11): persisted, per-chart/ayanamsha/domain "spine bundle" — the pre-joined '
  'signal → activation windows → phala anchors → calibration chain — computed post-build '
  'and served as a fast-path read instead of a live 4-capability fan-out on every request. '
  'Delete-then-insert per (chart_id, ayanamsha_id, domain), never accreted (§N.3).';

COMMENT ON COLUMN bodha_spine_bundles.source_asset_marker IS
  'MAX(asset_throughput.last_built_at) across bo_laksana/ka_kalasutra/ph_nimitta/mi_pramana '
  'at computation time — the staleness marker a reader compares against the CURRENT max to '
  'decide whether this row is still fresh or must be recomputed.';

COMMIT;

-- DOWN:
-- BEGIN;
-- DROP TABLE IF EXISTS bodha_spine_bundles;
-- COMMIT;
