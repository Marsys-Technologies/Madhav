# LANE 10 — Promise-vs-Delivery — shard-3 (bo_* L2 Bodha assets)

Grader: Lane 10 sub-agent. Charter §7.5 decision tree. Deployed channel (read-only) = amjis-mcp Cloud Run. DB truth via mcp__postgres__query. Charts: native `482012f1-710e-4a25-994a-93821f5871aa` (N), Abhinandan `1c826d5a-41cb-4450-b4dc-59d440e5f75a` (A).

## Data-plane census (verbatim DB counts, both charts)
| asset | table | N rows | A rows | floor | status |
|---|---|---|---|---|---|
| bo_chart_gestalt | bodha_chart_gestalt | 5 | 5 | 1 | present (catalog_status=DRAFT) |
| bo_drishti | bodha_question_lenses | 60 | 60 | 60 | present |
| bo_karanajala | bodha_cgm_edges | 534 | 523 | 300 | present |
| bo_laksana | bodha_msr_signals | 66836 | 66747 | 60000 | present |
| bo_pramana_mapa | synthesis_quality_scorecard | 1 | 1 | 1 | present |
| bo_pratijna | bodha_pratijna | 110 | 110 | 0 | present |
| bo_samskara | bodha_signal_embeddings | 66836 | 66747 | 60000 | present (1:1 w/ signals) |

Every asset's data plane is PRESENT on BOTH charts. All shortfalls below are therefore retrieval/ranking, never data-plane.

## Per-asset grade

### AP-022 bo_chart_gestalt — SHORTFALL (retrieval-plane) — promise re-sourced
- Promise NOT FOUND in brief (no CLAUDECODE_BRIEF for gestalt). Re-sourced from asset_registry.english_description: "Per-chart gestalt: defining threads, central dynamics, domain verdict map, zoom spine — pointer-only, no verdicts stored." → promise_status=re-sourced.
- Data plane: 5 rows/chart both charts. ✓
- Retrieval plane: NO MCP tool serves bodha_chart_gestalt. Source grep `bodha_chart_gestalt` across platform/src → zero serving references (only cockpit registry.body + asset seed). get_chart_orientation serves the UCD (bo_samvada), NOT the gestalt table. The gestalt "zoom spine / defining threads / domain verdict map" navigational surface has no reachable path via the deployed channel. → class 1 UNREACHABLE.
- Verdict: SHORTFALL, shortfall_layer=retrieval-plane. (catalog_status=DRAFT corroborates unfinished serving.)

### AP-023 bo_drishti — DELIVERS
- Promise (brief): question-type → chart-specific structural elements + evidence ledger, "answer-FOCUSED bundle in one call."
- Data plane: 60 lenses/chart. ✓
- Retrieval plane: get_domain_reading(domain=relationship) surfaces `question_lenses:[{lens_id, question_type:"marriage", template_element_ids_jsonb:[...], lens_template_version:"classical_v1.0"}, ...], lens_count:2`. One-call answer-focused bundle delivered. Consuming code: query_domain_reading.ts + register_d8_assess_domain.ts SELECT bodha_question_lenses.
- Verdict: DELIVERS (modest promise met, one-call retrieval confirmed).

### AP-024 bo_karanajala — DELIVERS (minor topology-null note)
- Promise (brief): heavy writer owns edges/sub_graphs/motifs/topology/paths/contradictions.
- Data plane: 534/523 edges. ✓
- Retrieval plane: get_cgm_subgraph (modes neighbors/paths/contradictions) returns full edge objects — edge_type, computed_strength (-1.15), valence (antagonistic), relationship_basis, affected_domains, is_cross_subsystem, subsystem_from/to, underlying_msr_signal_ids_array, present_in_traditions_array. provenance.tables=[bodha_cgm_nodes,bodha_cgm_edges,bodha_cgm_chart_topology_summary]. Heavy compute reachable + usable.
- Minor: `topology_summary:null` and `cross_ayanamsha_edge_stability_score:null` in neighbors payload — the promised "topology" facet returns null in this mode (class 4 EMPTY SHELL, low sev).
- Verdict: DELIVERS.

