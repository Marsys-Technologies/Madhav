-- Migration 599: immutable bilingual labels for the Nirmana elevation tracker
-- Created: 2026-08-25

BEGIN;

CREATE TABLE IF NOT EXISTS nirmana_elevation_asset_labels (
  campaign_id text NOT NULL,
  definition_revision text NOT NULL,
  catalogue_revision text NOT NULL CHECK (catalogue_revision ~ '^[A-Za-z0-9._-]{1,128}$'),
  asset_id text NOT NULL,
  sanskrit_name text,
  english_name text,
  description text,
  legacy_aliases jsonb NOT NULL DEFAULT '[]'::jsonb
    CHECK (jsonb_typeof(legacy_aliases) = 'array'),
  source_ref text NOT NULL,
  label_digest text NOT NULL CHECK (label_digest ~ '^[a-f0-9]{64}$'),
  recorded_at timestamptz NOT NULL DEFAULT now(),
  recorded_by text NOT NULL,
  PRIMARY KEY (campaign_id, definition_revision, catalogue_revision, asset_id),
  CONSTRAINT nirmana_elevation_label_definition_fk
    FOREIGN KEY (campaign_id, definition_revision)
    REFERENCES nirmana_elevation_campaign_definitions (campaign_id, definition_revision),
  CONSTRAINT nirmana_elevation_label_has_human_text CHECK (
    sanskrit_name IS NOT NULL OR english_name IS NOT NULL OR description IS NOT NULL
  )
);

CREATE INDEX IF NOT EXISTS nirmana_elevation_asset_labels_revision_idx
  ON nirmana_elevation_asset_labels (campaign_id, definition_revision, catalogue_revision);

CREATE OR REPLACE FUNCTION nirmana_elevation_prevent_label_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  RAISE EXCEPTION 'nirmana_elevation_asset_labels is append-only';
END;
$$;

DROP TRIGGER IF EXISTS nirmana_elevation_asset_labels_append_only
  ON nirmana_elevation_asset_labels;
CREATE TRIGGER nirmana_elevation_asset_labels_append_only
  BEFORE UPDATE OR DELETE ON nirmana_elevation_asset_labels
  FOR EACH ROW EXECUTE FUNCTION nirmana_elevation_prevent_label_mutation();

COMMENT ON TABLE nirmana_elevation_asset_labels IS
  'Append-only, definition-scoped canonical Sanskrit, English, description, and verified legacy labels for the Nirmana elevation projection.';

COMMIT;
