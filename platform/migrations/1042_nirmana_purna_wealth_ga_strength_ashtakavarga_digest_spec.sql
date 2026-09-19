-- 1042_nirmana_purna_wealth_ga_strength_ashtakavarga_digest_spec.sql
--
-- Pūrṇa Anveṣaṇa wealth completion: revise ga_strength's output-digest contract
-- so a governed rebuild can attest the two Ashtakavarga fact families that the
-- wealth reading consumes.  Migration 891 covered only graha_shadbala_total;
-- ga_strength_writer.py also owns the two categories below.  The runner owns
-- the transaction, so this migration deliberately contains no BEGIN/COMMIT.
--
-- The digest-spec table permits historical versions under its composite
-- (asset_id, spec_sha256) primary key.  The loader selects an unretired row
-- without an ORDER BY, so exactly one active version is required.  Fail closed
-- if an unrecognised active version exists; do not silently retire another
-- lane's revision.

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
      '7251b1192714e6e1b09720fff165f78f6089bc74dca862dfaab0f7537ee677c3',
      '3743484c996bf41a9b957224fd5c54cf04f1f1de27ef91116726b60b483bb07a'
    );

  IF unexpected_active_count <> 0 THEN
    RAISE EXCEPTION
      'ga_strength digest-spec revision refused: % unrecognised active row(s)',
      unexpected_active_count;
  END IF;

  UPDATE asset_output_digest_specs
  SET retired_at = now()
  WHERE asset_id = 'ga_strength'
    AND spec_sha256 = '7251b1192714e6e1b09720fff165f78f6089bc74dca862dfaab0f7537ee677c3'
    AND retired_at IS NULL;

  INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
  VALUES (
    'ga_strength',
    '3743484c996bf41a9b957224fd5c54cf04f1f1de27ef91116726b60b483bb07a',
    '{"version":"nirmana-output-digest-spec-v1","components":[{"name":"chart_facts","relation":"chart_facts","where_in":{"fact_category":["ashtakavarga_bindu_per_varga","ashtakavarga_pinda_sarva_per_varga","graha_shadbala_total"]},"key_columns":["fact_id"],"where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"},"value_columns":["fact_id","chart_id","ayanamsha_id","fact_category","fact_subject","fact_key","fact_value_text","fact_value_num","fact_value_jsonb","unit","citation_ref","citation_human","source_calculation","verification_pass_status","engine_version","salience_formula_ver","tolerance_arcsec","near_sign_boundary_flag","near_nakshatra_boundary_flag","vargottama_flag_at_point","formula_provenance_text","cross_ayanamsha_divergence_arcsec","formula_id"]}]}'::jsonb
  )
  ON CONFLICT (asset_id, spec_sha256) DO NOTHING;

  SELECT count(*)
  INTO active_new_count
  FROM asset_output_digest_specs
  WHERE asset_id = 'ga_strength'
    AND spec_sha256 = '3743484c996bf41a9b957224fd5c54cf04f1f1de27ef91116726b60b483bb07a'
    AND retired_at IS NULL;

  IF active_new_count <> 1 THEN
    RAISE EXCEPTION
      'ga_strength digest-spec revision failed: expected one active new row, got %',
      active_new_count;
  END IF;
END $$;
