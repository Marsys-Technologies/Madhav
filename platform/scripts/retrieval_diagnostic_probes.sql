-- =============================================================
-- MARSYS-JIS — Retrieval Diagnostic Probes
-- Purpose: ground-truth inspection of what the 10 retrieval tools
--          ACTUALLY have to work with in Cloud SQL today.
--          Confirms or refutes the static analysis from source files.
--
-- Run via: psql $DATABASE_URL -f retrieval_diagnostic_probes.sql
-- Or via Auth Proxy on port 5433.
-- =============================================================

\echo ''
\echo '================================================================'
\echo 'PROBE 1 — MSR signal density per (domain × planet × forward_looking)'
\echo 'Purpose: identify (domain, planet) cells where filter returns 0–2 rows.'
\echo 'These are the cells where msr_sql is structurally starved.'
\echo '================================================================'
SELECT
  domain,
  planet,
  is_forward_looking,
  COUNT(*) AS signals,
  ROUND(AVG(confidence)::numeric, 2) AS avg_conf,
  ROUND(AVG(significance)::numeric, 2) AS avg_sig
FROM msr_signals
WHERE native_id = 'abhisek_mohanty'
GROUP BY domain, planet, is_forward_looking
ORDER BY signals ASC, domain, planet
LIMIT 40;
-- Read: rows at the top (signals=1 or 2) are starved cells. If a user
-- query lands on one, msr_sql will return ~nothing.

\echo ''
\echo '================================================================'
\echo 'PROBE 2 — MSR signals by signal_type and temporal_activation'
\echo 'Purpose: confirm signal_type / temporal_activation columns exist'
\echo 'and how usable they would be as new filter axes.'
\echo '================================================================'
SELECT
  COALESCE(signal_type, '<null>')          AS signal_type,
  COALESCE(temporal_activation, '<null>')  AS temporal_activation,
  COUNT(*)                                 AS signals
FROM msr_signals
WHERE native_id = 'abhisek_mohanty'
GROUP BY signal_type, temporal_activation
ORDER BY signals DESC;
-- Read: if signal_type/temporal_activation are mostly NULL, ETL has
-- dropped them; we cannot filter on them yet. If populated, they're
-- ready to wire as new query facets.

\echo ''
\echo '================================================================'
\echo 'PROBE 3 — CGM edges valid set: which types, between which nodes?'
\echo 'Purpose: see what cgm_graph_walk can actually traverse today.'
\echo '================================================================'
SELECT
  edge_type,
  COUNT(*) AS valid_edges
FROM l25_cgm_edges
WHERE status = 'valid'
GROUP BY edge_type
ORDER BY valid_edges DESC;

\echo ''
SELECT
  source_node_id,
  COUNT(*) AS out_degree
FROM l25_cgm_edges
WHERE status = 'valid'
GROUP BY source_node_id
ORDER BY out_degree DESC
LIMIT 15;
-- Read: top nodes here are the only viable graph_seed_hints today.
-- Anything with out_degree=0 is a dead-end seed.

\echo ''
\echo '================================================================'
\echo 'PROBE 4 — CGM orphan edges: what targets are missing?'
\echo 'Purpose: confirm whether the 105 orphans target UCN section nodes'
\echo 'that were never ingested (the agent hypothesis).'
\echo '================================================================'
SELECT
  orphan_reason,
  COUNT(*) AS edges
FROM l25_cgm_edges
WHERE status = 'orphan'
GROUP BY orphan_reason
ORDER BY edges DESC;

\echo ''
SELECT
  CASE
    WHEN target_node_id LIKE 'UCN.%' THEN 'UCN.* (UCN sections)'
    WHEN target_node_id LIKE 'PLN.%' THEN 'PLN.*'
    WHEN target_node_id LIKE 'HSE.%' THEN 'HSE.*'
    WHEN target_node_id LIKE 'YOG.%' THEN 'YOG.*'
    WHEN target_node_id LIKE 'KRK.%' THEN 'KRK.*'
    WHEN target_node_id LIKE 'DVS.%' THEN 'DVS.*'
    WHEN target_node_id LIKE 'NAK.%' THEN 'NAK.*'
    WHEN target_node_id LIKE 'SEN.%' THEN 'SEN.*'
    WHEN target_node_id LIKE 'DSH.%' THEN 'DSH.*'
    ELSE 'other'
  END AS target_namespace,
  COUNT(*) AS orphan_edges
