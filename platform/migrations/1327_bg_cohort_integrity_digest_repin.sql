-- 1327_bg_cohort_integrity_digest_repin.sql
--
-- Suvarna routine migration 1327 (block 1320-1329 claimed on campaign-coordination; mandatory companion item (b) of the delta
-- review of PR #3215, REVIEW_3215; SS ruling N-190): re-pin the whole-table content digest inside bg_cohort's registered
-- integrity_check_sql to the value the L0 rebuild will actually produce once PR #3215 (bg_cohort.py: Ketu retrograde flag mirrors
-- Rahu, sampling_method v2 -> v3) has landed. ONE md5-guarded UPDATE of ONE column of ONE asset_registry row (asset_id 'bg_cohort');
-- nothing else. Transaction ownership belongs to platform/scripts/migrate.ts (no BEGIN/COMMIT here). Data-only: no table or function
-- is created or altered, so it runs as the routine role (amjis_app: no DDL, no CREATE on public).
--
-- THE DEFECT (a time bomb, not a failing check today). Migration 626 pinned into bg_cohort's integrity_check_sql a sha256 over the
-- semantic content of bg_synthetic_cohort:
--     sha256(string_agg(jsonb_build_array(synthetic_id, birth_datetime_utc, birth_lat, birth_lon, ayanamsha_key, positions,
--                                         sampling_method, source_citation)::text, E'\n' ORDER BY synthetic_id))
--     = 921b0f62ca118932608ea3d3da89e8757ba7c6fbb64c41c2bbdc6b1f99e0c5fa
-- Production matches that pin today (read 2026-10-07). PR #3215 changes what the writer stores: Ketu's is_retrograde becomes Rahu's
-- speed-derived flag (7,475 of 10,000 rows flip false -> true; Rahu 0 changes) and SAMPLING_METHOD_VERSION becomes
-- 'uniform_1900_2099_lat60_lon180_true_node_pinned_se1_v3'. The expected L0 rebuild of bg_cohort therefore stores rows whose digest is
-- no longer 921b0f62..., and the writer's post-write integrity check would FAIL the rebuild.
--
-- WHY A RE-PIN AND NOT A NEW DIGEST DEFINITION (SS ruling N-190: prefer a content-only digest that excludes run identity). The
-- digest ALREADY IS content-only. It covers exactly eight columns: the sampled inputs (synthetic_id, birth_datetime_utc, birth_lat,
-- birth_lon, ayanamsha_key), the computed positions, and the two constant labels (sampling_method, source_citation). It already
-- EXCLUDES the run-identity columns of bg_synthetic_cohort (id, build_id, computed_at); a rebuild rewrites build_id and
-- computed_at (verified: the writer's INSERT ... ON CONFLICT (synthetic_id) DO UPDATE sets both on every run; the surrogate id is
-- never touched) and none of the three is read. No column in the digest is volatile across a rebuild: the sampled inputs come from random.Random(20260729) (pure,
-- synthetic_id = i + 1, no random id), the positions from the pinned Swiss Ephemeris corpus, and the two labels are writer constants.
-- So the only thing that must change is the pinned VALUE, and once it is the post-#3215 value a later rebuild that reproduces the
-- same content passes without another re-pin. The definition (columns, ordering, casting) is left BYTE-IDENTICAL on purpose: it is
-- the definition whose method was proven against production on 921b0f62.
--     Residual environment premise, stated plainly: jsonb serialises birth_datetime_utc (timestamptz) in the SESSION time zone, so
--     the digest assumes a UTC session, exactly as it does today (production TimeZone = UTC, read 2026-10-07).
--
-- THE VALUE (derived exactly, three independent ways; the test module reproduces the first two from a committed fixture)
--   NEW pin  c516b597165e2e248b918a4001dce6fd77f137468f9ed8a029d5488613a7c844
--   1. Method proof: the 10,000 stored production rows, each serialised by PostgreSQL's own jsonb_build_array(...)::text and joined
--      with E'\n' in synthetic_id order, hash to 921b0f62... (the existing pin), so the method is the production method.
--   2. Projection: apply the PR's two changes to those stored rows and hash again: positions.Ketu.is_retrograde := positions.Rahu.
--      is_retrograde (7,475 rows change, in exactly ONE path, ('Ketu','is_retrograde'); no other column of any row differs except
--      sampling_method -> the v3 string in all 10,000) = c516b597... Isolation: the method change alone hashes to
--      d1c4c614...; the Ketu change alone to 32653c6c...; both together to c516b597... (so the post-rebuild value is fully
--      explained by those two changes on today's rows).
--   3. Replay: the PR's bg_cohort.py (compute_synthetic_positions, sample_birth_params, the v3 constant, the pinned sepl_18/semo_18/
--      seas_18 files with their pinned sha256s) was run offline over ALL 10,000 seeds. Result vs the stored rows: birth inputs,
--      ayanamsha_key, source_citation: 0 differences; positions: 7,475 Ketu flag differences (the intended change) and SIX
--      +-0.000001 differences in the sixth decimal of a Moon or Lagna sidereal longitude (synthetic ids 173, 459, 1589, 4582, 5207,
--      9876): the replay ran on macOS arm64, the production rows were written on Linux/x86_64 (the writer's own
--      _require_reproducible_write_runtime exists for exactly this rounding-key reason). With those six rows' positions taken from
--      the stored rows (Ketu flag still mirrored) the replay digest is c516b597... too. So the projection is what the writer produces
--      from the seed, up to a platform rounding the writer itself pins to Linux/x86_64.
--   Caveat for the pass: the digest is only proven on the platform it is pinned from; verify after the L0 rebuild that
--   the stored rows hash to the new pin (acceptance S2). If the production rebuild produced any other value, the check stays FALSE and says
--   so; it never silently passes.
--
--   OLD (live, read 2026-10-07 as suvarna_reader; md5 391d0f02482c1a669400a895286103f5, 1959 chars; = the $check$ text of migration 626)
--   NEW (md5 c9fa9795e24ed65843026adf3ba74252, 1959 chars: the OLD text with the single 64-hex literal replaced; same length)
--
-- GUARD AND WHAT HAPPENS WHEN IT DOES NOT MATCH (precedents 1259, 1297, 1299, 1326). The UPDATE is guarded by md5(integrity_check_sql)
-- of the OLD text and replaces the literal with replace(). If the live text is anything else the migration is a NOTICE-and-NO-OP that
-- does not fail the deploy (the NOTICE names the md5 found); the check keeps whatever text it has until reconciled by hand. If the live
-- text already equals the NEW text it is an idempotent no-op (NOTICE, nothing rewritten, trigger not fired). The ONE case that RAISES:
-- the UPDATE ran on the OLD text and the row does not carry the NEW md5 afterwards (the update silently did not take; never trust a
-- silent no-op, CLAUDE.md N.4 / Trap 103). No active-run guard (as 1299/1326): a build straddling the apply reads the new text at its
-- next check.
--
-- SERVING EFFECT AT APPLY (binding). `UPDATE ... SET integrity_check_sql` fires the live trigger nirmana_registry_receipt_invalidation
-- (migration 596): AFTER UPDATE OF depends_on, natural_key_partition, health_probe, integrity_check_sql, target_floor, asset_kind,
-- asset_type, scope, has_writer, is_active, target_table, FOR EACH ROW WHEN (old.* IS DISTINCT FROM new.*), which sets
-- asset_freshness.freshness_state = 'stale' (reason registry_changed) WHERE asset_id = NEW.asset_id. So applying this STALES
-- bg_cohort's freshness rows. That is accepted: bg_cohort is rebuilt in the L0 run of the pass, which writes fresh receipts. No other
-- asset is touched (the trigger is keyed on NEW.asset_id). A re-run updates 0 rows and does not fire the trigger.
--
-- THE WINDOW BETWEEN THIS MIGRATION AND THE REBUILD (accepted by ruling N-190). From the apply until bg_cohort is rebuilt with the
-- #3215 code, the digest conjunct reads FALSE on TODAY'S rows (they still hash to 921b0f62...), so bg_cohort's integrity check is
-- false in that window; the pass rebuilds bg_cohort in the L0 run, after which the check reads true. Order of landing: #3215 and
-- this migration may land in either order as long as both are in before the L0 rebuild; applying this one while the rows are still
-- the v2/Ketu-false rows is the only state where the check is knowingly false.
--
-- VERIFICATION BY PRODUCTION STRUCTURE (Trap 103: never trust a deploy log). After the deploy, as suvarna_reader, expect
-- md5 c9fa9795e24ed65843026adf3ba74252 and length 1959:
--   SELECT asset_id, md5(integrity_check_sql), length(integrity_check_sql) FROM asset_registry WHERE asset_id = 'bg_cohort';
-- (the acceptance SELECTs are 00_ARCHITECTURE/briefs/suvarna/exec/s_l2_acceptance/ACCEPTANCE_BG_COHORT_DIGEST_REPIN.sql.txt).
--
-- NOT CHANGED HERE: the md digest conjunct (1f9e7fcf..., bg_synthetic_cohort_md, unaffected: derived from Moon only), any other
-- conjunct, any other asset's check, the writer, any data row, migration 626 (never edited after apply). Frozen governance copies of
-- 626's text (NIRMANA_T0_MANIFEST_v1_1.json, the L0 registry snapshot) record history and are not rewritten here.
--
-- ROLLBACK (not executed by migrate.ts): UPDATE asset_registry SET integrity_check_sql = replace(integrity_check_sql, <NEW pin>,
-- <OLD pin>) WHERE asset_id = 'bg_cohort' AND md5(integrity_check_sql) = 'c9fa9795e24ed65843026adf3ba74252'; fires the same trigger.
-- Restoring the old pin makes the check false on any rebuild that stores the #3215 rows.

