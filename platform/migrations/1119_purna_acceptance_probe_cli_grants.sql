-- 1119_purna_acceptance_probe_cli_grants.sql
--
-- Purna Anveṣaṇa acceptance — provider lane (owner-surrogate rulings OSR-007 / OSR-011, campaign
-- madhav-purna-anvesana; independent security + migration-guard review recorded in the ledger).
--
-- WHY: the dedicated acceptance principal `probe-service-account` (role `guest`, status `active`,
-- chart_grants 'view' only) cannot complete a planner call on its own Google AI Console
-- connection (every planner invocation ended AI_EXECUTION_FAILED), the legacy non-BYOK route is
-- closed by MARSYS_FLAG_AI_CONSOLE_BYOK=true, and no system-owned provider connection exists. The
-- system-owned local-CLI bridge (private VM `marsys-jis-ai-cli`, PR #2753) is reachable for
-- `claude_code`; the only gate is a non-revoked `ai_cli_grants` row. `claude_code` is chosen over
-- `codex` deliberately: the bridge runs it tool-less (`--tools ''`, empty MCP config), so it is the
-- strictly smaller grant, and its catalog row supports structured output for the planner role.
--
-- WHAT: one non-revoked `ai_cli_grants` row for exactly one installation (`claude_code`) for
-- exactly one principal (`probe-service-account`), plus one `ai_configuration_audit_log`
-- (`cli_granted`) row and one `admin_audit_log` (`ai_cli_grant`) row per newly created grant.
--
-- HONESTY: `granted_by` / audit actors are the probe principal itself, never a human admin: the
-- admin route (PATCH /api/admin/users/[id]/ai-cli-grants) requires super_admin and this migration
-- must not impersonate one. `granted_by` is only written, never read for authority (the runtime
-- gate checks a non-revoked row). The admin audit row's detail names this migration as the source.
--
-- SAFETY: no other user's grant is read or changed; an existing row (granted or explicitly
-- revoked) is never modified (ON CONFLICT DO NOTHING preserves a revocation); no privilege, role,
-- credential, flag or IAM is changed. The whole body is guarded on the AI Console tables existing:
-- on a database where this file sorts before 1124 (fresh CI / local / rebuild) it is a NOTICE-only
-- no-op and blocks nothing. It is also a no-op without an active probe profile or the installation
-- row, and idempotent (a second run inserts and audits nothing).
--
-- The runner wraps each file in its own transaction; no BEGIN/COMMIT here.

DO $$
DECLARE
  granted_count integer;
BEGIN
  IF to_regclass('public.profiles') IS NULL
     OR to_regclass('public.ai_cli_installations') IS NULL
     OR to_regclass('public.ai_cli_grants') IS NULL
     OR to_regclass('public.ai_configuration_audit_log') IS NULL
     OR to_regclass('public.admin_audit_log') IS NULL THEN
    RAISE NOTICE 'migration 1119: AI Console / audit tables not present yet; nothing to grant (no-op)';
    RETURN;
  END IF;

  IF NOT EXISTS (SELECT 1 FROM profiles WHERE id = 'probe-service-account' AND status = 'active') THEN
    RAISE NOTICE 'migration 1119: probe-service-account profile absent or inactive; nothing to grant (no-op)';
    RETURN;
  END IF;

  IF NOT EXISTS (SELECT 1 FROM ai_cli_installations WHERE cli_id = 'claude_code') THEN
    RAISE NOTICE 'migration 1119: claude_code installation row absent; nothing to grant (no-op)';
    RETURN;
  END IF;

  WITH granted AS (
    INSERT INTO ai_cli_grants (user_id, cli_id, granted_by)
    VALUES ('probe-service-account', 'claude_code', 'probe-service-account')
    ON CONFLICT (user_id, cli_id) DO NOTHING
    RETURNING user_id, cli_id
  ),
  config_audit AS (
    INSERT INTO ai_configuration_audit_log (user_id, actor_user_id, event, cli_id)
    SELECT g.user_id, g.user_id, 'cli_granted', g.cli_id FROM granted g
    RETURNING 1
  ),
  admin_audit AS (
    INSERT INTO admin_audit_log (actor_id, action, target_user_id, detail)
    SELECT g.user_id, 'ai_cli_grant', g.user_id,
           jsonb_build_object('cliId', g.cli_id, 'source', 'migration 1119 (Purna OSR-007)')
      FROM granted g
    RETURNING 1
  )
  SELECT count(*) INTO granted_count FROM granted;

  IF NOT EXISTS (
    SELECT 1 FROM ai_cli_grants WHERE user_id = 'probe-service-account' AND cli_id = 'claude_code'
  ) THEN
    RAISE EXCEPTION 'migration 1119: probe-service-account has no claude_code grant row after insert';
  END IF;

  IF granted_count = 0 THEN
    RAISE NOTICE 'migration 1119: grant row already present (granted or explicitly revoked); left unchanged';
  END IF;

  -- Informational only: this migration never widens beyond claude_code, but it also must not block a
  -- deploy because an admin separately granted the probe something else.
  IF EXISTS (
    SELECT 1 FROM ai_cli_grants g
     WHERE g.user_id = 'probe-service-account' AND g.cli_id <> 'claude_code' AND g.revoked_at IS NULL
  ) THEN
    RAISE NOTICE 'migration 1119: probe-service-account holds other active CLI grants not created by this migration';
  END IF;
END $$;
