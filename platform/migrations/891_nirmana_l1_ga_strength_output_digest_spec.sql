-- 891_nirmana_l1_ga_strength_output_digest_spec.sql
--
-- NIRMĀṆA L1 Gaṇita — cycle 195: continues the frontier-drain, closes the fleet-wide
-- `asset_output_digest_specs` gap for `ga_strength`. Its `asset_registry.natural_key_
-- partition`/`target_table` are both NULL (a registry-data gap, not fixed here -- out of
-- this migration's scope); its own `integrity_check_sql` header comment identifies the real
-- target directly: "graha_shadbala_total fact_category ONLY; target table: chart_facts".
-- Single-category `where_in` array, trivially sorted (no ordering risk the `ga_nakshatra`
-- fix, migration 889, had to correct for a multi-category list).

BEGIN;

INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
VALUES (
  'ga_strength',
  '7251b1192714e6e1b09720fff165f78f6089bc74dca862dfaab0f7537ee677c3',
  '{"version":"nirmana-output-digest-spec-v1","components":[{"name":"chart_facts","relation":"chart_facts","where_in":{"fact_category":["graha_shadbala_total"]},"key_columns":["fact_id"],"where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"},"value_columns":["fact_id","chart_id","ayanamsha_id","fact_category","fact_subject","fact_key","fact_value_text","fact_value_num","fact_value_jsonb","unit","citation_ref","citation_human","source_calculation","verification_pass_status","engine_version","salience_formula_ver","tolerance_arcsec","near_sign_boundary_flag","near_nakshatra_boundary_flag","vargottama_flag_at_point","formula_provenance_text","cross_ayanamsha_divergence_arcsec","formula_id"]}]}'::jsonb
);

COMMIT;
