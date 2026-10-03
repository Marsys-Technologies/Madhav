-- 1254_nirmana_l1_ga_sensitive_integrity_tier_vocabulary.sql
--
-- S-L1 tier-honesty follow-up (L1 tier-honesty lane #2941): the ga_sensitive integrity_check_sql conjunct (a)
-- (verification_pass_status vocabulary) is relaxed from {two_pass_verified, floored} to
-- {two_pass_verified, floored, single, computed_extension}. NOTHING ELSE in the check changes: conjuncts (b) and
-- (c) are byte-identical. Transaction ownership belongs to platform/scripts/migrate.ts (no BEGIN/COMMIT here).
-- Data-only: one UPDATE of one asset_registry row (amjis_app-owned); no table is altered; no owner path.
--
-- HELD. This file lives in its own draft PR (suvarna/land/TI-mig-1254-sensitive-tiers-001), number 1254 reserved for
-- it. MERGE = APPLY at the next deploy (migrate.ts runs on every deploy, before that deploy's images roll), so it
-- merges ONLY in the S-L1 window W1.
--
-- WHY. After the S-L1 rebuild (tier-honesty lane #2941) the 18 explicit categories, the esoteric_point_% /
-- tajik_% families and bhava_arudha carry single, computed_extension, floored and two_pass_verified (five
-- upagrahas). Conjunct (a) of the live text accepts only two_pass_verified/floored, so after the rebuild it FAILS
-- and ga_sensitive ends in `error` (the post-write integrity gate and the freeze-time integrity_verified detector
-- both run this text). Production TODAY: the scope holds exactly two_pass_verified 26,250 and floored 75 (read
-- 2026-10-02, suvarna_reader), so the relaxed text is TRUE today as well as after the rebuild.
--
-- THE VOCABULARY IS AN EXPLICIT LIST OF FOUR. two_pass_verified MUST stay: the clause is unscoped (every chart),
-- and the other two charts keep their old rows until their own rebuild. single_pass is NOT needed and is not
-- added. divergent_flagged, pending_*, classical_match and documented_approximation are NOT in the vocabulary
-- and still make conjunct (a) false: the list is not widened beyond the four tiers the rebuild writes.
--
-- BASE TEXT. The live ga_sensitive integrity_check_sql was read as suvarna_reader on 2026-10-02: 3,069 chars, md5
-- 77099c39ae07a2dfb18c8812d9345c2d, byte-identical to migration 743's check body (migration 744 targets the sibling
-- ga_sensitive_degree and does not touch this row). The new text is 3,303 chars, md5
-- d6dc29259125e4007c3506a42d983296. It differs from the base in exactly two places, both inside conjunct (a):
-- the vocabulary list (`NOT IN ('two_pass_verified', 'floored')` -> `NOT IN ('two_pass_verified', 'floored',
-- 'single', 'computed_extension')`) and the comment sentence that said "exactly two_pass_verified/floored today",
-- which would otherwise stay in the live text as a false statement (CLAUDE.md N.7 item 4 / N.8). The post-check
-- below proves this: replacing those two fragments back in the stored text reproduces the base md5.
--
-- ORDERING (hard rule).
--   * Merges ONLY in the S-L1 window W1. It must apply BEFORE the ga_sensitive rebuild in W4/W6, never after: the
--     rebuild's post-write integrity gate and the freeze-time integrity_verified detector then run the relaxed
--     text against the rebuilt rows. After the rebuild, with the old text, ga_sensitive ends in `error`.
--   * Independent of 1219, 1221, 1222, 1223 and 1226 in content: it writes asset_registry.integrity_check_sql of
--     ga_sensitive only, and the md5 guard below is on that column of that row, which none of the others touches
--     (1221: ga_structural integrity_check_sql; 1222: ga_vargas integrity_check_sql; 1223: the ga_vargas output
--     digest spec; 1226: depends_on of ga_dashas, ga_yoga, ga_vargas). Any apply order among 1219, 1221, 1222, 1223,
--     1226 and 1254 is fine.
--   * 0 ACTIVE RUNS AT APPLY: no build run may be in flight for ga_sensitive at apply (read-only check, expected 0):
--       SELECT count(*) FROM build_runs r JOIN build_run_assets a ON a.run_id = r.id
--        WHERE a.asset_id = 'ga_sensitive' AND r.state NOT IN ('completed', 'failed', 'stopped');
--
-- SERVING EFFECT AT APPLY (binding for every migration PR; same trigger as 1222, read from the catalog 2026-10-02).
--   `UPDATE ... SET integrity_check_sql` fires the live trigger nirmana_registry_receipt_invalidation
--   (migration 596): AFTER UPDATE OF depends_on, natural_key_partition, health_probe, integrity_check_sql,
--   target_floor, asset_kind, asset_type, scope, has_writer, is_active, target_table, FOR EACH ROW WHEN
--   (old.* IS DISTINCT FROM new.*), function nirmana_invalidate_registry_receipts(), which sets
--   asset_freshness.freshness_state = 'stale' (reason registry_changed) WHERE asset_id = NEW.asset_id.
--   So ga_sensitive freshness goes STALE ON EVERY CHART (every scope/partition row of ga_sensitive) the moment this
--   applies. No other asset is touched. A stale receipt reads `receipt_not_fresh` in the served-generation resolver
--   (platform/src/lib/retrieval/registry/generation/served_generation.ts, partitionDefect), so ga_sensitive is
--   UNRESOLVED for serving until a governed ga_sensitive rebuild writes a fresh receipt.
--   Degraded set when this PR merges in W1 together with 1221, 1222, 1223 and 1226 = FIVE assets:
--   {ga_structural (1221), ga_vargas (1222, 1223, 1226), ga_dashas (1226), ga_yoga (1226), ga_sensitive (1254)};
--   all five are rebuilt inside the S-L1 window anyway, so the degradation is bounded by the window. A re-run
--   (idempotent no-op, below) updates 0 rows and does NOT fire the trigger again.
--
-- IDEMPOTENT SHAPE. The pre-check accepts exactly two states: the base text (apply) or the target text (already
-- applied: NOTICE, and the UPDATE below matches 0 rows, so nothing is rewritten and the trigger does not fire).
-- Any other md5, or anything but exactly one ga_sensitive registry row, RAISES: the migration refuses to overwrite
-- a text it was not written against. The post-check proves the new text took AND that only conjunct (a) changed.
--
-- NEVER EDIT THIS FILE AFTER IT HAS BEEN APPLIED (CLAUDE.md N.4): a further vocabulary change is a new migration.
--
-- VERIFICATION BY PRODUCTION STRUCTURE (CLAUDE.md N.4, Trap 103: never trust a deploy log). After the deploy, as
-- suvarna_reader, expect one row with md5 = d6dc29259125e4007c3506a42d983296 and length 3303:
--   SELECT md5(integrity_check_sql), length(integrity_check_sql) FROM asset_registry WHERE asset_id = 'ga_sensitive';
-- and expect the trigger's effect on ga_sensitive only (stale until the rebuild writes a fresh receipt):
--   SELECT asset_id, freshness_state, reasons FROM asset_freshness WHERE asset_id = 'ga_sensitive';
-- The new text was also evaluated read-only against production as suvarna_reader (2026-10-02, READ ONLY
-- transaction): integrity_passed = true (the base text: true).
--
-- ROLLBACK (not executed by migrate.ts): UPDATE asset_registry SET integrity_check_sql = <migration 743's check body,
-- md5 77099c39ae07a2dfb18c8812d9345c2d> WHERE asset_id = 'ga_sensitive'; fires the same trigger (freshness is already
-- stale, so a rollback does not restore the pre-apply 'fresh'; only a governed ga_sensitive rebuild does).

SET LOCAL lock_timeout = '5s';

DO $pre$
DECLARE v_md5 text; v_n int;
BEGIN
  SELECT count(*), max(md5(integrity_check_sql)) INTO v_n, v_md5 FROM asset_registry WHERE asset_id = 'ga_sensitive';
  IF v_n <> 1 THEN
    RAISE EXCEPTION '1254: expected exactly one ga_sensitive registry row, found %', v_n;
  END IF;
  IF v_md5 = 'd6dc29259125e4007c3506a42d983296' THEN
    RAISE NOTICE '1254: ga_sensitive integrity_check_sql already carries the relaxed tier vocabulary; nothing to do';
  ELSIF v_md5 IS DISTINCT FROM '77099c39ae07a2dfb18c8812d9345c2d' THEN
    RAISE EXCEPTION '1254: ga_sensitive integrity_check_sql is not the text this migration was written against (md5 %)', v_md5;
  END IF;
END
$pre$;

UPDATE asset_registry
SET integrity_check_sql = $ck$
-- ga_sensitive integrity contract (target table: chart_facts, scoped to the count_sql's own
-- 18-category-family scope: 17 explicit fact_categories, esoteric_point_%/tajik_% LIKE families,
-- and bhava_arudha). D-CND-03: chart-partitioned / row-wise, attribution-preserving. No bare
-- count pin (C12). chart_facts_unique_null_formula already exactly matches the natural key -- no
-- distinctness conjunct (D-CND-03 rule 4).
SELECT
  -- (a) verification_pass_status vocabulary: the writer's own module docstring claims "Every row
  -- two-pass verified (zero single, zero divergent_flagged)" -- absent-prerequisite rows floor to
  -- 'floored' instead of fabricating a value (no third state existed at 743). Migration 1254
  -- relaxes ONLY this vocabulary, to the four tiers the S-L1 rebuild writes in this scope:
  -- two_pass_verified, floored, single, computed_extension (explicit list; classical_match,
  -- divergent_flagged, single_pass, documented_approximation, pending_* and any other tier still fail).
  NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE (fact_category IN (
             'upagraha_position', 'saturn_derived_point', 'saham_position',
             'karaka_chara_position', 'karakamsa_position', 'swamsa_position',
             'arudha_pada', 'midpoint', 'aprakasha_position',
             'lal_kitab_special_point', 'maharsi_specific_point', 'bhrigu_nadi_point',
             'sensitive_point_gulika_mandi', 'sun_derived_upagraha', 'special_lagna',
             'nakshatra_pada_sensitive', 'kp_ruling_planets_natal', 'kp_cuspal_significators'
           )
        OR fact_category LIKE 'esoteric_point_%'
        OR fact_category LIKE 'tajik_%'
        OR fact_category = 'bhava_arudha')
      AND verification_pass_status NOT IN ('two_pass_verified', 'floored', 'single', 'computed_extension')
  )
  -- (b) special_lagna's sign_lord must equal the L0 reference_signs authority's lord for the
  -- stored sign (§N.5) -- never restated from a local table. 105/105 rows matched live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts s
    JOIN chart_facts l ON l.chart_id = s.chart_id AND l.ayanamsha_id = s.ayanamsha_id
      AND l.fact_subject = s.fact_subject AND l.fact_category = 'special_lagna'
      AND l.fact_key = 'sign_lord'
    WHERE s.fact_category = 'special_lagna' AND s.fact_key = 'sign'
      AND NOT EXISTS (
        SELECT 1 FROM reference_signs r
        WHERE lower(r.canonical_name_en) = lower(s.fact_value_text)
          AND lower(r.lord) = lower(l.fact_value_text)
      )
  )
  -- (c) bhava_arudha's classical Parashari 2-exception rule (BPHS ch.32 v.2-3, cited in
  -- _build_bhava_arudha_rows, ga_sensitive_writer.py:1619): an arudha can never land in its own
  -- origin house, nor the 7th house counted from the origin -- the writer shifts by 10 signs when
  -- the raw formula would produce either. Re-asserted here directly against the stored house_d1.
  -- 0/210 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'bhava_arudha' AND fact_key = 'house_d1'
      AND (
        fact_value_num::int = substring(fact_subject from 'BHAVA_ARUDHA_A(\d+)')::int
        OR fact_value_num::int = (((substring(fact_subject from 'BHAVA_ARUDHA_A(\d+)')::int - 1 + 6) % 12) + 1)
      )
  )
  AS integrity_passed
