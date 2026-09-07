-- 883_nirmana_l1_ga_vargas_output_digest_spec.sql
--
-- NIRMĀṆA L1 Gaṇita — cycle 194: continues closing the fleet-wide `asset_output_digest_specs`
-- gap (`ga_positions` only, until migration 881 closed it for `ga_dashas` too) for `ga_vargas`,
-- authored BEFORE any build dispatch this time (cycle 189-190's `ga_dashas` lesson: dispatching
-- first and discovering the gap afterward burns a real ~20-minute build for nothing).
--
-- Spec design verified against live data before authoring:
--   * `chart_divisionals` already carries a genuine DB UNIQUE constraint,
--     `chart_divisionals_unique_idx (chart_id, graha, ayanamsha_id, varga, fact_category,
--     fact_key) NULLS NOT DISTINCT` -- unlike `chart_dashas`, no `build_id` is baked into this
--     natural key, so no live collision-check reasoning is needed the way `ga_dashas`' spec
--     (migration 881) required; the DB itself already enforces this key's uniqueness.
--   * `output_digest_spec`'s key-preflight rejects any row with a NULL key column outright.
--     Live-checked (not assumed from the constraint's own "NULLS NOT DISTINCT" naming, which
--     is a different guarantee): 0 NULLs across all 6 candidate key columns for the canonical
--     chart's 23,542 live rows.
--   * `id` (PK, `uuid_generate_v4()`) and `build_id`/`build_id_uuid` are excluded from
--     `value_columns` -- all three are per-rebuild identifiers, not content, the same
--     reasoning `ga_dashas`' spec applied to its own `dasha_row_id`/`parent_row_id`/`build_id`.
--   * `created_at`/`computed_at` (wall-clock write timestamps) excluded for the same reason.
--   * Every other column is genuine varga-position content and is included.

BEGIN;

INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
VALUES (
  'ga_vargas',
  '5f332a4889cb465f317fe7f2315bd59a7aee9d53df58e283b436040403a9bb51',
  '{"version":"nirmana-output-digest-spec-v1","components":[{"name":"chart_divisionals","relation":"chart_divisionals","where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"},"key_columns":["chart_id","graha","ayanamsha_id","varga","fact_category","fact_key"],"value_columns":["chart_id","graha","ayanamsha_id","varga","fact_category","fact_key","sign","sign_number","degree_in_sign","house","vargottama","source_citation","fact_value_text","fact_value_num","fact_subject","verification_pass_status","engine_version","citation_ref","citation_human","source_calculation","tolerance_arcsec","near_sign_boundary_flag","near_nakshatra_boundary_flag","vargottama_flag_at_point","formula_provenance_text","cross_ayanamsha_divergence_arcsec"]}]}'::jsonb
);

COMMIT;
