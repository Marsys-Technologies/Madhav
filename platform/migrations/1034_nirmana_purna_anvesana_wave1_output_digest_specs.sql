-- Migration 1034: Purna Anvesana Wave 1 producer output digest specifications
-- Created: 2026-09-14
--
-- Source-only delivery. This migration has not been applied to a shared or
-- production database. Each specification was derived from the complete
-- writer/static-owner INSERT surface and its current natural key, then checked
-- with pipeline.orchestrator.output_digest._validate_spec.
--
-- Six of the eight W1 relational gaps close here. Two remain explicit blocked
-- contracts rather than receiving lossy hashes:
--   * ka_vighnakara: kala_obstruction has no stable, non-null unique key for
--     both convergence-anchored and dasha-anchored rows. Its BIGSERIAL id is
--     execution history, not content identity.
--   * ka_gochara_v3_century_materialize: parent_window_id is a table-local
--     BIGSERIAL link but encodes semantic era->month->day hierarchy. The v1
--     digest grammar cannot project the parent's stable natural identity, so
--     excluding it would make broken hierarchy attachments hash identically.

INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
VALUES (
  'bg_sign_medical',
  '44333a746758f9a71288524273a4941071391f60ec753062d5295fafba6dcad7',
  '{"components":[{"key_columns":["sign_number"],"name":"bg_sign_medical","relation":"bg_sign_medical","value_columns":["sign_number","sign_name","body_part","organ_systems","element","dosha","classical_citation"]}],"version":"nirmana-output-digest-spec-v1"}'::jsonb
)
ON CONFLICT (asset_id, spec_sha256) DO NOTHING;

INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
VALUES (
  'bg_nakshatra_medical',
  'ae8016ab4ee18b5794d027c593dcf9662d5bfd05562f9df509985f176a1fd4b1',
  '{"components":[{"key_columns":["nakshatra_name"],"name":"bg_nakshatra_medical","relation":"bg_nakshatra_medical","value_columns":["nakshatra_name","nakshatra_number","body_part","dosha","classical_citation"]}],"version":"nirmana-output-digest-spec-v1"}'::jsonb
)
ON CONFLICT (asset_id, spec_sha256) DO NOTHING;

INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
VALUES (
  'bg_transit_engine',
  '6b94337ac05cfdd83c8fc9c7d443d0cc823b04329e5d8f94b8b3311e0a29751e',
  '{"components":[{"key_columns":["graha"],"name":"bg_transit_engine","relation":"bg_transit_engine","value_columns":["graha","avg_daily_motion_deg","zodiac_period_days","sign_residence_days","classical_citation"]}],"version":"nirmana-output-digest-spec-v1"}'::jsonb
)
ON CONFLICT (asset_id, spec_sha256) DO NOTHING;

INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
VALUES (
  'bg_gochara_citation_resolution',
  '24e755f951d96360df115b25e693a70b81376fca4fecf81d22f733a95de8deb6',
  '{"components":[{"key_columns":["citation_string","chunk_id"],"name":"bg_gochara_citation_resolution","relation":"bg_gochara_citation_resolution","value_columns":["citation_string","chunk_id","text_id","verse_ref","status","source_citation","constant_name","note"]}],"version":"nirmana-output-digest-spec-v1"}'::jsonb
)
ON CONFLICT (asset_id, spec_sha256) DO NOTHING;

INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
VALUES (
  'ka_avadhi',
  '123eb9fff14621a4002f2d674dd10e5cd2bce2d8efcbf2b7e8a02d32076cf5ad',
  '{"components":[{"key_columns":["chart_id","system_id","level_n","period_start"],"name":"kala_avadhi","relation":"kala_avadhi","value_columns":["chart_id","system_id","level_n","lord_graha","period_start","period_end","dossier","quality","citations","formula_version"],"where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"}}],"version":"nirmana-output-digest-spec-v1"}'::jsonb
)
ON CONFLICT (asset_id, spec_sha256) DO NOTHING;

INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
VALUES (
  'ka_kalasutra',
  '7681e4848c9a8d64abee6de58b1ac5bdb7bf65daa09f28ae8f18b6fc7e2be5b1',
  '{"components":[{"key_columns":["chart_id","signal_id","ayanamsha_id","source_citation"],"name":"kala_activation","relation":"kala_activation","value_columns":["chart_id","signal_id","ayanamsha_id","signature_class","active_dasha_periods_jsonb","activation_predicted_dates_jsonb","dasha_activation_proximity_score","activation_start","activation_end","activation_peak_date","orb_strength","convergence_score","source_citation"],"where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"}}],"version":"nirmana-output-digest-spec-v1"}'::jsonb
)
ON CONFLICT (asset_id, spec_sha256) DO NOTHING;
