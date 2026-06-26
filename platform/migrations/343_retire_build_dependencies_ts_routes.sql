-- Migration 343: Document build_dependencies retirement progress (TS routes only)
--
-- Status: PARTIAL RETIREMENT — physical DROP deferred per ROOT_FILE_POLICY.
--
-- Completed (A3 / 2026-06-26):
--   • cascade-preview/route.ts rewritten to use asset_registry.depends_on
--   • cascade/route.ts rewritten to use asset_registry.depends_on
--   • data-readiness/route.ts rewritten to use asset_registry for asset list
--   • plan.test.ts comment updated
--
-- Remaining blocker (prevents full retirement):
--   • python-sidecar/pipeline/dispatcher.py still queries build_dependencies
--     (lines 34, 39, 191, 197) for forward-edge dep graph and category_prefix.
--     This is Python sidecar code; repointing it to asset_registry requires
--     a coordinated Python-side change. Raise with native before touching dispatcher.
--
-- When dispatcher.py is repointed: add a follow-up migration to DROP TABLE build_dependencies.
-- No schema change in this migration — data-only comment record.

SELECT 1; -- no-op; retirement comment only
