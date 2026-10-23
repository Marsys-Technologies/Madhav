-- 1400_ka_yojaka_output_digest_v3.sql  (K9 round 4, D6: an identical rebuild must not read as a changed output)
--
-- Number 1400 allocated in MIGRATION_ALLOCATION.json. Lands together with the reader in
-- pipeline/orchestrator/output_digest.py (the `newest_candidate_generation` component key) and with 1399 (#3813):
-- deploy the reader WITH or BEFORE this migration (a reader without the key refuses it, N.8).
-- Requires 1399 (spec v2) to be the current ka_yojaka spec. Transaction ownership belongs to platform/scripts/migrate.ts.
-- Idempotent: when the v3 spec is already current it does nothing. Additive: it retires the v2 row, never edits or deletes it.
--
-- Why.  Spec v2 (1399) covers every non-legacy generation and keys / hashes the generation label, so a forced rebuild that
-- rewrites byte-identical rows still digests differently (rehearsal r4 B2: 2,053 identical rows, output_changed=true, 29-32
-- downstream assets staled).  v3 = v2 with the generation column moved from content to scope: each component carries
-- `newest_candidate_generation`: 'generation', so the digest reads only the generation of the newest kala_layer_candidate of the
-- pinned chart (the one the running build wrote; single build slot).  Superseded generations stay in the table, untouched:
-- no deletion (OWNER-AUTH-TEARDOWN-v2 is not needed).
-- (I) INTERPRETATION: "newest" = ORDER BY created_at DESC, generation DESC on kala_layer_candidate.  Alternative: scope by the
-- candidate bound to the running build; that needs the build id in compute_output_digest, i.e. a change to FROZEN asset_runner.py.
-- A change in an OLDER generation no longer moves the digest (it is not this build's output).
-- The first rebuild after this migration reads as changed once (new spec sha); identical rebuilds after that do not.
-- The v2 row is RETIRED (not edited, not deleted), as 1399 did for 1024; past receipts keep their FK.

DO $pre$
DECLARE v_cur int; v_old int; v_new int;
BEGIN
  SELECT count(*) INTO v_cur FROM asset_output_digest_specs WHERE asset_id = 'ka_yojaka' AND retired_at IS NULL;
  SELECT count(*) INTO v_old FROM asset_output_digest_specs
   WHERE asset_id = 'ka_yojaka' AND retired_at IS NULL AND spec_sha256 = '8e6f307085e417e63cdb85e768a833a1b6305d6cd0b7b138f6371d98ce956367';
  SELECT count(*) INTO v_new FROM asset_output_digest_specs
   WHERE asset_id = 'ka_yojaka' AND retired_at IS NULL AND spec_sha256 = 'd7a0f921e7499b108f1b3dde92417bac898df268639812f8909e20f2fe6f894b';
  IF v_cur <> 1 OR (v_old + v_new) <> 1 THEN
    RAISE EXCEPTION 'ka_yojaka v3 digest spec: the live spec is neither v2 (1399) nor v3 (% current rows, % v2, % v3)', v_cur, v_old, v_new;
  END IF;
  IF v_new = 1 THEN
    RAISE NOTICE 'ka_yojaka v3 digest spec is already current; nothing to do';
  END IF;
END
$pre$;

UPDATE asset_output_digest_specs
   SET retired_at = now()
 WHERE asset_id = 'ka_yojaka' AND spec_sha256 = '8e6f307085e417e63cdb85e768a833a1b6305d6cd0b7b138f6371d98ce956367' AND retired_at IS NULL;

INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
VALUES ('ka_yojaka', 'd7a0f921e7499b108f1b3dde92417bac898df268639812f8909e20f2fe6f894b', '{"version":"nirmana-output-digest-spec-v1","components":[{"name":"kap_candidate_classed","relation":"kala_activation_predicates","key_columns":["chart_id","ayanamsha_id","mechanism_id","event_class_id"],"where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"},"where_not_null":["event_class_id","mechanism_id"],"value_columns":["chart_id","ayanamsha_id","signal_id","signature_class","dasha_eligibility_rule_jsonb","transit_trigger_jsonb","strength_affliction_hook_jsonb","derivation_ledger_jsonb","mechanism_route","conclusion_state_jsonb","mechanism_id","event_class_id"],"newest_candidate_generation":"generation"},{"name":"kap_candidate_classless","relation":"kala_activation_predicates","key_columns":["chart_id","ayanamsha_id","mechanism_id"],"where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"},"where_is_null":["event_class_id"],"where_not_null":["mechanism_id"],"value_columns":["chart_id","ayanamsha_id","signal_id","signature_class","dasha_eligibility_rule_jsonb","transit_trigger_jsonb","strength_affliction_hook_jsonb","derivation_ledger_jsonb","mechanism_route","conclusion_state_jsonb","mechanism_id","event_class_id"],"newest_candidate_generation":"generation"}]}'::jsonb)
ON CONFLICT (asset_id, spec_sha256) DO NOTHING;

DO $post$
DECLARE v_cur int; v_ok int;
BEGIN
  SELECT count(*) INTO v_cur FROM asset_output_digest_specs WHERE asset_id = 'ka_yojaka' AND retired_at IS NULL;
  SELECT count(*) INTO v_ok FROM asset_output_digest_specs
   WHERE asset_id = 'ka_yojaka' AND retired_at IS NULL AND spec_sha256 = 'd7a0f921e7499b108f1b3dde92417bac898df268639812f8909e20f2fe6f894b'
     AND jsonb_array_length(spec -> 'components') = 2;
  IF v_cur <> 1 OR v_ok <> 1 THEN
    RAISE EXCEPTION 'ka_yojaka v3 digest spec is not the single current row (% current, % matching)', v_cur, v_ok;
  END IF;
END
$post$;
