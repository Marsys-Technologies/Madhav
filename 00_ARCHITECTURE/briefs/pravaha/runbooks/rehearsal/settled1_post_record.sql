-- SETTLED-1 POST RECORD + the verifier-predicate mirror — READ-ONLY SQL for the steward (Stream B, ST-REPIN-TOOL-DECISION 2026-10-04).
-- Run ONLY after the steward has announced 'SETTLED-1 received' (ST-SL1-HOLD: no production read of chart 482012f1 before that).
--   source ~/.config/pravaha/pgenv.sh
--   PGOPTIONS='-c default_transaction_read_only=on' psql -X -A -F '|' -v ON_ERROR_STOP=1 -f settled1_post_record.sql | tee post_record.out ; shasum -a 256 post_record.out
-- One REPEATABLE READ / READ ONLY transaction = one snapshot for every query below.
BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;
SELECT 'snapshot' AS section, pg_current_snapshot()::text AS value, current_user AS who, current_setting('transaction_read_only') AS read_only, now()::text AS at;

-- (a) THE VERIFIER-PREDICATE MIRROR (what inventory_verifier.validate_consumed_dasha_population reads): EVERY Vimshottari / Lahiri row of the canonical chart, ALL levels, ALL tiers, NULL build included.
--     EXPECTED: exactly ONE row, and its build_id equals the SETTLED-1 build id.
SELECT 'a_verifier_predicate_builds' AS section, coalesce(build_id::text, 'NULL') AS build_id, count(*) AS rows
  FROM public.chart_dashas
 WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa' AND system_id = 'vimshottari' AND ayanamsha_id = 'lahiri_chitrapaksha'
 GROUP BY 2 ORDER BY 2;

-- (b1) rows per LEVEL and per TIER for that selection (levels 1-4 and any deeper). Before S-L1 (capture): level 1 = 13, level 2 = 104, level 3 = 923, all two_pass_verified; level 4 changes by design.
SELECT 'b1_levels_by_tier' AS section, level_n, verification_pass_status AS tier, count(*) AS rows
  FROM public.chart_dashas
 WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa' AND system_id = 'vimshottari' AND ayanamsha_id = 'lahiri_chitrapaksha'
 GROUP BY 2, 3 ORDER BY 2, 3;

-- (b2) the WHOLE chart_dashas of the chart: distinct build ids (every system). EXPECTED: exactly ONE row = the SETTLED-1 build.
SELECT 'b2_whole_table_builds' AS section, coalesce(build_id::text, 'NULL') AS build_id, count(*) AS rows
  FROM public.chart_dashas WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa' GROUP BY 2 ORDER BY 2;

-- (b3) the re-pin tool's pair count: distinct (system_id, ayanamsha_id) partitions. EXPECTED: non_scope = 45, scope_cap = 1.
SELECT 'b3_partition_pairs' AS section,
       count(*) FILTER (WHERE system_id <> 'scope_cap') AS non_scope, count(*) FILTER (WHERE system_id = 'scope_cap') AS scope_cap
  FROM (SELECT DISTINCT system_id, ayanamsha_id FROM public.chart_dashas WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa') p;

-- (b4) the full per-partition picture: rows, tiers and builds per (system, ayanamsha) — the pre capture had 45 + 1 pairs on ONE build.
SELECT 'b4_partitions' AS section, system_id, ayanamsha_id, count(*) AS rows, string_agg(DISTINCT verification_pass_status, ',' ORDER BY verification_pass_status) AS tiers,
       count(DISTINCT coalesce(build_id::text, 'NULL')) AS builds
  FROM public.chart_dashas WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa' GROUP BY 2, 3 ORDER BY 2, 3;

-- (b5) asset state. EXPECTED: ga_dashas | lit and ga_positions | lit.
SELECT 'b5_asset_state' AS section, asset_id, state
  FROM public.asset_throughput WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa' AND asset_id IN ('ga_dashas', 'ga_positions') ORDER BY asset_id;

-- (b6) the ten natal longitudes the capture records (Lahiri graha_position / longitude_sidereal).
SELECT 'b6_natal' AS section, fact_subject, fact_value_num, verification_pass_status AS tier, build_id::text AS build_id
  FROM public.chart_facts
 WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa' AND ayanamsha_id = 'lahiri_chitrapaksha' AND fact_category = 'graha_position' AND fact_key = 'longitude_sidereal'
 ORDER BY fact_subject;
ROLLBACK;
