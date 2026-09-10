-- 1020_nirmana_l3_ka_avadhi_integrity_conjunct_d_graha_code_fix.sql
--
-- NIRMANA v2.5 -- L3 (Kala). Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Fixes an independent defect in ka_avadhi's integrity_check_sql (migration
-- 670) conjunct (d), found this cycle while diagnosing a real build failure
-- on a fresh W1/W2/implementation_accepted-evidenced dispatch attempt
-- (build_runs a40c5e9f-296d-4f79-a1e6-3c651da8ac77, failed on
-- integrity_check_sql -> False after the M4 fact_subject-casing defect
-- (W2 M4, commit 97fd08e1c) had already landed and was live).
--
-- Conjunct (d) compares upper(r->>'fact_subject') against upper(a.lord_graha)
-- to confirm every emitted lord_condition_fact_refs entry names its own
-- period's lord. chart_facts.fact_subject for fact_category='graha_position'
-- uses the SHORT subject codes (live-queried, canonical: SUN, MOON, MAR,
-- MER, JUP, VEN, SAT, RAH_MEAN, KET_MEAN -- see
-- brahmagyan/graha_vocabulary.py's _GRAHA_ALIASES / norm_graha, the SSoT
-- this migration mirrors), while kala_avadhi.lord_graha (sourced from
-- chart_dashas.lord_graha) uses Title-case FULL NAMES (Sun, Moon, Mars,
-- Mercury, Jupiter, Venus, Saturn, Rahu, Ketu). upper() alone does not
-- reconcile a short code against a full name -- 'MAR' != 'MARS', 'MER' !=
-- 'MERCURY', 'JUP' != 'JUPITER', 'VEN' != 'VENUS', 'SAT' != 'SATURN',
-- 'RAH_MEAN' != 'RAHU', 'KET_MEAN' != 'KETU'. Only Sun/Moon happen to
-- survive uppercasing unchanged. This fires for 7 of 9 grahas regardless of
-- how correct the writer's fact-selection is -- an independent bug in the
-- CONTRACT itself, masked until now because conjunct (c) failed first and
-- the whole check was only ever measured as one AND'd boolean (all
-- kala_avadhi rows currently carry empty lord_condition_fact_refs arrays
-- pre-rebuild, under the M4 defect that commit 97fd08e1c already fixed in
-- the writer -- so conjunct (d)'s CROSS JOIN LATERAL over an empty array
-- currently produces zero candidate rows and passes vacuously; this bug
-- would only have surfaced AFTER a rebuild populated the arrays, exactly
-- the state the next real ka_avadhi dispatch is meant to reach).
--
-- Fix, scoped ONLY to conjunct (d) -- same discipline as #2552's scoping to
-- ka_yojaka's conjunct (c): normalize a.lord_graha to the short-code
-- vocabulary chart_facts.fact_subject actually uses via an inline CASE
-- mirroring brahmagyan/graha_vocabulary.py's canonical alias table, before
-- comparing. Every other conjunct ((a), (b), (c), (e)) and every comment is
-- byte-identical to the live migration-670 text (independently re-fetched
-- from asset_registry.integrity_check_sql and diffed against this file
-- before authoring, confirmed no drift from migration 670's original).
--
-- Verified against live production BEFORE this migration (read-only,
-- non-mutating): all 29 distinct kala_avadhi.lord_graha values currently
-- have jsonb_array_length(dossier->'lord_condition_fact_refs') = 0 on every
-- row (0 non-empty out of 2,930 total rows across all lord_graha groups) --
-- so this migration is a genuine no-op against CURRENT data (conjunct (d)
-- passes vacuously before and after), and only changes behavior once a
-- rebuild under the already-landed M4 fix populates the arrays. Overall
-- integrity_passed for ka_avadhi remains FALSE before and immediately after
-- this migration (still blocked on conjunct (c), the true positive migration
-- 670's header documents -- unchanged, expected, not this migration's
-- concern).
--
-- Post-apply verification (N.4/N.8 -- never trust a silent no-op): expect
-- UPDATE 1, then
--   SELECT integrity_check_sql FROM asset_registry WHERE asset_id='ka_avadhi'
-- should contain the literal string 'RAH_MEAN' THEN' inside conjunct (d)'s
-- CASE (grep-verify, cheap positive signal the new text actually landed vs.
-- the old text which had no CASE at all), and re-running the check_sql
-- verbatim against live kala_avadhi should still return integrity_passed=f
-- (conjunct (c) still red, as expected -- this migration does not and
-- cannot flip the overall result until a rebuild lands).
--
-- Numbered 1020, not 1019: authored and applied to live production against this worktree's
-- migrations/ tip (1018), but origin/main had independently landed 1019
-- (nirmana_l3_ka_yojaka_integrity_check_scope.sql, PR #2552) by the time this migration was
-- written up -- a sibling fix for ka_yojaka's own conjunct (c), same "scope the fix to exactly
-- the one broken conjunct" discipline this migration follows for ka_avadhi's conjunct (d).
-- Renumbered to the next free slot after re-fetching origin/main; verified via
-- `git diff --name-only HEAD origin/main -- platform/migrations/` that 1019 was the ONLY new
-- migration file on main since this worktree's branch point, and that it does not touch
-- ka_avadhi or asset_registry's ka_avadhi row.

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
    SELECT 1 FROM kala_avadhi a
    WHERE NOT EXISTS (
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
    SELECT 1 FROM chart_dashas d
    WHERE d.ayanamsha_id = 'lahiri_chitrapaksha'
      AND d.level_n IN (1, 2)
      AND d.system_id = ANY (ARRAY['vimshottari','yogini','ashtottari',
                                   'chara','naisargika','mudda','kalachakra'])
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
    SELECT 1 FROM kala_avadhi a
    WHERE a.lord_graha = ANY (ARRAY['Sun','Moon','Mars','Mercury','Jupiter',
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
    WHERE upper(r->>'fact_subject') IS DISTINCT FROM (
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
  -- (e) the second attribution array must resolve too: every activated_pratijna_id must be a
  -- real bodha_pratijna row of the same chart (B.3 -- no claim without a resolvable source).
  AND NOT EXISTS (
    SELECT 1 FROM kala_avadhi a
    CROSS JOIN LATERAL jsonb_array_elements_text(
      COALESCE(a.dossier->'activated_pratijna_ids','[]'::jsonb)) AS p
    WHERE NOT EXISTS (
      SELECT 1 FROM bodha_pratijna bp
      WHERE bp.chart_id = a.chart_id AND bp.pratijna_id::text = p)
  )
  AS integrity_passed
$ck$
 WHERE asset_id = 'ka_avadhi';
