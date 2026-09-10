-- 569_sampurti_r0_kshetra_dep_fix.sql
-- SAMPŪRTI campaign, R0 gate packet.
--
-- RB-1: Remove the retired ka_gochara_sweep dependency edge from ka_kshetra.
--
-- WHY: Migration 563 (W6.4 UTK-R2) set ka_gochara_sweep's catalog_status =
-- 'RETIRED' and asset_throughput.state to 'stale'. The orchestrator's
-- dependency seeder refuses non-lit states — any ka_kshetra dispatch now
-- deadlocks at preflight waiting for an asset that will never become lit.
-- The v1 sweep DATA and protection remain intact; only the DAG edge is
-- removed. ka_kshetra's stage4 crosscheck reads continue via its own
-- load_legacy_crosscheck query (generation-seam guarded by PG-31's
-- COALESCE filter — PR #1193, merged to sampurti/integration).
--
-- DOWN (undo path for ops reference — not executed by migrate.ts):
--   UPDATE asset_registry
--   SET depends_on = array_append(depends_on, 'ka_gochara_sweep')
--   WHERE asset_id = 'ka_kshetra'
--     AND NOT (depends_on @> ARRAY['ka_gochara_sweep']);
--
-- Idempotent: safe to run multiple times (no-op if edge already absent).

BEGIN;

UPDATE asset_registry
SET depends_on = array_remove(depends_on, 'ka_gochara_sweep')
WHERE asset_id = 'ka_kshetra'
  AND depends_on @> ARRAY['ka_gochara_sweep'];

COMMIT;
