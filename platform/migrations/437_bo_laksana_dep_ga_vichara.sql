-- Migration 437: bo_laksana gains ga_vichara as a declared dependency
-- Created: 2026-07-15

-- D-1.5a wave gate finding: bo_laksana.py reads chart_vichara (ga_vichara's
-- output table) directly via _load_vichara_valence / _load_varga_ratification /
-- _load_vichara_divergence_signals, but asset_registry.depends_on for bo_laksana
-- never included 'ga_vichara' -- so the orchestrator's DEP-ASSERT never enforced
-- build ordering between them. This was already known and explicitly DEFERRED in
-- migration 367_bo_laksana_ratification_valence_source.sql ("the brief 'bo_laksana
-- .depends_on must gain ga_vichara' is DEFERRED... land the depends_on edge in
-- that same migration" as ga_vichara's own registration in
-- 435_ga_vichara.sql) but the follow-up never actually landed.
--
-- Confirmed live impact: on chart 482012f1, bo_laksana last built at
-- 2026-07-14 22:05:07 UTC while ga_vichara's corrected data (D-1.5a Lane A-alpha
-- fix) wasn't ready until 2026-07-14 23:10:50 UTC -- over an hour later. Without
-- the dependency edge, bo_laksana was free to run (and did run) against stale/
-- incomplete ga_vichara data, serving wrong valence for at least one live
-- specimen (Mars aspect on house 2, chart 482012f1) despite chart_vichara's own
-- data being correct.
--
-- Idempotent: array_append guarded by a NOT (already present) check.

BEGIN;

UPDATE asset_registry
SET depends_on = array_append(depends_on, 'ga_vichara')
WHERE asset_id = 'bo_laksana'
  AND NOT ('ga_vichara' = ANY(depends_on));

COMMIT;
