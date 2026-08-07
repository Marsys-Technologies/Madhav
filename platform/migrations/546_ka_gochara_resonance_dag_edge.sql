-- Migration 546: Add missing DAG edge for ka_gochara_resonance
-- Created: 2026-08-07
-- Campaign: PRATIJÑA-SATYA Phase A, Lane A3
--
-- ka_gochara_resonance consumes bg_transit_rules (via gochara_resonance_map.source_rule_id
-- REFERENCES bg_transit_rules(id), migration 459) but was registered with depends_on = ARRAY[]::text[].
-- The orchestrator needs this edge to schedule ka_gochara_resonance after bg_transit_rules is built.

BEGIN;

UPDATE asset_registry
SET depends_on = ARRAY['bg_transit_rules']
WHERE asset_id = 'ka_gochara_resonance'
  AND (depends_on IS NULL OR NOT depends_on @> ARRAY['bg_transit_rules']);

COMMIT;
