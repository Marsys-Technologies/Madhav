-- Migration 576: NO-LEAKAGE arm-1 (five roles + grant walls), chart-scoped RLS
--                policies on the C1/C3 tables, and the arm-3 ledger outbox.
-- Paripraśna P1 FOUNDATION, lane G1-C (NCD-5 · PPR-21/PPR-22/PPR-26/PPR-31) · 2026-08-19
--
-- ══════════════════════════════════════════════════════════════════════════════
-- WHY THIS EXISTS
-- ══════════════════════════════════════════════════════════════════════════════
-- PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md §7.4, finding F-25q (critical):
--
--   "None of §7.4's five roles exist; the single `amjis_app` credential the web
--    app serves every request with holds full CRUD on the prediction ledger +
--    calibration it is designed to be walled from. Repo-wide grep for the five
--    role names: zero hits."
--
-- NCD-5 (PARIPRASHNA_DECISION_REGISTER_v1_0.md §4, RULED (a) 2026-08-18):
--   "roles + RLS at Gate 1 on C1 (sacred-personal) and C3 (predictive) tables."
--
-- PPR-21 — the five serving DB roles MUST exist with their grant walls, and the
--   web app MUST NOT serve reads on a credential holding ledger/calibration write.
-- PPR-22 — chart-scoped RLS MUST protect C1 and C3 tables beneath application authz.
-- PPR-26 — safety/retraction/consent audit rows MUST be append-only (INSERT-only
--   grant OR hash chain). G1-B took the hash-chain option; this lane adds the
--   INSERT-only grant as the second, independent layer.
-- PPR-31 — NO-LEAKAGE arm-1 (roles+RLS) and arm-3 (out-of-process ledger writer).
--
-- ══════════════════════════════════════════════════════════════════════════════
-- WHAT THIS MIGRATION DOES *NOT* DO — READ THIS BEFORE ASSUMING IT ARMED ANYTHING
-- ══════════════════════════════════════════════════════════════════════════════
-- This migration is INERT on the live system when it applies. Deliberately.
--
--   1. The five roles are created **NOLOGIN, NOBYPASSRLS, with no members**.
--      Nothing can connect as them. They are grant-holding group roles; the
--      cutover act is `GRANT role_web_serve TO <login user>`, which is NOT here.
--      No credential is created, changed, or rotated by this file.
--
--   2. RLS policies are CREATEd but ROW LEVEL SECURITY is **NOT ENABLED** on any
--      table. A policy on a table without RLS enabled is stored and never
--      consulted. Arming is a separate, deliberate operator act —
--      `platform/scripts/pariprashna/g1c_arm_rls.sql`, which is NOT in a
--      migrations directory and therefore is NOT auto-applied by the deploy-time
--      runner (`platform/scripts/migrate.ts` reads only `platform/migrations/`
--      and `platform/supabase/migrations/`).
--
--      Why not arm here: enabling RLS is only safe for the CURRENT app credential
--      if that credential OWNS these tables (owner bypass, absent FORCE ROW LEVEL
--      SECURITY). This session cannot verify production table ownership — it is
--      forbidden from touching the production database — and CLAUDE.md §N.8
--      forbids asserting a safety property with no detector behind it. The
--      arming script carries that detector: it verifies ownership and REFUSES to
--      arm otherwise.
--
--   3. `amjis_app` is NOT touched. No GRANT to it, no REVOKE from it, no ALTER
--      ROLE, no password change. Its rotation is owed (it pairs with CCD-004's
--      standing owner-action MCP credential rotation — CROSS_CUTTING_DECISION_
--      REGISTER_v1_0.md §CCD-004 "SECURITY — owner action") and is explicitly
--      WITHHELD from this lane by the native for a separate real-time decision.
--      See the cutover runbook: 00_ARCHITECTURE/briefs/pariprashna_swarm/
--      G1_C_ROLES_RLS_CUTOVER_RUNBOOK_v1_0.md.
--
--   4. The arm-3 outbox table is created EMPTY and nothing enqueues into it until
--      the `PARIPRASHNA_LEDGER_OUT_OF_PROCESS` feature flag (default false) is
--      flipped. The in-process ledger write path is byte-for-byte unchanged while
--      the flag is off.
--
-- Idempotent: DO-guarded role creation, `CREATE TABLE IF NOT EXISTS`, DROP POLICY
-- IF EXISTS before CREATE POLICY, `CREATE OR REPLACE FUNCTION`. Safe to re-run.
-- §N.4: surgical, verified. NEVER edit this file after it has been applied.

