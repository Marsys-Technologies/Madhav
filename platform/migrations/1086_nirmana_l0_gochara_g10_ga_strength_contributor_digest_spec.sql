-- 1086_nirmana_l0_gochara_g10_ga_strength_contributor_digest_spec.sql
--
-- Gochara G-10 (ruling sheet v2.0, row M-7): ga_strength_writer now emits the
-- per-contributor BAV matrix as chart_facts category
-- `ashtakavarga_bindu_contributor` (7 grahas × 8 contributors × 12 rāśis,
-- PyJHora prastara; nāḍī kakṣyā rows PG1615/PG1616 attest the doctrine at
-- TESTIMONY grade only — testimony never supplies computation weight).
-- Revise ga_strength's output-digest contract so a governed rebuild attests
-- the new family alongside the existing three.  Mirrors 1042's pattern.
-- The runner owns the transaction, so this migration deliberately contains
-- no BEGIN/COMMIT.
--
-- spec_sha256 computed via the REAL server function
-- pipeline.orchestrator.provenance.canonical_digest (verified: hashing the
-- 1042 spec reproduces its stored sha exactly).  count_sql coverage needs no
-- change: asset_registry.count_sql for ga_strength already matches
-- `ashtakavarga_%` (migration 307).  target_floor is aspirational (§N.4) and
-- is deliberately NOT bumped here — it rebaselines at the first governed
-- rebuild, which is also when this digest revision is exercised.

DO $$
DECLARE
  unexpected_active_count integer;
  active_new_count integer;
BEGIN
  SELECT count(*)
  INTO unexpected_active_count
  FROM asset_output_digest_specs
  WHERE asset_id = 'ga_strength'
    AND retired_at IS NULL
    AND spec_sha256 NOT IN (
      '3743484c996bf41a9b957224fd5c54cf04f1f1de27ef91116726b60b483bb07a',
      '52a0d2537dc43fc04effe54fd65a165a223e918b14544f96a0892e1df3987a97'
    );

  IF unexpected_active_count <> 0 THEN
    RAISE EXCEPTION
      'ga_strength digest-spec revision refused: % unrecognised active row(s)',
      unexpected_active_count;
  END IF;

  UPDATE asset_output_digest_specs
  SET retired_at = now()
  WHERE asset_id = 'ga_strength'
    AND spec_sha256 = '3743484c996bf41a9b957224fd5c54cf04f1f1de27ef91116726b60b483bb07a'
    AND retired_at IS NULL;

  INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
  VALUES (
    'ga_strength',
    '52a0d2537dc43fc04effe54fd65a165a223e918b14544f96a0892e1df3987a97',
    '{"version":"nirmana-output-digest-spec-v1","components":[{"name":"chart_facts","relation":"chart_facts","where_in":{"fact_category":["ashtakavarga_bindu_contributor","ashtakavarga_bindu_per_varga","ashtakavarga_pinda_sarva_per_varga","graha_shadbala_total"]},"key_columns":["fact_id"],"where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"},"value_columns":["fact_id","chart_id","ayanamsha_id","fact_category","fact_subject","fact_key","fact_value_text","fact_value_num","fact_value_jsonb","unit","citation_ref","citation_human","source_calculation","verification_pass_status","engine_version","salience_formula_ver","tolerance_arcsec","near_sign_boundary_flag","near_nakshatra_boundary_flag","vargottama_flag_at_point","formula_provenance_text","cross_ayanamsha_divergence_arcsec","formula_id"]}]}'::jsonb
  )
  ON CONFLICT (asset_id, spec_sha256) DO NOTHING;

  SELECT count(*)
  INTO active_new_count
  FROM asset_output_digest_specs
  WHERE asset_id = 'ga_strength'
    AND spec_sha256 = '52a0d2537dc43fc04effe54fd65a165a223e918b14544f96a0892e1df3987a97'
    AND retired_at IS NULL;

  IF active_new_count <> 1 THEN
    RAISE EXCEPTION
      'ga_strength digest-spec revision failed: expected one active new row, got %',
      active_new_count;
  END IF;
END $$;
