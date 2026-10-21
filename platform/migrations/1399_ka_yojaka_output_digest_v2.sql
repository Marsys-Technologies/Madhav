-- 1399_ka_yojaka_output_digest_v2.sql  (owner decision OWNER-K9-DIGEST-READER-20261021)
--
-- K9 D10 / D6.  Transaction ownership belongs to platform/scripts/migrate.ts.
--
-- Why.  Spec 1024 keys ka_yojaka's digest on (chart_id, signal_id, ayanamsha_id).  Since
-- migration 1339 the writer also writes candidate rows whose signal_id is legitimately NULL
-- (L1 mechanisms exist without an L2 signal; shared signals are never guessed), and
-- compute_output_digest raises on any NULL reviewed key.  1024 also has no generation scope,
-- so every generation's rows enter the digest (D6).
--
-- Design (every item is an (I) INTERPRETATION for the spec owner):
--  1. Identity = the real unique index idx_kap_mechanism_generation_class:
--     (chart_id, ayanamsha_id, generation, mechanism_id, COALESCE(event_class_id, '')).
--  2. event_class_id is NULL-able but a digest key column must be a plain non-null column, so the
--     tie-break is TWO DISJOINT components: rows with event_class_id NOT NULL are keyed on
--     (chart_id, ayanamsha_id, generation, mechanism_id, event_class_id); rows with
--     event_class_id IS NULL are keyed on (chart_id, ayanamsha_id, generation, mechanism_id).
--     The index maps NULL to '' and the writer never writes '', so within each component the key
--     is unique; together the components cover every candidate row exactly once.
--  3. Generation scoping.  generation is a key and a value column of both components.  Legacy rows
--     (generation 'legacy', mechanism_id NULL) are scoped out by where_not_null mechanism_id --
--     the same predicate as the index's WHERE.  A fixed where_equals on generation is impossible:
--     candidate generations are 'candidate:<build_id>', one per build, and a spec is static.
--     So the digest covers every non-legacy generation of the pinned chart.  Residual D6 scope:
--     per-build isolation would need a parameterised spec, i.e. a change to the digest path.
--  4. Chart pin unchanged from 1024 (canonical chart; the campaign can only rebuild it).
--  5. signal_id stays a VALUE column (may be NULL).  template_version / bound_at are excluded as in
--     1024.  generation, mechanism_route, conclusion_state_jsonb, mechanism_id, event_class_id are
--     added so the digest is sensitive to the candidate graph's content.
--  6. Needs the additive spec filter `where_not_null` (pipeline/orchestrator/output_digest.py,
--     same PR).  Specs that do not use it digest byte-identically to before.  Deploy the reader
--     with (or before) this migration: a reader older than this PR silently IGNORES the unknown
--     `where_not_null` key and would digest the legacy rows; the new reader refuses any key it
--     does not implement (N.8).
--  7. Legacy rows no longer enter the digest (retained published data the writer refuses to touch).
--     Alternative: a third component, where_equals generation='legacy', keyed as in 1024.
--  8. The registry allows ONE current spec per asset (asset_output_digest_specs_one_current), so the
--     1024 row is RETIRED (not edited, not deleted) in the same transaction, as 1223 did for
--     ga_vargas.  Past receipts keep their FK to the 1024 spec.
--
-- spec_sha256 computed by the real canonical_digest and validated by the real _validate_spec.

DO $pre$
DECLARE v_cur int; v_old int; v_new int;
BEGIN
  SELECT count(*) INTO v_cur FROM asset_output_digest_specs
   WHERE asset_id = 'ka_yojaka' AND retired_at IS NULL;
  SELECT count(*) INTO v_old FROM asset_output_digest_specs
   WHERE asset_id = 'ka_yojaka' AND retired_at IS NULL
     AND spec_sha256 = '9f6bbfd1011ebf82aec647c3b80da57365e11a2fffbaf00f3a4df5bc77d307a5';
  SELECT count(*) INTO v_new FROM asset_output_digest_specs
   WHERE asset_id = 'ka_yojaka' AND retired_at IS NULL
     AND spec_sha256 = '8e6f307085e417e63cdb85e768a833a1b6305d6cd0b7b138f6371d98ce956367';
  IF v_cur <> 1 OR (v_old + v_new) <> 1 THEN
    RAISE EXCEPTION '1399: the live ka_yojaka digest spec is neither the 1024 spec nor this migration''s spec (% current rows, % matching 1024, % matching the new spec)', v_cur, v_old, v_new;
  END IF;
  IF v_new = 1 THEN
    RAISE NOTICE '1399: the v2 ka_yojaka digest spec is already current; nothing to do';
  END IF;
END
$pre$;

UPDATE asset_output_digest_specs
   SET retired_at = now()
 WHERE asset_id = 'ka_yojaka'
   AND spec_sha256 = '9f6bbfd1011ebf82aec647c3b80da57365e11a2fffbaf00f3a4df5bc77d307a5'
   AND retired_at IS NULL;

INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
VALUES (
  'ka_yojaka',
  '8e6f307085e417e63cdb85e768a833a1b6305d6cd0b7b138f6371d98ce956367',
  '{"version":"nirmana-output-digest-spec-v1","components":[{"name":"kap_candidate_classed","relation":"kala_activation_predicates","key_columns":["chart_id","ayanamsha_id","generation","mechanism_id","event_class_id"],"where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"},"where_not_null":["event_class_id","mechanism_id"],"value_columns":["chart_id","ayanamsha_id","signal_id","signature_class","dasha_eligibility_rule_jsonb","transit_trigger_jsonb","strength_affliction_hook_jsonb","derivation_ledger_jsonb","generation","mechanism_route","conclusion_state_jsonb","mechanism_id","event_class_id"]},{"name":"kap_candidate_classless","relation":"kala_activation_predicates","key_columns":["chart_id","ayanamsha_id","generation","mechanism_id"],"where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"},"where_is_null":["event_class_id"],"where_not_null":["mechanism_id"],"value_columns":["chart_id","ayanamsha_id","signal_id","signature_class","dasha_eligibility_rule_jsonb","transit_trigger_jsonb","strength_affliction_hook_jsonb","derivation_ledger_jsonb","generation","mechanism_route","conclusion_state_jsonb","mechanism_id","event_class_id"]}]}'::jsonb
)
ON CONFLICT (asset_id, spec_sha256) DO NOTHING;

DO $post$
DECLARE v_cur int; v_ok int;
BEGIN
  SELECT count(*) INTO v_cur FROM asset_output_digest_specs
   WHERE asset_id = 'ka_yojaka' AND retired_at IS NULL;
  SELECT count(*) INTO v_ok FROM asset_output_digest_specs
   WHERE asset_id = 'ka_yojaka' AND retired_at IS NULL
     AND spec_sha256 = '8e6f307085e417e63cdb85e768a833a1b6305d6cd0b7b138f6371d98ce956367'
     AND jsonb_array_length(spec -> 'components') = 2;
  IF v_cur <> 1 OR v_ok <> 1 THEN
    RAISE EXCEPTION '1399: the v2 ka_yojaka digest spec is not the single current row (% current, % matching)', v_cur, v_ok;
  END IF;
END
$post$;
