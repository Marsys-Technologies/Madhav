-- Migration 578: Paripraśna durable-persistence write-ahead outbox table.
-- Paripraśna P2-D (PPR-10, FD-9) · DD-16 execution · 2026-08-20
--
-- ══════════════════════════════════════════════════════════════════════════════
-- WHY THIS EXISTS
-- ══════════════════════════════════════════════════════════════════════════════
-- `platform/src/lib/pariprashna/store/durable_outbox.ts`'s own module header names
-- this exact schema and has carried a "NEEDS A MIGRATION" banner since P2-D was
-- built — the code (writeAheadTurn, claimPendingPersistenceEntries,
-- markPersistenceApplied/Failed, replayPendingPersistence) has been real and
-- unit-tested (11/11, against a fake OutboxDb port) since then, but had no real
-- table to run against. This migration creates exactly that table, nothing else.
--
-- DD-16 (PARIPRASHNA_SWARM_REVIEW_AND_AMENDMENTS_v1_1.md §2) ruled: open the
-- migration, additive only, do not touch the feature flag.
--
-- ══════════════════════════════════════════════════════════════════════════════
-- WHAT THIS MIGRATION DOES *NOT* DO
-- ══════════════════════════════════════════════════════════════════════════════
--   1. `MARSYS_FLAG_PARIPRASHNA_DURABLE_PERSISTENCE_ENABLED` is NOT touched by this
--      file (it is an application env var, not a DB object) and stays OFF. The
--      DIRECT-mode write path (`durable_writer.ts`, flag off) is byte-for-byte
--      unchanged — this table is created empty and nothing enqueues into it until
--      that flag is separately flipped, a decision this migration does not make.
--
--   2. RLS is CREATEd, NOT ENABLED — same arming discipline as migration 576
--      (`576_pariprashna_roles_rls_arm3.sql` §5's own header: a policy on a table
--      without RLS enabled is stored and never consulted). Arming is a separate,
--      deliberate act this migration does not perform, for the same reason 576
--      gives: this session cannot verify production table ownership and CLAUDE.md
--      §N.8 forbids asserting a safety property with no detector behind it.
--
--   3. No GRANT statements. `durable_outbox.ts`'s own header names only the RLS
--      policy shape, not a grant; DD-16's ruling scoped this migration to
--      "additive only... per its own header spec — no other schema change".
--      DISCLOSED, NOT FIXED HERE: once `PARIPRASHNA_DURABLE_PERSISTENCE_ENABLED`
--      is armed for real, `role_web_serve` (or whichever role ends up owning the
--      write-ahead enqueue) will need an explicit GRANT INSERT here, mirroring
--      `pariprashna_ledger_outbox`'s "arm-3 outbox: INSERT only" grant in
--      migration 576 §3e — that grant is intentionally NOT added by this
--      migration and is owed to whichever session performs the real cutover.
--
--   4. No backfill, no data migration, no ALTER/DROP on any existing table or
--      column. This migration only ever adds.
--
-- Idempotent: `CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`, `DROP
-- POLICY IF EXISTS` before `CREATE POLICY`. Safe to re-run.
-- §N.4: surgical, verified. NEVER edit this file after it has been applied.

BEGIN;

-- ═══════════════════════════════════════════════════════════════════════════════
-- 1. THE WRITE-AHEAD OUTBOX TABLE
-- ═══════════════════════════════════════════════════════════════════════════════
-- Schema is copied verbatim from `durable_outbox.ts`'s own header — this migration
-- does not redesign it. One row per assistant message; `writeTurn` (store/writer.ts)
-- is already idempotent by message id, so `ON CONFLICT (message_id) DO UPDATE` at
-- the enqueue call site (not here — that is application code) is safe: a
-- re-enqueue of the same message replaces the pending payload, never duplicates.

