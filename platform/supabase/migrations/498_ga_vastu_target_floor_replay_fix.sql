-- Migration 498: repair the ga_vastu target_floor REPLAY GAP left by migration 294
--
-- SAMĀPTI integrity-residual TASK 2. Not a behaviour change: production already holds the
-- correct value. This closes a fresh-database REPLAYABILITY hole.
--
-- WHAT WAS FOUND
-- `294_ga_vastu_target_floor.sql` is one of the 25 disclosed sha256 residuals (DVA RULING 73) and
-- was one of the 4 filed as `cause: UNDER-INVESTIGATION` — "well-formed sha256, no matching git
-- blob anywhere in history". Investigating its EFFECT rather than its bytes identified the drift
-- positively:
--
--   the committed file says   WHERE asset_id = 'ga_vastu_planet_direction_map'   <- a TABLE name
--   the asset's actual id is  'ga_vastu'                                          (see mig 287)
--
-- So the on-disk 294 matches zero rows: it is a no-op. Yet production has
-- asset_registry.target_floor = 40 for 'ga_vastu' — exactly what 294's own header says it intends
-- (correcting 45 -> 40, since Ketu has no classical Vastu direction and the writer emits
-- 8 grahas x 5 ayanamshas = 40 rows). No other migration anywhere in either directory sets that
-- value: 287 inserts 45, and 381's floor calibration does not touch ga_vastu.
--
-- The only consistent explanation is that the version APPLIED on 2026-06-17 carried the correct
-- predicate and the version COMMITTED (2026-06-17T13:37 IST, ~8 minutes later) carried the broken
-- one. The recorded sha256 is of content that was never committed, which is why no git blob
-- matches it — verified by sweeping all 68,303 objects in the repository object database
-- (22,112 blobs, reachable AND dangling), under every filename, plus LF-normalisation.
--
-- CONSEQUENCE (the real defect, previously invisible)
-- Replaying every migration onto a fresh database does NOT reproduce production: ga_vastu would
-- be left at target_floor = 45. This migration is the forward fix.
--
-- WHY A NEW MIGRATION AND NOT AN EDIT TO 294
-- 294 is already applied in production. Editing it is forbidden (CLAUDE.md; MigrationHashMismatch
-- Error's own instruction: "either revert to the content that was applied, or create a NEW
-- migration file to carry the intended change forward"), and would additionally break its pinned
-- disclosure entry in scripts/ci/migration_hash_disclosed_residuals.json. 294 stays exactly as it
-- is, no-op and all; this file carries the intent forward.
--
-- EFFECT ON PRODUCTION: none. target_floor is already 40 (verified read-only via
-- `SELECT target_floor FROM asset_registry WHERE asset_id = 'ga_vastu'` -> 40, 2026-07-30).
-- This is a no-op there and a correction on any fresh replay. Idempotent; safe to re-run.
--
-- Per CLAUDE.md §N.4: floors are aspirational, set to the achieved count — 40 is measured, not
-- fabricated.

BEGIN;

UPDATE asset_registry
SET target_floor = 40
WHERE asset_id = 'ga_vastu'
  AND (target_floor IS DISTINCT FROM 40);

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   UPDATE asset_registry SET target_floor = 45 WHERE asset_id = 'ga_vastu';
--   COMMIT;
-- =============================================================================
