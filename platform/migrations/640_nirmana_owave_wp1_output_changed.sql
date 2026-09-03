-- 640_nirmana_owave_wp1_output_changed.sql
--
-- NIRMANA_UNIFIED_ELEVATION_PLAN_v2_0.md §3.1 (O-wave WP-1, truthful invalidation).
-- Transaction ownership belongs to platform/scripts/migrate.ts.
--
-- Records, per (run_id, asset_id), whether a data writer's completion actually
-- produced a different output_digest than the previous complete provenance
-- receipt. staleness.py's delta-directional propagation reads this column from
-- a fresh connection in the orchestrator's on_complete callback (it cannot see
-- the writer's own transaction-local state) to decide whether to mark
-- downstream assets 'stale' or emit a refreshed_no_delta event instead.
--
-- NULL is the honest "no signal recorded" default (probes/service assets that
-- never capture a data receipt, or any row written before this migration) --
-- the propagation code treats NULL the same as TRUE (fail-open: never assume
-- no-delta on missing evidence, per CLAUDE.md §N.8 / plan §3.1 point 4).

ALTER TABLE build_run_assets
    ADD COLUMN IF NOT EXISTS output_changed BOOLEAN;

COMMENT ON COLUMN build_run_assets.output_changed IS
    'O-wave WP-1: TRUE when this run''s completion produced a different output_digest than the prior complete receipt; FALSE when it matched exactly (safe to skip downstream staleness propagation); NULL when no comparison was made (fail-open, treated as changed).';

-- Forward reversal (safe at any time -- the column is additive and read-only
-- outside this migration's writers): DROP COLUMN build_run_assets.output_changed.