CREATE TABLE IF NOT EXISTS pariprashna_persistence_outbox (
  id              bigserial   PRIMARY KEY,
  message_id      uuid        NOT NULL UNIQUE,
  conversation_id uuid        NOT NULL,
  -- Carried explicitly (not joined) so this table is RLS-scopable like every
  -- other C1 table — mirrors migration 576 §2's pariprashna_ledger_outbox.chart_id
  -- precedent.
  chart_id        uuid        NOT NULL,
  turn_id         text        NOT NULL,
  -- The full write-ahead payload: { message: CanonicalMessage, parts:
  -- MessagePartInput[] } — Zod-validated on the way IN (enqueue) and again on the
  -- way OUT (replay), same untrusted-queue discipline as arm3/outbox.ts.
  payload         jsonb       NOT NULL,
  status          text        NOT NULL DEFAULT 'pending'
                                CHECK (status IN ('pending', 'applied', 'failed')),
  attempts        integer     NOT NULL DEFAULT 0 CHECK (attempts >= 0),
  enqueued_at     timestamptz NOT NULL DEFAULT now(),
  claimed_at      timestamptz,
  applied_at      timestamptz,
  last_error      text,
  CONSTRAINT pariprashna_persistence_outbox_applied_has_no_error
    CHECK (status <> 'applied' OR last_error IS NULL)
);

CREATE INDEX IF NOT EXISTS idx_pariprashna_persistence_outbox_pending
  ON pariprashna_persistence_outbox (enqueued_at)
  WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_pariprashna_persistence_outbox_chart
  ON pariprashna_persistence_outbox (chart_id);

COMMENT ON TABLE pariprashna_persistence_outbox IS
  'P2-D (PPR-10/FD-9) write-ahead outbox: records the INTENT to persist a turn before '
  'attempting the real write, so a process death between turn.close and the write actually '
  'committing leaves a durable, replayable record. Inert until '
  'MARSYS_FLAG_PARIPRASHNA_DURABLE_PERSISTENCE_ENABLED is flipped on (DD-16, migration 578).';

-- ═══════════════════════════════════════════════════════════════════════════════
-- 2. CHART-SCOPED RLS POLICY — CREATED, NOT ENABLED (PPR-22 shape, DD-16 scope)
-- ═══════════════════════════════════════════════════════════════════════════════
-- `durable_outbox.ts`'s own header: "a chart_id = app_chart_context() policy for
-- role_web_serve, matching the pariprashna_ledger_outbox precedent exactly."
-- `app_chart_context()` already exists (migration 576 §4) — not recreated here.

DO $preflight$
BEGIN
  IF to_regclass('public.pariprashna_persistence_outbox') IS NULL THEN
    RAISE EXCEPTION
      'DD16_PREFLIGHT_TABLE_MISSING: pariprashna_persistence_outbox does not exist — '
      'the CREATE TABLE IF NOT EXISTS above should have made this impossible.';
  END IF;
  IF to_regprocedure('app_chart_context()') IS NULL THEN
    RAISE EXCEPTION
      'DD16_PREFLIGHT_FUNCTION_MISSING: app_chart_context() does not exist. This migration '
      'depends on migration 576 having already applied.';
  END IF;
END
$preflight$;

DROP POLICY IF EXISTS pariprashna_persistence_outbox_g1c_chart_context
  ON pariprashna_persistence_outbox;
CREATE POLICY pariprashna_persistence_outbox_g1c_chart_context
  ON pariprashna_persistence_outbox
  AS PERMISSIVE FOR ALL TO role_web_serve
  USING (chart_id = app_chart_context())
  WITH CHECK (chart_id = app_chart_context());

-- Deliberately absent: any `ALTER TABLE ... ENABLE ROW LEVEL SECURITY`, and any
-- GRANT. See the header, items 2 and 3.

COMMIT;

-- ═══════════════════════════════════════════════════════════════════════════════
-- DOWN (manual rollback) — additive; this removes exactly what was added.
-- ═══════════════════════════════════════════════════════════════════════════════
--   -- 1. DROP POLICY IF EXISTS pariprashna_persistence_outbox_g1c_chart_context
--   --      ON pariprashna_persistence_outbox;
--   -- 2. DROP TABLE IF EXISTS pariprashna_persistence_outbox;