SET LOCAL lock_timeout = '5s';

DO $m1327$
DECLARE
  c_old_md5 constant text := '391d0f02482c1a669400a895286103f5';
  c_new_md5 constant text := 'c9fa9795e24ed65843026adf3ba74252';
  c_old_pin constant text := '921b0f62ca118932608ea3d3da89e8757ba7c6fbb64c41c2bbdc6b1f99e0c5fa';
  c_new_pin constant text := 'c516b597165e2e248b918a4001dce6fd77f137468f9ed8a029d5488613a7c844';
  v_found boolean;
  v_live  text;
  v_md5   text;
BEGIN
  SELECT true, integrity_check_sql INTO v_found, v_live
    FROM asset_registry WHERE asset_id = 'bg_cohort' FOR UPDATE;
  IF v_found IS NOT TRUE THEN
    RAISE NOTICE '1327: no bg_cohort registry row (empty registry); nothing to do';
    RETURN;
  END IF;
  v_md5 := md5(v_live);
  IF v_md5 = c_new_md5 THEN
    RAISE NOTICE '1327: bg_cohort integrity_check_sql already carries the post-#3215 content digest pin; nothing to do';
    RETURN;
  ELSIF v_md5 IS DISTINCT FROM c_old_md5 THEN
    RAISE NOTICE '1327: bg_cohort integrity_check_sql is not the text this migration was written against (md5 %); NO-OP, integrity_check_sql left as is', v_md5;
    RETURN;
  END IF;

  UPDATE asset_registry
     SET integrity_check_sql = replace(integrity_check_sql, c_old_pin, c_new_pin)
   WHERE asset_id = 'bg_cohort'
     AND md5(integrity_check_sql) = c_old_md5;

  SELECT md5(integrity_check_sql) INTO v_md5 FROM asset_registry WHERE asset_id = 'bg_cohort';
  IF v_md5 IS DISTINCT FROM c_new_md5 THEN
    RAISE EXCEPTION '1327: bg_cohort integrity_check_sql update did not take (md5 now %, expected %)', v_md5, c_new_md5;
  END IF;
END
$m1327$;