FROM l25_cgm_edges
WHERE status = 'orphan'
GROUP BY target_namespace
ORDER BY orphan_edges DESC;
-- Read: the agent hypothesis is "105 orphans target UCN.SEC.* nodes
-- not in l25_cgm_nodes". If UCN.* dominates, hypothesis confirmed:
-- ingesting UCN section nodes converts orphans to valid.

\echo ''
\echo '================================================================'
\echo 'PROBE 5 — rag_chunks doc_type and layer distribution'
\echo 'Purpose: confirm vector_search corpus is L1-only or whether'
\echo 'L2.5 / L3 chunks have already been ingested.'
\echo '================================================================'
SELECT
  COALESCE(layer, '<null>')      AS layer,
  COALESCE(doc_type, '<null>')   AS doc_type,
  COUNT(*)                       AS chunks,
  COUNT(DISTINCT source_file)    AS distinct_sources
FROM rag_chunks
WHERE is_stale = false
GROUP BY layer, doc_type
ORDER BY layer, chunks DESC;
-- Read: if you only see (L1, l1_fact, 102), then vector_search has
-- access to L1 only. Chunking UCN/CDLM/RM/CGM/MSR + L3 reports would
-- multiply vector_search reach.

\echo ''
\echo '================================================================'
\echo 'PROBE 6 — Recent audit_events: per-query tool firing breakdown'
\echo 'Purpose: see which tools fire / return empty / are skipped'
\echo 'for the last 5 real queries.'
\echo '================================================================'
SELECT
  ae.id,
  ae.created_at,
  LEFT(ae.query_text, 70)                          AS query_preview,
  ae.latency_ms,
  jsonb_array_length(ae.tool_bundles)              AS tools_fired
FROM audit_events ae
ORDER BY ae.created_at DESC
LIMIT 5;

\echo ''
\echo '--- per-tool result counts for the LAST query ---'
SELECT
  bundle->>'tool_name'                          AS tool,
  (bundle->>'latency_ms')::int                  AS ms,
  jsonb_array_length(bundle->'results')         AS result_count
FROM (
  SELECT tool_bundles
  FROM audit_events
  ORDER BY created_at DESC
  LIMIT 1
) latest, jsonb_array_elements(tool_bundles) AS bundle
ORDER BY tool;

\echo ''
\echo '--- per-tool average result count over last 20 queries ---'
SELECT
  bundle->>'tool_name'                                    AS tool,
  COUNT(*)                                                AS invocations,
  ROUND(AVG(jsonb_array_length(bundle->'results')), 1)    AS avg_results,
  COUNT(*) FILTER (WHERE jsonb_array_length(bundle->'results') = 0) AS zero_result_runs
FROM (
  SELECT tool_bundles
  FROM audit_events
  ORDER BY created_at DESC
  LIMIT 20
) recent, jsonb_array_elements(tool_bundles) AS bundle
GROUP BY tool
ORDER BY zero_result_runs DESC, avg_results ASC;
-- Read: tools with high zero_result_runs are failing in production.
-- Tools with avg_results=0 across all 20 queries are dead.

\echo ''
\echo '================================================================'
\echo 'PROBE 7 — query_plans content: what is the classifier emitting?'
\echo 'Purpose: see whether classifier populates planet_hints, '
\echo 'graph_seed_hints, etc. or leaves them empty.'
\echo '================================================================'
SELECT
  qp.created_at,
  qp.query_class,
  qp.forward_looking,
  qp.domains,
  qp.planets,
  qp.graph_seed_hints,
  qp.tools_authorized
FROM query_plans qp
ORDER BY qp.created_at DESC
LIMIT 10;
-- Read: if planets[] and graph_seed_hints[] are consistently NULL or
-- [], the classifier isn't filling them in — that's why the matching
-- tools (cgm_graph_walk, msr_sql with planets) come back thin.
-- If the table doesn't exist or column names differ, the classifier
-- may be writing only to query_trace_steps. Adapt accordingly.

