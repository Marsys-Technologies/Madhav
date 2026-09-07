-- 889_nirmana_l1_ga_nakshatra_output_digest_spec.sql
--
-- NIRMĀṆA L1 Gaṇita — cycle 194: closes the fleet-wide `asset_output_digest_specs` gap for
-- `ga_nakshatra`. Same shape as `ga_positions`/`ga_sensitive`/`ga_panchanga`'s own specs
-- (shared `chart_facts` table, `key_columns: [fact_id]`, its own 15-category
-- `natural_key_partition` list used as `where_in`).
--
-- `where_in.fact_category` is SORTED lexicographically (`output_digest.py` requires every
-- `where_in` array to be unique AND sorted -- discovered live: this asset's first real
-- dispatch failed with "output digest spec where_in values must be unique and sorted"
-- because the registry's own `natural_key_partition` text lists categories in an
-- unsorted, hand-authored order. `ga_sensitive`/`ga_panchanga`'s own specs happened to
-- already be alphabetical by coincidence of their own `natural_key_partition` ordering;
-- this one was not. Fixed in place before this file was ever committed/shared (the mistaken
-- version was applied and immediately reconciled, never pushed) -- content-identical except
-- for `where_in` ordering, so `spec_sha256` is recomputed accordingly.

BEGIN;

INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
VALUES (
  'ga_nakshatra',
  '83400fbd84db6fb9f42df4d101ce375777aa5669fe7c8451ef4fb43b0b51b650',
  '{"version":"nirmana-output-digest-spec-v1","components":[{"name":"chart_facts","relation":"chart_facts","where_in":{"fact_category":["cusp_kp_lords","graha_degree_flags","graha_gandanta","graha_kp_lords","graha_nakshatra_join","graha_pada_join","graha_tara_bala","kp_house_significators","kp_planet_significations","nakshatra_cogravity","nakshatra_conjunction","nakshatra_cross_ayanamsha","nakshatra_dispositor","nakshatra_exchange","nakshatra_statistics"]},"key_columns":["fact_id"],"where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"},"value_columns":["fact_id","chart_id","ayanamsha_id","fact_category","fact_subject","fact_key","fact_value_text","fact_value_num","fact_value_jsonb","unit","citation_ref","citation_human","source_calculation","verification_pass_status","engine_version","salience_formula_ver","tolerance_arcsec","near_sign_boundary_flag","near_nakshatra_boundary_flag","vargottama_flag_at_point","formula_provenance_text","cross_ayanamsha_divergence_arcsec","formula_id"]}]}'::jsonb
);

COMMIT;
