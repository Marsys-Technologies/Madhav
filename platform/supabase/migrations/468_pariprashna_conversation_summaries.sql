-- Migration 468: pariprashna durable conversation summaries — PB-2 (SMṚTI) lane M-3
-- Created: 2026-07-28
--
-- Numbering note: after merging lane M-1 (migration 467
-- 467_pariprashna_canonical_message_parts.sql) into this branch, 467 is the
-- highest numbered file across supabase/migrations. 468 is the next free number
-- per platform/supabase/migrations/README.md's guidance. At time of writing, no
-- other PB-2 lane (M-2, M-4, M-5, M-6) had pushed a migration of its own — if a
-- sibling lane's migration lands with the SAME number at integration time, that
-- is an expected, disclosed integration-time renumbering fix (per the M-3 brief),
-- not a defect in this file.
--
-- Context: Paripraśna Build campaign wave PB-2 lane M-3 ("durable summaries").
-- Long pariprashna conversation threads need periodic summarization so the
-- synthesis prompt's context does not grow unbounded. This table is the
-- append-only ledger of those summaries: one row per threshold-crossing,
-- pointing at the last canonical message it covers
-- (`message_parts.message_id` / `conversation_messages.id`, the M-1 canonical
-- schema). This lane does NOT touch M-1's schema or DAL — it only reads
-- `message_parts` via M-1's `readTurnParts` (imported, not modified) and adds
-- this new, independent table.
--
-- ADDITIVE-ONLY guarantee: a fresh CREATE TABLE cannot affect any existing row
-- in any other table. No columns are added to conversation_messages or
-- message_parts here.
--
-- Idempotency: per §N.4 "surgical migrations only" — CREATE TABLE IF NOT
-- EXISTS throughout. Safe to re-run. The two FKs below are declared inline in
-- the CREATE TABLE (mirroring 467's own convention), so — same as 467's own
-- numbering note documents — they are skipped on a re-run once the table
-- already exists (no duplicate-constraint error).
--
-- Reuse-on-restart contract (service.ts / store.ts, PgSummaryStore): the
-- summarizer writes exactly one new row per threshold crossing and reuses the
-- most recent row (ORDER BY created_at DESC LIMIT 1) across process restarts —
-- a restart is just a fresh read of this table, no in-memory state to lose.
-- Rows are never updated or deleted by the application; a rebuild/re-summarize
-- of the SAME logical range is deliberately append-only (unlike M-1's
-- delete-then-insert message_parts pattern) because a summary row is an
-- immutable historical artifact a downstream grounding-gate check may already
-- have cited — mutating or deleting it in place would invalidate that
-- reference.
BEGIN;

CREATE TABLE IF NOT EXISTS conversation_summaries (
  id                          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id             uuid NOT NULL REFERENCES conversations(id),
  covers_through_message_id   uuid NOT NULL REFERENCES conversation_messages(id),
  summary_text                text NOT NULL,
  model_id                    text,
  created_at                  timestamptz NOT NULL DEFAULT now()
);

-- Lookup index: "most recent summary for this conversation" (PgSummaryStore's
-- findLatest) and "does a row already cover through this message" both filter
-- on conversation_id and want created_at-ordered access.
CREATE INDEX IF NOT EXISTS idx_conversation_summaries_conversation_created
  ON conversation_summaries(conversation_id, created_at DESC);

COMMENT ON TABLE conversation_summaries IS
  'PB-2/M-3 (Paripraśna SMṚTI): durable, periodic summaries of a pariprashna '
  'conversation''s earlier canonical turns, so the synthesis prompt''s context '
  'stays bounded on long threads. One row per threshold crossing (append-only, '
  'never updated/deleted). covers_through_message_id points at the last '
  'conversation_messages row (M-1 canonical schema, migration 467) folded into '
  'summary_text. Citation (signal_id/fact-id) references from message_parts '
  'citation-kind rows within the summarized range are carried forward VERBATIM '
  'inside summary_text (see src/lib/pariprashna/summaries/render.ts '
  'appendCitationBlock) so a later grounding-gate check can still resolve them.';

COMMENT ON COLUMN conversation_summaries.covers_through_message_id IS
  'The last conversation_messages.id folded into this summary — the natural '
  '"high-water mark" the next summarization pass reads to find only the NEW '
  'turns since this row.';

COMMENT ON COLUMN conversation_summaries.model_id IS
  'The summarizer worker''s model id for this row (NULL only if the worker '
  'implementation did not report one). Not a foreign key — models rotate.';

COMMIT;

-- DOWN (manual rollback — this project has no automated down-migration runner;
-- drop is listed for audit + local throwaway-DB rollback testing only):
-- BEGIN;
-- DROP TABLE IF EXISTS conversation_summaries;
-- COMMIT;
