-- 1017_nirmana_l2_bo_upaya_digest_spec_narrow_fk_columns.sql
--
-- NIRMANA v2.5 -- L2 (Bodha). Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Amends bo_upaya's output_digest_spec (migration 1012, PR #2538) to drop
-- four value_columns that are FK copies of non-deterministic surrogate PKs.
-- Filed as issue #2540 (L2 lane finding, 2026-09-10T00:06Z, zero comments /
-- no prior Conductor ruling as of this migration): `bo_upaya.py` (live on
-- origin/main, unchanged by #2529's determinism fix -- that fix addressed
-- ORDER BY tiebreaks, not ID generation) assigns bare `uuid.uuid4()` for
-- `resonance_id`, `prescription_id`, `summary_id`, `bundle_id`,
-- `pattern_remedy_id`, `window_prescription_id` (bo_upaya.py lines
-- 1531/1813/1917/1961/2003/2100). The digest spec never hashes these PKs
-- themselves (correctly excluded, migration 1012 already omits them from
-- every component's value_columns) but two components hash FK COPIES of
-- them, and two more hash ARRAY COPIES the issue itself didn't name:
--
--   bodha_rm_remedy_prescriptions.target_resonance_id
--     -- FK copy of resonance_id (named in #2540)
--   bodha_rm_dasha_windowed_prescriptions.base_prescription_id
--     -- FK copy of prescription_id (named in #2540)
--   bodha_rm_dosha_remedy_bundles.prescription_ids_in_bundle_array
--     -- ARRAY of prescription_id, built at bo_upaya.py:1969 from `pids`
--     -- (NOT named in #2540 -- found this cycle by reading the writer's
--     -- row-construction code directly, same defect class)
--   bodha_rm_pattern_remedies.prescription_ids_array
--     -- ARRAY of prescription_id, built at bo_upaya.py:2010
--     -- (`[p["prescription_id"] for p in presc]` -- NOT named in #2540,
--     -- found this cycle, same defect class)
--
-- Each of these four columns regenerates to entirely different random
-- values on every writer rebuild (delete-then-insert, CLAUDE.md §N.3) even
-- when nothing semantically changed, so compute_output_digest for bo_upaya
-- would spuriously drift on every future rebuild -- precisely what
-- output_digest_spec exists to prevent (same defect class as #1770's
-- non-deterministic bodha_msr_signals.signal_id, one layer up: here a
-- digest spec's column CHOICE surfaces a pre-existing non-deterministic ID
-- into the stability contract the spec exists to provide).
--
-- Fix: narrow the four affected components' value_columns (option (b) from
-- #2540's own recommended-fix list) rather than porting deterministic-ID
-- generation into bo_upaya.py (option (a) -- out of scope for a migration,
-- and unlike #1770/bo_laksana this ID never crosses into another table's
-- own PRIMARY KEY, so no cross-layer referential-identity concern forces
-- the writer-code fix). Every other value_column, every key_columns
-- declaration, and all six components' where_equals/relation/name is
-- otherwise byte-identical to migration 1012 -- this is a pure column
-- removal, not a re-derivation.
--
-- Does NOT invalidate the existing freeze: bo_upaya's asset_frozen event
-- (2026-09-10, t1-2026-09-08-be255ffe) only required one internally-
-- consistent `proven` receipt for one specific build, not cross-build
-- digest stability. 2 asset_provenance_receipts already exist under the
-- OLD spec_sha256 (ac4e04a2...) -- both remain valid, pinned to that sha,
-- untouched by this migration; only FUTURE rebuilds pick up the corrected
-- spec.
--
-- spec_sha256 computed and independently re-verified via the REAL server
-- functions, never hand-reimplemented:
--   cd platform/python-sidecar && python3 -c "
--   from pipeline.orchestrator.provenance import canonical_digest
--   from pipeline.orchestrator.output_digest import _validate_spec
--   spec = {...}  # exact object below, minus the 4 columns
--   print(canonical_digest(spec))                          # == the literal below
--   print(_validate_spec('bo_upaya', spec, sha).asset_id)   # passes the server's own validator
--   "
--
-- Rehearsed end-to-end against live prod inside a ROLLED-BACK transaction
-- (psycopg3, autocommit=False, dict_row): retire the current row, INSERT
-- this exact corrected spec row -> call the REAL
-- `compute_output_digest(cur, asset_id='bo_upaya')` -> got back a clean
-- digest hex (d857a34759cfc6a496fcea123d7eef77c91e768bce50de455af7402947701768)
-- paired with the matching spec_sha256, no exception -> conn.rollback() ->
-- re-queried `asset_output_digest_specs` from a FRESH connection afterward
-- and confirmed the pre-existing migration-1012 row (spec_sha256
-- ac4e04a2...) is still the sole non-retired row for bo_upaya, i.e.
-- genuinely rolled back, nothing persisted by the rehearsal.
--
-- Post-apply verification (N.4/§N.8 -- never trust a silent no-op): expect
-- UPDATE 1 (retiring migration 1012's row), then INSERT 0 1, then
--   SELECT spec_sha256 FROM asset_output_digest_specs
--    WHERE asset_id = 'bo_upaya' AND retired_at IS NULL
--   -- expect exactly 1 row, spec_sha256 = e73b69a632b238e29d3f24fa1c78ea6ca0aed81260558135d0579e5a7b794dee

UPDATE asset_output_digest_specs
   SET retired_at = now()
 WHERE asset_id = 'bo_upaya'
   AND spec_sha256 = 'ac4e04a2fd349df5ece501338e03ecfb9c1d5845fda27a3cd65e3d623524de45'
   AND retired_at IS NULL;

INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
VALUES (
  'bo_upaya',
  'e73b69a632b238e29d3f24fa1c78ea6ca0aed81260558135d0579e5a7b794dee',
  '{"version":"nirmana-output-digest-spec-v1","components":[{"name":"bodha_rm_resonances","relation":"bodha_rm_resonances","key_columns":["ayanamsha_id","snapshot_type","graha"],"value_columns":["chart_id","ayanamsha_id","snapshot_type","graha","resonance_score","resonance_score_formula_version","weakness_score","contradiction_factor","domain_burden","motif_burden","is_yoga_karaka_flag","weakest_rank_in_chart","remedy_priority_class","associated_doshas_array","associated_cdlm_cells_array","ephemeris_audit_jsonb","verification_pass_status","citation_ref","citation_human"],"where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"}},{"name":"bodha_rm_remedy_prescriptions","relation":"bodha_rm_remedy_prescriptions","key_columns":["ayanamsha_id","snapshot_type","target_graha","tradition","remedy_category","remedy_id_g27"],"value_columns":["chart_id","ayanamsha_id","snapshot_type","target_graha","tradition","remedy_category","remedy_id_g27","remedy_label_human","prescription_detail_jsonb","classical_strength_rating","classical_sources_jsonb","targets_dosha_class","resonance_match_score","match_score_formula_version","counter_indications_array","feasibility_score","estimated_cost_inr_range_jsonb","ritual_complexity_class","requires_acharya_review_flag","cross_tradition_corroboration_count","verification_pass_status","citation_ref","citation_human"],"where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"}},{"name":"bodha_rm_dasha_windowed_prescriptions","relation":"bodha_rm_dasha_windowed_prescriptions","key_columns":["ayanamsha_id","dasha_lord"],"value_columns":["chart_id","ayanamsha_id","dasha_system","dasha_level","dasha_lord","window_start_iso","window_end_iso","window_intensity_multiplier","schedule_jsonb","phase_within_window","verification_pass_status","citation_ref","citation_human"],"where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"}},{"name":"bodha_rm_chart_summary","relation":"bodha_rm_chart_summary","key_columns":["ayanamsha_id","snapshot_type"],"value_columns":["chart_id","ayanamsha_id","snapshot_type","top_3_resonance_targets_jsonb","top_10_priority_prescriptions_jsonb","recommended_intensity_class","total_active_dosha_count","primary_dosha_class","cross_tradition_convergence_jsonb","remedy_chart_typology","acharya_review_required_count","feasibility_assessment_jsonb","verification_pass_status","citation_ref","citation_human"],"where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"}},{"name":"bodha_rm_dosha_remedy_bundles","relation":"bodha_rm_dosha_remedy_bundles","key_columns":["ayanamsha_id","dosha_class"],"value_columns":["chart_id","ayanamsha_id","dosha_class","active_flag","intensity_score","cancellation_count","bundle_summary_jsonb","classical_sources_jsonb","verification_pass_status","citation_ref","citation_human"],"where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"}},{"name":"bodha_rm_pattern_remedies","relation":"bodha_rm_pattern_remedies","key_columns":["ayanamsha_id","source_kind","source_id"],"value_columns":["chart_id","ayanamsha_id","source_kind","source_id","remedy_theme","theme_strength","cross_tradition_unanimity_score","verification_pass_status","citation_ref","citation_human"],"where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"}}]}'::jsonb
)
ON CONFLICT (asset_id, spec_sha256) DO NOTHING;
