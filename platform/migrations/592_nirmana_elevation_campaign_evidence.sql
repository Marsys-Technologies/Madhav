-- Migration 592: Nirmana elevation campaign definitions and immutable evidence
-- Created: 2026-08-25
--
-- The tracker is a projection. These tables hold only versioned campaign intent
-- and append-only receipts; primary runtime truth remains in the build tables.

BEGIN;

CREATE TABLE IF NOT EXISTS nirmana_elevation_campaign_definitions (
  campaign_id text NOT NULL,
  definition_revision text NOT NULL,
  definition_status text NOT NULL CHECK (definition_status IN ('reconciling', 'frozen', 'superseded')),
  manifest jsonb NOT NULL,
  manifest_sha256 text NOT NULL CHECK (manifest_sha256 ~ '^[a-f0-9]{64}$'),
  created_at timestamptz NOT NULL DEFAULT now(),
  created_by text NOT NULL,
  superseded_at timestamptz,
  CONSTRAINT nirmana_elevation_definition_status_consistent CHECK (
    (definition_status = 'superseded') = (superseded_at IS NOT NULL)
  ),
  PRIMARY KEY (campaign_id, definition_revision)
);

CREATE UNIQUE INDEX IF NOT EXISTS nirmana_elevation_one_current_definition
  ON nirmana_elevation_campaign_definitions (campaign_id)
  WHERE superseded_at IS NULL;

CREATE TABLE IF NOT EXISTS nirmana_elevation_campaign_events (
  event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  campaign_id text NOT NULL,
  definition_revision text NOT NULL,
  idempotency_key text NOT NULL,
  event_type text NOT NULL,
  entity_type text NOT NULL,
  entity_id text NOT NULL,
  layer text,
  evidence_payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  source_kind text NOT NULL,
  source_ref text NOT NULL,
  observed_at timestamptz NOT NULL,
  recorded_at timestamptz NOT NULL DEFAULT now(),
  recorded_by text NOT NULL,
  CONSTRAINT nirmana_elevation_event_idempotency_unique
    UNIQUE (campaign_id, definition_revision, idempotency_key),
  CONSTRAINT nirmana_elevation_event_definition_fk
    FOREIGN KEY (campaign_id, definition_revision)
    REFERENCES nirmana_elevation_campaign_definitions (campaign_id, definition_revision)
);

CREATE INDEX IF NOT EXISTS nirmana_elevation_events_campaign_recorded_idx
  ON nirmana_elevation_campaign_events (campaign_id, recorded_at);

-- These trigger names belong exclusively to this migration. CREATE OR REPLACE and
-- DROP TRIGGER IF EXISTS make a safe re-run restore the intended append-only guards.
CREATE OR REPLACE FUNCTION nirmana_elevation_prevent_event_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  RAISE EXCEPTION 'nirmana_elevation_campaign_events is append-only';
END;
$$;

DROP TRIGGER IF EXISTS nirmana_elevation_events_append_only
  ON nirmana_elevation_campaign_events;
CREATE TRIGGER nirmana_elevation_events_append_only
  BEFORE UPDATE OR DELETE ON nirmana_elevation_campaign_events
  FOR EACH ROW EXECUTE FUNCTION nirmana_elevation_prevent_event_mutation();

CREATE OR REPLACE FUNCTION nirmana_elevation_guard_definition_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    RAISE EXCEPTION 'nirmana_elevation_campaign_definitions are versioned and cannot be deleted';
  END IF;

  IF OLD.definition_status = 'superseded' THEN
    RAISE EXCEPTION 'a superseded Nirmana elevation definition cannot be changed';
  END IF;

  IF OLD.definition_status = 'frozen' THEN
    IF NEW.definition_status = 'superseded'
       AND NEW.superseded_at IS NOT NULL
       AND NEW.campaign_id = OLD.campaign_id
       AND NEW.definition_revision = OLD.definition_revision
       AND NEW.manifest = OLD.manifest
       AND NEW.manifest_sha256 = OLD.manifest_sha256
       AND NEW.created_at = OLD.created_at
       AND NEW.created_by = OLD.created_by THEN
      RETURN NEW;
    END IF;
    RAISE EXCEPTION 'a frozen Nirmana elevation definition is immutable except for supersession';
  END IF;

  IF NEW.definition_status = 'superseded' THEN
    RAISE EXCEPTION 'only a frozen Nirmana elevation definition may be superseded';
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS nirmana_elevation_definitions_versioned
  ON nirmana_elevation_campaign_definitions;
CREATE TRIGGER nirmana_elevation_definitions_versioned
  BEFORE UPDATE OR DELETE ON nirmana_elevation_campaign_definitions
  FOR EACH ROW EXECUTE FUNCTION nirmana_elevation_guard_definition_mutation();

COMMENT ON TABLE nirmana_elevation_campaign_definitions IS
  'Versioned Nirmana elevation denominator/DAG definitions. The tracker projects them with live build evidence.';
COMMENT ON TABLE nirmana_elevation_campaign_events IS
  'Append-only idempotent Nirmana elevation evidence receipts; never a manually mutated projection.';

COMMIT;
