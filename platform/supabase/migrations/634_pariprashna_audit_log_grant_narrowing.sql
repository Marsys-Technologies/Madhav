-- Migration 634: narrow amjis_app's grant on audit_log — revoke DELETE, TRUNCATE.
-- Paripraśna v3 stream S5 (security/privacy), lane E-001 · finding E-001 / PPR-26 · 2026-08-28
--
-- ══════════════════════════════════════════════════════════════════════════════
-- WHY THIS EXISTS
-- ══════════════════════════════════════════════════════════════════════════════
-- Confirmed LIVE, read-only, against production Cloud SQL
-- (madhav-astrology:asia-south1:amjis-postgres, db amjis): the app's serving
-- credential `amjis_app` currently holds DELETE, UPDATE, INSERT, SELECT,
-- TRIGGER, TRUNCATE, and REFERENCES on `audit_log`.
--
-- `audit_log` is the LLM-query audit trail (platform/src/lib/audit/writer.ts /
-- consumer.ts) — every synthesized answer's query text, tools called,
-- validators run, and final output. PPR-26 (migration 576's own header, line
-- 21-23): "safety/retraction/consent audit rows MUST be append-only
-- (INSERT-only grant OR hash chain)." `audit_log` is a DIFFERENT audit surface
-- from the ones migration 576 already hash-chained (chart_subject_consent_events)
-- — it has never had PPR-26 applied to it. A credential that can DELETE or
-- TRUNCATE its own audit trail can destroy the evidence of its own prior
-- actions; a credential that can UPDATE it can rewrite history. This migration
-- closes the DELETE/TRUNCATE half of that gap.
--
-- ══════════════════════════════════════════════════════════════════════════════
-- WHAT THIS MIGRATION DOES *NOT* DO — READ THIS BEFORE ASSUMING IT'S THE WHOLE FIX
-- ══════════════════════════════════════════════════════════════════════════════
--   1. UPDATE is NOT revoked here. `writer.ts`'s single write path is
--      `INSERT ... ON CONFLICT ON CONSTRAINT uq_audit_log_query_id DO UPDATE SET
--      <every content column> = EXCLUDED.<column>` — an intentional idempotent
--      upsert keyed on query_id, actively used and actively tested
--      (`platform/src/lib/audit/__tests__/writer.test.ts` "writeAuditLog —
--      idempotency" literally re-writes a row with a DIFFERENT final_output and
--      asserts the same UPDATE SQL fires). That means UPDATE genuinely can
--      change already-written audit content on a second call with the same
--      query_id, not merely re-affirm identical values — a real, distinct
--      history-rewrite exposure from the DELETE/TRUNCATE one this migration
--      closes. Narrowing it safely (e.g. a trigger that rejects a changed
--      final_output/tools_called/etc. on UPDATE) was evaluated and NOT pursued
--      in this pass: it is not possible to tell, from the schema alone, whether
--      a legitimate retry is ever expected to carry different content (e.g. a
--      token count finalized after a partial write) versus purely accidental
--      drift — bounding it wrong would either leave a hole or break the
--      idempotent-retry path writer.ts depends on today. This is left OPEN,
--      not silently declared safe (§N.7 item 6) — see the PR description for
--      the full writeup.
--
--   2. This migration is NOT applied to production by this session. It is a
--      proposed, scratch-DB-tested artifact awaiting Native Surrogate +
--      integrator sign-off, per this stream's charter (mirrors how PR #1598
--      landed a narrowed proof for a different RLS finding without touching
--      production). `migrate.ts`'s deploy-time runner will pick this file up
--      on the next deploy ONLY once this PR merges to main — merging is itself
--      the gated act here, not a separate manual apply step.
--
--   3. No other privilege on `audit_log` is touched: SELECT, INSERT, TRIGGER,
--      REFERENCES survive unchanged (INSERT is the writer's normal path;
--      SELECT/TRIGGER/REFERENCES are not implicated by PPR-26's append-only
--      requirement and this session found no evidence narrowing them is safe
--      or necessary).
--
-- Idempotent: `to_regclass` preflight, plain REVOKE (REVOKE of a privilege
-- already absent is a no-op, not an error), and a post-condition DO block that
-- RAISEs if the claim isn't actually true afterward (§N.8: a detector that
-- measures the specific claim, not a proxy). Safe to re-run.
-- §N.4: surgical, verified. NEVER edit this file after it has been applied.

