-- 1215_suvarna_i8_ka_avadhi_integrity_check_chart_scope.sql
--
-- Suvarna Track I-8 (SS pre-approved: a migration that ONLY updates asset_registry rows).
-- Transaction ownership belongs to platform/scripts/migrate.ts (BEGIN/COMMIT around this file).
--
-- WHAT. Re-writes ka_avadhi's `integrity_check_sql` (migration 670, conjunct (d) corrected by 1023)
-- in two ways and no other:
--   (1) every conjunct (a)-(e) is SCOPED to the canonical chart
--       482012f1-710e-4a25-994a-93821f5871aa (hard-coded literal, same mechanism as ka_yojaka's
--       migrations 1019 and 1022);
--   (2) conjunct (b)'s system array lists 'chara_karaka' (the L1 / writer vocabulary) instead of
--       'chara'.
-- Nothing else changes: all five conjuncts and every predicate inside them are kept; only the ROW SET
-- each one scans narrows (conjunct (a), (c), (d), (e) on kala_avadhi a; conjunct (b) on chart_dashas d).
-- The pre-existing comments are byte-identical; one `-- SCOPE (migration 1215)` line is added per conjunct.
--
-- WHY (diagnosis I-7, TRACK_I_FIX_ITEMS). The runner executes `integrity_check_sql` with NO parameters
-- (asset_runner.py `_probe_asset`: `cur.execute(integrity_sql)`), so the registry text cannot know which
-- chart is being built; before this migration it read kala_avadhi for ALL charts. Conjunct (c)
-- (every graha-lord row must carry >= 1 lord_condition_fact_refs) was measured failing on EVERY graha-lord
-- row of all three charts (Abhinandan 770/770, cb73cd3d 902/902, canonical 771/771; the stale rows predate
-- the M4 writer fix 97fd08e1c). The dispatch can only rebuild the canonical chart, so a canonical-only
-- rebuild, however correct, could never turn the table-wide AND true and every run rolled back with
-- 'post-write integrity check failed: integrity_check_sql -> False' (build_runs a40c5e9f, 7cdd60a9, 474811e3).
-- Second, independent defect: fa9857f00 moved the writer to the L1 vocabulary 'chara_karaka' while
-- conjunct (b) still listed 'chara', so (b) silently ignored chara_karaka coverage (a vacuous guard, N.8).
--
-- DISCLOSED TRADEOFF (same as 1019/1022, 882/884/902). Abhinandan (1c826d5a) and cb73cd3d are no longer
-- measured by this check: their stale kala_avadhi rows still violate (c) (and (e)) and are NOT declared
-- fixed here; they need their own coordinated rebuild, after which this scope can be widened. What the
-- scope does NOT trade away: every conjunct still runs, in full, against the chart this campaign can certify.
-- A canonical rebuild now ADDS chara_karaka rows (21 MD + 241 AD); with 'chara_karaka' in (b) their coverage
-- is guarded for the first time.
--
-- DEPLOY. Applies surgically via the normal migrate.ts run. Pre- and post-conditions are asserted below
-- (loud failure, never a silent no-op: CLAUDE.md N.4). Idempotent: re-running writes the same constant.
-- Read-only before/after check: /Users/Dev/suvarna-evidence/TrackI/i8_ka_avadhi_integrity_verify.sql

SET LOCAL lock_timeout = '5s';

DO $pre$
BEGIN
  IF (SELECT count(*) FROM asset_registry WHERE asset_id = 'ka_avadhi') <> 1 THEN
    RAISE EXCEPTION '1215: expected exactly one asset_registry row for ka_avadhi';
  END IF;
END
$pre$;

UPDATE asset_registry SET integrity_check_sql = $ck$

