-- Migration 426: extend build_runs.scope CHECK to include 'asset_set'.
-- Created: 2026-07-08
--
-- Adds a targeted build scope: an 'asset_set' run builds a caller-chosen SUBSET of
-- assets for one chart (scope_target carries a comma-separated asset_id list). The
-- FROZEN orchestrator WriterBase contract is untouched — only the build-plan resolver
-- (plan.ts) + the /api/cockpit/runs route + this scope domain change.
--
-- 171_build_runs.sql defined build_runs.scope with an inline CHECK
--   CHECK (scope IN ('global','layer','asset'))
-- which Postgres auto-named build_runs_scope_check. We drop + recreate it (named,
-- idempotent) to add 'asset_set'. Surgical + transactional; DOWN block below.

BEGIN;

ALTER TABLE build_runs DROP CONSTRAINT IF EXISTS build_runs_scope_check;
ALTER TABLE build_runs ADD CONSTRAINT build_runs_scope_check
  CHECK (scope IN ('global','layer','asset','asset_set'));

COMMIT;

-- DOWN:
-- BEGIN;
-- ALTER TABLE build_runs DROP CONSTRAINT IF EXISTS build_runs_scope_check;
-- ALTER TABLE build_runs ADD CONSTRAINT build_runs_scope_check
--   CHECK (scope IN ('global','layer','asset'));
-- COMMIT;
-- (Reverting requires no 'asset_set' rows to exist, or the re-add will fail loudly — safe.)
