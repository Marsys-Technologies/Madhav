-- Migration 1362: K-CERT-2 citation-resolution writer registry contract
-- Created: 2026-10-10
-- Data-only; no citation rows, integrity seal, permissions or grid state change.
-- Paired with @register('bg_gochara_citation_resolution') in this same PR.
-- Suvarṇa owns merge/application/dispatch in its certification window.

DO $$
DECLARE
  changed integer;
BEGIN
  UPDATE asset_registry
  SET has_writer = true,
      count_sql = 'SELECT COUNT(*) FROM bg_gochara_citation_resolution'
  WHERE asset_id = 'bg_gochara_citation_resolution'
    AND target_table = 'bg_gochara_citation_resolution'
    AND scope = 'global'
    AND is_active = true;
  GET DIAGNOSTICS changed = ROW_COUNT;
  IF changed <> 1 THEN
    RAISE EXCEPTION 'migration 1362 refuses missing or incompatible citation registry contract';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM asset_registry
    WHERE asset_id = 'bg_gochara_citation_resolution'
      AND has_writer = true
      AND count_sql = 'SELECT COUNT(*) FROM bg_gochara_citation_resolution'
  ) THEN
    RAISE EXCEPTION 'migration 1362 citation registry contract postflight failed';
  END IF;
END $$;
