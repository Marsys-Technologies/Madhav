-- 892_nirmana_l1_ga_ayurdaya_output_digest_spec.sql
--
-- NIRMĀṆA L1 Gaṇita — cycle 195: continues the frontier-drain, closes the fleet-wide
-- `asset_output_digest_specs` gap for `ga_ayurdaya`. Single-category `natural_key_
-- partition` (`chart_facts.fact_category = ayurdaya`), trivially sorted.

BEGIN;

INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
VALUES (
  'ga_ayurdaya',
  '0060fe5fd1d53cacfc00a8789321e247997e65ea8f836f6ff6b9e567761daf7a',
  '{"version":"nirmana-output-digest-spec-v1","components":[{"name":"chart_facts","relation":"chart_facts","where_in":{"fact_category":["ayurdaya"]},"key_columns":["fact_id"],"where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"},"value_columns":["fact_id","chart_id","ayanamsha_id","fact_category","fact_subject","fact_key","fact_value_text","fact_value_num","fact_value_jsonb","unit","citation_ref","citation_human","source_calculation","verification_pass_status","engine_version","salience_formula_ver","tolerance_arcsec","near_sign_boundary_flag","near_nakshatra_boundary_flag","vargottama_flag_at_point","formula_provenance_text","cross_ayanamsha_divergence_arcsec","formula_id"]}]}'::jsonb
);

COMMIT;
