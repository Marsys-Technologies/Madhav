-- Migration 1095 — build_run_assets: separate blocked-from-failed at the source
-- (Nirmāṇa engine packet B1 — "Cascade reads as one cause, N blocked")
--
-- Before this migration, a dependent asset skipped because an upstream failed/was
-- blocked (runner.py::_mark_asset_blocked) was recorded IDENTICALLY to a genuine
-- writer failure: state='error' in both asset_throughput and build_run_assets, with
-- the ONLY distinguishing signal being free-text prose in the `error` column
-- ("BLOCKED: upstream dependency(ies) <X> did not complete..."). No structured field
-- anywhere recorded which asset was the immediate blocker, and every failure-counting
-- surface (cockpit badges, the run-level banner, the governance census) therefore
-- counted a 20-asset cascade from one root failure as 20 failures.
--
-- What this migration does (Decision 1, B1_before_20260926T173931Z.json §3):
--   1. Adds ONE new nullable column, build_run_assets.blocked_by_asset_id, for the
--      immediate blocking asset id(s) (comma-joined when more than one, matching the
--      existing `error` message's own join style). PROSPECTIVE-ONLY — see below for
--      why historical rows are deliberately left NULL here.
--   2. Reclassifies (Decision 3) the `disposition` of historical rows whose `error`
--      text already carries the engine's own literal 'BLOCKED:' prefix, EXCLUDING the
--      53 rows where that prefix was itself a mislabeled writer-timeout (a root cause,
--      not a cascade — see Packet B1 Decision 2 / runner.py execute_dag, fixed in the
--      same commit as this migration). Setting disposition to match text the engine
--      itself already wrote is structuring an existing record, not inventing one.
--
-- Deliberately NOT done, and why (verdict, §6 of the before-measurement):
--   - No new `state` value. A3's own precedent (_terminalize_diverged_assets docstring)
--     already ruled that a cascade victim stays at state='error' — the stronger,
--     already-monitored signal — and every state-keyed surface keeps matching.
--     C-6 (review B1_review_20260926T182200Z.md): this decision is load-bearing for a
--     SECOND reason beyond the one above. asset_census.py's build_history() tallies
--     per-state counters (d[state] += 1) keyed by the literal state string, and
--     d['skipped'] already collides with the permitted state value 'skipped'
--     (pre-existing, not introduced by this migration). This migration's own new
--     d['blocked'] counter (disposition-derived, not state-derived) is safe from that
--     SAME collision class only because no state value literally named 'blocked' exists
--     — verified: build_run_assets_state_check permits exactly
--     queued/building/complete/skipped/error/aborted. If a later migration ever adds a
--     'blocked' STATE value, asset_census.py's `genuine_error = h["error"] - h["blocked"]`
--     arithmetic would silently double-count against the same key and go wrong. Recorded
--     here, next to the decision it depends on, so the two are not read independently by
--     whoever reopens this question next.
--   - `disposition='blocked_dependency'` needed NO constraint change: it was already
--     present in build_run_assets_disposition_check (provisioned, zero rows, zero code
--     references before this migration) — the CHECK constraint is untouched here.
--   - blocked_by_asset_id is NOT backfilled for historical rows. Of the 1,183 genuine
--     (non-timeout) BLOCKED rows' 2,856 blocking-dependency edges, 2,545 (89%) name
--     ANOTHER blocked asset rather than a root cause, only 223 (8%) name a real
--     terminal root directly, and 88 (3%) name an id absent from that run's
--     build_run_assets entirely. Recovering a true root asset id requires a multi-hop
--     graph walk the engine never performed or stored as a decision, and that walk
--     dead-ends outright for the 3%. Populating this column historically would mean
--     inventing/reconstructing data the code never asserted — CLAUDE.md §N.7 item 6
--     ("an honest null beats an invented judgment") and the campaign's own
--     never-invent-data constraint both rule this out. The column is written only by
--     runs that execute AFTER this migration + the accompanying runner.py fix land.
--
-- Idempotency: the backfill UPDATE is guarded by `disposition IS NULL`, so re-running
-- this migration changes zero rows the second time (every row it would touch already
-- has disposition set from the first run). ADD COLUMN uses IF NOT EXISTS.
--
-- The 7 anomalous rows (6x bo_laksana_rerank, 1x ka_sangam — state='complete' with
-- stale 'BLOCKED:' text from a pre-existing, separate bug: build_run_assets' own
-- state='complete' UPDATE statements in asset_runner.py never clear `error`, unlike
-- their asset_throughput counterparts which clear last_error) are UNTOUCHED by this
-- backfill: the WHERE clause requires state='error', which excludes all 7 outright,
-- independent of the timeout-text exclusion. That pre-existing bug is registered as
-- A2b-5 and is explicitly out of scope for this migration.
--
-- Numbered max+1 scanned across BOTH platform/migrations/ and platform/supabase/migrations/
-- at execution time (max found: 1094, platform/supabase/migrations/
-- 1094_asset_throughput_duration_seconds.sql; platform/migrations/ max was 1070).
-- migration_number_guard.ts's own docstring names platform/supabase/migrations/ as
-- "the active sequence -- all new migrations go here", matching where 1092-1094 landed.

ALTER TABLE build_run_assets
    ADD COLUMN IF NOT EXISTS blocked_by_asset_id text;

COMMENT ON COLUMN build_run_assets.blocked_by_asset_id IS
    'The immediate upstream asset_id(s) that caused this row to be blocked (comma-joined '
    'when more than one), written ONLY by _mark_asset_blocked() at the moment a genuine '
    'dependency cascade or deadlock is recorded (runner.py execute_dag lines ~633/~653). '
    'NEVER written for a writer-timeout root cause (execute_dag''s timeout branch is a '
    'distinct, non-blocking code path as of Packet B1 -- see _mark_asset_timeout()) and '
    'NEVER backfilled for historical rows (migration 1095''s own header explains why a '
    'true root asset id is not recoverable from the stored error text for the ~92% of '
    'historical blocking edges that do not name a terminal root directly). NULL means '
    'either: this row was never blocked, or it was blocked before this column existed. '
    'Read alongside disposition=''blocked_dependency'' -- this column is prospective '
    'detail for that disposition value, not a replacement carrier.';

-- Decision 3 backfill: reclassify only rows whose `error` text already carries the
-- engine's OWN literal 'BLOCKED:' prefix (genuine dependency/deadlock cascade), never
-- the timeout-mislabeled subset. Guarded by `disposition IS NULL` for idempotency.
UPDATE build_run_assets
SET disposition = 'blocked_dependency'
WHERE state = 'error'
  AND disposition IS NULL
  AND error LIKE 'BLOCKED:%'
  AND error NOT LIKE '%timeout:%s%';