BEGIN;

-- ── 0. PREFLIGHT — fail loudly if the target table or role does not exist ───
-- §N.8: asserting "amjis_app is walled from DELETE/TRUNCATE on audit_log" is
-- worthless if the REVOKE silently no-oped because either name was wrong.
DO $preflight$
BEGIN
  IF to_regclass('public.audit_log') IS NULL THEN
    RAISE EXCEPTION
      'E001_PREFLIGHT_MISSING_TABLE: migration 634 narrows a grant on public.audit_log, '
      'which does not exist in this database. Refusing to apply a grant change against a '
      'table that is not there.';
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'amjis_app') THEN
    RAISE EXCEPTION
      'E001_PREFLIGHT_MISSING_ROLE: migration 634 narrows amjis_app''s grant on audit_log, '
      'but role amjis_app does not exist in this database.';
  END IF;
END
$preflight$;

-- ── 1. REVOKE — close the destroy-the-evidence half of PPR-26 for audit_log ──
-- REVOKE of a privilege the grantee does not currently hold is a documented
-- Postgres no-op (not an error), which is what makes this safe to re-run.
-- Schema-qualified to match the preflight's to_regclass('public.audit_log')
-- check exactly — no ambiguity via search_path.
REVOKE DELETE, TRUNCATE ON TABLE public.audit_log FROM amjis_app;

-- ── 2. POST-CONDITION — a real detector for the claim this migration makes ──
-- §N.8: the claim is "amjis_app can no longer DELETE or TRUNCATE audit_log,
-- and its remaining legitimate privileges (SELECT, INSERT, UPDATE, TRIGGER,
-- REFERENCES) are untouched." This checks the claim directly, for ALL FIVE
-- surviving privileges named in header item 3 (not just three of them),
-- rather than trusting the REVOKE statement above ran without silently
-- affecting the wrong grantee or a wider set of privileges than intended.
DO $postcondition$
BEGIN
  IF has_table_privilege('amjis_app', 'public.audit_log', 'DELETE') THEN
    RAISE EXCEPTION
      'E001_POSTCONDITION_FAILED: amjis_app still holds DELETE on audit_log after REVOKE.';
  END IF;
  IF has_table_privilege('amjis_app', 'public.audit_log', 'TRUNCATE') THEN
    RAISE EXCEPTION
      'E001_POSTCONDITION_FAILED: amjis_app still holds TRUNCATE on audit_log after REVOKE.';
  END IF;
  -- Deliberately NOT revoked (see header item 1 for UPDATE, item 3 for the
  -- rest) — confirm all five survived so a future edit to this file cannot
  -- accidentally widen its blast radius without this check catching it.
  IF NOT has_table_privilege('amjis_app', 'public.audit_log', 'SELECT') THEN
    RAISE EXCEPTION
      'E001_POSTCONDITION_FAILED: amjis_app unexpectedly lost SELECT on audit_log.';
  END IF;
  IF NOT has_table_privilege('amjis_app', 'public.audit_log', 'INSERT') THEN
    RAISE EXCEPTION
      'E001_POSTCONDITION_FAILED: amjis_app unexpectedly lost INSERT on audit_log.';
  END IF;
  IF NOT has_table_privilege('amjis_app', 'public.audit_log', 'UPDATE') THEN
    RAISE EXCEPTION
      'E001_POSTCONDITION_FAILED: amjis_app unexpectedly lost UPDATE on audit_log '
      '(UPDATE is intentionally NOT revoked by this migration — see header item 1).';
  END IF;
  IF NOT has_table_privilege('amjis_app', 'public.audit_log', 'TRIGGER') THEN
    RAISE EXCEPTION
      'E001_POSTCONDITION_FAILED: amjis_app unexpectedly lost TRIGGER on audit_log.';
  END IF;
  IF NOT has_table_privilege('amjis_app', 'public.audit_log', 'REFERENCES') THEN
    RAISE EXCEPTION
      'E001_POSTCONDITION_FAILED: amjis_app unexpectedly lost REFERENCES on audit_log.';
  END IF;
END
$postcondition$;

COMMIT;

-- ═══════════════════════════════════════════════════════════════════════════════
-- DOWN (manual rollback) — additive; this restores exactly what was revoked.
-- ═══════════════════════════════════════════════════════════════════════════════
--   GRANT DELETE, TRUNCATE ON TABLE audit_log TO amjis_app;
