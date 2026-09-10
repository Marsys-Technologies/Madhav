-- 886_nirmana_l1_ga_sensitive_output_digest_spec.sql
--
-- NIRMĀṆA L1 Gaṇita — cycle 194: continues closing the fleet-wide `asset_output_digest_specs`
-- gap for `ga_sensitive`. Same `chart_facts` table `ga_positions` already has a spec for
-- (migration 875), scoped to `ga_sensitive`'s OWN 36 `fact_category` values (its
-- `natural_key_partition`), not `ga_positions`'.
--
-- `key_columns: ["fact_id"]` -- same stable, build-id-free key `ga_positions`' own spec uses
-- (PR #1898 made `fact_id` stable across rebuilds for the whole `chart_facts` table, not
-- per-asset). `value_columns` mirror `ga_positions`' own spec's column list exactly (same
-- table, same schema).

BEGIN;

INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
VALUES (
  'ga_sensitive',
  '5ca1e15a3aee2720fa71993e7de5938e3db296b2641da3b7f3ac69a7f366633a',
  '{"version":"nirmana-output-digest-spec-v1","components":[{"name":"chart_facts","relation":"chart_facts","where_in":{"fact_category":["aprakasha_position","arudha_pada","bhava_arudha","bhrigu_nadi_point","esoteric_point_avayogi","esoteric_point_bhrigu_bindu","esoteric_point_brahma","esoteric_point_chatushphuta","esoteric_point_mrityu","esoteric_point_panchasphuta","esoteric_point_pranapada_sphuta","esoteric_point_shiva","esoteric_point_sphuta_fertility","esoteric_point_sri_yantra_position","esoteric_point_trikona_dasha_sphuta","esoteric_point_trisphuta","esoteric_point_vishnu","esoteric_point_yogi","esoteric_point_yogi_system","karaka_chara_position","karakamsa_position","kp_cuspal_significators","kp_ruling_planets_natal","lal_kitab_special_point","maharsi_specific_point","midpoint","nakshatra_pada_sensitive","saham_position","saturn_derived_point","sensitive_point_gulika_mandi","special_lagna","sun_derived_upagraha","swamsa_position","tajik_hadda_lord","tajik_triraashipathi","tajik_vargottama_specific","upagraha_position"]},"key_columns":["fact_id"],"where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"},"value_columns":["fact_id","chart_id","ayanamsha_id","fact_category","fact_subject","fact_key","fact_value_text","fact_value_num","fact_value_jsonb","unit","citation_ref","citation_human","source_calculation","verification_pass_status","engine_version","salience_formula_ver","tolerance_arcsec","near_sign_boundary_flag","near_nakshatra_boundary_flag","vargottama_flag_at_point","formula_provenance_text","cross_ayanamsha_divergence_arcsec","formula_id"]}]}'::jsonb
);

COMMIT;
