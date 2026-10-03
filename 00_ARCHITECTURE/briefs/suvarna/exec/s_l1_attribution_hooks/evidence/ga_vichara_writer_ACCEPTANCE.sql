-- ga_vichara_writer_ACCEPTANCE.sql  (lane TI-l1-vichara-writer-001)
--
-- *** W7 OPERATOR: AN EMPTY FLIP REPORT SAYS NOTHING ABOUT ga_vichara. *** chart_vichara is outside the
-- flip detector's compared tables, so the detector cannot see this lane (it prints a NOT CHECKED line for it).
-- RUN THIS FILE; EVERY ROW MUST READ ok = t. Expected after the rebuild on the canonical chart:
--   valence_pass 7,500 (canonical total across the 5 ayanamshas; 1,500 each), chart_vichara 7,774,
--   leverage as-of = the build run's date (A10), constituent_fact_ids sorted on every row (A8).
--
-- READ-ONLY acceptance queries for the ga_vichara writer change (sorted constituent_fact_ids,
-- whole-row dedupe, nine-column identity assertion, as-of = build-run creation date).
-- Run as a SELECT-only reader (suvarna_reader) AFTER the S-L1 rebuild of ga_vichara on the
-- canonical chart. Counts only; no birth data. Every check returns one row
--   (check_name, observed, expected, ok)
-- and the lane is accepted only when EVERY row has ok = t. A missing ayanamsha or family prints an explicit
-- observed = 0 row (it can never pass by absence).
--
--   ( source ~/.config/suvarna/pgenv.sh >/dev/null 2>&1; psql -X -A -t -F '|' -f ga_vichara_writer_ACCEPTANCE.sql )
--
-- BEFORE THE REBUILD (reader-measured on the stored canonical generation, 2026-10-02): run it and save the output.
-- The rows below are EXPECTED to read ok = f before the rebuild; this is the baseline to compare against:
--   check                                  before (stored today)                       after (expected)
--   A1 valence_pass per ayanamsha          1650 each                                   1500 each
--   A2 valence_pass canonical total        8250                                        7500
--   A3 chart_vichara canonical total       8524                                        7774
--   A4 total per ayanamsha                 krishnamurti 1706, lahiri_chitrapaksha 1706,  1556, 1556, 1553, 1553, 1556
--                                          raman 1703, surya_siddhanta_classical 1703,   (same order)
--                                          true_chitra 1706
--   A5 other four families per ayanamsha   already t (unchanged: leverage 35, consistency 9, ratification 9,
--                                          divergence 3 on krishnamurti/lahiri_chitrapaksha/true_chitra, 0 on
--                                          raman/surya_siddhanta_classical)          t
--   A6 exact-duplicate rows (every stored column, cf SORTED)     750                0
--   A7 identity collisions (nine-column identity, cf SORTED)     750                0
--   A8 rows with unsorted/unmirrored cf    5133                                        0
--   A9 orphan constituent_fact_ids         0 (already t)                               0
--   A10 leverage rows with wrong/missing as_of   175 (no as_of keys yet)             0
--   A11 distinct as_of per ayanamsha (max) 0 (no as_of keys yet)                       1
--   A12 leverage rows missing dasha-system disclosure   175                            0
--   INFO setting system                    (none)|35  (no disclosure keys yet)         the mix, e.g. vimshottari/mudda/...
-- (A6/A7 are measured on the SORTED provenance set, i.e. the 750 true exact duplicates = 150 x 5 ayanamshas;
--  comparing the RAW stored arrays would under-count at 690 because 60 duplicate pairs differ only in cf order.)
--
-- Identity used by the writer assertion and the data-plane capture trigger (after the owner-side
-- constituent_fact_ids addition): (chart_id, ayanamsha_id, vichara_family, subject, target, domain,
-- varga_id, formula_version, constituent_fact_ids sorted) = GRAIN PLUS L1 SOURCE-FACT PROVENANCE SET,
-- NOT a natural key (chart_vichara has none; migration 747).

WITH ayas(a) AS (VALUES ('krishnamurti'), ('lahiri_chitrapaksha'), ('raman'), ('surya_siddhanta_classical'), ('true_chitra')),
fams(f) AS (VALUES ('valence_pass'), ('varga_ratification'), ('varga_ratification_divergence'), ('varga_consistency'), ('leverage_index')),
grid AS (
  SELECT a, f,
         CASE f WHEN 'valence_pass' THEN 1500 WHEN 'leverage_index' THEN 35 WHEN 'varga_consistency' THEN 9
                WHEN 'varga_ratification' THEN 9
                WHEN 'varga_ratification_divergence' THEN CASE WHEN a IN ('raman', 'surya_siddhanta_classical') THEN 0 ELSE 3 END
         END AS expected
  FROM ayas, fams),
