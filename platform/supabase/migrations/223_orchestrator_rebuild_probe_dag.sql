-- 223_orchestrator_rebuild_probe_dag.sql
-- Orchestrator Convergence Phase 4 — generic rebuild-on-probe-fail metadata +
-- the real L1 Gaṇita depends_on DAG. Surgical migration (no bulk/auto runner).
--
-- (1) Two genuinely-new registry columns power the orchestrator's only new
--     primitive: a metadata-driven verify-then-conditionally-regenerate path that
--     works for BOTH L0 service probes AND L0 data-asset integrity checks. (2) A
--     has_substeps hint mirrors the code-derived heavy-writer sub-step capability.
--     (3) depends_on was [] for every GA asset (only ga_sensitive→bg_reference), so
--     the plan was correct only by sort_order luck; this sets the real edges so
--     topoSort + downstream-stale propagation are real.

-- ── 1. New columns (idempotent) ──────────────────────────────────────────────
ALTER TABLE asset_registry ADD COLUMN IF NOT EXISTS rebuild_on_probe_fail boolean NOT NULL DEFAULT false;
ALTER TABLE asset_registry ADD COLUMN IF NOT EXISTS integrity_check_sql   text;
ALTER TABLE asset_registry ADD COLUMN IF NOT EXISTS has_substeps          boolean NOT NULL DEFAULT false;

COMMENT ON COLUMN asset_registry.rebuild_on_probe_fail IS
  'When true, the orchestrator runs this asset''s probe/integrity check first; GREEN → skip, FAIL → regenerate ONLY this asset via its registered writer → re-probe (Orchestrator Convergence Phase 4).';
COMMENT ON COLUMN asset_registry.integrity_check_sql IS
  'Optional SQL for a DATA asset''s health check; returns a single row whose first column is truthy when healthy. Service assets use health_probe instead.';
COMMENT ON COLUMN asset_registry.has_substeps IS
  'Hint that the asset''s writer is chunked (heavy). The actual sub-step list is code-derived from writer.plan_substeps(); this only lets the cockpit/planner know before invoking.';

-- ── 2. Heavy writers declare sub-steps ───────────────────────────────────────
UPDATE asset_registry SET has_substeps = true WHERE asset_id IN ('ga_dashas', 'ga_vargas');

-- ── 3. Backfill the real L1 Gaṇita DAG ───────────────────────────────────────
-- Root: ga_positions (graha positions) stays []. Everything computational depends
-- on it; ga_structural is the synthesis layer over the GA3-GA7 computational
-- assets; ga_sade_sati + ga_tajaka consume positions + dashas (+ structural).
UPDATE asset_registry SET depends_on = ARRAY['ga_positions']::text[]                WHERE asset_id = 'ga_strength';
UPDATE asset_registry SET depends_on = ARRAY['ga_positions']::text[]                WHERE asset_id = 'ga_vargas';
UPDATE asset_registry SET depends_on = ARRAY['ga_positions']::text[]                WHERE asset_id = 'ga_panchanga';
UPDATE asset_registry SET depends_on = ARRAY['ga_positions', 'bg_reference']::text[] WHERE asset_id = 'ga_sensitive';
UPDATE asset_registry SET depends_on = ARRAY['ga_positions']::text[]                WHERE asset_id = 'ga_dashas';
UPDATE asset_registry SET depends_on =
  ARRAY['ga_positions', 'ga_strength', 'ga_panchanga', 'ga_sensitive', 'ga_vargas', 'ga_dashas']::text[]
  WHERE asset_id = 'ga_structural';
UPDATE asset_registry SET depends_on =
  ARRAY['ga_positions', 'ga_strength', 'ga_panchanga', 'ga_vargas', 'ga_dashas', 'ga_structural']::text[]
  WHERE asset_id = 'ga_sade_sati';
UPDATE asset_registry SET depends_on = ARRAY['ga_positions', 'ga_dashas']::text[]   WHERE asset_id = 'ga_tajaka';

-- ── 4. Populate estimated_seconds (planner warns on long assets; NULL = unknown) ─
UPDATE asset_registry SET estimated_seconds = 2400 WHERE asset_id = 'ga_dashas';
UPDATE asset_registry SET estimated_seconds = 600  WHERE asset_id = 'ga_vargas';
UPDATE asset_registry SET estimated_seconds = 120  WHERE asset_id IN ('ga_sensitive', 'ga_structural', 'ga_sade_sati');
UPDATE asset_registry SET estimated_seconds = 60   WHERE asset_id IN ('ga_positions', 'ga_strength', 'ga_panchanga', 'ga_tajaka')
                                                      AND estimated_seconds IS NULL;
