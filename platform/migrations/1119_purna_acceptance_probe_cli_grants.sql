-- 1119_purna_acceptance_probe_cli_grants.sql
--
-- Purna Anveṣaṇa acceptance — provider lane (owner-surrogate ruling OSR-007, campaign
-- madhav-purna-anvesana).
--
-- WHY: the dedicated acceptance principal `probe-service-account` (role `guest`, status `active`)
-- cannot complete a planner call on its own Google AI Console connection (15/15 planner
-- invocations ended AI_EXECUTION_FAILED), the legacy non-BYOK route is closed by
-- MARSYS_FLAG_AI_CONSOLE_BYOK=true, and no system-owned provider connection exists. The
-- system-owned local-CLI bridge route (private VM `marsys-jis-ai-cli`, PR #2753) is reachable for
-- `codex` and `claude_code`; the only gate is a non-revoked `ai_cli_grants` row.
--
-- WHAT: one non-revoked `ai_cli_grants` row for exactly two installations (`codex`,
-- `claude_code`) for exactly one principal (`probe-service-account`), plus one honest
-- `ai_configuration_audit_log` row (`cli_granted`) per newly created grant.
--
-- HONESTY: `granted_by` and the audit `actor_user_id` are the probe principal itself, never a
-- human admin — the admin route (PATCH /api/admin/users/[id]/ai-cli-grants) requires
-- super_admin and this migration must not impersonate one. The audit table has no detail column;
-- the provenance is this file and the OSR-007 ledger entry.
--
-- SAFETY: no other user's grant is read or changed; an existing row (granted or explicitly
-- revoked) is never modified (ON CONFLICT DO NOTHING preserves a revocation); no privilege,
-- role, credential, flag or IAM is changed; the probe still holds only `view` chart grants. It is
-- a no-op on any database without the probe profile or the installation rows (CI, local), and
-- is idempotent: a second run inserts nothing and audits nothing.
--
-- The runner wraps each file in its own transaction; no BEGIN/COMMIT here.

WITH targets AS (
  SELECT p.id AS user_id, i.cli_id
    FROM profiles p
    JOIN ai_cli_installations i ON i.cli_id IN ('codex', 'claude_code')
   WHERE p.id = 'probe-service-account'
     AND p.status = 'active'
),
granted AS (
  INSERT INTO ai_cli_grants (user_id, cli_id, granted_by)
  SELECT t.user_id, t.cli_id, t.user_id FROM targets t
  ON CONFLICT (user_id, cli_id) DO NOTHING
  RETURNING user_id, cli_id
)
INSERT INTO ai_configuration_audit_log (user_id, actor_user_id, event, cli_id)
SELECT g.user_id, g.user_id, 'cli_granted', g.cli_id FROM granted g;

-- Post-condition (fails the migration if the intended state is absent where it should exist).
DO $$
DECLARE
  probe_active boolean;
  missing      text;
BEGIN
  SELECT EXISTS (SELECT 1 FROM profiles WHERE id = 'probe-service-account' AND status = 'active')
    INTO probe_active;
  IF NOT probe_active THEN
    RAISE NOTICE 'migration 1119: probe-service-account profile absent or inactive; nothing to grant (no-op)';
    RETURN;
  END IF;

  SELECT string_agg(i.cli_id, ',') INTO missing
    FROM ai_cli_installations i
   WHERE i.cli_id IN ('codex', 'claude_code')
     AND NOT EXISTS (
       SELECT 1 FROM ai_cli_grants g
        WHERE g.user_id = 'probe-service-account' AND g.cli_id = i.cli_id);
  IF missing IS NOT NULL THEN
    RAISE EXCEPTION 'migration 1119: probe-service-account has no grant row for: %', missing;
  END IF;

  -- Scope guard: this migration must never widen beyond the two named CLIs for the probe.
  IF EXISTS (
    SELECT 1 FROM ai_cli_grants g
     WHERE g.user_id = 'probe-service-account'
       AND g.cli_id NOT IN ('codex', 'claude_code')
       AND g.revoked_at IS NULL
  ) THEN
    RAISE EXCEPTION 'migration 1119: unexpected active grant for probe-service-account outside codex/claude_code';
  END IF;
END $$;