$ck$
WHERE asset_id = 'ga_sensitive'
  AND md5(integrity_check_sql) = '77099c39ae07a2dfb18c8812d9345c2d';

DO $post$
DECLARE v_text text; v_back text;
BEGIN
  SELECT integrity_check_sql INTO v_text FROM asset_registry WHERE asset_id = 'ga_sensitive';
  IF md5(v_text) IS DISTINCT FROM 'd6dc29259125e4007c3506a42d983296' THEN
    RAISE EXCEPTION '1254: the new ga_sensitive integrity_check_sql did not take (md5 %)', md5(v_text);
  END IF;
  -- ONLY conjunct (a) changed: undoing the two (a) fragments in the stored text reproduces the base text exactly.
  v_back := replace(replace(v_text,
    $f$AND verification_pass_status NOT IN ('two_pass_verified', 'floored', 'single', 'computed_extension')$f$,
    $f$AND verification_pass_status NOT IN ('two_pass_verified', 'floored')$f$),
    $f$(no third state existed at 743). Migration 1254
  -- relaxes ONLY this vocabulary, to the four tiers the S-L1 rebuild writes in this scope:
  -- two_pass_verified, floored, single, computed_extension (explicit list; classical_match,
  -- divergent_flagged, single_pass, documented_approximation, pending_* and any other tier still fail).$f$,
    $f$(no third state exists). Confirmed live: exactly
  -- two_pass_verified/floored appear in this scope today (26,250 + 75), nothing else.$f$);
  IF md5(v_back) IS DISTINCT FROM '77099c39ae07a2dfb18c8812d9345c2d' THEN
    RAISE EXCEPTION '1254: the new ga_sensitive integrity_check_sql differs from the base outside conjunct (a) (md5 %)', md5(v_back);
  END IF;
END
$post$;
