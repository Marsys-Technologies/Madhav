-- 880_nirmana_l1_ga_dashas_output_digest_spec.sql
--
-- NIRMĀṆA L1 Gaṇita — cycle 189/190 discovery: `asset_output_digest_specs` (the table
-- `compute_output_digest()` reads to turn a completed build into a `proven`
-- `asset_provenance_receipts` row) has ROWS FOR `ga_positions` ONLY. Every other L1
-- asset's `accepted_rebuild_observed` is structurally blocked: a completed, correct
-- build with real data still lands `receipt_state='unknown'`
-- (`unknown_reasons: ["output_digest_spec_unavailable", "output_digest_unavailable"]`)
-- because `load_output_digest_spec()` finds nothing to load. `ga_positions`' own spec was
-- added under adjudication #2180 (migration 875) scoped to that one asset only — never
-- generalized. This migration closes the gap for `ga_dashas` specifically (the asset this
-- W4 dispatch cycle needs); the same gap remains open for the other 6 not-yet-dispatched
-- newly-eligible L1 assets and should be closed the same way, asset-by-asset, as each is
-- dispatched (not batched sight-unseen — each table's natural key needs the same live
-- verification this one got, see below).
--
-- Spec design, verified against live data before authoring (not guessed):
--   * `chart_dashas`'s own DB unique index (`chart_dashas_natural_key_kp_idx`) is
--     `(chart_id, ayanamsha_id, system_id, level_n, start_iso, build_id,
--     COALESCE(kp_sublevel, ''))` — it bakes in `build_id` (a per-rebuild identifier, not
--     content) and needs COALESCE for `kp_sublevel` because that column is nullable, but
--     `output_digest_spec`'s `key_columns` mechanism REJECTS any row with a NULL key column
--     outright (`output_digest.py::compute_output_digest`, "output digest component has a
--     NULL reviewed key") and has no COALESCE/where-is-not-null primitive to express a
--     conditional key.
--   * Live-checked (not assumed) whether `(chart_id, ayanamsha_id, system_id, level_n,
--     start_iso)` — WITHOUT `kp_sublevel` or `build_id` — is already collision-free and
--     non-null for the canonical chart's current (post-migration) build:
--       SELECT chart_id, ayanamsha_id, system_id, level_n, start_iso, count(*)
--       FROM chart_dashas WHERE chart_id = '482012f1-...' AND build_id = '<current>'
--       GROUP BY 1,2,3,4,5 HAVING count(*) > 1;   -- 0 rows
--     Confirmed 0 collisions, 0 NULLs across 483,870 live rows — physically expected, since
--     no two periods of the same dasha system at the same level can share a start instant.
--     `kp_sublevel` is therefore safe to carry as a VALUE column (still hashed, still
--     detects a real change) without being part of the row-matching key.
--   * `dasha_row_id` (PK) and `parent_row_id` (self-referencing FK to `dasha_row_id`) are
--     BOTH random `gen_random_uuid()` values regenerated on every rebuild regardless of
--     content — including either in `value_columns` would make the digest differ on every
--     single rebuild even when nothing about the dasha periods themselves changed,
--     defeating the entire purpose of `output_contract: digest_identical` detection. Both
--     are deliberately excluded, same reasoning as excluding `build_id`.
--   * `computed_at` (wall-clock write timestamp) is excluded for the same reason.
--   * Every other column is genuine period content and is included.
--
-- spec_sha256 computed via the real `canonical_digest()` (python-sidecar/pipeline/
-- orchestrator/provenance.py) against the exact JSON below, and the spec's own structural
-- validity (`output_digest.py::_validate_spec` — no duplicate columns, valid lowercase
-- identifiers, non-empty component list) was independently re-run against this literal
-- payload before this migration was written, not assumed from the ga_positions precedent.

BEGIN;

INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
VALUES (
  'ga_dashas',
  '573e8aa1a0298d6626784b5ff540c004fd4d2298b6b47d2980a447acdc193d14',
  '{"version":"nirmana-output-digest-spec-v1","components":[{"name":"chart_dashas","relation":"chart_dashas","where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"},"key_columns":["chart_id","ayanamsha_id","system_id","level_n","start_iso"],"value_columns":["chart_id","ayanamsha_id","system_id","level_n","start_iso","lord_graha","lord_sign","start_date","end_date","end_iso","duration_days","sandhi_flag","karaka_role_at_period","verification_pass_status","verification_method","citation_ref","citation_human","engine_version","kp_sublevel","kp_sub_lord","kp_sub_sub_lord","lord_natal_house_d1","lord_natal_sign","lord_natal_nakshatra","lord_natal_dignity_d1","lord_natal_shadbala_total","sandhi_with_next_dasha_lord","next_dasha_start_iso","concurrent_system_lords_jsonb","convergence_count_at_start","applies_to_this_chart_flag","period_deity_or_marker","lord_to_parent_relationship","varsha_year_lord","anchored_solar_return_iso","karakas_active_during_period","is_truncated_at_window_start","is_truncated_at_window_end"]}]}'::jsonb
);

COMMIT;