BEGIN;

-- ═══════════════════════════════════════════════════════════════════════════════
-- 0. PREFLIGHT — fail loudly if a table this migration walls does not exist
-- ═══════════════════════════════════════════════════════════════════════════════
-- Without this, a missing table would make the corresponding GRANT/REVOKE/POLICY
-- silently absent and the wall would have a hole nobody could see. §N.8: a signal
-- must be computed by a detector that measures the claim. The claim here is "every
-- named C1/C3 table is walled"; this is the detector that can make it read false.

DO $preflight$
DECLARE
  required text[] := ARRAY[
    -- C1 sacred-personal
    'charts', 'life_events', 'conversations', 'conversation_messages',
    'message_parts', 'conversation_summaries', 'pariprashna_stream_capture',
    'chart_subject_consent', 'chart_subject_consent_events',
    'chart_subject_exclusions', 'chart_subject_deletion_tombstones',
    'chart_subject_deletion_disputes',
    -- C3 predictive
    'brahma_mimamsa_prediction_ledger', 'brahma_prospective_ledger',
    'mimamsa_predictions', 'mimamsa_calibration', 'mimamsa_calibration_snapshot',
    'mimamsa_multipliers', 'mimamsa_adjudication_log', 'mimamsa_snapshot_cosign',
    'mimamsa_resonance_feedback', 'mimamsa_pool_contributions',
    'mimamsa_intervention_ledger', 'gochara_v3_calibration',
    'mcp_prediction_outcomes'
  ];
  missing text[];
BEGIN
  SELECT array_agg(t) INTO missing
  FROM unnest(required) AS t
  WHERE to_regclass('public.' || quote_ident(t)) IS NULL;

  IF missing IS NOT NULL THEN
    RAISE EXCEPTION
      'G1C_PREFLIGHT_MISSING_TABLES: migration 576 walls tables that do not exist here: %. '
      'Refusing to apply a partial wall — a grant wall with an invisible hole is worse than no '
      'wall. Create the missing tables (or correct this list in a NEW migration) and retry.',
      array_to_string(missing, ', ');
  END IF;
END
$preflight$;

-- ═══════════════════════════════════════════════════════════════════════════════
-- 1. THE FIVE ROLES (PPR-21 · TA §7.4)
-- ═══════════════════════════════════════════════════════════════════════════════
-- All five: NOLOGIN (cannot connect), NOSUPERUSER, NOCREATEDB, NOCREATEROLE,
-- NOBYPASSRLS (explicitly — a role that bypasses RLS defeats PPR-22), NOINHERIT
-- left at the default INHERIT so that a login user granted one of these roles
-- actually receives its privileges without SET ROLE gymnastics.
--
-- Template: platform/supabase/migrations/557_utkarsha_builder_role.sql, the
-- repository's one existing restricted-role migration.

DO $roles$
DECLARE
  r text;
BEGIN
  FOREACH r IN ARRAY ARRAY[
    'role_web_serve',      -- the web app's SERVING reads + conversation store
    'role_orchestrator',   -- the chart-build path (layer-table writes)
    'role_ledger_write',   -- arm-3 ONLY: the sole holder of ledger/outcome/calibration write
    'role_jobs',           -- scheduled jobs: model health, summaries, digests
    'role_sidecar'         -- python-sidecar: minimal compute-support read
  ] LOOP
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = r) THEN
      EXECUTE format(
        'CREATE ROLE %I NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS', r
      );
    ELSE
      -- Idempotent re-run: re-assert the attributes that matter for the wall,
      -- so a re-apply cannot leave a role that drifted into BYPASSRLS.
      EXECUTE format(
        'ALTER ROLE %I NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS', r
      );
    END IF;
  END LOOP;
END
$roles$;

COMMENT ON ROLE role_web_serve IS
  'Paripraśna NO-LEAKAGE arm-1 (PPR-21). The web app''s serving credential. Reads the layer '
  'stack, read/writes the conversation store, and is WALLED from every C3 calibration surface '
  'and from ALL ledger writes. Group role: NOLOGIN, granted to a login user at cutover.';
