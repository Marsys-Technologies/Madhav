-- Migration 588: SAMĪKṢĀ digest journal — a real DB record of the periodic digest.
-- Paripraśna P4-I (T-P4-REMEMBER, PARIPRASHNA_P3_P4_OVERNIGHT_AUTONOMOUS_RUN_v2_0.md §10.2/§10.5)
-- · DD-21 · 2026-08-23
--
-- ══════════════════════════════════════════════════════════════════════════════
-- WHY THIS EXISTS
-- ══════════════════════════════════════════════════════════════════════════════
-- `platform/src/lib/pariprashna/samiksha/daily_job.ts` (PB-3 lane L-4) runs the SAMĪKṢĀ daily
-- consolidated digest: it detects windows that closed and windows closing soon, renders one
-- digest, and dispatches it. Until this migration, "dispatch" meant TWO things, both non-durable:
--   1. `LogOnlyTransport` (digest.ts) — a `console.info` banner. Not queryable, not joinable to a
--      chart or a prediction, not durable past log retention, and cannot be read back by the
--      system that produced it (charter's own framing of the defect).
--   2. `FileDigestJournal` (digest_journal.ts) — a per-`as_of` JSON marker FILE on local disk
--      (`.samiksha-state/digest-<as_of>.json`, gitignored), used only to answer "has a digest
--      already been sent for date D" and storing COUNTS ONLY (closed_count/closing_soon_count/
--      transport_mode/real_delivery) — never the digest's actual content (subject/text/payload).
--      Its own header already discloses why it was a file, not a table: lane L-4's `may_touch`
--      grant excluded `platform/supabase/migrations/**` at the time it was written. That
--      exclusion does not apply to this P4-I lane.
--
-- This migration creates the real table `DbDigestJournal` (digest_journal.ts) writes to and
-- reads back from: one row per `as_of` day, carrying the FULL rendered digest (subject + body
-- text) and the structured payload (jsonb) — so a digest is queryable by date, joinable to the
-- charts and prediction-ledger rows its items reference (via `payload->'closed'`/`'closing_soon'`
-- items' `chart_id`/`id` fields), and durable in the same database as the predictions it reports
-- on, not a side-channel file or a log line.
--
-- ══════════════════════════════════════════════════════════════════════════════
-- SCHEMA SHAPE — why it looks like this (follows the real digest, not an imagined one)
-- ══════════════════════════════════════════════════════════════════════════════
-- `DigestPayload` (digest.ts) is NOT chart-scoped 1:1 — `runDailyJob` sweeps ALL charts by
-- default (`chartId` is an optional narrowing filter), and one digest's `closed`/`closing_soon`
-- arrays can carry items across many different charts in the same row. That is why this table
-- does NOT follow the `chart_id uuid NOT NULL` + `chart_id = app_chart_context()` RLS pattern
-- used by `pariprashna_persistence_outbox` (migration 578) and `pariprashna_ledger_outbox`
-- (migration 576) — those tables' rows are genuinely one-chart-each; this table's rows are not.
-- `run_chart_id` is carried as a NULLABLE column instead (populated only when `daily_job.ts` is
-- invoked with `--chart <uuid>`, the one supported single-chart mode) so a future scoped run is
-- still filterable, without forcing a false single-chart identity onto the common all-charts row.
--
-- RLS is DELIBERATELY NOT ADDED here (disclosed, not silently skipped): this is an internal
-- job-status/audit table (job runs, not a per-chart web-serve read surface), and the five-role
-- chart-scoped RLS model (migration 576) has no natural predicate for a row that spans charts.
-- If this table is ever exposed to a per-chart web surface, RLS keyed on `run_chart_id` (with an
-- explicit IS NULL carve-out for all-charts rows, reviewed by whoever adds that surface) is owed
-- then, not invented speculatively here. Today's actual security posture is unaffected either
-- way: migration 576's chart-scoped policies on the OTHER pariprashna tables are themselves
-- CREATEd but NOT ENABLED (576 §2), so no table in this schema is presently RLS-enforced; this
-- table simply does not pretend otherwise.
--
-- ══════════════════════════════════════════════════════════════════════════════
-- WHAT THIS MIGRATION DOES *NOT* DO
-- ══════════════════════════════════════════════════════════════════════════════
--   1. Does not touch `pariprashna_persistence_outbox`, `pariprashna_ledger_outbox`, or any
--      existing table/column. Purely additive: one new table, two new indexes.
--   2. Does not delete or migrate `.samiksha-state/*.json` marker files or the `FileDigestJournal`
--      class — kept as an offline/no-DB fallback for local dev and as the class the CLI script
--      falls back to if `--file-journal` is passed explicitly. The DEFAULT production path moves
--      to `DbDigestJournal` (this table); that wiring is the accompanying application-code change
--      in this same PR, not this migration.
--   3. No GRANT statements — the daily job runs today through the same unscoped `amjis_app`
--      credential every other `LedgerExecutor` call in this file already uses (per §N.4/§N.8,
--      asserting a grant wall here with no armed RLS behind it and no verified table ownership
--      would be an unearned safety claim); walling this table off is future work for whoever
--      arms migration 576's roles for real.
--   4. No backfill, no data migration, no ALTER/DROP on any existing table or column.
--
-- Idempotent: `CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`. Safe to re-run.
-- §N.4: surgical, verified. NEVER edit this file after it has been applied.

BEGIN;

-- ═══════════════════════════════════════════════════════════════════════════════
-- 1. THE DIGEST JOURNAL TABLE
-- ═══════════════════════════════════════════════════════════════════════════════
-- One row per `as_of` day (the daily job's own idempotency unit — see digest_journal.ts's
-- header on why the send is not self-idempotent without an explicit marker). `subject` +
-- `body_text` are the actual rendered digest (`renderDigest()`'s output) — the content a human
-- would have read in the log line, now durable and queryable. `payload` is the full structured
-- `DigestPayload` (as_of, closed[], closing_soon[], closing_soon_days, generated_at) as jsonb,
-- so a caller can join/filter on the item-level `chart_id` and prediction-ledger `id` fields the
-- digest actually reports on, without re-parsing rendered text.

CREATE TABLE IF NOT EXISTS pariprashna_samiksha_digest_journal (
  id                  bigserial   PRIMARY KEY,
  as_of               date        NOT NULL,
  -- Populated only for a `--chart <uuid>`-scoped run; NULL means "swept all charts" (the
  -- default and, today, only production mode). See header for why this is not the row's
  -- identity, just an optional filter.
  run_chart_id        uuid,
  sent_at             timestamptz NOT NULL DEFAULT now(),
  closed_count        integer     NOT NULL CHECK (closed_count >= 0),
  closing_soon_count  integer     NOT NULL CHECK (closing_soon_count >= 0),
  -- Transport identity at send time (e.g. 'log-only-stub' today; a future real email transport's
  -- mode once one exists — see digest.ts's W-5 header). This journal row exists independently of
  -- which transport carried the message; it is the durable record, not the transport itself.
  transport_mode      text        NOT NULL,
  -- Whether a real external delivery (an actual email) occurred. Mirrors `TransportResult.
  -- realDelivery` byte-for-byte — NEVER set true by this table; it only stores what the
  -- transport honestly reported. See digest.ts: still false for every transport that exists in
  -- this codebase today (W-5 — no email transport exists).
  real_delivery       boolean     NOT NULL DEFAULT false,
  subject             text        NOT NULL,
  body_text           text        NOT NULL,
  payload             jsonb       NOT NULL,
  created_at          timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT pariprashna_samiksha_digest_journal_as_of_unique UNIQUE (as_of)
);

-- Read-back-by-date is the journal's primary access pattern (hasSent(asOf) + the digest history
-- view a future admin surface would want).
CREATE INDEX IF NOT EXISTS idx_pariprashna_samiksha_digest_journal_sent_at
  ON pariprashna_samiksha_digest_journal (sent_at DESC);

-- Joinability to a chart or a prediction (the charter's own framing of what a log line cannot
-- do): a GIN index over the jsonb payload so `payload @> '{"closed": [{"chart_id": "..."}]}'`-
-- style queries and `jsonb_path_query` over `closed`/`closing_soon` item arrays are indexed, not
-- sequential-scanned.
CREATE INDEX IF NOT EXISTS idx_pariprashna_samiksha_digest_journal_payload_gin
  ON pariprashna_samiksha_digest_journal USING gin (payload);

COMMENT ON TABLE pariprashna_samiksha_digest_journal IS
  'P4-I (DD-21) real digest journal: one row per as_of day the SAMĪKṢĀ daily job dispatched a '
  'non-empty digest, carrying the full rendered content (subject/body_text) and structured '
  'payload (jsonb, joinable to chart_id/prediction-ledger ids inside closed[]/closing_soon[]). '
  'Retires log-only-transport-is-the-only-record: the digest now lands here, durably and '
  'queryably, in addition to whatever transport (still log-only, W-5) carried it.';

COMMIT;

-- ═══════════════════════════════════════════════════════════════════════════════
-- DOWN (manual rollback) — additive; this removes exactly what was added.
-- ═══════════════════════════════════════════════════════════════════════════════
--   -- DROP TABLE IF EXISTS pariprashna_samiksha_digest_journal;
