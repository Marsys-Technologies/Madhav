-- 900_nirmana_l3_wave0_overlay_output_digest_specs.sql
--
-- NIRMĀṆA L3 Kāla — overnight frontier drain (cycle ~551): closes the fleet-wide
-- asset_output_digest_specs gap (D-CND-27 class) for the five wave-0 quality overlays,
-- following the exact per-asset authoring precedent of migrations 891-896.
-- Without these rows, accepted_rebuild_observed cannot be recorded for build_run
-- 08983928-3820-4bdb-bf77-125caecd1b2c (executed 2026-09-07T19:57Z: 4/5 complete,
-- output_changed=t; ka_vedha_gochara DEP-ASSERT-refused on the empty-by-ruling
-- bg_sarvatobhadra_grid receipt — its spec is authored here anyway, ready for its
-- redispatch once that gate question is ruled).
--
-- Spec design verified against live data before authoring (895's own discipline):
--   * All five tables carry genuine DB UNIQUE natural keys (constraint defs read from
--     pg_constraint, not assumed): key_columns below are exactly those constraints'
--     column sets.
--   * Live-checked: 0 NULLs across every key column for the canonical chart
--     (585 / 71 / 120 / 120 rows post-rebuild; vedha pre-rebuild).
--   * id (serial PK) and computed_at (wall-clock write timestamp) excluded from
--     value_columns; every other column is genuine asset content and is included.
--   * spec_sha256 = sha256(stableJson(spec)) — formula oracle-verified byte-exact
--     against migration 895's own recorded value before computing anything new.

BEGIN;

INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
VALUES (
  'ka_kota_chakra',
  '8342bf27050bd96d6fbf3e45980a04fbb5be1863af2a8e483123c3543da9f953',
  '{"version":"nirmana-output-digest-spec-v1","components":[{"name":"kala_kota_chakra","relation":"kala_kota_chakra","where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"},"key_columns":["chart_id","ayanamsha_id","graha","window_start"],"value_columns":["chart_id","ayanamsha_id","graha","nakshatra_idx","nakshatra_name","count_from_janma","kota_ring","is_natural_malefic","posture","severity","window_start","window_end","start_truncated","end_truncated","janma_nakshatra_fact_id","ring_table_citation","uncited_extension","formula_version"]}]}'::jsonb
);

INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
VALUES (
  'ka_moorti_nirnaya',
  'd18ffa0ab8a8b89db432ae20cbf9d5e74c19fbe6ef06ca682adaff4bbbe1bfee',
  '{"version":"nirmana-output-digest-spec-v1","components":[{"name":"kala_moorti_nirnaya","relation":"kala_moorti_nirnaya","where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"},"key_columns":["chart_id","ayanamsha_id","graha","window_start"],"value_columns":["chart_id","ayanamsha_id","graha","target_sign_idx","target_sign_name","window_start","window_end","start_truncated","end_truncated","moorti_computed","moon_nakshatra_idx_at_ingress","moon_nakshatra_name_at_ingress","janma_nakshatra_idx","janma_nakshatra_fact_id","nakshatra_offset","moorti_name","quality_tier","phala_brief","moorti_classical_citation","formula_version"]}]}'::jsonb
);

INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
VALUES (
  'ka_sudarshana_varsha',
  '00aab332092a6dca0cfe66073e9fd777f4d78f9c2b1811c6d36892bc7f020629',
  '{"version":"nirmana-output-digest-spec-v1","components":[{"name":"kala_sudarshana_varsha","relation":"kala_sudarshana_varsha","where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"},"key_columns":["chart_id","ayanamsha_id","varsha_year"],"value_columns":["chart_id","ayanamsha_id","varsha_year","window_start","window_end","jl_natal_sign_idx","cl_natal_sign_idx","sl_natal_sign_idx","jl_active_sign_idx","cl_active_sign_idx","sl_active_sign_idx","jl_active_sign_name","cl_active_sign_name","sl_active_sign_name","tri_lagna_convergence","lagna_fact_id","moon_fact_id","sun_fact_id","formula_version"]}]}'::jsonb
);

INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
VALUES (
  'ka_tithi_pravesha',
  '364deb07cc0c7cce78ab6982b56fdbc16e5d46c27adac4c3f4ed4bf33faef03e',
  '{"version":"nirmana-output-digest-spec-v1","components":[{"name":"kala_tithi_pravesha","relation":"kala_tithi_pravesha","where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"},"key_columns":["chart_id","ayanamsha_id","pravesha_year"],"value_columns":["chart_id","ayanamsha_id","pravesha_year","window_start","window_end","start_converged","end_converged","pravesha_lagna_sign_idx","pravesha_lagna_sign_name","pravesha_lagna_degree","graha_positions_jsonb","natal_moon_longitude_deg","moon_fact_id","ephemeris_audit_jsonb","verification_pass_status","classical_source_citation","formula_version"]}]}'::jsonb
);

INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
VALUES (
  'ka_vedha_gochara',
  '11d4a150a73e1375fe6b71a01ba5c14e2edee4576bb26ca98716b651b59c8404',
  '{"version":"nirmana-output-digest-spec-v1","components":[{"name":"kala_vedha_gochara","relation":"kala_vedha_gochara","where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"},"key_columns":["chart_id","ayanamsha_id","vedha_kind","graha","window_start"],"value_columns":["chart_id","ayanamsha_id","vedha_kind","graha","window_start","window_end","start_truncated","end_truncated","janma_reference_fact_id","classical_citation","uncited_extension","grid_basis","grid_school_tag","detail","formula_version"]}]}'::jsonb
);

COMMIT;