COMMENT ON ROLE role_orchestrator IS
  'Paripraśna NO-LEAKAGE arm-1 (PPR-21). The chart-build path: layer-table DML + build-state '
  'writes. No conversation store, no ledger, no consent tables. Group role: NOLOGIN.';
COMMENT ON ROLE role_ledger_write IS
  'Paripraśna NO-LEAKAGE arm-3 (PPR-31). The ONLY role holding write on the prediction ledgers, '
  'outcomes and calibration. Held exclusively by the out-of-process ledger writer '
  '(platform/scripts/pariprashna/ledger_writer_worker.ts). Group role: NOLOGIN.';
COMMENT ON ROLE role_jobs IS
  'Paripraśna NO-LEAKAGE arm-1 (PPR-21). Scheduled jobs: model_health, conversation summaries, '
  'digest reads. No ledger write (that is role_ledger_write). Group role: NOLOGIN.';
COMMENT ON ROLE role_sidecar IS
  'Paripraśna NO-LEAKAGE arm-1 (PPR-21). Minimal compute-support READ for the python sidecar. '
  'No writes anywhere. Group role: NOLOGIN.';

-- ═══════════════════════════════════════════════════════════════════════════════
-- 2. THE ARM-3 LEDGER OUTBOX (PPR-31 arm 3)
-- ═══════════════════════════════════════════════════════════════════════════════
-- §14.10 arm 3, verbatim: "The ledger writer runs outside the synthesis process
-- and holds the only write role."
--
-- Today it does not. Every INSERT into `brahma_mimamsa_prediction_ledger` happens
-- IN-PROCESS inside the Next.js request pipeline (persistence_stage.ts →
-- capture.ts → samiksha/writer.ts). The daily job (samiksha-daily.yml) is
-- out-of-process but only UPDATEs lifecycle — it is not the writer arm-3 means.
--
-- This outbox is the seam that makes arm-3 possible without a distributed
-- transaction: the serving process INSERTs an INTENT here (a privilege
-- role_web_serve keeps), and the out-of-process writer — the only holder of
-- role_ledger_write — drains it and performs the real ledger write.
--
-- The outbox is deliberately NOT append-only: `claimed_at`/`applied_at`/`error`
-- are the drain's own bookkeeping. Integrity of the LEDGER is protected by the
-- grant wall + the existing trg_bmpl_freeze_confirmed trigger, not by this table.

