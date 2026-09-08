-- 941_nirmana_l2_bo_drishti_output_digest_spec.sql
--
-- NIRMANA v2.5 -- L2 (Bodha). Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Continuation of RESOLUTION_L1 v5 priority 3 (chain pre-clear) past the
-- originally-named 7-asset list (all 7 dispositioned as of #1770's
-- ~22:55Z 2026-09-08 comment). A fresh fleet-wide audit this cycle
-- (`asset_registry LEFT JOIN asset_output_digest_specs WHERE has_writer`)
-- found the 7-asset list was NOT exhaustive -- many more has_writer assets
-- across L2/L3/L4/L5 still lack a spec. bo_drishti is the first picked up
-- from that wider list, per the brief's own sequencing ("then L3 spine,
-- then L4/L5 tails" -- read here as "keep going past the named list").
--
-- bo_drishti (BoDrishtiWriter, pipeline/orchestrator/writers/bo_drishti.py)
-- is the SOLE writer of bodha_question_lenses (grepped every writer file
-- for INSERT/UPDATE against the table; one hit). Its own module docstring
-- states the invariant directly: "one row per (question_type x ayanamsha)".
-- run() does a plain `DELETE FROM bodha_question_lenses WHERE chart_id = %s`
-- (chart-wide, N.3 delete-then-insert) then inserts exactly
-- len(QUESTION_TYPE_CONFIG) x len(CANONICAL_AYAS) = 12 x 5 = 60 rows.
--
-- `lens_id` is a bare `uuid.uuid4()` (writer line ~254), regenerated fresh
-- every rebuild -- excluded from both key_columns and value_columns per the
-- established random-PK-exclusion rule (crib, #1770). The REAL natural key
-- is the composite (ayanamsha_id, question_type) within a chart_id scope,
-- confirmed live: no NULLs on either column for the canonical chart, and
-- COUNT(*) == COUNT(DISTINCT (ayanamsha_id, question_type)) == 60 (exact
-- match to the writer's own declared cardinality).
--
-- Checked bo_drishti's own upstream reads for the same contamination class
-- that ruled out bo_yantra_mechanism this cycle (its fingerprint_hash
-- transitively embeds bodha_cgm_nodes.node_id, which is bare-uuid4 on any
-- node bo_karanajala wrote -- NOT fixed yet, unlike bo_bimba's nodes):
-- bo_drishti's jsonb payload columns reference `signal_id` from
-- bodha_msr_signals only (see _fetch_template_signals/_fetch_dict calls) --
-- bodha_msr_signals.signal_id is the SAME deterministic key every other
-- co-writer spec in this series already relies on (926/929/939 etc.), not
-- a node_id. No contamination risk found.
--
-- value_columns = every live column on bodha_question_lenses EXCEPT
-- lens_id (random uuid, excluded per the rule above) and {build_id,
-- computed_at} (the standard table-invariant exclusion set used by every
-- prior spec in this series, e.g. 926's header). Live schema re-verified
-- via psql \d bodha_question_lenses immediately before authoring this
-- migration: 15 columns total, 12 in the spec, excluded set exactly
-- {lens_id, build_id, computed_at}.
--
-- spec_sha256 computed and independently re-verified via the REAL server
-- functions, never hand-reimplemented:
--   cd platform/python-sidecar && python3 -c "
--   from pipeline.orchestrator.provenance import canonical_digest
--   from pipeline.orchestrator.output_digest import _validate_spec
--   spec = {...}  # exact object below
--   print(canonical_digest(spec))                          # == the literal below
--   print(_validate_spec('bo_drishti', spec, sha).asset_id) # passes the server's own validator
--   "
--
-- Rehearsed end-to-end against live prod inside a ROLLED-BACK transaction
-- (psycopg3, autocommit=False, row_factory=dict_row): INSERT this exact
-- spec row -> call the REAL compute_output_digest() -> got back a clean
-- digest hex (3c2867232bfa1307440f906949e9bc52b31fd43839f08d70f877d6e20b5b01f8,
-- no exception, key-preflight passed) -> conn.rollback() -> re-queried
-- asset_output_digest_specs from a FRESH connection afterward and confirmed
-- 0 rows for bo_drishti, i.e. genuinely rolled back, nothing persisted by
-- the rehearsal.
--
-- Post-apply verification (N.4 -- never trust a silent no-op): expect
-- INSERT 0 1, then
--   SELECT asset_id FROM asset_output_digest_specs
--    WHERE asset_id = 'bo_drishti' AND retired_at IS NULL  -- expect 1 row

INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
VALUES (
  'bo_drishti',
  'fd76f79e2f1b6a6659ef5d7bad4f5a422515fee85ab9245ac0e52fc58f9b81d2',
  '{"version":"nirmana-output-digest-spec-v1","components":[{"name":"bodha_question_lenses","relation":"bodha_question_lenses","key_columns":["ayanamsha_id","question_type"],"value_columns":["chart_id","ayanamsha_id","question_type","template_element_ids_jsonb","wildcard_element_ids_jsonb","all_relevant_ranked_jsonb","lens_template_version","lens_formula_version","points_only_assertion","verification_pass_status","citation_ref","engine_version"],"where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"}}]}'::jsonb
)
ON CONFLICT (asset_id, spec_sha256) DO NOTHING;
