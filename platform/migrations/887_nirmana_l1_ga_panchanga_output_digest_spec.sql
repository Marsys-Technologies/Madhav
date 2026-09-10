-- 887_nirmana_l1_ga_panchanga_output_digest_spec.sql
--
-- NIRMĀṆA L1 Gaṇita — cycle 194: continues closing the fleet-wide `asset_output_digest_specs`
-- gap for `ga_panchanga`. `natural_key_partition` is a LIKE pattern
-- (`chart_facts.fact_category LIKE panchanga_%`), not a finite list -- the spec mechanism's
-- `where_in` only supports finite sets, so the 32 concrete `fact_category` values matching
-- that pattern for the canonical chart were enumerated live (not guessed) and used directly.
-- Same `key_columns: ["fact_id"]`/`value_columns` shape as `ga_positions`/`ga_sensitive`'s
-- own specs (same table, same schema, same stable post-PR-#1898 key).

BEGIN;

INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
VALUES (
  'ga_panchanga',
  '8fe4086e675d7eecd54dd882709059e281a878340ce2cd395ea0ee8cf71e4111',
  '{"version":"nirmana-output-digest-spec-v1","components":[{"name":"chart_facts","relation":"chart_facts","where_in":{"fact_category":["panchanga_abhijit_muhurta","panchanga_agni_vasa","panchanga_brahma_muhurta","panchanga_calendrical","panchanga_choghadiya_birth","panchanga_disha_shul","panchanga_durmuhurta","panchanga_godhuli_muhurta","panchanga_gulika_kalam","panchanga_hora_birth","panchanga_karana","panchanga_krakaca","panchanga_madhyahna_sandhya","panchanga_nakshatra_moon","panchanga_nakshatra_shoonya_rashi","panchanga_nishita_kala","panchanga_panchaka_classification","panchanga_pratah_sandhya","panchanga_rahu_kalam","panchanga_sashtighati","panchanga_sayam_sandhya","panchanga_solar_context","panchanga_special_yoga_combinations","panchanga_sun_moon_dynamics","panchanga_tithi","panchanga_tithi_shoonya_rashi","panchanga_vara","panchanga_varjyam","panchanga_vijaya_muhurta","panchanga_visha_ghati","panchanga_yamaganda_kalam","panchanga_yamakantaka","panchanga_yoga"]},"key_columns":["fact_id"],"where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"},"value_columns":["fact_id","chart_id","ayanamsha_id","fact_category","fact_subject","fact_key","fact_value_text","fact_value_num","fact_value_jsonb","unit","citation_ref","citation_human","source_calculation","verification_pass_status","engine_version","salience_formula_ver","tolerance_arcsec","near_sign_boundary_flag","near_nakshatra_boundary_flag","vargottama_flag_at_point","formula_provenance_text","cross_ayanamsha_divergence_arcsec","formula_id"]}]}'::jsonb
);

COMMIT;
