-- Migration 584: remedy_review_queue.remedy_id unique index (F-187)
-- Created: 2026-08-22
--
-- Root cause: platform/python-sidecar/brahmagyan/l0_remedy_loader.py
-- insert_to_review_queue() (:122-165) issues
--   INSERT INTO remedy_review_queue (...) VALUES (...)
--   ON CONFLICT (remedy_id) DO UPDATE SET
--       rejection_reason = EXCLUDED.rejection_reason,
--       review_status = 'pending'
-- but remedy_review_queue (created by 081_l0fr_schema.sql:126-163) has no
-- unique index or constraint on remedy_id -- its PK is the surrogate `id`
-- column, and the table's only two indexes (idx_remedy_review_status,
-- idx_remedy_review_planet) are both non-unique. Postgres requires a unique
-- index/constraint matching an ON CONFLICT inference clause; with none
-- present, every call raises 42P10 ("there is no unique or exclusion
-- constraint matching the ON CONFLICT specification"). The function
-- re-raises (does not swallow), so the error propagates through
-- load_remedies()'s tantric gate -> bg_remedies.py's run(ctx) -> the whole
-- bg_remedies L0 build fails, on exactly the rows the gate exists to
-- handle. F-183's merged fix (PR #1437) unmasked this path; it is now
-- reachable in production.
--
-- Natural key: remedy_id alone. The existing
-- `DO UPDATE SET rejection_reason = EXCLUDED.rejection_reason` states
-- overwrite-on-remedy_id semantics unambiguously -- a wider key such as
-- (remedy_id, rejection_reason) would let one remedy accumulate a row per
-- distinct rejection reason, contradicting the code's own intent. Do not
-- widen the key.
--
-- Not a general problem: the sibling brahma_remedy_corpus.remedy_id is
-- already TEXT NOT NULL UNIQUE (platform/migrations/ws2_l0_remedy_corpus.sql),
-- so insert_to_corpus's ON CONFLICT (:183/:204) already works correctly.
-- The defect is isolated to remedy_review_queue.
--
-- SEQUENCING -- duplicate pre-flight (must return zero rows before this
-- migration is applied; the ON CONFLICT path has never successfully
-- executed since this table's origin commit, so duplicates are not
-- expected, but verify, do not assume):
--   SELECT remedy_id, count(*) FROM remedy_review_queue
--     GROUP BY 1 HAVING count(*) > 1;
-- Verified 2026-08-22 against production (via the project's postgres MCP
-- connection, database `amjis`): zero rows returned, and the table itself
-- currently holds zero total rows -- consistent with this ON CONFLICT path
-- never having successfully executed before now.
--
-- Lock note: this repo's migration runner (platform/scripts/migrate.ts)
-- wraps every migration file in BEGIN/COMMIT, and CREATE INDEX CONCURRENTLY
-- cannot run inside a transaction block -- migrations 359/414/415/429 hit
-- the same constraint and were deliberately written without CONCURRENTLY
-- for that reason. Following that precedent: this is a plain
-- (non-concurrent) index build, which takes a brief SHARE lock blocking
-- writes to remedy_review_queue for the build's duration -- acceptable at
-- current scale (table is currently empty), index-only, no data rewrite,
-- fully idempotent (IF NOT EXISTS).

BEGIN;

CREATE UNIQUE INDEX IF NOT EXISTS ux_remedy_review_queue_remedy_id
  ON remedy_review_queue (remedy_id);

COMMENT ON INDEX ux_remedy_review_queue_remedy_id IS
  'F-187: matches insert_to_review_queue()''s ON CONFLICT (remedy_id) inference clause in platform/python-sidecar/brahmagyan/l0_remedy_loader.py -- without this index the upsert raises 42P10.';

DO $f187_verify$
DECLARE
  v_index_exists boolean;
BEGIN
  SELECT EXISTS (
    SELECT 1 FROM pg_indexes
     WHERE tablename = 'remedy_review_queue'
       AND indexname = 'ux_remedy_review_queue_remedy_id'
  ) INTO v_index_exists;

  IF NOT v_index_exists THEN
    RAISE EXCEPTION 'F-187: unique index was not created';
  END IF;

  RAISE NOTICE 'F-187 applied: ux_remedy_review_queue_remedy_id present on remedy_review_queue(remedy_id)';
END $f187_verify$;

COMMIT;

-- DOWN:
-- BEGIN;
-- DROP INDEX IF EXISTS ux_remedy_review_queue_remedy_id;
-- COMMIT;

-- §N.4: surgical, verified. NEVER edit this file after it has been applied.
