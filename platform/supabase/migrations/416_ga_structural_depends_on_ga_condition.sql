-- Migration 416: restore the ga_structural -> ga_condition DAG edge
-- (BA-P3 FIX: wave-parallel chart_facts writer lock-contention).
--
-- Root cause (BA Phase-3 Abhinandan diagnostic, 2026-07-06): ga_condition and
-- ga_structural BOTH delete-then-insert the SAME two chart_facts categories
-- (graha_avastha_lajjitadi, graha_avastha_sayanadi). Their asset_registry
-- depends_on lists share upstreams (ga_positions, ga_vargas, ga_dashas) but
-- neither depends on the other, so the wave-parallel scheduler places them in
-- the same wave. Running concurrently, ga_condition's idempotency DELETE on
-- those shared categories blocks on ga_structural's uncommitted row locks (the
-- orchestrator holds each asset's transaction open until the asset completes)
-- -> 30s statement_timeout -> "canceling statement ... while deleting tuple in
-- relation chart_facts" -> failed L1 that blocked the entire L2-L5 DAG. Serial
-- execution (ORCHESTRATOR_WORKER_LIMIT=1) avoided it by never running the two
-- concurrently; this migration is the durable fix that keeps everything else
-- parallel.
--
-- This is a REGISTRY DRIFT bug: the ga_structural WRITER CLASS already declares
-- `depends_on = ['ga_condition', 'ga_nakshatra']` in code, but the scheduler
-- reads asset_registry.depends_on from the DB (runner.py), and that row was
-- missing the ga_condition edge. This migration realigns the DB with the
-- already-intended code dependency, serializing exactly the one overlapping
-- pair (ga_structural runs after ga_condition) while all other assets stay
-- parallel. No cycle: ga_condition depends on [ga_positions, ga_vargas,
-- ga_dashas] and never on ga_structural.

BEGIN;

UPDATE asset_registry
SET depends_on = (
  SELECT array_agg(DISTINCT d ORDER BY d)
  FROM unnest(depends_on || ARRAY['ga_condition']) AS d
)
WHERE asset_id = 'ga_structural'
  AND NOT ('ga_condition' = ANY(depends_on));

COMMIT;

-- DOWN:
-- UPDATE asset_registry
-- SET depends_on = array_remove(depends_on, 'ga_condition')
-- WHERE asset_id = 'ga_structural';
