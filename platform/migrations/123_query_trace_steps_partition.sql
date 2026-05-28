-- 123_query_trace_steps_partition.sql
-- Convert `query_trace_steps` from a regular table to a Postgres declarative
-- RANGE-partitioned table by `created_at` (monthly partitions). v1.2 follow-on
-- patch session (post-seal operator cleanup; OPERATOR_CLEANUP_V1_2_PATCH_BRIEF.md §2(d)).
--
-- Targets queried in the patch brief:
--   * chart_facts        HASH (chart_id)  — DEFERRED (100% rows have chart_id NULL).
--   * l25_msr_signals    HASH (chart_id)  — DEFERRED (same).
--   * query_trace_steps  RANGE (created_at) monthly — THIS migration.
--   * mcp_predictions    RANGE (logged_at) monthly  — DEFERRED (inbound FK from
--       mcp_prediction_outcomes blocks composite PK extension; n=9 rows is
--       zero partition value).
--
-- Strategy (declarative partitioning, idempotent abort-on-mismatch):
--   1. Snapshot live row count.
--   2. Create `query_trace_steps_new` with the same column shape and the
--      partition-required composite PK `(id, created_at)` (Postgres requires
--      the partition key in every PRIMARY KEY / UNIQUE constraint).
--   3. Create monthly partitions covering 2026-04 → 2027-04 (12 forward + the
--      current bucket) plus a DEFAULT partition for anything outside the range
--      (defensive — should never have rows today).
--   4. Recreate the non-PK indexes (partition-local) so existing query plans
--      keep working.
--   5. INSERT live data into the partitioned table; ANALYZE.
--   6. Verify row count matches — abort otherwise.
--   7. Atomic rename swap inside the transaction:
--        query_trace_steps     → query_trace_steps_pre_partition_archive
--        query_trace_steps_new → query_trace_steps
--      The archive is dropped in a follow-on commit (defense window per the
--      patch brief: keep archives for ONE green production day).
--
-- Forward compat:
--   * No FKs reference `query_trace_steps` (verified pre-author).
--   * The composite PK `(id, created_at)` extends the prior PK `(id)`; lookups
--     by `id` alone still hit the per-partition index efficiently (created_at
--     is range-filtered by partition routing).
--
-- ROLLBACK: see end of file. The pre-Phase-C snapshot + the v1.2 pre-flight
-- snapshot (`pre-v1.2-patch-cleanup`) are the operator-grade rollback anchors.

BEGIN;

-- ─── 0. Pre-flight: snapshot the live row count to verify post-copy ─────────
DO $$
DECLARE
  v_pre_count BIGINT;
BEGIN
  SELECT count(*) INTO v_pre_count FROM query_trace_steps;
  RAISE NOTICE 'query_trace_steps pre-partition row count: %', v_pre_count;
  -- Stash for the verification step via a temp table.
  CREATE TEMP TABLE _qts_pre (n BIGINT) ON COMMIT DROP;
  INSERT INTO _qts_pre VALUES (v_pre_count);
END $$;

-- ─── 1. Create the partitioned shape ────────────────────────────────────────
CREATE TABLE query_trace_steps_new (
  id               uuid                       NOT NULL,
  query_id         uuid                       NOT NULL,
  conversation_id  uuid                       NULL,
  step_seq         smallint                   NOT NULL,
  step_name        text                       NOT NULL,
  step_type        text                       NOT NULL,
  status           text                       NOT NULL,
  started_at       timestamp with time zone   NOT NULL,
  completed_at     timestamp with time zone   NULL,
  latency_ms       integer                    NULL,
  parallel_group   text                       NULL,
  data_summary     jsonb                      NOT NULL,
  payload          jsonb                      NOT NULL,
  created_at       timestamp with time zone   NOT NULL,
  user_id          text                       NULL,
  mcp_tool         text                       NULL,
  PRIMARY KEY (id, created_at)
)
PARTITION BY RANGE (created_at);

-- ─── 2. Monthly partitions: 2026-04 → 2027-04 + DEFAULT ─────────────────────
CREATE TABLE query_trace_steps_2026_04 PARTITION OF query_trace_steps_new
  FOR VALUES FROM ('2026-04-01') TO ('2026-05-01');
CREATE TABLE query_trace_steps_2026_05 PARTITION OF query_trace_steps_new
  FOR VALUES FROM ('2026-05-01') TO ('2026-06-01');
CREATE TABLE query_trace_steps_2026_06 PARTITION OF query_trace_steps_new
  FOR VALUES FROM ('2026-06-01') TO ('2026-07-01');
CREATE TABLE query_trace_steps_2026_07 PARTITION OF query_trace_steps_new
  FOR VALUES FROM ('2026-07-01') TO ('2026-08-01');
CREATE TABLE query_trace_steps_2026_08 PARTITION OF query_trace_steps_new
  FOR VALUES FROM ('2026-08-01') TO ('2026-09-01');
CREATE TABLE query_trace_steps_2026_09 PARTITION OF query_trace_steps_new
  FOR VALUES FROM ('2026-09-01') TO ('2026-10-01');
CREATE TABLE query_trace_steps_2026_10 PARTITION OF query_trace_steps_new
  FOR VALUES FROM ('2026-10-01') TO ('2026-11-01');