CREATE TABLE IF NOT EXISTS pariprashna_ledger_outbox (
  id             bigserial   PRIMARY KEY,
  -- Chart scope: carried explicitly so this table is RLS-scopable like every
  -- other C1/C3 table, rather than hiding the chart inside `payload`.
  chart_id       uuid        NOT NULL,
  -- The ledger operation being requested. Closed enum — an outbox that accepts
  -- an open-ended operation string is an arbitrary-write channel wearing a
  -- queue's clothes, which would defeat the wall it exists to enforce.
  op             text        NOT NULL CHECK (op IN (
                               'create_detected',
                               'create_confirmed',
                               'transition',
                               'record_outcome'
                             )),
  -- Zod-validated in platform/src/lib/pariprashna/arm3/outbox.ts before enqueue
  -- AND re-validated by the worker after dequeue. The worker never trusts the
  -- producer: role_web_serve can write this table, so its contents are, from the
  -- writer's point of view, untrusted input.
  payload        jsonb       NOT NULL,
  enqueued_at    timestamptz NOT NULL DEFAULT now(),
  -- Drain bookkeeping.
  claimed_at     timestamptz,
  applied_at     timestamptz,
  attempts       integer     NOT NULL DEFAULT 0 CHECK (attempts >= 0),
  -- The resulting ledger row id, once applied. NULL while pending — an honest
  -- null, never a placeholder (§N.7 item 6).
  ledger_row_id  uuid,
  -- Last failure, verbatim. NULL while healthy.
  last_error     text,
  CONSTRAINT pariprashna_ledger_outbox_applied_has_row
    CHECK (applied_at IS NULL OR ledger_row_id IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS idx_pariprashna_ledger_outbox_pending
  ON pariprashna_ledger_outbox (enqueued_at)
  WHERE applied_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_pariprashna_ledger_outbox_chart
  ON pariprashna_ledger_outbox (chart_id);

COMMENT ON TABLE pariprashna_ledger_outbox IS
  'NO-LEAKAGE arm-3 (PPR-31) seam. The serving process (role_web_serve) may INSERT a ledger '
  'write INTENT here; only the out-of-process writer (role_ledger_write) may drain it and touch '
  'the ledger itself. Inert until MARSYS_FLAG_PARIPRASHNA_LEDGER_OUT_OF_PROCESS is flipped on.';

-- ═══════════════════════════════════════════════════════════════════════════════
-- 3. GRANT WALLS
-- ═══════════════════════════════════════════════════════════════════════════════
-- Shape: a broad SELECT allow-list for the serving role, then an EXPLICIT,
-- BY-NAME deny-list. The deny-list is the auditable artifact — it is the thing a
-- reviewer reads to answer "what is role_web_serve walled from?".
--
-- NOTE ON `ALL TABLES IN SCHEMA public`: this is a point-in-time snapshot. A
-- table created after this migration is NOT granted, and role_web_serve simply
-- cannot see it. That is fail-CLOSED and is the correct default for a serving
-- role — but it means new tables need an explicit grant. The cutover runbook
-- carries the verification query that lists ungranted tables. This repository has
-- no `ALTER DEFAULT PRIVILEGES` anywhere and this migration does not introduce
-- one, because default privileges are scoped to the role that creates objects and
-- this session cannot verify who that is in production.

GRANT USAGE ON SCHEMA public TO
  role_web_serve, role_orchestrator, role_ledger_write, role_jobs, role_sidecar;

-- ── 3a. role_web_serve — read the layer stack ────────────────────────────────
GRANT SELECT ON ALL TABLES IN SCHEMA public TO role_web_serve;

-- ── 3b. role_web_serve — C3 FULL WALL: no read, no write ─────────────────────
-- The calibration surfaces. PPR-25: "C3 data MUST never enter a synthesis prompt
-- or leave to a provider." A role that cannot SELECT them cannot leak them by
-- proxy, whatever the application layer does.
REVOKE ALL ON TABLE
  mimamsa_calibration,
  mimamsa_calibration_snapshot,
  mimamsa_multipliers,
  mimamsa_snapshot_cosign,
  mimamsa_adjudication_log,
  mimamsa_pool_contributions,
  mimamsa_resonance_feedback,
  mimamsa_intervention_ledger,
  gochara_v3_calibration,
  mcp_prediction_outcomes
FROM role_web_serve;

-- ── 3c. role_web_serve — C3 WRITE WALL: SELECT survives, every write revoked ──
-- The prediction ledgers. TA §7.4: "ledger SELECT-status-only. NO ledger
-- INSERT/UPDATE."
--
-- DISCLOSED DEVIATION FROM §14.10 arm-1's LITERAL TEXT — read this, do not assume
-- it was an oversight. §14.10 arm-1 says the serving role has "no SELECT on
-- ledger outcome columns". A column-level REVOKE of (outcome, outcome_value,
-- outcome_note, outcome_recorded_at) is expressible in Postgres and was
-- considered. It is NOT applied, because the SAMĪKṢĀ review tab — a shipped
-- surface the native uses, proven live by C4-LOOP-LIVE-PROOF — reads exactly
-- those columns to show a human their resolved predictions. Revoking them would
-- turn the flag flip into an outage of a working feature.
--
-- The invariant §14.10 protects is that outcome data must not reach GENERATION.
-- The review tab is a human surface, not generation, and arm-2 (the runtime
-- capability filter + assertNoCalibrationLeak on every emitter write) is what
-- enforces the generation boundary today. The clean architectural answer is to
-- split role_web_serve into a narrower generation role and a review role — that
-- is a real design decision and is NOT this lane's to rule. Raised in the cutover
-- runbook's open-questions section.
REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON TABLE
  brahma_mimamsa_prediction_ledger,
  brahma_prospective_ledger,
  mimamsa_predictions
FROM role_web_serve;

-- ── 3d. role_web_serve — conversation store R/W (TA §7.4 "conv store R/W") ───
GRANT INSERT, UPDATE, DELETE ON TABLE
  conversations,
  conversation_messages,
  message_parts,
  conversation_summaries,
  pariprashna_stream_capture
TO role_web_serve;

-- ── 3e. role_web_serve — the arm-3 outbox: INSERT only ───────────────────────
-- The serving role may REQUEST a ledger write. It may not amend or withdraw the
-- request, and it may not read the drain's bookkeeping back.
GRANT INSERT ON TABLE pariprashna_ledger_outbox TO role_web_serve;

-- ── 3f. PPR-26 — INSERT-ONLY grants on the audit surfaces ────────────────────
-- "Safety decisions, retractions, and consent transitions MUST be written
--  append-only (INSERT-only grant or hash chain)."
--
-- G1-B took the hash-chain option (chart_subject_consent_events carries
-- prev_hash/entry_hash; verifyConsentChain() in
-- platform/src/lib/pariprashna/consent/hash_chain.ts is the real detector; and
-- trg_chart_subject_consent_events_append_only blocks UPDATE/DELETE at the
-- trigger layer). This lane adds the OTHER option as an independent second
-- layer, exactly as PPR-26 permits — the hash chain proves tampering happened,
-- the grant stops it happening. Neither is reused as evidence for the other.
--
-- Deliberate asymmetry, matching G1-B's own:
--   · consent_events / exclusions / disputes — INSERT only (the record is a fact
--     that occurred; it is never amended)
--   · deletion_tombstones — INSERT + UPDATE (G1-B's `verified_empty` is set by
--     the POST-delete re-count in the same sweep: the receipt may be completed,
--     never erased). DELETE stays revoked, as does the trigger.
--   · chart_subject_consent — the CURRENT-STATE row, not an audit row. Full DML;
--     its transitions are what the append-only event chain records.
REVOKE ALL ON TABLE
  chart_subject_consent_events,
  chart_subject_exclusions,
  chart_subject_deletion_disputes,
  chart_subject_deletion_tombstones
FROM role_web_serve;
GRANT SELECT, INSERT ON TABLE
  chart_subject_consent_events,
  chart_subject_exclusions,
  chart_subject_deletion_disputes
TO role_web_serve;
GRANT SELECT, INSERT, UPDATE ON TABLE chart_subject_deletion_tombstones TO role_web_serve;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE chart_subject_consent TO role_web_serve;

-- Sequence usage for everything role_web_serve may INSERT into.
GRANT USAGE, SELECT ON SEQUENCE
  pariprashna_ledger_outbox_id_seq,
  chart_subject_consent_events_event_id_seq,
  chart_subject_exclusions_exclusion_id_seq,
  chart_subject_deletion_tombstones_tombstone_id_seq,
  chart_subject_deletion_disputes_dispute_id_seq
TO role_web_serve;

-- ── 3g. role_orchestrator — the build path ───────────────────────────────────
-- Layer-table DML + build-state writes. TA §7.4: "No conv, no ledger."
GRANT SELECT ON ALL TABLES IN SCHEMA public TO role_orchestrator;
GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO role_orchestrator;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO role_orchestrator;
-- ...then the walls. The build path writes mimamsa_predictions (mi_bhavisya is an
-- L5 build writer, delete-then-insert) so that table is NOT walled here — but the
-- conversational ledger, the consent surfaces and the conversation store are.
REVOKE ALL ON TABLE
  brahma_mimamsa_prediction_ledger,
  brahma_prospective_ledger,
  pariprashna_ledger_outbox,
  conversations,
  conversation_messages,
  message_parts,
  conversation_summaries,
  pariprashna_stream_capture,
  chart_subject_consent,
  chart_subject_consent_events,
  chart_subject_exclusions,
  chart_subject_deletion_tombstones,
  chart_subject_deletion_disputes
FROM role_orchestrator;

-- ── 3h. role_ledger_write — arm-3, and ONLY arm-3 ────────────────────────────
-- The sole holder of write on the ledgers, outcomes and calibration.
-- No DELETE anywhere: C3 retention is "permanent (research record) unless subject
-- withdrawal" (SAFETY_PRIVACY_TENANCY §5), and subject-withdrawal deletion runs
-- under the G1-B consent sweep, not under the ledger writer.
GRANT SELECT, INSERT, UPDATE ON TABLE
  brahma_mimamsa_prediction_ledger,
  brahma_prospective_ledger,
  mimamsa_predictions,
  mimamsa_calibration,
  mimamsa_calibration_snapshot,
  mimamsa_multipliers,
  mimamsa_snapshot_cosign,
  mimamsa_adjudication_log,
  mimamsa_pool_contributions,
  mimamsa_resonance_feedback,
  mimamsa_intervention_ledger,
  mcp_prediction_outcomes
TO role_ledger_write;
-- Drains the outbox: reads intents, marks them claimed/applied. No INSERT — the
-- writer must never be able to manufacture its own work item.
GRANT SELECT, UPDATE ON TABLE pariprashna_ledger_outbox TO role_ledger_write;
-- Reads it needs to validate an intent (chart exists, the message part exists).
GRANT SELECT ON TABLE charts, message_parts, conversations TO role_ledger_write;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO role_ledger_write;

-- ── 3i. role_jobs — model health, summaries, digests ─────────────────────────
GRANT SELECT ON ALL TABLES IN SCHEMA public TO role_jobs;
GRANT INSERT, UPDATE ON TABLE conversation_summaries TO role_jobs;
-- The SAMĪKṢĀ daily job transitions window_closed. That is a ledger WRITE, so it
-- belongs to role_ledger_write, not here — the daily job runs under
-- role_ledger_write after cutover. Explicitly walled so the boundary is visible:
REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON TABLE
  brahma_mimamsa_prediction_ledger,
  brahma_prospective_ledger,
  mimamsa_predictions
FROM role_jobs;
REVOKE ALL ON TABLE
  mimamsa_calibration,
  mimamsa_calibration_snapshot,
  mimamsa_multipliers,
  gochara_v3_calibration,
  pariprashna_ledger_outbox
FROM role_jobs;

-- ── 3j. role_sidecar — minimal compute-support read ──────────────────────────
-- TA §7.4 annotates the MCP edge as "NO ROLE — no DB connection exists", and that
-- is still true of platform-mcp (verified: no `pg` import, no DATABASE_URL). The
-- python sidecar, however, DOES hold a connection
-- (platform/python-sidecar/pipeline/orchestrator/db.py), and role_sidecar is that
-- role. Read-only, and walled from every C1 conversation surface and every C3
-- surface — a compute helper has no business reading either.
GRANT SELECT ON ALL TABLES IN SCHEMA public TO role_sidecar;
REVOKE ALL ON TABLE
  conversations, conversation_messages, message_parts, conversation_summaries,
  pariprashna_stream_capture, pariprashna_ledger_outbox,
  chart_subject_consent, chart_subject_consent_events, chart_subject_exclusions,
  chart_subject_deletion_tombstones, chart_subject_deletion_disputes,
  brahma_mimamsa_prediction_ledger, brahma_prospective_ledger,
  mimamsa_calibration, mimamsa_calibration_snapshot, mimamsa_multipliers,
  mimamsa_snapshot_cosign, mimamsa_adjudication_log, mimamsa_pool_contributions,
  mimamsa_resonance_feedback, mimamsa_intervention_ledger, gochara_v3_calibration,
  mcp_prediction_outcomes, life_events
FROM role_sidecar;

-- ═══════════════════════════════════════════════════════════════════════════════
-- 4. THE CHART-CONTEXT ACCESSOR (PPR-22)
-- ═══════════════════════════════════════════════════════════════════════════════
-- One function, so every policy reads the same way and there is exactly one place
-- the semantics live.
--
-- FAIL-CLOSED BY CONSTRUCTION: an unset context, an empty context, or a malformed
-- context all yield NULL. Every policy predicate compares against it with `=`, and
-- `x = NULL` is NULL, which RLS treats as "row not visible". So the failure
-- direction of a missing or garbled pin is DENY, never allow.
--
-- The malformed case returns NULL rather than raising, because raising inside a
-- row-security predicate turns one bad value into a per-row exception storm. The
-- LOUD detector lives on the application side instead:
-- `setChartContext()` in platform/src/lib/db/roles.ts validates the uuid and
-- throws before it ever reaches the database. Two layers, each honest about its
-- own job (§N.8).

CREATE OR REPLACE FUNCTION app_chart_context()
RETURNS uuid
LANGUAGE plpgsql
STABLE
PARALLEL SAFE
AS $ctx$
DECLARE
  raw text;
BEGIN
  raw := nullif(current_setting('app.chart_context', true), '');
  IF raw IS NULL THEN
    RETURN NULL;
  END IF;
  BEGIN
    RETURN raw::uuid;
  EXCEPTION WHEN others THEN
    RETURN NULL;   -- malformed pin == no pin == deny
  END;
END
$ctx$;

COMMENT ON FUNCTION app_chart_context() IS
  'PPR-22: the chart the current session is authorized for, from the `app.chart_context` GUC set '
  'per request by setChartContext() (platform/src/lib/db/roles.ts). NULL when unset, empty or '
  'malformed — and every RLS policy compares with `=`, so NULL means DENY, never allow.';

-- ═══════════════════════════════════════════════════════════════════════════════
-- 5. CHART-SCOPED RLS POLICIES (PPR-22) — CREATED, NOT ENABLED
-- ═══════════════════════════════════════════════════════════════════════════════
-- Two policies per table. RLS is permissive-OR, so a role appearing in both lists
-- would receive the union; deliberately, no role appears in both.
--
--   <table>_g1c_chart_context  TO role_web_serve, role_sidecar
--       Scoped to app_chart_context(). This is the wall PPR-22 asks for.
--
--   <table>_g1c_unscoped       TO role_orchestrator, role_ledger_write, role_jobs
--       USING (true). These roles legitimately work across charts: the build path
--       builds whichever chart it was handed, the daily job scans every open
--       prediction window, the summariser sweeps all conversations. Pinning them
--       to one chart would not be security, it would be breakage. Their wall is
--       the GRANT wall in §3, not the row filter.
--
-- `charts` ITSELF IS DELIBERATELY NOT GIVEN A CHART-CONTEXT POLICY. Two reasons,
-- both load-bearing:
--   (a) it already carries its own RLS — `0001_brahma_baseline.sql:6162-6185`
--       enables RLS on public.charts with chart_owner_policy / chart_grant_policy /
--       chart_service_policy, keyed to a DIFFERENT GUC (`app.principal_id`). That
--       is tenancy RLS and it is the right key for the chart INDEX;
--   (b) `app.chart_context` is DERIVED FROM `charts` — the request resolves which
--       chart the caller may pin by reading the grants. A chart-pin filter on the
--       table the pin is looked up in would make "list my charts" impossible and
--       force a bypass hole, and a policy with a bypass hole is worse than a
--       documented boundary.
-- HONEST FINDING, NOT FIXED HERE: `app.principal_id` is set by NOTHING in the
-- codebase today, so `chart_service_policy USING (current_setting('app.principal_id',
-- true) IS NULL OR = '')` is unconditionally TRUE — those baseline policies are a
-- §N.8 no-op-shaped signal. `setChartContext()` accepts an optional principalId and
-- sets that GUC too, which makes them real the moment a caller passes it. Turning
-- them on for everyone is a live behaviour change and is NOT this lane's call.

DO $policies$
DECLARE
  -- (table, chart-scope predicate). The predicate is the ONLY thing that varies.
  spec text[][] := ARRAY[
    -- ── C1 sacred-personal, direct chart_id ──────────────────────────────────
    ARRAY['life_events',                        'chart_id = app_chart_context()'],
    ARRAY['conversations',                      'chart_id = app_chart_context()'],
    ARRAY['chart_subject_consent',              'chart_id = app_chart_context()'],
    ARRAY['chart_subject_consent_events',       'chart_id = app_chart_context()'],
    ARRAY['chart_subject_exclusions',           'chart_id = app_chart_context()'],
    ARRAY['chart_subject_deletion_tombstones',  'chart_id = app_chart_context()'],
    ARRAY['chart_subject_deletion_disputes',    'chart_id = app_chart_context()'],
    -- `pariprashna_stream_capture.chart_id` is TEXT, not uuid, and nullable (mig
    -- 475). Cast the CONTEXT to text rather than the column to uuid: a row whose
    -- chart_id is not uuid-shaped would raise on a column cast, and an
    -- exception-per-row is not a security control. A NULL chart_id row is
    -- invisible under this policy — correct: an unattributed capture row has no
    -- chart to be authorized for.
    ARRAY['pariprashna_stream_capture',         'chart_id = app_chart_context()::text'],
    -- ── C1, reached by join ─────────────────────────────────────────────────
    ARRAY['conversation_messages',
          'EXISTS (SELECT 1 FROM conversations c WHERE c.id = conversation_messages.conversation_id'
          || ' AND c.chart_id = app_chart_context())'],
    ARRAY['message_parts',
          'EXISTS (SELECT 1 FROM conversation_messages m JOIN conversations c ON c.id = m.conversation_id'
          || ' WHERE m.id = message_parts.message_id AND c.chart_id = app_chart_context())'],
    ARRAY['conversation_summaries',
          'EXISTS (SELECT 1 FROM conversations c WHERE c.id = conversation_summaries.conversation_id'
          || ' AND c.chart_id = app_chart_context())'],
    -- ── C3 predictive ────────────────────────────────────────────────────────
    ARRAY['brahma_mimamsa_prediction_ledger',   'chart_id = app_chart_context()'],
    ARRAY['brahma_prospective_ledger',          'chart_id = app_chart_context()'],
    ARRAY['mimamsa_predictions',                'chart_id = app_chart_context()'],
    ARRAY['mimamsa_calibration',                'chart_id = app_chart_context()'],
    ARRAY['mimamsa_calibration_snapshot',       'chart_id = app_chart_context()'],
    ARRAY['mimamsa_adjudication_log',           'chart_id = app_chart_context()'],
    ARRAY['mimamsa_pool_contributions',         'chart_id = app_chart_context()'],
    ARRAY['mimamsa_resonance_feedback',         'chart_id = app_chart_context()'],
    ARRAY['mimamsa_intervention_ledger',        'chart_id = app_chart_context()'],
    -- ── The arm-3 seam ───────────────────────────────────────────────────────
    ARRAY['pariprashna_ledger_outbox',          'chart_id = app_chart_context()']
  ];
  i int;
  tbl text;
  pred text;
BEGIN
  FOR i IN 1 .. array_length(spec, 1) LOOP
    tbl  := spec[i][1];
    pred := spec[i][2];

    IF to_regclass('public.' || quote_ident(tbl)) IS NULL THEN
      RAISE EXCEPTION
        'G1C_POLICY_TARGET_MISSING: cannot create a chart-context policy on %, which does not '
        'exist. The §0 preflight should have caught this — if you are seeing it, the preflight '
        'list and the policy list have drifted apart.', tbl;
    END IF;

    EXECUTE format('DROP POLICY IF EXISTS %I ON %I', tbl || '_g1c_chart_context', tbl);
    EXECUTE format(
      'CREATE POLICY %I ON %I AS PERMISSIVE FOR ALL TO role_web_serve, role_sidecar '
      'USING (%s) WITH CHECK (%s)',
      tbl || '_g1c_chart_context', tbl, pred, pred
    );

    EXECUTE format('DROP POLICY IF EXISTS %I ON %I', tbl || '_g1c_unscoped', tbl);
    EXECUTE format(
      'CREATE POLICY %I ON %I AS PERMISSIVE FOR ALL '
      'TO role_orchestrator, role_ledger_write, role_jobs '
      'USING (true) WITH CHECK (true)',
      tbl || '_g1c_unscoped', tbl
    );
  END LOOP;
END
$policies$;

-- Deliberately absent: any `ALTER TABLE ... ENABLE ROW LEVEL SECURITY`.
-- See the header, item 2. Arming is platform/scripts/pariprashna/g1c_arm_rls.sql.

COMMIT;

-- ═══════════════════════════════════════════════════════════════════════════════
-- DOWN (manual rollback) — additive; this removes exactly what was added.
-- ═══════════════════════════════════════════════════════════════════════════════
--   -- 1. disarm first if it was ever armed (see g1c_disarm_rls.sql)
--   -- 2. drop policies
--   --    DO $$ DECLARE p record; BEGIN
--   --      FOR p IN SELECT policyname, tablename FROM pg_policies
--   --               WHERE policyname LIKE '%\_g1c\_%' LOOP
--   --        EXECUTE format('DROP POLICY IF EXISTS %I ON %I', p.policyname, p.tablename);
--   --      END LOOP; END $$;
--   -- 3. DROP FUNCTION IF EXISTS app_chart_context();
--   -- 4. DROP TABLE IF EXISTS pariprashna_ledger_outbox;
--   -- 5. REASSIGN/DROP OWNED then:
--   --    DROP ROLE IF EXISTS role_web_serve, role_orchestrator, role_ledger_write,
--   --                        role_jobs, role_sidecar;
