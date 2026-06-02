-- platform/migrations/057_aiops_routing_override_trigger.sql
-- Migration: Phase 3C observability hardening — DB trigger on llm_stack_routing_override.
--
-- Rationale: The Control Panel API routes write to llm_config_audit on PUT/DELETE,
-- but direct DB writes (psql, migrations, background jobs) bypass that path.
-- The 2026-05-15 3-day silent demote happened via a direct DB insert that produced
-- no audit entry. This trigger closes the gap by writing to llm_config_audit for
-- ALL mutations, regardless of source.
--
-- Deduplication: The API routes continue writing their own audit entries. The trigger
-- writes a second row with notes='db_trigger'. Consumers can deduplicate by filtering
-- notes!='db_trigger' for UI display, or include both for a complete audit trail.

BEGIN;

CREATE OR REPLACE FUNCTION llm_routing_override_audit_fn()
RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    INSERT INTO llm_config_audit
      (occurred_at, actor_user_id, action, scope, stack, call_type, before_value, after_value, notes)
    VALUES (
      NOW(),
      COALESCE(NEW.updated_by, 'db_direct'),
      'set_routing',
      NEW.scope,
      NEW.stack,
      NEW.call_type,
      NULL,
      jsonb_build_object(
        'primary_model', NEW.primary_model,
        'fallback_model', NEW.fallback_model,
        'expires_at',    NEW.expires_at
      ),
      'db_trigger'
    );
  ELSIF TG_OP = 'UPDATE' THEN
    INSERT INTO llm_config_audit
      (occurred_at, actor_user_id, action, scope, stack, call_type, before_value, after_value, notes)
    VALUES (
      NOW(),
      COALESCE(NEW.updated_by, 'db_direct'),
      'set_routing',
      NEW.scope,
      NEW.stack,
      NEW.call_type,
      jsonb_build_object(
        'primary_model', OLD.primary_model,
        'fallback_model', OLD.fallback_model,
        'expires_at',    OLD.expires_at
      ),
      jsonb_build_object(
        'primary_model', NEW.primary_model,
        'fallback_model', NEW.fallback_model,
        'expires_at',    NEW.expires_at
      ),
      'db_trigger'
    );
  ELSIF TG_OP = 'DELETE' THEN
    INSERT INTO llm_config_audit
      (occurred_at, actor_user_id, action, scope, stack, call_type, before_value, after_value, notes)
    VALUES (
      NOW(),
      COALESCE(OLD.updated_by, 'db_direct'),
      'reset_routing',
      OLD.scope,
      OLD.stack,
      OLD.call_type,
      jsonb_build_object(
        'primary_model', OLD.primary_model,
        'fallback_model', OLD.fallback_model,
        'expires_at',    OLD.expires_at
      ),
      NULL,
      'db_trigger'
    );
  END IF;
  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER llm_routing_override_audit
AFTER INSERT OR UPDATE OR DELETE ON llm_stack_routing_override
FOR EACH ROW EXECUTE FUNCTION llm_routing_override_audit_fn();

COMMIT;

-- Down:
-- DROP TRIGGER IF EXISTS llm_routing_override_audit ON llm_stack_routing_override;
-- DROP FUNCTION IF EXISTS llm_routing_override_audit_fn();