### AP-025 bo_laksana — DELIVERS (UNATTRIBUTED-share note)
- Promise (brief): projects EVERY meaningful L1 fact into one bodha_msr_signals row each, native × 5 ayanamshas.
- Data plane: 66836 signals/chart. ✓ (per-ayanamsha slice = 13364, digest confirms.)
- Retrieval plane: get_signals reachable; orientation digest reports msr_signal_count 13364, yoga 15, dosha 22.
- Note (ranking/form, R-44 territory — Lane 6 anchor): entity_profiles top entity is `UNATTRIBUTED` with signal_count 299 (career/character/wealth). DEFECT-001 residual: get_chart_quality reports 845/67590 constituent-fact refs orphaned (1.3%). Projection promise itself DELIVERS; attribution-share is a downstream ranking concern.
- Verdict: DELIVERS.

### AP-026 bo_pramana_mapa — DELIVERS
- Promise (brief): scorecard audits judgment substrate, proves pillars meet, lays calibration frame, voices limits.
- Data plane: 1 scorecard/chart. ✓
- Retrieval plane: get_chart_quality / bodha_quality_get returns scorecard: `scorecard_id d15059ca-..., citation_ref_coverage_pct:100, trap1_authority_inversion_count:0, trap2_narration_leak_count:0, unresolved_constituent_facts_count:0, scored_at:2026-07-11`. Tool ALSO honestly voices its own limit via `defect_001_alert` (severity HIGH: stored unresolved count "may not reflect" live 1.3% orphan derivation) — that is the promise's "honestly VOICE the limits" facet, working.
- Verdict: DELIVERS.

### AP-027 bo_pratijna — PARTIAL (retrieval-plane) — promise re-sourced
- Promise NOT FOUND in brief (no dedicated brief). Re-sourced from asset_registry.english_description: "Per-event-class promise registry: promised/denied/conditional verdicts with grade, supporting and contradicting signal IDs, varga confirmation, derivation audit trail. Written by bo_pratijna after bo_laksana. Downstream: P5B ph_nimitta uses grade as promise_lift." → promise_status=re-sourced.
- Data plane: 110 promise rows/chart both charts. ✓
- Retrieval plane: NO MCP tool serves bodha_pratijna to a consuming LLM. Source grep → only platform/python-sidecar/services/ph_nimitta/engine.py reads it (internal L4 consumer). pact_query (register_d10_pact) computes the promise→confirmation→activation grammar live and does NOT read bodha_pratijna. The rich stored verdicts (grade, supporting/contradicting signal IDs, varga confirmation, derivation trail) are invisible over the wire. Declared internal consumer (ph_nimitta) IS satisfied, so promise not fully broken — but the LLM-consumption plane is dark. → class 1 UNREACHABLE for the verdict content.
- Verdict: PARTIAL, shortfall_layer=retrieval-plane.

### AP-028 bo_samskara — PARTIAL (retrieval-plane/EMPTY-SHELL) — promise declared
- Promise (brief): REAL Vertex AI embeddings of bo_laksana signal_summary_text, in the SAME vector space as L0's classical corpus, so a signal can be similarity-matched to its classical sources (the L0↔L2 bridge).
- Data plane: 66836 embeddings/chart, exact 1:1 with signals, 100% populated (query_signals.ts confirms "66,738 rows, 100% embedded"; pgvector 768-dim Vertex). Writer-level promise (real embeddings, shared space) DELIVERS at data plane. ✓
- Retrieval plane (the USE — L0↔L2 bridge): get_signals `semantic_query` path is the only tool over bodha_signal_embeddings, but query_signals.ts lines 273/453 hardcode a fallback: "Semantic embedding not available at query time — salience-ranked fallback used. Full vector search requires Vertex embedding of the query string." Deployed test of get_signals(semantic_query=...) returned the salience digest with no semantic marker. vector_search hits the L0 classical document corpus (nadi_navamsa_patel citations), NOT signal→classical matching. So the advertised semantic bridge silently degrades to salience — the promised signal↔classical similarity is not live-consumable. → class 4 EMPTY SHELL (advertised semantic stage returns non-semantic fallback).
- Verdict: PARTIAL, shortfall_layer=retrieval-plane. (Writer delivered; serving-query layer degrades the promised use.)

## Summary
- DELIVERS: bo_drishti, bo_karanajala, bo_laksana, bo_pramana_mapa (4)
- PARTIAL: bo_pratijna, bo_samskara (2)
- SHORTFALL: bo_chart_gestalt (1)
- All shortfalls are retrieval-plane; every data plane present on both charts.
- Two promises re-sourced from asset_registry (gestalt, pratijna) — neither had a build brief.
