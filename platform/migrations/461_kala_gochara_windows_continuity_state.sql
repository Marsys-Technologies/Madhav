-- Migration 461: kala_gochara_windows.continuity_state — DB-driven segment consolidation
-- =============================================================================
-- D-5 Gochara-Chitra RED-C fix v4 (2026-07-20, third independent verification).
--
-- WHY: earlier RED-C fix attempts (v1: cross-substep runtime carry; v2/v3: a
-- bounded lookback/lookahead re-evaluation scan past a chunk's own boundary)
-- were both REJECTED on independent verification for the same underlying
-- reason -- they anchor correctness to something a chunk does AT RUNTIME
-- relative to ITS OWN position (a "prior substep" that may not have run yet,
-- or a scan distance that may not reach a true edge for a long enough
-- episode) rather than to durable, already-committed state. v2/v3's bounded
-- scan also risked approaching the writer's own `writer_timeout_seconds`
-- budget for a chunk deep inside a very long episode.
--
-- WHAT (v4): each year-substep computes ONLY its own strictly-bounded local
-- segment (zero cross-boundary compute, ~365 evaluations max, no scan-
-- distance risk at ANY episode length) and records two booleans -- was the
-- segment active at its own leftmost grid day, was it active at its own
-- rightmost grid day. A separate, idempotent, DB-driven consolidation step
-- (writer.py `_consolidate_interval_segment`) looks up whether an ALREADY-
-- COMMITTED adjacent segment exists (by exact calendar-date adjacency on
-- this column, not by runtime dispatch-order assumption) and merges chains
-- into one served row via delete-then-reinsert (the SAME idempotency
-- pattern already used elsewhere in this codebase, per §N.3). Because the
-- merge step only ever reads what is ACTUALLY in the database, it is
-- correct under ANY dispatch order -- numeric, lexical, specimen-priority-
-- shuffled, or fully random/reversed -- with no scan-distance dependency at
-- all: merge cost is proportional to the number of already-committed
-- adjacent segments (small, O(1) per merge), never to how far a signal
-- might extend.
--
-- Additive-only, idempotent (ADD COLUMN IF NOT EXISTS). No destructive ops.
-- NULL for point/chain-shaped rows (this mechanism is interval-shape-only;
-- point/chain rows are single-day and never span a chunk boundary the way
-- an interval-shaped elevated-hazard span can).

BEGIN;

ALTER TABLE kala_gochara_windows
    ADD COLUMN IF NOT EXISTS continuity_state JSONB;

COMMENT ON COLUMN kala_gochara_windows.continuity_state IS
    'Migration 461 (D-5 RED-C fix v4): interval-shape-only, NULL for point/chain '
    'rows. Shape: {"left_active": bool, "right_active": bool, "raw_start": '
    '"YYYY-MM-DD", "raw_end": "YYYY-MM-DD"} -- whether THIS row''s currently-known '
    'span was active at its own leftmost/rightmost grid day (raw, pre-widen/cap '
    'bounds), and those raw bounds themselves. Read by writer.py''s DB-driven '
    'consolidation to chain adjacent already-committed segments for the same '
    '(chart_id, event_class) by exact calendar-date adjacency -- never by runtime '
    'dispatch-order assumption. A row with left_active=false and right_active=false '
    'is a settled/final window (no further chaining possible); either flag true '
    'means a later-committed neighbor could still merge into it.';

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   ALTER TABLE kala_gochara_windows DROP COLUMN IF EXISTS continuity_state;
--   COMMIT;
-- =============================================================================
