-- ============================================================
-- MARSYS-JIS — L1 Data Assets Volumetric Check
-- Compares expected local-source counts against Cloud SQL rows.
--
-- Run via Auth Proxy:
--   psql $DATABASE_URL -f platform/scripts/l1_volumetric_check.sql
-- Or inline:
--   python3 - << 'EOF'
--   import psycopg, os
--   from dotenv import load_dotenv
--   load_dotenv("platform/.env.local")
--   with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
--       sql = open("platform/scripts/l1_volumetric_check.sql").read()
--       # run section by section (skip \echo lines)
--   EOF
-- ============================================================

-- ---------------------------------------------------------------------------
-- rag_chunks — L1 facts from FORENSIC v8.0 (chart_facts via forensic_render; md archived 99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md)
-- Source has 30 H2 + 79 H3 = 109 section boundaries.
-- Chunker applies MIN_BODY_TOKENS=20 filter — 7 stub/intro sections fall below threshold.
-- EXPECTED: 102 rows (not 109 — the 7-row gap is correct extractor behavior, not missing data)
-- ---------------------------------------------------------------------------
SELECT 'rag_chunks (l1_fact)' AS check, doc_type, layer, COUNT(*) AS rows
FROM rag_chunks
WHERE layer = 'L1' AND doc_type = 'l1_fact' AND is_stale = false
GROUP BY doc_type, layer;

-- ---------------------------------------------------------------------------
-- rag_embeddings — 768-dim vectors for L1 chunks
-- EXPECTED: ~109 rows (1:1 with l1_fact chunks)
-- ---------------------------------------------------------------------------
SELECT 'rag_embeddings (L1)' AS check, re.model, COUNT(*) AS rows
FROM rag_embeddings re
JOIN rag_chunks rc ON rc.chunk_id = re.chunk_id
WHERE rc.layer = 'L1' AND rc.doc_type = 'l1_fact' AND rc.is_stale = false
GROUP BY re.model;

-- ---------------------------------------------------------------------------
-- life_events — from LIFE_EVENT_LOG_v1_2.md
-- Extractor only processes §3 dated point events (EVT.* IDs). §4 chronic patterns
-- and §5 inner turning-point periods are NOT decomposed into rows by the extractor.
-- Sanity gate in extractor is hard-coded to 30–40 (comment reads "expected ~36").
-- EXPECTED: 36 rows (36 point events; the 46 estimate was based on incorrect assumptions)
-- ---------------------------------------------------------------------------
SELECT 'life_events total' AS check, COUNT(*) AS rows FROM life_events;

SELECT 'life_events by category' AS check, category, COUNT(*) AS rows
FROM life_events
GROUP BY category
ORDER BY rows DESC;

-- ---------------------------------------------------------------------------
-- sade_sati_phases — from SADE_SATI_CYCLES_ALL.md (46 transit rows)
-- EXPECTED: 46 rows (Rising:16, Peak:15, Setting:15)
-- ---------------------------------------------------------------------------
SELECT 'sade_sati_phases total' AS check, COUNT(*) AS rows FROM sade_sati_phases;

SELECT 'sade_sati_phases by phase' AS check, phase, COUNT(*) AS rows
FROM sade_sati_phases
GROUP BY phase
ORDER BY phase;

-- ---------------------------------------------------------------------------
-- chart_facts — from CHART_FACTS_EXTRACTION_v1_0.yaml (589 entries)
-- EXPECTED: 589 rows (house:149, dasha_chara:144, planet:54, ...)
-- ---------------------------------------------------------------------------
SELECT 'chart_facts total' AS check, COUNT(*) AS rows
FROM chart_facts
WHERE is_stale = false;

SELECT 'chart_facts by category' AS check, category, COUNT(*) AS rows
FROM chart_facts
WHERE is_stale = false
GROUP BY category
ORDER BY rows DESC;

-- ---------------------------------------------------------------------------
-- eclipses — from ECLIPSES_1900_2100.csv (913 rows)
-- EXPECTED: 913 rows (459 Lunar + 454 Solar)
-- ---------------------------------------------------------------------------
SELECT 'eclipses total' AS check, COUNT(*) AS rows FROM eclipses;

SELECT 'eclipses by kind' AS check,
  CASE WHEN type ILIKE '%lunar%' THEN 'lunar' ELSE 'solar' END AS kind,
  COUNT(*) AS rows
FROM eclipses
GROUP BY kind;

SELECT 'eclipses date range' AS check,
  MIN(date) AS earliest, MAX(date) AS latest
FROM eclipses;

-- ---------------------------------------------------------------------------
-- retrogrades — from RETROGRADES_1900_2100.csv (1,231 periods)
-- EXPECTED: 1,231 or 2,462 rows depending on whether start+end are
--           stored as separate station_type rows per period.
-- ---------------------------------------------------------------------------
SELECT 'retrogrades total' AS check, COUNT(*) AS rows FROM retrogrades;