CREATE TABLE query_trace_steps_2026_11 PARTITION OF query_trace_steps_new
  FOR VALUES FROM ('2026-11-01') TO ('2026-12-01');
CREATE TABLE query_trace_steps_2026_12 PARTITION OF query_trace_steps_new
  FOR VALUES FROM ('2026-12-01') TO ('2027-01-01');
CREATE TABLE query_trace_steps_2027_01 PARTITION OF query_trace_steps_new
  FOR VALUES FROM ('2027-01-01') TO ('2027-02-01');
CREATE TABLE query_trace_steps_2027_02 PARTITION OF query_trace_steps_new
  FOR VALUES FROM ('2027-02-01') TO ('2027-03-01');
CREATE TABLE query_trace_steps_2027_03 PARTITION OF query_trace_steps_new
  FOR VALUES FROM ('2027-03-01') TO ('2027-04-01');
CREATE TABLE query_trace_steps_2027_04 PARTITION OF query_trace_steps_new
  FOR VALUES FROM ('2027-04-01') TO ('2027-05-01');
CREATE TABLE query_trace_steps_default PARTITION OF query_trace_steps_new
  DEFAULT;

-- ─── 3. Recreate the non-PK indexes on the partitioned parent ────────────────
-- These propagate to existing partitions and to all future partitions.
CREATE INDEX query_trace_steps_new_user_id_idx
  ON query_trace_steps_new (user_id)
  WHERE user_id IS NOT NULL;

CREATE INDEX query_trace_steps_new_created_at_idx
  ON query_trace_steps_new (created_at DESC);

CREATE INDEX query_trace_steps_new_mcp_tool_idx
  ON query_trace_steps_new (mcp_tool)
  WHERE mcp_tool IS NOT NULL;

CREATE INDEX query_trace_steps_new_query_id_idx
  ON query_trace_steps_new (query_id, step_seq);

-- ─── 4. Copy data ───────────────────────────────────────────────────────────
INSERT INTO query_trace_steps_new (
  id, query_id, conversation_id, step_seq, step_name, step_type, status,
  started_at, completed_at, latency_ms, parallel_group, data_summary, payload,
  created_at, user_id, mcp_tool
)
SELECT
  id, query_id, conversation_id, step_seq, step_name, step_type, status,
  started_at, completed_at, latency_ms, parallel_group, data_summary, payload,
  created_at, user_id, mcp_tool
FROM query_trace_steps;

-- ─── 5. Verify row counts match ─────────────────────────────────────────────
DO $$
DECLARE
  v_pre  BIGINT;
  v_post BIGINT;
BEGIN
  SELECT n INTO v_pre FROM _qts_pre;
  SELECT count(*) INTO v_post FROM query_trace_steps_new;
  IF v_pre <> v_post THEN
    RAISE EXCEPTION 'partition row-count mismatch: pre=% post=%', v_pre, v_post;
  END IF;
  RAISE NOTICE 'partition row-count match OK: % rows.', v_post;
END $$;

ANALYZE query_trace_steps_new;

-- ─── 6. Atomic rename swap ──────────────────────────────────────────────────
-- 6a. Move the OLD indexes out of the way (Postgres keeps index names global,
--     so the new partition-parent indexes can't take the canonical names until
--     the old ones step aside). Same for the OLD PK constraint name.
ALTER INDEX query_trace_steps_pkey                RENAME TO query_trace_steps_pre_partition_archive_pkey;
ALTER INDEX idx_qts_user_id                       RENAME TO idx_qts_user_id_pre_partition_archive;
ALTER INDEX idx_query_trace_steps_created_at      RENAME TO idx_query_trace_steps_created_at_pre_partition_archive;
ALTER INDEX idx_query_trace_steps_mcp_tool        RENAME TO idx_query_trace_steps_mcp_tool_pre_partition_archive;
ALTER INDEX idx_query_trace_steps_query_id        RENAME TO idx_query_trace_steps_query_id_pre_partition_archive;

-- 6b. Rename the tables.
ALTER TABLE query_trace_steps RENAME TO query_trace_steps_pre_partition_archive;
ALTER TABLE query_trace_steps_new RENAME TO query_trace_steps;

-- 6c. Rename the NEW PK constraint + indexes to the canonical names.
ALTER TABLE query_trace_steps RENAME CONSTRAINT query_trace_steps_new_pkey TO query_trace_steps_pkey;
ALTER INDEX query_trace_steps_new_user_id_idx     RENAME TO idx_qts_user_id;
ALTER INDEX query_trace_steps_new_created_at_idx  RENAME TO idx_query_trace_steps_created_at;
ALTER INDEX query_trace_steps_new_mcp_tool_idx    RENAME TO idx_query_trace_steps_mcp_tool;
ALTER INDEX query_trace_steps_new_query_id_idx    RENAME TO idx_query_trace_steps_query_id;

COMMIT;

-- ─── ROLLBACK (manual operator action) ──────────────────────────────────────
-- BEGIN;
-- ALTER TABLE query_trace_steps RENAME TO query_trace_steps_rolled_back;
-- ALTER TABLE query_trace_steps_pre_partition_archive RENAME TO query_trace_steps;
-- DROP TABLE query_trace_steps_rolled_back CASCADE;
-- COMMIT;
