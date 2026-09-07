-- 876_nirmana_l1_ga_positions_sandhi_flag_correction.sql
--
-- NIRMANA v2.1 -- L1 (Ganita) W4 EXECUTE. Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Self-correction of two of this session's own already-applied migrations:
-- 868 (natural_key_partition, PR #2205, merged) and 875 (output_digest_spec,
-- PR #2220, mid-CI). Both undercounted ga_positions' true chart_facts
-- category ownership at 4 categories; the writer actually owns 5.
--
-- Found while recomputing ga_positions' LIVE registry fingerprint via
-- dispatch_nirmana_campaign_wave.py's own _load_candidates() ahead of a
-- prospective wave-1 verification attempt (cycle 166 follow-up): the live
-- candidate's own registry-authored count_sql already reads
-- "fact_category IN ('graha_position', 'graha_sign_attributes',
-- 'bhava_cusps', 'house_chalit', 'sandhi_flag')" -- 5 categories, one more
-- than migrations 868/875's 4. Traced directly against
-- ga_positions_writer.py: `_build_chalit_rows`'s own docstring (line 445)
-- names sandhi_flag as one of its three emitted categories alongside
-- bhava_cusps/house_chalit, and lines 511-523 confirm the genuine write
-- site (`_chalit_row(..., "sandhi_flag", subj, "sandhi_flag", ...)` /
-- `"sandhi_reasons"`) -- a real per-graha junction-flag category, not a
-- typo or dead code. Exhaustively re-checked the whole file (every literal
-- category-bearing tuple, both `fact_category` variable assignment sites)
-- for any further gap: none found. Confirmed live: all 5 categories
-- present in chart_facts for the canonical chart.
--
-- Fix 1: correct `natural_key_partition` to the true 5-category set
-- (migration 868 is already applied/merged and, per CLAUDE.md B.8/§N.4,
-- is never edited after being applied -- this UPDATE supersedes its value
-- in place, the same pattern already established for a plain corrective
-- registry UPDATE).
--
-- Fix 2: retire the migration-875 output_digest_spec row and insert a
-- corrected one with the same 5-category `where_in` filter.
-- asset_output_digest_specs enforces "one current spec per asset"
-- (asset_output_digest_specs_one_current, UNIQUE (asset_id) WHERE
-- retired_at IS NULL), so retiring the old row is mandatory before the new
-- one can be inserted, not optional cleanup.
--
-- New spec_sha256 computed and validated via the REAL server functions
-- (never hand-reimplemented):
--   cd platform/python-sidecar && python3 -c "
--   from pipeline.orchestrator.provenance import canonical_digest
--   from pipeline.orchestrator.output_digest import _validate_spec
--   spec = {...}  # exact object below
--   print(canonical_digest(spec))                     # == the literal below
--   print(_validate_spec('ga_positions', spec, sha))  # passes the server's own validator
--   "
-- End-to-end rehearsed live (read-only, rollback-only transaction:
-- UPDATE the old spec's retired_at, INSERT the corrected spec row, call
-- the real compute_output_digest(cur, asset_id='ga_positions') against
-- production, then ROLLBACK) before writing this migration. Result:
-- digest=4dacab7c6211c1a77fb4c9d54941fa194befef2d3041beae982c3179e4edd5ae
-- over 1205 live rows -- matching cycle 155's own wave-0 dispatch report
-- ("1205 rows written") exactly, confirming this 5-category scope is the
-- writer's true, complete output, not an over- or under-count. Zero
-- NULL-key rows; transaction rolled back; 0 residue confirmed via a fresh
-- SELECT afterward (old spec's retired_at still NULL post-rollback).

UPDATE asset_registry
   SET natural_key_partition = 'chart_facts.fact_category IN (graha_position, graha_sign_attributes, bhava_cusps, house_chalit, sandhi_flag)'
 WHERE asset_id = 'ga_positions';

UPDATE asset_output_digest_specs
   SET retired_at = NOW()
 WHERE asset_id = 'ga_positions'
   AND spec_sha256 = '474b77debe7776ee7f84a1d6b225b386d7846452cbeb2cc258a98706168e3c9f'
   AND retired_at IS NULL;

INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
VALUES (
  'ga_positions',
  '20afe6b277d6246d4499bbf243681ca650ecfd1bfb29b9614010b69e9c223191',
  '{"components":[{"name":"chart_facts","relation":"chart_facts","key_columns":["fact_id"],"value_columns":["fact_id","chart_id","ayanamsha_id","fact_category","fact_subject","fact_key","fact_value_text","fact_value_num","fact_value_jsonb","unit","citation_ref","citation_human","source_calculation","verification_pass_status","engine_version","salience_formula_ver","tolerance_arcsec","near_sign_boundary_flag","near_nakshatra_boundary_flag","vargottama_flag_at_point","formula_provenance_text","cross_ayanamsha_divergence_arcsec","formula_id"],"where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"},"where_in":{"fact_category":["bhava_cusps","graha_position","graha_sign_attributes","house_chalit","sandhi_flag"]}}],"version":"nirmana-output-digest-spec-v1"}'::jsonb
)
ON CONFLICT (asset_id, spec_sha256) DO NOTHING;
