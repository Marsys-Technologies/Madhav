-- 1223_nirmana_l1_ga_vargas_output_digest_spec_seven_column_key.sql
--
-- S-L1 / F-A2 (SS ruling on the #2858 review, item 5): revise the ga_vargas output-digest spec to the SEVEN-column
-- key, `fact_subject` appended to key_columns. Transaction ownership belongs to platform/scripts/migrate.ts (no
-- BEGIN/COMMIT here). Data-only: retire one asset_output_digest_specs row and add one (the pattern of migrations
-- 1016/1017); the table is amjis_app-owned, no owner path, no triggers. Intent record (on #2858's branch, F-A2):
-- 00_ARCHITECTURE/briefs/suvarna/exec/f_a2_key_widening/F_A2_1223_OUTPUT_DIGEST_SPEC_INTENT_v1_0.md.
--
-- HELD. This file lives in its own draft PR (suvarna/land/TI-mig-1222-1223-001) together with migration 1222. MERGE =
-- APPLY at the next deploy (migrate.ts runs on every deploy, before that deploy's images roll), so it merges
-- ONLY in the S-L1 window W1.
--
-- ORDERING (hard rule).
--   * Merges ONLY in the S-L1 window W1, BACK TO BACK with 1221, 1222 and 1226, so ONE deploy applies all four.
--     Numeric apply order: 1221, 1222, 1223, 1226.
--   * Applied BEFORE the F-A2 ga_vargas rebuild, NEVER after. Applied first, the rebuild's receipt carries the new
--     spec and a deterministic digest; applied after, the first receipt is computed with tied ordering
--     (non-reproducible) and needs one more rebuild to settle.
--   * Valid with the OLD ga_vargas writer image AND the NEW F-A2 writer image: the new key is valid for TODAY'S rows.
--     Read as suvarna_reader on 2026-10-02: chart_divisionals has fact_subject NULL on 0 of 71,476 rows (0 of
--     24,392 rows of the canonical chart, the only rows the spec's where_equals selects), so the key preflight in
--     compute_output_digest (which raises on a NULL key column) passes. With the old image the six-column key
--     is already unique, so the seven-column ORDER BY is the same total order; with the F-A2 image, rows that differ
--     only in fact_subject no longer TIE.
--   * 0 ACTIVE RUNS AT APPLY: no build run may be in flight for ga_vargas at apply (the digest is computed at the end
--     of a build from whichever spec is current then). Read-only check, expected 0:
--       SELECT count(*) FROM build_runs r JOIN build_run_assets a ON a.run_id = r.id
--        WHERE a.asset_id = 'ga_vargas' AND r.state NOT IN ('completed', 'failed', 'stopped');
--
-- SERVING EFFECT AT APPLY (binding for every migration PR; read 2026-10-02, suvarna_reader).
--   Retiring the active ga_vargas spec means EXISTING ga_vargas receipts (built under spec 5f332a48...) no longer
--   join an active spec: the served-generation resolver reads them as `receipt_spec_retired`
--   (platform/src/lib/retrieval/registry/generation/served_generation.ts:200-206 spec_active, :265 partitionDefect),
--   and the reading-checklist / source-query availability joins on retired_at IS NULL drop them. ga_vargas is
--   therefore UNRESOLVED for serving until a ga_vargas rebuild writes a receipt under the new spec. (When 1222
--   has also applied, freshness is stale and the resolver reports `receipt_not_fresh` first: that check precedes
--   the spec check; the spec defect remains underneath and survives a freshness refresh.) This migration has no
--   registry trigger of its own (asset_output_digest_specs carries none); the staleness comes from 1222 and 1226.
--   Degraded set when this PR merges in W1 together with 1221/1226 = {ga_structural, ga_vargas, ga_dashas,
--   ga_yoga}, all rebuilt inside the S-L1 window. Dependents' compute_upstream_hash read the ga_vargas receipt's
--   output_digest, so they go stale when it changes; that cascade is the S-L1 wave order's job (L1 first).
--   The asset is asset_frozen (N-51) and needs no refreeze for a spec revision.
--   KNOWLEDGE-PIN FOLLOW-UP (NOT in this PR; it must land in the same S-L1 window, before the F-A2 ga_vargas rebuild's
--   receipt is relied on): the editorial knowledge declaration of get_divisionals
--   (platform/src/lib/retrieval/registry/knowledge/editorial.ts, producer_output requirement + claim) pins the OLD spec
--   sha 5f332a48..., so a receipt written under the new spec does not satisfy that requirement until the pin moves to
--   9c278d21... Moving it changes the capability knowledge snapshot content hash, which re-pins files owned by other
--   campaigns (the Beyond-Acarya acceptance artifact and the Pariprashna route golden baselines), so it is a separate,
--   coordinated change; the census generator's digest-spec replay order (lexical: 1223 before 883) needs its numeric-order
--   fix in that same change. Until then the census lists the 883 spec as current for ga_vargas.
--
-- WHAT CHANGES. Only key_columns of the one component: `fact_subject` is appended. name, relation, where_equals
-- (chart 482012f1-710e-4a25-994a-93821f5871aa) and value_columns (26, `fact_subject` already among them: re-read live
-- 2026-10-02 from the active spec) are untouched. WHY: after F-A2 a six-column key no longer identifies a row, so rows
-- that differ only in fact_subject TIE in compute_output_digest's ORDER BY and the digest stops being a function of
-- the content (spurious stale/rebuild signals). fact_subject is the writer's own discriminator and the seventh column
-- of the widened chart_divisionals_unique_idx.
--
-- spec_sha256 5f332a4889cb465f317fe7f2315bd59a7aee9d53df58e283b436040403a9bb51 (live, migration 883) was reproduced exactly by canonical_digest over the live spec JSON; the new
-- sha was recomputed (not copied) with the repository's own function:
--   cd platform/python-sidecar && python3 -c "from pipeline.orchestrator.provenance import canonical_digest; ..."
--   -> 9c278d217f045f140596b452aa3c929bc83632bf96f0a266a2532dfe2ee60862
-- and the real compute_output_digest was run read-only against the live table with the new spec: key preflight
-- 0 NULL keys, ORDER BY ... fact_subject, 24,392 rows, identical digest on two runs.
--
-- IDEMPOTENT SHAPE. The pre-check accepts exactly two states: the migration-883 spec is the single current row (apply)
-- or the new spec is the single current row (already applied: NOTICE; the UPDATE matches 0 rows and the INSERT hits
-- ON CONFLICT DO NOTHING). Anything else RAISES. The one-current partial unique index requires retiring FIRST and
-- inserting SECOND, in this order, in the runner's one transaction.
--
-- VERIFICATION BY PRODUCTION STRUCTURE (CLAUDE.md N.4, Trap 103). After the deploy, as suvarna_reader, expect exactly
-- one row, spec_sha256 = 9c278d217f045f140596b452aa3c929bc83632bf96f0a266a2532dfe2ee60862, key_columns ending in fact_subject, and the old row retired:
--   SELECT spec_sha256, retired_at IS NULL AS current, jsonb_array_length(spec #> '{components,0,key_columns}') AS nkey
--     FROM asset_output_digest_specs WHERE asset_id = 'ga_vargas' ORDER BY reviewed_at;
--   -- expect 2 rows: (5f332a48..., false, 6) and (9c278d21..., true, 7)
--
-- ROLLBACK (not executed by migrate.ts): clean only BEFORE the F-A2 ga_vargas rebuild; after it, receipts written under the
-- new spec would read `receipt_spec_retired`. Retire the new row FIRST, then clear retired_at on the old one (the one-current
-- index forbids two current rows):
--   UPDATE asset_output_digest_specs SET retired_at = now() WHERE asset_id = 'ga_vargas' AND spec_sha256 = '9c278d217f045f140596b452aa3c929bc83632bf96f0a266a2532dfe2ee60862' AND retired_at IS NULL;
--   UPDATE asset_output_digest_specs SET retired_at = NULL WHERE asset_id = 'ga_vargas' AND spec_sha256 = '5f332a4889cb465f317fe7f2315bd59a7aee9d53df58e283b436040403a9bb51';

SET LOCAL lock_timeout = '5s';

DO $pre$
DECLARE v_cur int; v_old int; v_new int;
BEGIN
  SELECT count(*) INTO v_cur FROM asset_output_digest_specs
   WHERE asset_id = 'ga_vargas' AND retired_at IS NULL;
  SELECT count(*) INTO v_old FROM asset_output_digest_specs
   WHERE asset_id = 'ga_vargas' AND retired_at IS NULL
     AND spec_sha256 = '5f332a4889cb465f317fe7f2315bd59a7aee9d53df58e283b436040403a9bb51'
     AND spec #> '{components,0,key_columns}' = '["chart_id","graha","ayanamsha_id","varga","fact_category","fact_key"]'::jsonb;
  SELECT count(*) INTO v_new FROM asset_output_digest_specs
   WHERE asset_id = 'ga_vargas' AND retired_at IS NULL
     AND spec_sha256 = '9c278d217f045f140596b452aa3c929bc83632bf96f0a266a2532dfe2ee60862';
  IF v_cur <> 1 OR (v_old + v_new) <> 1 THEN
    RAISE EXCEPTION '1223: the live ga_vargas digest spec is neither the 883 spec nor this migration''s spec (% current rows, % matching the 883 spec, % matching the new spec)', v_cur, v_old, v_new;
  END IF;
  IF v_new = 1 THEN
    RAISE NOTICE '1223: the seven-column ga_vargas digest spec is already current; nothing to do';
  END IF;
END
$pre$;

UPDATE asset_output_digest_specs
   SET retired_at = now()
 WHERE asset_id = 'ga_vargas'
   AND spec_sha256 = '5f332a4889cb465f317fe7f2315bd59a7aee9d53df58e283b436040403a9bb51'
   AND retired_at IS NULL;

INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
VALUES (
  'ga_vargas',
  '9c278d217f045f140596b452aa3c929bc83632bf96f0a266a2532dfe2ee60862',
  '{"version":"nirmana-output-digest-spec-v1","components":[{"name":"chart_divisionals","relation":"chart_divisionals","key_columns":["chart_id","graha","ayanamsha_id","varga","fact_category","fact_key","fact_subject"],"where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"},"value_columns":["chart_id","graha","ayanamsha_id","varga","fact_category","fact_key","sign","sign_number","degree_in_sign","house","vargottama","source_citation","fact_value_text","fact_value_num","fact_subject","verification_pass_status","engine_version","citation_ref","citation_human","source_calculation","tolerance_arcsec","near_sign_boundary_flag","near_nakshatra_boundary_flag","vargottama_flag_at_point","formula_provenance_text","cross_ayanamsha_divergence_arcsec"]}]}'::jsonb
)
ON CONFLICT (asset_id, spec_sha256) DO NOTHING;

DO $post$
DECLARE v_cur int; v_ok int;
BEGIN
  SELECT count(*) INTO v_cur FROM asset_output_digest_specs
   WHERE asset_id = 'ga_vargas' AND retired_at IS NULL;
  SELECT count(*) INTO v_ok FROM asset_output_digest_specs
   WHERE asset_id = 'ga_vargas' AND retired_at IS NULL
     AND spec_sha256 = '9c278d217f045f140596b452aa3c929bc83632bf96f0a266a2532dfe2ee60862'
     AND jsonb_array_length(spec #> '{components,0,key_columns}') = 7
     AND spec #>> '{components,0,key_columns,6}' = 'fact_subject';
  IF v_cur <> 1 OR v_ok <> 1 THEN
    RAISE EXCEPTION '1223: the revised ga_vargas digest spec is not the single current row (% current, % matching)', v_cur, v_ok;
  END IF;
END
$post$;
