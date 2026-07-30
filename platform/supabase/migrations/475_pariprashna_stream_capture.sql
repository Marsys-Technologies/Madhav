-- Migration 475: pariprashna real-reading stream capture — SAMĀPTI lane B-PB8-BYTEEQ
-- Created: 2026-07-30
--
-- ⚠ NUMBERING: 475 is the next free number as read from origin/main at authoring time
-- (highest across BOTH dirs = platform/migrations/474_asset_throughput_incomplete_state.sql).
-- Per SAMAPTI_CONDUCTOR_PROMPT §5 the Conductor RE-ALLOCATES the number at MERGE time —
-- if another lane merges a 475 first, rename BOTH this filename and the header line above.
--
-- WHY THIS EXISTS
-- ───────────────
-- FOLLOWUP_PB-2_BYTE_EQUALITY_FIXTURE_COVERAGE.md §3: BRIEF_PB-2 §G-1 requires the
-- byte-equality gate run "against one real deployed reading", and no such run has ever
-- happened because nothing durable holds a real reading's raw SSE event stream.
--
-- CORRECTION TO THAT FOLLOW-UP'S WORDING (measured, 2026-07-30): §3 states "no mechanism
-- persists a real reading's raw event stream at all". That is REFUTED as worded — since
-- PB-2/M-5, `src/lib/pariprashna/protocol/ring_buffer.ts` writes EVERY event of EVERY
-- turn to Redis (`parp:buf:<turn_id>`) for the resume path. What is true is that the
-- ring buffer is deliberately EPHEMERAL and unsuited to this job:
--   • capped at RING_BUFFER_MAX_EVENTS = 500 (a long reading's early events are trimmed),
--   • TTL 600 s while open / 180 s once closed,
--   • not queryable after the fact, and gone entirely when Redis is unconfigured.
-- This table is the DURABLE, QUERYABLE counterpart — an opt-in capture sink, not a
-- replacement for the ring buffer.
--
-- PRIVACY / RETENTION (the design decision the follow-up §3 said this needed)
-- ──────────────────────────────────────────────────────────────────────────
--   1. OFF BY DEFAULT. Nothing is ever written unless PARIPRASHNA_STREAM_CAPTURE=1 is
--      explicitly set on the deployment. The table can exist empty indefinitely.
--   2. SAMPLED. PARIPRASHNA_STREAM_CAPTURE_SAMPLE (0..1) decides per TURN — a turn is
--      captured whole or not at all, so a captured turn is always replayable.
--   3. ASSISTANT-SIDE ONLY. No event in the PariprashnaEvent union carries the user's
--      question text (verified against protocol/events.ts: turn.open carries ids +
--      request tiers; no event has a user/prompt field). This table therefore holds the
--      assistant's own output stream and its grounding metadata, never the native's
--      question.
--   4. BOUNDED RETENTION. `expires_at` is set by the writer (default 14 days) and
--      `purgeExpiredStreamCaptures()` deletes past it. A row without a purge is still
--      bounded by this column being a hard, queryable expiry date.
--
-- Idempotency: CREATE TABLE / CREATE INDEX IF NOT EXISTS throughout (§N.4, surgical).
-- Additive-only: one new table, no change to any existing table or row.

BEGIN;

CREATE TABLE IF NOT EXISTS pariprashna_stream_capture (
  turn_id         text        NOT NULL,
  seq             int         NOT NULL,
  event_type      text        NOT NULL,
  event           jsonb       NOT NULL,
  conversation_id text,
  chart_id        text,
  captured_at     timestamptz NOT NULL DEFAULT now(),
  expires_at      timestamptz NOT NULL,
  PRIMARY KEY (turn_id, seq)
);

COMMENT ON TABLE pariprashna_stream_capture IS
  'SAMAPTI/B-PB8-BYTEEQ: opt-in, sampled, bounded-retention capture of a real reading''s '
  'raw Paripraśna SSE event stream, so BRIEF_PB-2 §G-1''s "byte-equality against one real '
  'deployed reading" can actually be run. OFF unless PARIPRASHNA_STREAM_CAPTURE=1. '
  'Holds assistant-side wire events only — the PariprashnaEvent union carries no user text.';
COMMENT ON COLUMN pariprashna_stream_capture.seq IS
  'The event''s own monotonic per-turn wire seq — NOT a row counter. (turn_id, seq) is the '
  'natural key, so a re-delivered event upserts rather than duplicating.';
COMMENT ON COLUMN pariprashna_stream_capture.expires_at IS
  'Hard retention bound written at capture time. purgeExpiredStreamCaptures() deletes past it.';

-- Purge / retention sweeps scan by expiry.
CREATE INDEX IF NOT EXISTS pariprashna_stream_capture_expires_idx
  ON pariprashna_stream_capture (expires_at);

-- The comparator resolves a captured turn from its conversation when the operator has a
-- conversation id rather than a turn id.
CREATE INDEX IF NOT EXISTS pariprashna_stream_capture_conversation_idx
  ON pariprashna_stream_capture (conversation_id, captured_at DESC);

COMMIT;
