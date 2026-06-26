-- Migration 356: G2 — close hidden DAG edge bo_karanajala → bo_bimba
--
-- bo_karanajala reads bodha_cgm_nodes (produced by bo_bimba) to build CGM edges.
-- depends_on previously omitted bo_bimba, so topo-sort could schedule karanajala
-- before bimba → empty node_map → 0 CGM edges silently, build green.
--
-- Kept in exact agreement with asset_registry_seed.ts (anti-drift, per PR #304 lesson).
-- ON CONFLICT DO UPDATE is idempotent: safe to re-apply.

UPDATE asset_registry
SET depends_on = ARRAY['bo_laksana', 'bo_bimba']
WHERE asset_id = 'bo_karanajala';
