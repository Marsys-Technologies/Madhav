-- Migration 136: chart_facts audit tables extension + purge function
-- A3-S3: Extends chart_facts_history and chart_facts_supersedence with new A3 schema columns,
-- recreates the audit trigger to capture fact_subject, and adds a 30-day purge function.
-- Idempotent: all changes use ADD COLUMN IF NOT EXISTS and CREATE OR REPLACE.

-- 1. Add fact_subject to chart_facts_history
ALTER TABLE chart_facts_history
  ADD COLUMN IF NOT EXISTS fact_subject TEXT DEFAULT 'CHART';

-- 2. Add ayanamsha_id and engine_version to chart_facts_supersedence
ALTER TABLE chart_facts_supersedence
  ADD COLUMN IF NOT EXISTS ayanamsha_id TEXT DEFAULT '';

ALTER TABLE chart_facts_supersedence
  ADD COLUMN IF NOT EXISTS engine_version TEXT DEFAULT '';

-- 3. Recreate audit trigger (drops old trigger + old function, creates new function + trigger)
DROP TRIGGER IF EXISTS trg_chart_facts_audit ON chart_facts;

CREATE OR REPLACE FUNCTION fn_chart_facts_audit_trigger()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    INSERT INTO chart_facts_history (fact_id, change_type, changed_at, old_value, new_value, build_id, engine_version)
    VALUES (OLD.fact_id, 'delete', NOW(),
            jsonb_build_object('fact_category', OLD.fact_category, 'fact_subject', OLD.fact_subject,
                               'fact_key', OLD.fact_key, 'fact_value_text', OLD.fact_value_text,
                               'fact_value_num', OLD.fact_value_num, 'verification_pass_status', OLD.verification_pass_status),
            NULL, OLD.build_id, COALESCE(OLD.engine_version, ''));
    RETURN OLD;
  ELSIF TG_OP = 'UPDATE' THEN
    INSERT INTO chart_facts_history (fact_id, change_type, changed_at, old_value, new_value, build_id, engine_version)
    VALUES (NEW.fact_id, 'update', NOW(),
            jsonb_build_object('fact_category', OLD.fact_category, 'fact_subject', OLD.fact_subject,
                               'fact_key', OLD.fact_key, 'fact_value_text', OLD.fact_value_text,
                               'verification_pass_status', OLD.verification_pass_status),
            jsonb_build_object('fact_category', NEW.fact_category, 'fact_subject', NEW.fact_subject,
                               'fact_key', NEW.fact_key, 'fact_value_text', NEW.fact_value_text,
                               'verification_pass_status', NEW.verification_pass_status),
            NEW.build_id, COALESCE(NEW.engine_version, ''));
    RETURN NEW;
  ELSIF TG_OP = 'INSERT' THEN
    INSERT INTO chart_facts_history (fact_id, change_type, changed_at, old_value, new_value, build_id, engine_version)
    VALUES (NEW.fact_id, 'insert', NOW(), NULL,
            jsonb_build_object('fact_category', NEW.fact_category, 'fact_subject', NEW.fact_subject,
                               'fact_key', NEW.fact_key, 'fact_value_text', NEW.fact_value_text,
                               'verification_pass_status', NEW.verification_pass_status),
            NEW.build_id, COALESCE(NEW.engine_version, ''));
    RETURN NEW;
  END IF;
  RETURN NULL;
END;
$$;

CREATE TRIGGER trg_chart_facts_audit
  AFTER INSERT OR UPDATE OR DELETE ON chart_facts
  FOR EACH ROW EXECUTE FUNCTION fn_chart_facts_audit_trigger();

-- 4. Purge function: delete chart_facts_history rows older than 30 days
CREATE OR REPLACE FUNCTION fn_purge_chart_facts_history()
RETURNS void LANGUAGE sql AS $$
  DELETE FROM chart_facts_history WHERE changed_at < NOW() - INTERVAL '30 days';
$$;
