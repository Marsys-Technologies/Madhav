-- Migration 635: narrow amjis_app's grant on pariprashna_safety_decisions
-- (revoke DELETE, TRUNCATE, UPDATE) and on mimamsa_predictions
-- (revoke TRUNCATE only — DELETE and UPDATE are genuinely used, kept).
-- Pariparaśna v3 closeout, Phase C · extends E-001 / PPR-26 (PR #1615) · 2026-08-29
--
-- ══════════════════════════════════════════════════════════════════════════════
-- WHY THIS EXISTS
-- ══════════════════════════════════════════════════════════════════════════════
-- Native Surrogate ruling (tracker event 5e1a5a17-f7c6-4c4c-820d-b591e38950d9)
-- directed PR #1615 (migration 634, audit_log grant narrowing) to be EXTENDED to
-- cover two more tables before merge, once live DB reads confirmed `amjis_app`
-- holds the IDENTICAL over-broad grant (DELETE, INSERT, REFERENCES, SELECT,
-- TRIGGER, TRUNCATE, UPDATE) on BOTH of them — and unlike `audit_log` (empty),
-- these two are live, growing, real data: `pariprashna_safety_decisions`
-- (369+ rows) and `mimamsa_predictions` (195 rows).
--
-- ══════════════════════════════════════════════════════════════════════════════
-- TABLE 1: pariprashna_safety_decisions — revoke DELETE, TRUNCATE, UPDATE
-- ══════════════════════════════════════════════════════════════════════════════
-- Repo-wide grep of platform/, python-sidecar/, and migrations found exactly
-- TWO write shapes against this table anywhere: an INSERT in
-- platform/src/lib/pariprashna/safety/audit.ts (the append path) and SELECTs in
-- audit.ts / observability/queries.ts (read paths). NO DELETE, TRUNCATE, or
-- UPDATE caller exists anywhere in the codebase.
--
-- This table ALSO already carries a hard, unconditional append-only enforcement
-- trigger — migration 577's `trg_pariprashna_safety_decisions_append_only`
-- (`BEFORE UPDATE OR DELETE ... RAISE EXCEPTION 'APPEND_ONLY_VIOLATION'`), applied
-- to every role, not just amjis_app. So UPDATE and DELETE at the grant level are
-- already dead weight — the trigger blocks them for anyone. TRUNCATE is NOT
-- caught by a `BEFORE UPDATE OR DELETE` row trigger (TRUNCATE is a separate
-- statement class with its own trigger event), so the TRUNCATE grant is a real,
-- live exposure the trigger does nothing about — the same "destroy the evidence"
-- gap migration 634 closed for `audit_log`.
--
-- Net effect: this migration revokes all three (DELETE, TRUNCATE, UPDATE) as
-- belt-and-suspenders defense-in-depth for DELETE/UPDATE (trigger already blocks
-- them; grant narrowing removes the redundant permission so a future trigger
-- edit/DISABLE doesn't silently reopen the hole) and as the SOLE closure for
-- TRUNCATE (nothing else stops it). Unlike audit_log, there is no UPDATE
-- exception to carve out here — no idempotent-upsert or any other legitimate
-- UPDATE caller exists against this table, so §N.8 applies: an unused grant on
-- 369+ rows of real safety-decision data is worth closing, not worth leaving as
-- an open question.
--
-- ══════════════════════════════════════════════════════════════════════════════
-- TABLE 2: mimamsa_predictions — revoke TRUNCATE only; DELETE and UPDATE KEPT
-- ══════════════════════════════════════════════════════════════════════════════
-- Independently verified — NOT assumed from the audit_log or safety_decisions
-- precedent. Two genuine, live, chart-scoped write paths exist against this
-- table today, both reachable through the SAME shared connection pool amjis_app
-- serves on (`@/lib/db/client`'s `getPool()` — `PARIPRASHNA_ROLE_SEPARATION` is
-- OFF by default per platform/src/lib/db/roles.ts, so every platform query,
-- including these two, currently runs as amjis_app):
--
--   1. DELETE — platform/src/lib/cockpit/assetClearSpec.ts (JL-020 clear-
--      allowlist), executed by platform/src/app/api/cockpit/clear/execute/route.ts
--      via `getPool()`. The cockpit "clear chart" feature's derived DELETE for
--      the mi_bhavisya asset is explicitly SCOPED, not a bare table wipe:
--      `DELETE FROM mimamsa_predictions WHERE chart_id = $1 AND lifecycle_status
--      IN ('pending', 'due')` — assetClearSpec.ts's own header names this table
--      an IRREPLACEABLE surface precisely because already-resolved predictions
--      (confirmed/falsified/expired) must survive a chart rebuild; only rows
--      still awaiting an outcome are cleared. The SAME scoped shape is what the
--      build-path writer `mi_bhavisya.py` issues during a normal delete-then-
--      insert rebuild (line 223) — this is a designed, tested, actively-used
--      lifecycle operation, not incidental access.
--   2. UPDATE — platform/src/lib/retrieval/registry/layers/L5_mimamsa/
--      prediction_lifecycle_sweep.ts (wired into the L5_mimamsa capability
--      index, EL-58), executed via the same `getPool()`/`query()` path. Sweeps
--      lapsed `pending`/`due` predictions with no candidate LEL match forward to
--      the terminal `expired` state: `UPDATE mimamsa_predictions SET
--      lifecycle_status = 'expired' WHERE chart_id = $1 AND prediction_id = $2`.
--      Scoped to one column, one row, one deliberate state transition — the
--      same "genuine, bounded, actively-used write" shape as audit_log's
--      idempotent upsert, not an open-ended content-editable UPDATE.
--
-- These are the CURRENT live reality, not the end state: migration 576 already
-- revokes INSERT/UPDATE/DELETE/TRUNCATE on `mimamsa_predictions` from the
-- FUTURE `role_web_serve` role (§3c, "ledger SELECT-status-only"), because that
-- role is meant to be fully read-only on C3 predictive tables once role
-- separation is armed. `role_web_serve` is flag-gated OFF today (per
-- roles.ts's own module header) — activating it is a separate, disclosed,
-- not-yet-ruled cutover (576 §3c's own "raised in the cutover runbook's
-- open-questions section", not this lane's to decide). Revoking DELETE/UPDATE
-- from `amjis_app` NOW, before that cutover exists, would break the cockpit
-- clear feature and the EL-58 lifecycle sweep in production TODAY for no
-- narrowing benefit `role_web_serve`'s wall doesn't already plan to provide
-- properly (via a real role swap, not a grant amjis_app still needs). So DELETE
-- and UPDATE are kept on amjis_app; TRUNCATE — for which no caller of any kind
-- was found anywhere in platform/, python-sidecar/, or migrations — is revoked,
-- matching the audit_log pattern exactly for that one privilege.
--
-- ══════════════════════════════════════════════════════════════════════════════
-- WHAT THIS MIGRATION DOES *NOT* DO
-- ══════════════════════════════════════════════════════════════════════════════
--   1. It does not touch SELECT, INSERT, TRIGGER, or REFERENCES on either
--      table — unimplicated by this finding, same scoping discipline as 634.
--   2. It does not revoke DELETE or UPDATE on mimamsa_predictions — see the
--      independent per-table analysis above; both have live, scoped, tested
--      callers running under amjis_app today.
--   3. It is NOT applied to production by this session. Proposed, scratch-DB-
--      tested, awaiting Native Surrogate + integrator sign-off on the SPECIFIC
--      final diff, per PR #1615's own "NOT SAFE TO AUTO-MERGE" protocol notice
--      (merging to main auto-deploys and auto-runs migrate.ts against
--      production with no separate apply step).
--
-- Idempotent: `to_regclass`/`pg_roles` preflight per table, plain REVOKE
-- (REVOKE of an absent privilege is a documented no-op, not an error), and a
-- `has_table_privilege` postcondition DO block per table that RAISEs if the
-- claim doesn't actually hold afterward (§N.8: a detector that measures the
-- specific claim, not a proxy). Safe to re-run.
-- §N.4: surgical, verified. NEVER edit this file after it has been applied.

BEGIN;

-- ── 0. PREFLIGHT — fail loudly if either target table or the role is missing ──
DO $preflight$
BEGIN
  IF to_regclass('public.pariprashna_safety_decisions') IS NULL THEN
    RAISE EXCEPTION
      'E635_PREFLIGHT_MISSING_TABLE: migration 635 narrows a grant on '
      'public.pariprashna_safety_decisions, which does not exist in this database.';
  END IF;

  IF to_regclass('public.mimamsa_predictions') IS NULL THEN
    RAISE EXCEPTION
      'E635_PREFLIGHT_MISSING_TABLE: migration 635 narrows a grant on '
      'public.mimamsa_predictions, which does not exist in this database.';
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'amjis_app') THEN
    RAISE EXCEPTION
      'E635_PREFLIGHT_MISSING_ROLE: migration 635 narrows amjis_app''s grants, '
      'but role amjis_app does not exist in this database.';
  END IF;
END
$preflight$;

-- ── 1a. REVOKE — pariprashna_safety_decisions: close the full write surface ──
-- REVOKE of a privilege the grantee does not currently hold is a documented
-- Postgres no-op, which is what makes this safe to re-run.
REVOKE DELETE, TRUNCATE, UPDATE ON TABLE public.pariprashna_safety_decisions FROM amjis_app;

-- ── 1b. REVOKE — mimamsa_predictions: TRUNCATE only ──────────────────────────
REVOKE TRUNCATE ON TABLE public.mimamsa_predictions FROM amjis_app;

-- ── 2a. POST-CONDITION — pariprashna_safety_decisions ────────────────────────
-- §N.8: checks the claim directly, for the full surviving-and-revoked privilege
-- set, rather than trusting the REVOKE statement ran cleanly.
DO $postcondition_safety_decisions$
BEGIN
  IF has_table_privilege('amjis_app', 'public.pariprashna_safety_decisions', 'DELETE') THEN
    RAISE EXCEPTION
      'E635_POSTCONDITION_FAILED: amjis_app still holds DELETE on pariprashna_safety_decisions after REVOKE.';
  END IF;
  IF has_table_privilege('amjis_app', 'public.pariprashna_safety_decisions', 'TRUNCATE') THEN
    RAISE EXCEPTION
      'E635_POSTCONDITION_FAILED: amjis_app still holds TRUNCATE on pariprashna_safety_decisions after REVOKE.';
  END IF;
  IF has_table_privilege('amjis_app', 'public.pariprashna_safety_decisions', 'UPDATE') THEN
    RAISE EXCEPTION
      'E635_POSTCONDITION_FAILED: amjis_app still holds UPDATE on pariprashna_safety_decisions after REVOKE.';
  END IF;
  -- Confirm the untouched privileges survived, so a future edit to this file
  -- cannot accidentally widen its blast radius without this check catching it.
  IF NOT has_table_privilege('amjis_app', 'public.pariprashna_safety_decisions', 'SELECT') THEN
    RAISE EXCEPTION
      'E635_POSTCONDITION_FAILED: amjis_app unexpectedly lost SELECT on pariprashna_safety_decisions.';
  END IF;
  IF NOT has_table_privilege('amjis_app', 'public.pariprashna_safety_decisions', 'INSERT') THEN
    RAISE EXCEPTION
      'E635_POSTCONDITION_FAILED: amjis_app unexpectedly lost INSERT on pariprashna_safety_decisions.';
  END IF;
  IF NOT has_table_privilege('amjis_app', 'public.pariprashna_safety_decisions', 'TRIGGER') THEN
    RAISE EXCEPTION
      'E635_POSTCONDITION_FAILED: amjis_app unexpectedly lost TRIGGER on pariprashna_safety_decisions.';
  END IF;
  IF NOT has_table_privilege('amjis_app', 'public.pariprashna_safety_decisions', 'REFERENCES') THEN
    RAISE EXCEPTION
      'E635_POSTCONDITION_FAILED: amjis_app unexpectedly lost REFERENCES on pariprashna_safety_decisions.';
  END IF;
END
$postcondition_safety_decisions$;

-- ── 2b. POST-CONDITION — mimamsa_predictions ─────────────────────────────────
DO $postcondition_mimamsa_predictions$
BEGIN
  IF has_table_privilege('amjis_app', 'public.mimamsa_predictions', 'TRUNCATE') THEN
    RAISE EXCEPTION
      'E635_POSTCONDITION_FAILED: amjis_app still holds TRUNCATE on mimamsa_predictions after REVOKE.';
  END IF;
  -- DELETE and UPDATE are deliberately NOT revoked (see header) — confirm both
  -- survived, alongside the other untouched privileges, so a future edit to
  -- this file cannot accidentally widen its blast radius unnoticed.
  IF NOT has_table_privilege('amjis_app', 'public.mimamsa_predictions', 'DELETE') THEN
    RAISE EXCEPTION
      'E635_POSTCONDITION_FAILED: amjis_app unexpectedly lost DELETE on mimamsa_predictions '
      '(DELETE is intentionally NOT revoked by this migration — see header).';
  END IF;
  IF NOT has_table_privilege('amjis_app', 'public.mimamsa_predictions', 'UPDATE') THEN
    RAISE EXCEPTION
      'E635_POSTCONDITION_FAILED: amjis_app unexpectedly lost UPDATE on mimamsa_predictions '
      '(UPDATE is intentionally NOT revoked by this migration — see header).';
  END IF;
  IF NOT has_table_privilege('amjis_app', 'public.mimamsa_predictions', 'SELECT') THEN
    RAISE EXCEPTION
      'E635_POSTCONDITION_FAILED: amjis_app unexpectedly lost SELECT on mimamsa_predictions.';
  END IF;
  IF NOT has_table_privilege('amjis_app', 'public.mimamsa_predictions', 'INSERT') THEN
    RAISE EXCEPTION
      'E635_POSTCONDITION_FAILED: amjis_app unexpectedly lost INSERT on mimamsa_predictions.';
  END IF;
  IF NOT has_table_privilege('amjis_app', 'public.mimamsa_predictions', 'TRIGGER') THEN
    RAISE EXCEPTION
      'E635_POSTCONDITION_FAILED: amjis_app unexpectedly lost TRIGGER on mimamsa_predictions.';
  END IF;
  IF NOT has_table_privilege('amjis_app', 'public.mimamsa_predictions', 'REFERENCES') THEN
    RAISE EXCEPTION
      'E635_POSTCONDITION_FAILED: amjis_app unexpectedly lost REFERENCES on mimamsa_predictions.';
  END IF;
END
$postcondition_mimamsa_predictions$;

COMMIT;

-- ═══════════════════════════════════════════════════════════════════════════════
-- DOWN (manual rollback) — additive; this restores exactly what was revoked.
-- ═══════════════════════════════════════════════════════════════════════════════
--   GRANT DELETE, TRUNCATE, UPDATE ON TABLE pariprashna_safety_decisions TO amjis_app;
--   GRANT TRUNCATE ON TABLE mimamsa_predictions TO amjis_app;