SELECT
  -- ka_avadhi integrity contract (D-CND-03: chart-partitioned, attribution-preserving)
  -- Target table kala_avadhi. Its natural key (chart_id, system_id, level_n, period_start)
  -- is already a DB UNIQUE constraint, so no distinctness conjunct appears here (D-CND-03 item 4).
  -- (a) §N.5 L1-authority: kala_avadhi INHERITS its period spine from chart_dashas and must
  -- never restate it. Every served period must match an L1 row exactly on
  -- (system, level, start, end, lord) at the canonical ayanamsha. This is the machine form of
  -- the CR-110 double-dasha-spine defect: a boundary sourced from a NON-canonical ayanamsha,
  -- or a stale row surviving the writer's upsert, fails here.
  NOT EXISTS (
    -- SCOPE (migration 1215): canonical chart only -- see migration header.
    SELECT 1 FROM kala_avadhi a
    WHERE a.chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
      AND NOT EXISTS (
      SELECT 1 FROM chart_dashas d
      WHERE d.chart_id     = a.chart_id
        AND d.ayanamsha_id = 'lahiri_chitrapaksha'
        AND d.system_id    = a.system_id
        AND d.level_n      = a.level_n
        AND d.start_date   = a.period_start
        AND d.end_date     = a.period_end
        AND d.lord_graha   = a.lord_graha
    )
  )
  -- (b) §N.5 coverage (the other direction): for every chart the asset has built, every
  -- canonical MD/AD period of the seven declared systems must be present. Detects a partial
  -- build, a dropped dasha system, or a chart-scoped truncation that (a) alone cannot see.
  AND NOT EXISTS (
    -- SCOPE (migration 1215): canonical chart only -- see migration header.
    SELECT 1 FROM chart_dashas d
    WHERE d.chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
      AND d.ayanamsha_id = 'lahiri_chitrapaksha'
      AND d.level_n IN (1, 2)
      AND d.system_id = ANY (ARRAY['vimshottari','yogini','ashtottari',
                                   'chara_karaka','naisargika','mudda','kalachakra'])
      AND EXISTS (SELECT 1 FROM kala_avadhi k WHERE k.chart_id = d.chart_id)
      AND NOT EXISTS (
        SELECT 1 FROM kala_avadhi a
        WHERE a.chart_id     = d.chart_id
          AND a.system_id    = d.system_id
          AND a.level_n      = d.level_n
          AND a.period_start = d.start_date
      )
  )
  -- (c) B.3 / §N.5 grounding function is live, not void. The asset's whole stated purpose is
  -- lord_condition_fact_refs. Every period whose lord is one of the nine grahas (the only
  -- lords chart_facts can describe -- chara/yogini lords are signs and yogini names) must
  -- carry at least one ref. This conjunct is RED today by design: the writer queries
  -- fact_subject='Sun' while L1 stores 'SUN', so the array is [] on 100.00% of rows
  -- (W2 M4). A contract that passed both before and after that fix would measure nothing.
  AND NOT EXISTS (
    -- SCOPE (migration 1215): canonical chart only -- see migration header.
    SELECT 1 FROM kala_avadhi a
    WHERE a.chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
      AND a.lord_graha = ANY (ARRAY['Sun','Moon','Mars','Mercury','Jupiter',
                                    'Venus','Saturn','Rahu','Ketu'])
      AND jsonb_array_length(COALESCE(a.dossier->'lord_condition_fact_refs','[]'::jsonb)) = 0
  )
  -- (d) §N.5 refs must RESOLVE and must name their own lord. Every emitted fact ref must
  -- point at a real chart_facts row of the SAME chart, and its fact_subject must be the
  -- period's own lord (case-insensitive -- the exact axis the M4 defect sits on).
  -- FIXED (migration 1020): chart_facts.fact_subject uses short subject codes (SUN, MOON, MAR,
  -- MER, JUP, VEN, SAT, RAH_MEAN, KET_MEAN) while kala_avadhi.lord_graha uses Title-case full
  -- names (Sun, Moon, Mars, ..., Rahu, Ketu) -- upper() alone does not reconcile these for 7 of
  -- 9 grahas. Normalize a.lord_graha to the short-code vocabulary first, mirroring
  -- brahmagyan/graha_vocabulary.py's canonical alias table.
  AND NOT EXISTS (
    SELECT 1 FROM kala_avadhi a
    CROSS JOIN LATERAL jsonb_array_elements(
      COALESCE(a.dossier->'lord_condition_fact_refs','[]'::jsonb)) AS r
    -- SCOPE (migration 1215): canonical chart only -- see migration header.
    WHERE a.chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
      AND (upper(r->>'fact_subject') IS DISTINCT FROM (
            CASE upper(a.lord_graha)
              WHEN 'SUN'     THEN 'SUN'
              WHEN 'MOON'    THEN 'MOON'
              WHEN 'MARS'    THEN 'MAR'
              WHEN 'MERCURY' THEN 'MER'
              WHEN 'JUPITER' THEN 'JUP'
              WHEN 'VENUS'   THEN 'VEN'
              WHEN 'SATURN'  THEN 'SAT'
              WHEN 'RAHU'    THEN 'RAH_MEAN'
              WHEN 'KETU'    THEN 'KET_MEAN'
              ELSE upper(a.lord_graha)
            END
          )
       OR NOT EXISTS (
         SELECT 1 FROM chart_facts f
         WHERE f.chart_id = a.chart_id AND f.fact_id = r->>'fact_id')
    )
  )
  -- (e) the second attribution array must resolve too: every activated_pratijna_id must be a
  -- real bodha_pratijna row of the same chart (B.3 -- no claim without a resolvable source).
  AND NOT EXISTS (
    SELECT 1 FROM kala_avadhi a
    CROSS JOIN LATERAL jsonb_array_elements_text(
      COALESCE(a.dossier->'activated_pratijna_ids','[]'::jsonb)) AS p
    -- SCOPE (migration 1215): canonical chart only -- see migration header.
    WHERE a.chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
      AND NOT EXISTS (
      SELECT 1 FROM bodha_pratijna bp
      WHERE bp.chart_id = a.chart_id AND bp.pratijna_id::text = p)
  )
  AS integrity_passed
$ck$
 WHERE asset_id = 'ka_avadhi';

DO $post$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM asset_registry
    WHERE asset_id = 'ka_avadhi'
      AND position('482012f1-710e-4a25-994a-93821f5871aa' IN integrity_check_sql) > 0
      AND position('''chara_karaka''' IN integrity_check_sql) > 0
      AND position('''chara'',' IN integrity_check_sql) = 0
  ) THEN
    RAISE EXCEPTION '1215: ka_avadhi integrity_check_sql did not take the new text';
  END IF;
END
$post$;
