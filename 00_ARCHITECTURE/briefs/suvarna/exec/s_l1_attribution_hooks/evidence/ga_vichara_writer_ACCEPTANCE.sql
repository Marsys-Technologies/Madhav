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
-- and the lane is accepted only when EVERY row has ok = t.
-- Run it BEFORE the rebuild as well and save the output: the "before" baseline is the reader-measured
-- stored state (valence_pass 1650/aya, total 8524, cf-order changes N = 4773 surviving rows).
--
--   ( source ~/.config/suvarna/pgenv.sh >/dev/null 2>&1; psql -X -A -t -F '|' -f ga_vichara_writer_ACCEPTANCE.sql )
--
-- Identity used by the writer assertion and the data-plane capture trigger (after the owner-side
-- constituent_fact_ids addition): (chart_id, ayanamsha_id, vichara_family, subject, target, domain,
-- varga_id, formula_version, constituent_fact_ids sorted) = GRAIN PLUS L1 SOURCE-FACT PROVENANCE SET,
-- NOT a natural key (chart_vichara has none; migration 747).

-- A1. valence_pass per ayanamsha: 1,650 -> 1,500 (150 exact duplicates removed per ayanamsha)
SELECT 'A1 valence_pass '||ayanamsha_id AS check_name, count(*) AS observed, 1500 AS expected, count(*) = 1500 AS ok
FROM chart_vichara
WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa' AND vichara_family = 'valence_pass'
GROUP BY ayanamsha_id
UNION ALL
-- A2. canonical valence_pass total 8,250 -> 7,500 (750 exact-duplicate rows removed: 150 x 5 ayanamshas)
SELECT 'A2 valence_pass total', count(*), 7500, count(*) = 7500
FROM chart_vichara WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa' AND vichara_family = 'valence_pass'
UNION ALL
-- A3. chart_vichara canonical total 8,524 -> 7,774
SELECT 'A3 chart_vichara canonical total', count(*), 7774, count(*) = 7774
FROM chart_vichara WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
UNION ALL
-- A4. per-ayanamsha totals: 1,556 (krishnamurti, lahiri_chitrapaksha, true_chitra), 1,553 (raman, surya_siddhanta_classical)
SELECT 'A4 total '||ayanamsha_id, count(*),
       CASE WHEN ayanamsha_id IN ('raman','surya_siddhanta_classical') THEN 1553 ELSE 1556 END,
       count(*) = CASE WHEN ayanamsha_id IN ('raman','surya_siddhanta_classical') THEN 1553 ELSE 1556 END
FROM chart_vichara WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa' GROUP BY ayanamsha_id
UNION ALL
-- A5. the other four families are untouched per ayanamsha (35 / 9 / 9 / 3-or-0)
SELECT 'A5 '||vichara_family||' '||ayanamsha_id, count(*),
       CASE vichara_family WHEN 'leverage_index' THEN 35 WHEN 'varga_consistency' THEN 9 WHEN 'varga_ratification' THEN 9
            WHEN 'varga_ratification_divergence' THEN 3 END,
       count(*) = CASE vichara_family WHEN 'leverage_index' THEN 35 WHEN 'varga_consistency' THEN 9 WHEN 'varga_ratification' THEN 9
            WHEN 'varga_ratification_divergence' THEN 3 END
FROM chart_vichara
WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa' AND vichara_family <> 'valence_pass'
GROUP BY ayanamsha_id, vichara_family
UNION ALL
-- A6. no exact-duplicate whole rows remain (every stored column, cf sorted, value_jsonb canonical by jsonb equality)
SELECT 'A6 exact-duplicate rows', coalesce(sum(n - 1), 0), 0, coalesce(sum(n - 1), 0) = 0
FROM (SELECT count(*) AS n FROM chart_vichara
      WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
      GROUP BY ayanamsha_id, vichara_family, subject, actor, target, domain, varga_id, varga, value_num, value_text,
               value_jsonb, ratification_factor, constituent_fact_ids, formula_version, source_citation
      HAVING count(*) > 1) d
UNION ALL
-- A7. no two rows share the nine-column identity (grain + sorted source-fact provenance set)
SELECT 'A7 identity collisions', coalesce(sum(n - 1), 0), 0, coalesce(sum(n - 1), 0) = 0
FROM (SELECT count(*) AS n FROM chart_vichara
      WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
      GROUP BY ayanamsha_id, vichara_family, subject, target, domain, varga_id, formula_version, constituent_fact_ids
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
-- in the hook (no value, no membership change). Reader-measured 2026-10-02 on the stored canonical data:
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
