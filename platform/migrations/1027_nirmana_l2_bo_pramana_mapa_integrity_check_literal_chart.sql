-- Migration 1027: bo_pramana_mapa integrity_check_sql — inline literal canonical chart_id
-- Created: 2026-09-11
--
-- Context (issue #2579): migration 1025 rewrote bo_pramana_mapa's integrity_check_sql to be
-- chart-scoped using Postgres native `$1` bind placeholders (fix for #2566's cross-chart
-- contamination bug). But the orchestrator's `_probe_asset`
-- (platform/python-sidecar/pipeline/orchestrator/asset_runner.py) calls
-- `cur.execute(integrity_check_sql)` with NO bind parameters for every asset in the registry —
-- a live-DB audit (2026-09-11) confirmed bo_pramana_mapa is the ONLY row among 130+
-- integrity_check_sql rows using `$1`. Postgres correctly rejects the unbound placeholder
-- ("there is no parameter $1"), caught by _probe_asset's bare except and misreported as a plain
-- integrity failure.
--
-- Fix: inline the literal canonical chart_id UUID (CLAUDE.md §B — this campaign targets exactly
-- one native/chart) instead of using $1. This is a DB-row-only, migration-only change (no
-- orchestrator/frozen-runtime code touched, no deploy wait — live the moment this migration
-- applies, per this campaign's own established migration-only-is-live rule).

BEGIN;

UPDATE asset_registry
SET integrity_check_sql = replace(
  integrity_check_sql,
  '$1',
  '''482012f1-710e-4a25-994a-93821f5871aa''::uuid'
)
WHERE asset_id = 'bo_pramana_mapa'
  AND integrity_check_sql LIKE '%$1%';

COMMIT;