SELECT 'retrogrades by planet' AS check, planet, COUNT(*) AS rows
FROM retrogrades
GROUP BY planet
ORDER BY rows DESC;

SELECT 'retrogrades by station_type' AS check, station_type, COUNT(*) AS rows
FROM retrogrades
GROUP BY station_type
ORDER BY station_type;

-- ---------------------------------------------------------------------------
-- ephemeris_daily — from EPHEMERIS_MONTHLY_1900_2100.csv
-- Source file has monthly granularity (2,412 months × 9 planets = 21,708 rows at monthly res)
-- but the pipeline stores at DAILY granularity: 1900-01-01 → 2100-12-31 = ~73,414 days × 9 planets
-- EXPECTED: ~660,726 rows (9 planets × ~73,414 days, 1900-01-01 → 2100-12-31)
-- ---------------------------------------------------------------------------
SELECT 'ephemeris_daily total' AS check, COUNT(*) AS rows FROM ephemeris_daily;

SELECT 'ephemeris_daily by planet' AS check, planet, COUNT(*) AS rows
FROM ephemeris_daily
GROUP BY planet
ORDER BY rows DESC;

SELECT 'ephemeris_daily date range' AS check,
  MIN(date) AS earliest, MAX(date) AS latest
FROM ephemeris_daily;

-- ---------------------------------------------------------------------------
-- l25_cgm_nodes — from CGM_v9_0.md (234 nodes across 9 types)
-- EXPECTED: 234 rows
-- ---------------------------------------------------------------------------
SELECT 'l25_cgm_nodes total' AS check, COUNT(*) AS rows FROM l25_cgm_nodes;

SELECT 'l25_cgm_nodes by node_type' AS check, node_type, COUNT(*) AS rows
FROM l25_cgm_nodes
GROUP BY node_type
ORDER BY rows DESC;

-- ---------------------------------------------------------------------------
-- l25_cgm_edges — from 3 manifest JSONs (127 total: 21 valid + 105 orphan + 1 self_loop)
-- EXPECTED NOW:   21 rows (valid only; orphan+self_loop not yet stored)
-- EXPECTED POST-BRIEF STEP 8:  127 rows (all statuses stored)
-- ---------------------------------------------------------------------------
SELECT 'l25_cgm_edges total' AS check, COUNT(*) AS rows FROM l25_cgm_edges;

SELECT 'l25_cgm_edges by status' AS check, status, COUNT(*) AS rows
FROM l25_cgm_edges
GROUP BY status
ORDER BY status;

SELECT 'l25_cgm_edges valid by edge_type' AS check, edge_type, COUNT(*) AS rows
FROM l25_cgm_edges
WHERE status = 'valid'
GROUP BY edge_type
ORDER BY rows DESC;

-- ---------------------------------------------------------------------------
-- MASTER SUMMARY — one row per table
-- Run this last for a quick top-level count against expected values
-- ---------------------------------------------------------------------------
SELECT
  table_name,
  actual_count,
  expected_local AS expected,
  CASE
    WHEN actual_count = expected_local THEN 'MATCH'
    WHEN actual_count > expected_local * 0.9 AND actual_count < expected_local * 1.1 THEN 'CLOSE (~10%)'
    ELSE 'MISMATCH'
  END AS status
FROM (
  VALUES
    ('rag_chunks_l1',        (SELECT COUNT(*)::int FROM rag_chunks WHERE layer='L1' AND doc_type='l1_fact' AND is_stale=false),    102),
    ('life_events',          (SELECT COUNT(*)::int FROM life_events),                                                               36),
    ('sade_sati_phases',     (SELECT COUNT(*)::int FROM sade_sati_phases),                                                          46),
    ('chart_facts',          (SELECT COUNT(*)::int FROM chart_facts WHERE is_stale=false),                                         589),
    ('eclipses',             (SELECT COUNT(*)::int FROM eclipses),                                                                 913),
    ('retrogrades',          (SELECT COUNT(*)::int FROM retrogrades),                                                             1231),
    ('ephemeris_daily',      (SELECT COUNT(*)::int FROM ephemeris_daily),                                                       660726),
    ('l25_cgm_nodes',        (SELECT COUNT(*)::int FROM l25_cgm_nodes),                                                           234),
    ('l25_cgm_edges_valid',  (SELECT COUNT(*)::int FROM l25_cgm_edges WHERE status='valid'),                                        21),
    ('l25_cgm_edges_total',  (SELECT COUNT(*)::int FROM l25_cgm_edges),                                                           127)
) AS t(table_name, actual_count, expected_local)
ORDER BY table_name;