cnt AS (
  SELECT ayanamsha_id AS a, vichara_family AS f, count(*) AS n FROM chart_vichara
  WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa' GROUP BY 1, 2),
v AS (
  SELECT *, ARRAY(SELECT x FROM unnest(constituent_fact_ids) x ORDER BY x COLLATE "C") AS cf_sorted
  FROM chart_vichara WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa')
-- A1. valence_pass per ayanamsha: 1,650 -> 1,500 (150 exact duplicates removed per ayanamsha)
SELECT 'A1 valence_pass '||g.a AS check_name, coalesce(c.n, 0) AS observed, g.expected AS expected, coalesce(c.n, 0) = g.expected AS ok
FROM grid g LEFT JOIN cnt c ON c.a = g.a AND c.f = g.f WHERE g.f = 'valence_pass'
UNION ALL
-- A2. canonical valence_pass total 8,250 -> 7,500 (750 exact-duplicate rows removed: 150 x 5 ayanamshas)
SELECT 'A2 valence_pass total', coalesce(sum(n), 0), 7500, coalesce(sum(n), 0) = 7500 FROM cnt WHERE f = 'valence_pass'
UNION ALL
-- A3. chart_vichara canonical total 8,524 -> 7,774
SELECT 'A3 chart_vichara canonical total', coalesce(sum(n), 0), 7774, coalesce(sum(n), 0) = 7774 FROM cnt
UNION ALL
-- A4. per-ayanamsha totals: 1,556 (krishnamurti, lahiri_chitrapaksha, true_chitra), 1,553 (raman, surya_siddhanta_classical)
SELECT 'A4 total '||y.a, coalesce(sum(c.n), 0),
       CASE WHEN y.a IN ('raman', 'surya_siddhanta_classical') THEN 1553 ELSE 1556 END,
       coalesce(sum(c.n), 0) = CASE WHEN y.a IN ('raman', 'surya_siddhanta_classical') THEN 1553 ELSE 1556 END
FROM ayas y LEFT JOIN cnt c ON c.a = y.a GROUP BY y.a
UNION ALL
-- A5. the other four families are untouched per ayanamsha (35 / 9 / 9 / 3-or-0): an explicit row for EVERY
--     (ayanamsha, family) cell, observed = 0 when the family is absent, so absence can never pass
SELECT 'A5 '||g.f||' '||g.a, coalesce(c.n, 0), g.expected, coalesce(c.n, 0) = g.expected
FROM grid g LEFT JOIN cnt c ON c.a = g.a AND c.f = g.f WHERE g.f <> 'valence_pass'
UNION ALL
-- A6. no exact-duplicate whole rows remain (every stored column; constituent_fact_ids compared SORTED;
--     value_jsonb by jsonb equality)
SELECT 'A6 exact-duplicate rows (cf sorted)', coalesce(sum(n - 1), 0), 0, coalesce(sum(n - 1), 0) = 0
FROM (SELECT count(*) AS n FROM v
      GROUP BY ayanamsha_id, vichara_family, subject, actor, target, domain, varga_id, varga, value_num, value_text,
               value_jsonb, ratification_factor, cf_sorted, formula_version, source_citation
      HAVING count(*) > 1) d
UNION ALL
-- A7. no two rows share the nine-column identity (grain + SORTED source-fact provenance set)
SELECT 'A7 identity collisions (cf sorted)', coalesce(sum(n - 1), 0), 0, coalesce(sum(n - 1), 0) = 0
FROM (SELECT count(*) AS n FROM v
      GROUP BY ayanamsha_id, vichara_family, subject, target, domain, varga_id, formula_version, cf_sorted
      HAVING count(*) > 1) d
UNION ALL
-- A8. constituent_fact_ids stored sorted (codepoint order) and mirrored by constituent_facts_array
SELECT 'A8 rows with unsorted or unmirrored cf', count(*), 0, count(*) = 0
FROM chart_vichara v
WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
  AND (constituent_fact_ids <> ARRAY(SELECT x FROM unnest(constituent_fact_ids) x ORDER BY x COLLATE "C")
       OR constituent_fact_ids IS DISTINCT FROM constituent_facts_array)
UNION ALL
-- A9. provenance not lost: zero orphan constituent_fact_ids (every id resolves to chart_facts)
SELECT 'A9 orphan constituent_fact_ids', count(*), 0, count(*) = 0
FROM (SELECT DISTINCT x FROM chart_vichara v, unnest(v.constituent_fact_ids) x
      WHERE v.chart_id = '482012f1-710e-4a25-994a-93821f5871aa') a
WHERE NOT EXISTS (SELECT 1 FROM chart_facts f WHERE f.fact_id = a.x AND f.chart_id = '482012f1-710e-4a25-994a-93821f5871aa')
UNION ALL
-- A10. as-of recorded on EVERY leverage_index row: source = build_run_created_at and as_of = UTC date of
--      the build run that wrote the rows (W7 hand read-back: recorded as_of equals the run date)
SELECT 'A10 leverage rows with wrong/missing as_of', count(*), 0, count(*) = 0
FROM chart_vichara v LEFT JOIN build_runs b ON b.id = v.build_id
WHERE v.chart_id = '482012f1-710e-4a25-994a-93821f5871aa' AND v.vichara_family = 'leverage_index'
  AND (v.value_jsonb->>'as_of_source' IS DISTINCT FROM 'build_run_created_at'
       OR v.value_jsonb->>'as_of' IS DISTINCT FROM to_char((b.created_at AT TIME ZONE 'UTC')::date, 'YYYY-MM-DD'))
UNION ALL
-- A11. one recorded as-of per ayanamsha build (all 35 leverage rows agree)
SELECT 'A11 distinct as_of per ayanamsha (max)', coalesce(max(n), 0), 1, coalesce(max(n), 0) = 1
FROM (SELECT count(DISTINCT value_jsonb->>'as_of') AS n FROM chart_vichara
      WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa' AND vichara_family = 'leverage_index'
      GROUP BY ayanamsha_id) d
UNION ALL
-- A12. dasha-system disclosure on EVERY leverage row (disclosure only; no number changes): a sorted JSON array
--      dasha_runway_systems, and dasha_runway_setting_system (a member of that array when the runway was found,
--      JSON null when it was not)
SELECT 'A12 leverage rows with missing/invalid dasha-system disclosure', count(*), 0, count(*) = 0
FROM chart_vichara v
WHERE v.chart_id = '482012f1-710e-4a25-994a-93821f5871aa' AND v.vichara_family = 'leverage_index'
  AND (jsonb_typeof(v.value_jsonb->'dasha_runway_systems') IS DISTINCT FROM 'array'
       OR NOT (v.value_jsonb ? 'dasha_runway_setting_system')
       OR (v.value_jsonb->>'dasha_runway_found' = 'true'
           AND NOT (v.value_jsonb->'dasha_runway_systems') @> to_jsonb(v.value_jsonb->>'dasha_runway_setting_system'))
       OR (v.value_jsonb->>'dasha_runway_found' = 'false'
           AND (jsonb_typeof(v.value_jsonb->'dasha_runway_setting_system') IS DISTINCT FROM 'null'
                OR jsonb_array_length(v.value_jsonb->'dasha_runway_systems') <> 0)))
ORDER BY 1;

-- INFORMATIONAL: dasha-system mix behind the runway (finding 'leverage runway selects level-1 dasha periods
-- without a system pin: all eight systems mixed; section N.7 item 2'). Reader-measured on the stored canonical
-- data before the rebuild (35 graha x ayanamsha pairs): setting system vimshottari 8, mudda 15, naisargika 5,
-- ashtottari 7; 1 contributing system for 10 pairs, 2 for 17, 3 for 8.
SELECT 'INFO setting system '||coalesce(value_jsonb->>'dasha_runway_setting_system','(none)'),
       count(DISTINCT (ayanamsha_id, subject))
FROM chart_vichara
WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa' AND vichara_family = 'leverage_index'
GROUP BY 1 ORDER BY 1;

-- INFORMATIONAL (not pass/fail): before the rebuild, the stored rows that survive dedupe but whose stored
-- constituent_fact_ids order differs from sorted order. This is the ORDER-ONLY change count N declared
-- in the hook (no value change; the ids themselves are NEW on every row at S-L1 because the fact_id formula
-- drops build_id: membership is natural-key-equivalent, not id-identical; corrected 2026-10-03, N-91 condition 6).
-- N counts the rows stored unsorted in the OLD id space, not the rows that change. Reader-measured 2026-10-02 on the stored canonical data:
-- krishnamurti 980, lahiri_chitrapaksha 968, raman 1000, surya_siddhanta_classical 892, true_chitra 933 = 4,773
-- (stored order is the Python set order of whichever process built the rows, so N is a property of the
-- stored generation, not a constant; after the rebuild it is 0, see A8).
WITH v AS (
  SELECT *, ARRAY(SELECT x FROM unnest(constituent_fact_ids) x ORDER BY x COLLATE "C") AS cf_sorted
  FROM chart_vichara WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
), k AS (
  SELECT ayanamsha_id, constituent_fact_ids <> cf_sorted AS cf_unsorted,
         row_number() OVER (PARTITION BY ayanamsha_id, vichara_family, subject, actor, target, domain, varga_id, varga,
              value_num, value_text, value_jsonb, ratification_factor, cf_sorted, formula_version, source_citation
              ORDER BY id) AS rn
  FROM v
)
SELECT 'INFO surviving rows with cf order change '||ayanamsha_id, count(*) FILTER (WHERE rn = 1 AND cf_unsorted)
FROM k GROUP BY ayanamsha_id ORDER BY 1;
