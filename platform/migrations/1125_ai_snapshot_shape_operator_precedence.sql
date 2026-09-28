-- Migration 1125: Repair AI routing snapshot validation
-- Created: 2026-09-28
-- Forward-only repair for the already-applied migration 1124.
-- Transaction owned by platform/scripts/migrate.ts, including its tracking insert.
-- Do not add transaction control here: an inner COMMIT would break runner atomicity.

CREATE OR REPLACE FUNCTION ai_snapshot_shape(selection jsonb, choice jsonb, role_map jsonb, config_version bigint)
RETURNS boolean LANGUAGE plpgsql IMMUTABLE AS $$
DECLARE r text;
BEGIN
  IF NOT ai_safe_target(choice) OR jsonb_typeof(role_map) IS DISTINCT FROM 'object'
    OR role_map - ARRAY['synthesizer','planner','deep_planner','worker'] <> '{}'::jsonb
    OR ((choice->>'kind' = 'custom_configuration') <> (config_version IS NOT NULL))
    OR config_version <= 0 THEN RETURN false; END IF;
  IF selection IS DISTINCT FROM '{"kind":"default"}'::jsonb THEN
    IF jsonb_typeof(selection) IS DISTINCT FROM 'object' OR selection->>'kind' IS DISTINCT FROM 'explicit'
      OR selection - ARRAY['kind','choice'] <> '{}'::jsonb
      OR NOT ai_safe_target(selection->'choice') OR selection->'choice' IS DISTINCT FROM choice THEN RETURN false; END IF;
  END IF;
  FOREACH r IN ARRAY ARRAY['synthesizer','planner','deep_planner','worker'] LOOP
    IF NOT ai_safe_target(role_map->r, true, false) THEN RETURN false; END IF;
    IF choice->>'kind' <> 'custom_configuration' AND ((role_map->r) - 'providerId') IS DISTINCT FROM choice THEN RETURN false; END IF;
  END LOOP;
  RETURN true;
END $$;
