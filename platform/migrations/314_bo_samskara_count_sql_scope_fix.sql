-- Migration 314: fix bo_samskara count_sql and scope
--
-- bodha_signal_embeddings has no chart_id column — MSR signal embeddings are
-- chart-agnostic global reference data (one embedding per signal, not per chart).
-- The registered count_sql erroneously included `WHERE chart_id = $1`, which
-- caused a "column chart_id does not exist" error in the cockpit stats route.
-- Scope was also wrong (per_chart → global) for the same reason.

UPDATE asset_registry
SET
  count_sql = 'SELECT count(*) FROM bodha_signal_embeddings',
  scope     = 'global'
WHERE asset_id = 'bo_samskara';