\echo ''
\echo '================================================================'
\echo 'PROBE 8 — query_trace_steps: contribution per stage per recent query'
\echo 'Purpose: see live trace data quality after the conversation_id fix.'
\echo '================================================================'
SELECT
  query_id,
  step_seq,
  step_name,
  status,
  latency_ms,
  conversation_id IS NOT NULL AS has_conv,
  -- NB: payload JSONB shape varies per stage; the next line peeks at
  -- result count for retrieval steps if the field exists.
  COALESCE(jsonb_array_length(payload->'items'), 0) AS item_count
FROM query_trace_steps
WHERE created_at > NOW() - INTERVAL '24 hours'
ORDER BY query_id, step_seq;
-- Read: scan for steps where status='done' but item_count=0. Those
-- are silent zero-result tools. Cross-reference with PROBE 6.

\echo ''
\echo '================================================================'
\echo 'PROBE 9 — chart_facts category and L1 fact density'
\echo 'Purpose: see what L1 structured facts exist beyond MSR / FORENSIC'
\echo 'and whether any retrieval tool currently reaches them.'
\echo '================================================================'
SELECT
  category,
  COUNT(*) AS facts,
  ROUND(AVG(confidence)::numeric, 2) AS avg_conf
FROM chart_facts
WHERE is_stale = false
GROUP BY category
ORDER BY facts DESC;
-- Read: the 589 chart_facts contain placements, dignities, dasha
-- chara, sahams, yogas. None of the 10 retrieval tools currently
-- queries chart_facts — that data is reaching the LLM only via
-- the FORENSIC document chunks (vector_search) and indirectly via
-- MSR signals that derive from it. There's a gap.

\echo ''
\echo '================================================================'
\echo 'PROBE 10 — life_events distribution + sade_sati_phases coverage'
\echo 'Purpose: confirm temporal-prediction substrate density.'
\echo '================================================================'
SELECT
  category,
  COUNT(*) AS events,
  MIN(event_date) AS earliest,
  MAX(event_date) AS latest
FROM life_events
-- chart-scoped (SS N-110 / F11): life_events is people-entered, private, per-chart data;
-- this probe reads the native chart only. Substitute another chart id to probe that chart.
WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
GROUP BY category
ORDER BY events DESC;

\echo ''
SELECT
  phase,
  COUNT(*) AS phases,
  MIN(start_date) AS earliest,
  MAX(end_date)   AS latest
FROM sade_sati_phases
GROUP BY phase
ORDER BY phase;
-- Read: 36 life events + 46 sade-sati phases is the full predictive
-- timing substrate. None of the retrieval tools query these tables
-- directly today (predictive composition rule references the
-- LIFE_EVENT_LOG and SADE_SATI_CYCLES_ALL .md FILES via canonical_id,
-- but no tool inflates them into LLM context).

\echo ''
\echo '================================================================'
\echo 'SUMMARY TABLE — what is reachable today'
\echo '================================================================'
SELECT 'msr_signals_total'              AS metric, COUNT(*) AS value FROM msr_signals WHERE native_id='abhisek_mohanty'
UNION ALL
SELECT 'msr_starved_cells_lt_3',                COUNT(*) FROM (
  SELECT 1 FROM msr_signals
  WHERE native_id='abhisek_mohanty'
  GROUP BY domain, planet, is_forward_looking
  HAVING COUNT(*) < 3
) starved
UNION ALL
SELECT 'cgm_edges_valid',                       COUNT(*) FROM l25_cgm_edges WHERE status='valid'
UNION ALL
SELECT 'cgm_edges_orphan',                      COUNT(*) FROM l25_cgm_edges WHERE status='orphan'
UNION ALL
SELECT 'rag_chunks_total',                      COUNT(*) FROM rag_chunks WHERE is_stale=false
UNION ALL
SELECT 'audit_events_total',                    COUNT(*) FROM audit_events
UNION ALL
SELECT 'query_trace_steps_24h',                 COUNT(*) FROM query_trace_steps WHERE created_at > NOW() - INTERVAL '24 hours'
ORDER BY metric;

\echo ''
\echo '=== END OF DIAGNOSTIC PROBES ==='
