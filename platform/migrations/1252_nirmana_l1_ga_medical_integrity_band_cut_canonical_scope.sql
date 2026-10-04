-- 1252_nirmana_l1_ga_medical_integrity_band_cut_canonical_scope.sql
--
-- S-L1 band lane (PR #2890; L1 decision sheet Q-L1-16(c) = Track I I-28, SS-ruled N-62): the ONE band table at
-- ga_condition moves the ga_medical indication_strength cut from `<= 0.6 moderate` to `< 0.7 moderate`. The live
-- ga_medical integrity_check_sql (migration 740) re-derives the label with the OLD cut, so after the band-lane
-- writer rebuilds ga_medical its post-write integrity gate FAILS twice over: clause (b) (label = band rule) and the
-- chart-specific Saturn conjunct of (c) (pins 'mild'; the canonical Saturn scores are above 0.6 and below 0.7, i.e.
-- the MID band, 'moderate'). This migration is the registry half of that change. Transaction ownership belongs to
-- platform/scripts/migrate.ts (no BEGIN/COMMIT here). Data-only: one UPDATE of one asset_registry row (ga_medical,
-- amjis_app-owned); no table is altered; no owner path.
--
-- HELD. This file lives in its own draft PR (suvarna/land/TI-mig-1252-medical-band-001). MERGE = APPLY at the next
-- deploy (migrate.ts runs on every deploy, before that deploy's images roll), so it merges ONLY in the S-L1 window
-- W1.
--
-- ORDERING (hard rule).
--   * Applies in the S-L1 window W1, AFTER the writer deploy of the band-lane integration (#2890: the ga_medical
--     writer that stores 'moderate' for 0.6 <= score < 0.7) and BEFORE the ga_medical rebuild in W6. An OLD writer
--     under this NEW clause (it stores 'mild' for 0.6 to 0.7) or a NEW writer under the OLD clause (it stores
--     'moderate') FAILS the post-write integrity gate (the migration-902 failure mode), so the clause and the
--     writer must be on the same side of the rebuild, and nothing rebuilds ga_medical between the two.
--   * Order-independent versus 1221, 1222, 1223, 1226 and 1254: each of those writes a different registry row or
--     column, and the md5 guard below reads only ga_medical's own integrity_check_sql, which none of them touches
--     (1221: ga_structural integrity_check_sql; 1222: ga_vargas integrity_check_sql; 1223: ga_vargas output-digest
--     spec; 1226: depends_on of ga_dashas, ga_yoga, ga_vargas; 1254: ga_sensitive). All permutations are proved in
--     python-sidecar/tests/test_migration_1252_ga_medical_band_scope.py.
--   * 0 ACTIVE RUNS AT APPLY: no build run may be in flight for ga_medical at apply (read-only check, expected 0):
--       SELECT count(*) FROM build_runs r JOIN build_run_assets a ON a.run_id = r.id
--        WHERE a.asset_id = 'ga_medical' AND r.state NOT IN ('completed', 'failed', 'stopped');
--
-- EXPECTED STATE AT APPLY (read this before reading a failing integrity check as a bug). This clause encodes the
-- NEW cuts, so on TODAY's rows (the canonical chart's 15 medical rows whose condition_score lies in (0.6, 0.7) are
-- still labelled 'mild', the OLD band) the new clause reads FALSE. That is EXPECTED, not a defect: the writer
-- deploy changes the labels the rebuild stores, and this migration must apply right before that rebuild. Do NOT
-- apply it earlier "to be safe": between apply and the ga_medical rebuild the asset's integrity check is false by
-- construction (and the asset is stale anyway, see SERVING EFFECT). Read-only evidence, evaluated as
-- suvarna_reader against production on 2026-10-02 (SELECT only; the overlays are CTEs, nothing was written):
--   live (740) clause on today's rows ........................................................ true
--   NEW clause on today's rows (old labels, 15 canonical rows disagree) .................... FALSE (expected)
--   canonical rebuilt (labels recomputed from the stored scores, new cuts) + live clause ..... FALSE (why 1252 exists)
--   canonical rebuilt + NEW clause, the other charts' stale rows still present ............... true
--   all three charts rebuilt + NEW clause ................................................... true
--   canonical rebuilt + the band lane's TABLE-WIDE draft text, stale rows present ............ FALSE (why scoped)
--
-- SERVING EFFECT AT APPLY (binding for every migration PR; read from the catalog 2026-10-02, suvarna_reader).
--   `UPDATE ... SET integrity_check_sql` fires the live trigger nirmana_registry_receipt_invalidation
--   (migration 596): AFTER UPDATE OF depends_on, natural_key_partition, health_probe, integrity_check_sql,
--   target_floor, asset_kind, asset_type, scope, has_writer, is_active, target_table, FOR EACH ROW
--   WHEN (old.* IS DISTINCT FROM new.*), function nirmana_invalidate_registry_receipts(), which sets
--   asset_freshness.freshness_state = 'stale' (reason registry_changed) WHERE asset_id = NEW.asset_id.
--   So ga_medical freshness goes STALE ON EVERY CHART (every scope/partition row of ga_medical) the moment this
--   applies. No other asset is touched. A stale receipt reads `receipt_not_fresh` in the served-generation
--   resolver (platform/src/lib/retrieval/registry/generation/served_generation.ts, partitionDefect), so
--   ga_medical is UNRESOLVED for serving until a governed ga_medical rebuild writes a fresh receipt.
--   Degraded set when this PR merges in W1 together with 1221, 1222, 1223, 1226 and 1254 =
--   {ga_structural (1221), ga_vargas (1222, 1223, 1226), ga_dashas (1226), ga_yoga (1226), ga_sensitive (1254),
--   ga_medical (1252)}; ga_medical is rebuilt in W6 of the same window (the writer deploy moved its digest), so the
--   degradation is bounded by the window. ga_vastu is NOT touched here (see below) and is rebuilt in W6 anyway.
--   A re-run (idempotent no-op, below) updates 0 rows and does NOT fire the trigger again.
--
-- WHY THE CLAUSE IS CANONICAL-SCOPED. Conjunct (b) was table-wide: it measured every chart's ga_medical rows. The
-- band lane's drafted text kept it table-wide, but chart cb73cd3d's five ga_medical rows with a condition_score in
-- (0.6, 0.7) are labelled 'mild' (old cut) and S-L1 does NOT rebuild that chart (owner decision N-78: canonical
-- only, no S-L1b for now), so a table-wide (b) would fail the canonical chart's own ga_medical post-write gate on
-- another chart's stale rows. (b) is therefore scoped to chart_id = '482012f1-710e-4a25-994a-93821f5871aa' by
-- literal, exactly as ga_condition's clauses (a) and (e) already are (migration 899 idiom; the disclosed
-- 882/884/899/902/1019/1022/1215/1222 coverage tradeoff: other charts' builds are not measured here). The
-- canonical-scoped clause is true for the rebuilt canonical chart whatever the other two charts hold (proved
-- below, four-state test). The Saturn and Sun conjuncts of (c) already name the canonical chart and are unchanged
-- except Saturn's pinned label: 'mild' -> 'moderate'. (The band lane's drafted text REMOVED both (c) conjuncts and
-- pinned Saturn and Sun in golden tests instead; the owner-level decision recorded for this migration keeps them,
-- with Saturn moved to 'moderate'. The Sun conjunct, 'strong' below 0.4, is unchanged.)
-- WIDENING (b) BACK TO TABLE-WIDE IS AN S-L1b TASK: once the other two charts are rebuilt under the new cuts, a
-- later migration may drop the scope literal.
--
-- WHY ga_vastu IS NOT TOUCHED. Its cuts (0.4 / 0.7) are identical in the old and the new writer, so the live
-- (migration 741/924) clause (c) does not break on the new cuts: read-only on 2026-10-02, 0 of 120
-- ga_vastu_planet_direction_map rows (3 charts x 40) disagree with the new rule, no ga_condition_composite
-- condition_score is NULL on any chart, and the live clause evaluates true. The one difference in the lane's vastu
-- draft (a NULL score -> 'unknown' instead of 'neutral') is a latent text change that no stored row exercises; it
-- is not part of this migration and stays with the lane.
--
-- BASE TEXT. The live ga_medical integrity_check_sql was read as suvarna_reader on 2026-10-02: 2,811 chars, md5
-- 0b5d65e4933f10ec95b2db2e7d82289d, byte-identical to migration 740's body. The new text is 3,862 chars, md5
-- ae453edf2afeeaba086a444c66681676. The only differences from the base text are five hunks: (1) a header comment
-- naming the canonical scope; (2) the (b) comment; (3) clause (b) gains `WHERE m.chart_id = '<canonical>'` and its cut
-- `<= 0.6` becomes `< 0.7` (the nested block is re-indented); (4) the (c) comment; (5) the Saturn conjunct
-- `<> 'mild'` becomes `<> 'moderate'`. Conjunct (a) and the Sun conjunct are byte-identical.
--
-- IDEMPOTENT SHAPE. The pre-check accepts exactly two states: the base text (apply) or the target text (already
-- applied: NOTICE, and the UPDATE below matches 0 rows, so nothing is rewritten and the trigger does not fire).
-- Any other md5 RAISES: the migration refuses to overwrite a text it was not written against. The post-check proves
-- the new text took (md5 byte-equality to the reviewed target text).
--
-- VERIFICATION BY PRODUCTION STRUCTURE (CLAUDE.md N.4, Trap 103: never trust a deploy log). After the deploy,
-- as suvarna_reader, expect one row with md5 = ae453edf2afeeaba086a444c66681676 and length 3862:
--   SELECT md5(integrity_check_sql), length(integrity_check_sql) FROM asset_registry WHERE asset_id = 'ga_medical';
-- and expect the trigger's effect on ga_medical only (stale until the rebuild writes a fresh receipt):
--   SELECT asset_id, freshness_state, reasons FROM asset_freshness WHERE asset_id = 'ga_medical';
--
-- ROLLBACK (not executed by migrate.ts): UPDATE asset_registry SET integrity_check_sql = <migration 740's body,
-- md5 0b5d65e4933f10ec95b2db2e7d82289d> WHERE asset_id = 'ga_medical'; fires the same trigger (freshness is already
-- stale, so a rollback does not restore the pre-apply 'fresh'; only a governed ga_medical rebuild does).

