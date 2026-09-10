-- 901_nirmana_l3_ka_gochara_resonance_output_digest_spec.sql
--
-- NIRMĀṆA L3 Kāla — overnight frontier drain: authors ka_gochara_resonance's
-- asset_output_digest_specs row ahead of its first campaign dispatch (its #1734
-- canary-run hold was DISCHARGED by the #2387 ruling; standard wave path authorized).
-- Sibling of migration 900 (the five wave-0 overlays), same 891-896 precedent.
--
-- Spec design verified against live data before authoring (895's discipline):
--   * target_table read from asset_registry: gochara_resonance_map (not a kala_* name —
--     pre-rename legacy table name, real and live with 762 canonical-chart rows).
--   * Genuine DB UNIQUE natural key read from pg_constraint:
--     (chart_id, event_class, target_type, target_ref).
--   * Live-checked: 0 NULLs across all 4 key columns for the canonical chart.
--   * id (serial PK) and computed_at (wall-clock) excluded from value_columns;
--     every other column is genuine content and is included.
--   * spec_sha256 = sha256(stableJson(spec)), the formula oracle-verified against
--     migration 895's recorded value earlier tonight.

BEGIN;

INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
VALUES (
  'ka_gochara_resonance',
  '06beb342ce8c3a88cf0df7d8d7a489abb99db40b520979d6ac9783a61970dd0a',
  '{"version":"nirmana-output-digest-spec-v1","components":[{"name":"gochara_resonance_map","relation":"gochara_resonance_map","where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"},"key_columns":["chart_id","event_class","target_type","target_ref"],"value_columns":["chart_id","event_class","target_type","target_ref","weight","classical_citation","uncited_extension","source_rule_id"]}]}'::jsonb
);

COMMIT;
