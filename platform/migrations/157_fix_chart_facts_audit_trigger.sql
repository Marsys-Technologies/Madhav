-- Migration 157: fix audit trigger column name mismatch
-- fn_chart_facts_audit_trigger referenced NEW.fact_value_text but the actual
-- column is value_text. Applied directly 2026-05-31; file is audit record.
CREATE OR REPLACE FUNCTION fn_chart_facts_audit_trigger() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    INSERT INTO chart_facts_history (fact_id, change_type, changed_at, old_value, new_value, build_id, engine_version)
    VALUES (OLD.fact_id, 'delete', NOW(),
            jsonb_build_object('fact_category', OLD.fact_category, 'fact_subject', OLD.fact_subject,
                               'fact_key', OLD.fact_key, 'fact_value_text', OLD.value_text,
                               'fact_value_num', OLD.value_number, 'verification_pass_status', OLD.verification_pass_status),
            NULL, OLD.build_id, COALESCE(OLD.engine_version, ''));
    RETURN OLD;
  ELSIF TG_OP = 'UPDATE' THEN
    INSERT INTO chart_facts_history (fact_id, change_type, changed_at, old_value, new_value, build_id, engine_version)
    VALUES (NEW.fact_id, 'update', NOW(),
            jsonb_build_object('fact_category', OLD.fact_category, 'fact_subject', OLD.fact_subject,
                               'fact_key', OLD.fact_key, 'fact_value_text', OLD.value_text,
                               'verification_pass_status', OLD.verification_pass_status),
            jsonb_build_object('fact_category', NEW.fact_category, 'fact_subject', NEW.fact_subject,
                               'fact_key', NEW.fact_key, 'fact_value_text', NEW.value_text,
                               'verification_pass_status', NEW.verification_pass_status),
            NEW.build_id, COALESCE(NEW.engine_version, ''));
    RETURN NEW;
  ELSIF TG_OP = 'INSERT' THEN
    INSERT INTO chart_facts_history (fact_id, change_type, changed_at, old_value, new_value, build_id, engine_version)
    VALUES (NEW.fact_id, 'insert', NOW(), NULL,
            jsonb_build_object('fact_category', NEW.fact_category, 'fact_subject', NEW.fact_subject,
                               'fact_key', NEW.fact_key, 'fact_value_text', NEW.value_text,
                               'verification_pass_status', NEW.verification_pass_status),
            NEW.build_id, COALESCE(NEW.engine_version, ''));
    RETURN NEW;
  END IF;
  RETURN NULL;
END;
$$;