SET LOCAL lock_timeout = '5s';

DO $pre$
DECLARE v_md5 text; v_n int;
BEGIN
  SELECT count(*), max(md5(integrity_check_sql)) INTO v_n, v_md5 FROM asset_registry WHERE asset_id = 'ga_medical';
  IF v_n <> 1 THEN
    RAISE EXCEPTION '1252: expected exactly one ga_medical registry row, found %', v_n;
  END IF;
  IF v_md5 = 'ae453edf2afeeaba086a444c66681676' THEN
    RAISE NOTICE '1252: ga_medical integrity_check_sql already carries the band-cut canonical-scoped text; nothing to do';
  ELSIF v_md5 IS DISTINCT FROM '0b5d65e4933f10ec95b2db2e7d82289d' THEN
    RAISE EXCEPTION '1252: ga_medical integrity_check_sql is not the text this migration was written against (md5 %)', v_md5;
  END IF;
END
$pre$;

UPDATE asset_registry
SET integrity_check_sql = $ck$
-- ga_medical integrity contract (target table: ga_medical)
-- D-CND-03: chart-partitioned / row-wise, attribution-preserving. No bare count pin (C12).
-- Distinctness already DB-enforced (ga_medical_chart_id_ayanamsha_id_graha_key); not
-- re-asserted here (D-CND-03 rule 4).
-- Conjunct (b) and the (c) Saturn/Sun conjuncts are SCOPED to the canonical chart (migration 1252): the
-- band cut moved from <=0.6 to <0.7 (the I-28 band table, band lane #2890) and the other two charts'
-- ga_medical rows are not rebuilt (owner decision N-78: canonical only, no S-L1b for now), so a table-wide
-- (b) would fail on their stale rows. Same scoping idiom as ga_condition (migration 899); widening (b)
-- back to table-wide is an S-L1b task. (a) stays table-wide.
SELECT
  -- (a) §A Ethical Framework, encoded as a data-layer invariant: this writer's own module
  -- docstring and inline comments mark indication_tier='jyotish_indication' and
  -- not_diagnosis=TRUE as "NON-NEGOTIABLE" (ga_medical_writer.py:18,28,331-332) -- the exact
  -- disclosure discipline the project's stated mission (probabilistic, calibrated, auditable
  -- outputs, "not a fortune-telling product") depends on for this asset's domain. No row may
  -- ever read otherwise.
  NOT EXISTS (
    SELECT 1 FROM ga_medical WHERE indication_tier <> 'jyotish_indication'
  )
  AND NOT EXISTS (
    SELECT 1 FROM ga_medical WHERE not_diagnosis IS DISTINCT FROM true
  )
  -- (b) indication_strength must equal the writer's own threshold formula
  -- (indication_strength_from_score, ga_medical_writer.py: the ONE band table of I-28, cuts 0.4 / 0.7,
  -- lower bound inclusive) applied to the SAME (chart, ayanamsha, graha)'s condition_score in
  -- ga_condition_composite -- re-derived here directly, not restated. A row whose cross-table partner
  -- is missing entirely also fails this NOT EXISTS (an absent match can never satisfy the equality
  -- inside it). SCOPED to the canonical chart (migration 1252): the other charts' rows are not rebuilt
  -- under the new cuts (N-78), so they are not measured here; widening is an S-L1b task.
  AND NOT EXISTS (
    SELECT 1 FROM ga_medical m
    WHERE m.chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
      AND NOT EXISTS (
        SELECT 1 FROM ga_condition_composite c
        WHERE c.chart_id = m.chart_id AND c.ayanamsha_id = m.ayanamsha_id AND c.graha = m.graha
          AND m.indication_strength = (
            CASE
              WHEN c.condition_score IS NULL THEN 'unknown'
              WHEN c.condition_score < 0.4 THEN 'strong'
              WHEN c.condition_score < 0.7 THEN 'moderate'
              ELSE 'mild'
            END
          )
      )
  )
  -- (c) FORENSIC gate, re-asserted at the data layer for the canonical chart's own build-time
  -- check (lahiri_chitrapaksha only): Sun debilitated in Capricorn -> condition_score<0.4 ->
  -- 'strong'; Saturn exalted in Libra -> condition_score in the MID band (0.4 <= s < 0.7; the
  -- canonical lahiri score is above the old 0.6 cut and below 0.7) -> 'moderate' (migration 1252:
  -- was 'mild' under the old <=0.6 cut; the Sun conjunct is unchanged). This is the SAME classical
  -- claim F-E5 (cycle 9) corrected; nothing previously re-checked the writer's own build-time
  -- assertion against what actually landed in the table afterward. Both conjuncts name the
  -- canonical chart, so they were already chart-scoped.
  AND NOT EXISTS (
    SELECT 1 FROM ga_medical
    WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa' AND ayanamsha_id = 'lahiri_chitrapaksha'
      AND graha = 'Sun' AND indication_strength <> 'strong'
  )
  AND NOT EXISTS (
    SELECT 1 FROM ga_medical
    WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa' AND ayanamsha_id = 'lahiri_chitrapaksha'
      AND graha = 'Saturn' AND indication_strength <> 'moderate'
  )
  AS integrity_passed
$ck$
WHERE asset_id = 'ga_medical'
  AND md5(integrity_check_sql) = '0b5d65e4933f10ec95b2db2e7d82289d';

DO $post$
DECLARE v_md5 text;
BEGIN
  SELECT md5(integrity_check_sql) INTO v_md5 FROM asset_registry WHERE asset_id = 'ga_medical';
  IF v_md5 IS DISTINCT FROM 'ae453edf2afeeaba086a444c66681676' THEN
    RAISE EXCEPTION '1252: the new ga_medical integrity_check_sql did not take (md5 %)', v_md5;
  END IF;
END
$post$;
