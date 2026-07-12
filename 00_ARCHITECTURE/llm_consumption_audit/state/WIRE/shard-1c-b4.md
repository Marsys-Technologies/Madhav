# Lane 1c SERVICES-census — shard-1c-b4

Charter: LLM_CONSUMPTION_AUDIT_CHARTER v1.1. Chart: 482012f1-710e-4a25-994a-93821f5871aa.
Date probed: 2026-07-12. Wire: :3000 MCP surgical primitives + :8000 compute + DB read-only.
Status: COMPLETE — 6/6 services graded.

Surgical whitelist (captured this pass): query_chart_facts, query_signals,
query_dasha_periods, query_panchanga, query_ephemeris, query_transit_event, lel_query,
vector_search, get_cgm_subgraph, cross_school_lookup, read_classical_text, query_varshphal,
query_divisional_chart, query_remedial_mantras, muhurta_finder, query_varshaphala,
divisional_query, remedial_codex_query, query_muhurat, **query_tara_balam**,
**query_chandra_balam**, jaimini_chara_dasha, ... (NO graha_yuddha / active_yogas /
recall_session entry).

---

## 1. Tara Bala (query_tara_balam) — DEAD-19 (LCA-1)
- In surgical whitelist, but MCP invocation returns:
  `{"ok":false,"error":{"class":"internal","message":"Retrieval tool not found in registry: query_tara_balam","remediation":"...TOOL_NAME_TO_URI missing entry"}}`
- Compute EXISTS: `panchang_engine/tara_bala.py::compute_tara_bala_score` + serialize
  `_tara_bala_to_dict` (tara_count/tara_name/tara_quality/chandra_bala/chandra_bala_quality).
- Fallback surface also empty: `query_panchanga` WITH chart_id returns `native_context:null`
  (native overlay not populated even when the chart is supplied).
- GRADE FAIL/DEAD. compute_reachable=false. Primary class 1 UNREACHABLE (advertised, unwired);
  secondary class 5 (whitelist dishonestly advertises a tool that errors). HIGH.

## 2. Chandra Bala (query_chandra_balam) — DEAD-19 (LCA-1)
- Identical signature: `Retrieval tool not found in registry: query_chandra_balam ...
  TOOL_NAME_TO_URI missing entry`.
- chandra_bala is a sub-field of the same tara_bala serializer; no independent surface;
  panchanga native_context=null.
- GRADE FAIL/DEAD. compute_reachable=false. class 1 + secondary 5. HIGH.

## 3. Graha Yuddha (planetary war, current) — UNREACHABLE-BY-NONEXISTENCE
- No graha_yuddha/query_graha_yuddha/planet_war tool in whitelist
  (`Tool not in surgical whitelist: graha_yuddha`).
- DB: natal `graha_yuddha_per_varga` = 16 rows in chart_facts (reachable ONLY as static natal
  facts via query_chart_facts) — natal leg exists.
- The compute-on-demand "current wars for today = chart_facts planet_war ⊕ live ephemeris
  longitudes" is composed by NO single service.
- Live-ephemeris leg itself broken: `query_ephemeris` returns MCP envelope `ok:true` wrapping
  inner `{"ok":false,"error":"sidecar 401: Invalid API key"}`.
- GRADE FAIL. compute_reachable=false. Primary class 1 UNREACHABLE (no composed service);
  secondary class 5 DISHONEST (ephemeris ok:true over a 401). MEDIUM-HIGH.

## 4. Active yogas (dasha+transit triggered) — UNREACHABLE-BY-NONEXISTENCE / UN-SYNTHESIZABLE
- No active_yogas/query_yogas tool in whitelist.
- DB: 88 natal yoga rows reachable as static facts via query_chart_facts/query_signals; dasha
  via query_dasha_periods.
- NO service composes "natal yogas × running dasha lord × current transit → active-now". A
  consuming LLM must hand-compose across 3 tools = class 9 ungoverned judgment.
- GRADE FAIL. compute_reachable=false. Primary class 8 UN-SYNTHESIZABLE (secondary 1 + 9). MEDIUM.

## 5. v7_additions (capability stub) — EMPTY SHELL (honest)
- Reachable: `POST :8000/v7_additions` → HTTP 200,
  `{"status":"not_implemented","message":"v7_additions: endpoint not yet implemented"}`.
- Not in surgical whitelist; :8000-direct only. Honestly labeled intended stub pending M6.
- GRADE EMPTY_SHELL. compute_reachable=true (endpoint alive) but returns nothing usable.
  Primary class 4 EMPTY SHELL. LOW (honest, by-design stub).

## 6. recall_session / session-memory round-trip — UNREACHABLE (MCP-contract gap)
- Not in surgical whitelist: `Tool not in surgical whitelist: recall_session`. No tool_name in
  retrieval_capability_spec.ts (confirmed by service spec grep).
- Data plane EXISTS: `GET :3000/api/mcp/sessions` returns
  `{"sessions":[{"session_id":"fdfe6357-...","session_key":"default","active_chart_id":"1c826d5a-...","last_seen_at":"2026-07-11 10:24:28+00"}]}`.
  Route doc: "session history ... for recall_session / list_my_sessions MCP tools" — but the
  MCP tool is never wired; route is service-to-service only (X-MCP-Internal-Token; dev-mode
  bypass let it pass locally).
- GRADE FAIL. compute_reachable=false (via consuming-LLM surface). Primary class 1 UNREACHABLE
  (retrieval-plane / MCP-contract). MEDIUM.

---
Cross-lane note: DEAD-19 pattern (whitelisted tool, no TOOL_NAME_TO_URI) confirmed on
query_tara_balam + query_chandra_balam — matches LCA-1 anchor. query_ephemeris dishonest
envelope (ok:true over sidecar 401) is a live-compute breakage that also starves any
transit-dependent service (graha yuddha, active yogas).
