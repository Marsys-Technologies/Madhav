-- s_l1_ga_vargas_acceptance_check.sql
--
-- S-L1 ACCEPTANCE CRITERIA for ga_vargas after the F-A2 key widening (SS direction on #2858, 2026-10-02).
-- READ-ONLY: a single SELECT, no parameters, safe as suvarna_reader (run it inside BEGIN READ ONLY if you like).
-- Run AFTER the S-L1 ga_vargas rebuild of the canonical chart. These are bare count pins ON PURPOSE: they live here
-- as acceptance criteria checked from the run result, not in asset_registry.integrity_check_sql (SS dropped them
-- from the integrity check).
--
-- Reading the output: one row per criterion; status PASS / FAIL (INFO rows are not criteria). The LAST row,
-- ACCEPTED, is PASS only if every criterion row is PASS.
--
-- Criteria (canonical chart 482012f1-710e-4a25-994a-93821f5871aa; 5 declared ayanamshas x 30 declared vargas):
--   C1  canonical chart_divisionals total = 38,596   (5 x 7,718 + 6 INVARIANT sentinels; was 24,392)
--   C2  each ayanamsha holds 7,718 rows              (was 4,878)
--   C3  INVARIANT scope_cap sentinels = 6            (was 2)
--   C4  varga_house_lord = 12 rows in every ayanamsha x varga          (150 pairs; one lord per house)
--   C5  varga_ashtakavarga = 96 rows in every ayanamsha x varga        (12 signs x (7 grahas + SARVA))
--   C6  varga_d30_lord_per_amsa = 60 rows per ayanamsha                (5 lords x 12 signs)
--   C7  zero rows share the seven-column key (chart, graha, ayanamsha, varga, category, key, subject)
-- Family totals expected on the canonical chart: ashtakavarga 14,400, house_lord 1,800, d30 lords 300.
-- Caveat: C1/C2 include varga_deity_attribution, which follows the live bg_shashtiamsha_deities table (135 per ayanamsha).

WITH canon AS (SELECT '482012f1-710e-4a25-994a-93821f5871aa'::text AS chart_id),
ayas AS (SELECT unnest(ARRAY['lahiri_chitrapaksha','true_chitra','krishnamurti','raman','surya_siddhanta_classical']) AS ayanamsha_id),
vargas AS (SELECT unnest(ARRAY['D1','D2','D3','D4','D5','D6','D7','D8','D9','D10','D11','D12','D14','D15','D16','D20','D21','D24',
                               'D27','D30','D32','D33','D40','D45','D50','D54','D60','D108','D150','D2700']) AS varga),
pairs AS (SELECT a.ayanamsha_id, v.varga FROM ayas a CROSS JOIN vargas v),
cd AS (SELECT d.* FROM chart_divisionals d JOIN canon c ON d.chart_id::text = c.chart_id),
per_aya AS (
  SELECT a.ayanamsha_id, (SELECT count(*) FROM cd WHERE cd.ayanamsha_id = a.ayanamsha_id) AS n FROM ayas a
),
per_pair AS (
  SELECT p.ayanamsha_id, p.varga,
         (SELECT count(*) FROM cd WHERE cd.ayanamsha_id = p.ayanamsha_id AND cd.varga = p.varga AND cd.fact_category = 'varga_house_lord') AS hl,
         (SELECT count(*) FROM cd WHERE cd.ayanamsha_id = p.ayanamsha_id AND cd.varga = p.varga AND cd.fact_category = 'varga_ashtakavarga') AS av
  FROM pairs p
),
d30 AS (
  SELECT a.ayanamsha_id, (SELECT count(*) FROM cd WHERE cd.ayanamsha_id = a.ayanamsha_id AND cd.fact_category = 'varga_d30_lord_per_amsa') AS n FROM ayas a
),
criteria AS (
  SELECT 1 AS ord, 'C1 canonical total'::text AS criterion, '38596'::text AS expected,
         (SELECT count(*) FROM cd)::text AS observed,
         (SELECT count(*) FROM cd) = 38596 AS ok
  UNION ALL
  SELECT 2, 'C2 rows per ayanamsha (ayanamshas not holding 7,718)', '0',
         (SELECT count(*) FROM per_aya WHERE n <> 7718)::text
           || ' [' || (SELECT string_agg(ayanamsha_id || '=' || n, ', ' ORDER BY ayanamsha_id) FROM per_aya) || ']',
         (SELECT count(*) FROM per_aya WHERE n <> 7718) = 0
  UNION ALL
  SELECT 3, 'C3 INVARIANT scope_cap sentinels', '6',
         (SELECT count(*) FROM cd WHERE ayanamsha_id = 'INVARIANT' AND fact_category = 'scope_cap')::text,
         (SELECT count(*) FROM cd WHERE ayanamsha_id = 'INVARIANT' AND fact_category = 'scope_cap') = 6
  UNION ALL
  SELECT 4, 'C4 house_lord: (ayanamsha, varga) pairs not holding 12 (of 150)', '0',
         (SELECT count(*) FROM per_pair WHERE hl <> 12)::text,
         (SELECT count(*) FROM per_pair WHERE hl <> 12) = 0
  UNION ALL
  SELECT 5, 'C5 ashtakavarga: (ayanamsha, varga) pairs not holding 96 (of 150)', '0',
         (SELECT count(*) FROM per_pair WHERE av <> 96)::text,
         (SELECT count(*) FROM per_pair WHERE av <> 96) = 0
  UNION ALL
  SELECT 6, 'C6 D30 lords: ayanamshas not holding 60', '0',
         (SELECT count(*) FROM d30 WHERE n <> 60)::text,
         (SELECT count(*) FROM d30 WHERE n <> 60) = 0
  UNION ALL
  SELECT 7, 'C7 rows sharing the seven-column key', '0',
         ((SELECT count(*) FROM cd) - (SELECT count(*) FROM (SELECT DISTINCT chart_id, graha, ayanamsha_id, varga, fact_category, fact_key, fact_subject FROM cd) u))::text,
         ((SELECT count(*) FROM cd) - (SELECT count(*) FROM (SELECT DISTINCT chart_id, graha, ayanamsha_id, varga, fact_category, fact_key, fact_subject FROM cd) u)) = 0
)
SELECT ord, criterion, expected, observed, CASE WHEN ok THEN 'PASS' ELSE 'FAIL' END AS status FROM criteria
UNION ALL
SELECT 8, 'INFO family totals (ashtakavarga / house_lord / d30; expected 14400 / 1800 / 300)', '14400 / 1800 / 300',
       (SELECT count(*) FROM cd WHERE fact_category = 'varga_ashtakavarga')::text || ' / '
         || (SELECT count(*) FROM cd WHERE fact_category = 'varga_house_lord')::text || ' / '
         || (SELECT count(*) FROM cd WHERE fact_category = 'varga_d30_lord_per_amsa')::text,
       'INFO'
UNION ALL
SELECT 9, 'INFO rows per chart, all charts (canonical is the criterion; others only after their own rebuild)', '38596 each once rebuilt',
       (SELECT string_agg(left(chart_id::text, 8) || '=' || n, ', ' ORDER BY chart_id) FROM (SELECT chart_id, count(*) AS n FROM chart_divisionals GROUP BY chart_id) t),
       'INFO'
UNION ALL
SELECT 10, 'ACCEPTED (every criterion PASS)', 'PASS',
       CASE WHEN (SELECT bool_and(ok) FROM criteria) THEN 'PASS' ELSE 'FAIL' END,
       CASE WHEN (SELECT bool_and(ok) FROM criteria) THEN 'PASS' ELSE 'FAIL' END
ORDER BY ord;
