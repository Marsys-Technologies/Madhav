---
artifact: TOOLING_AUDIT_TRACKER_v1_0.md
version: 1.0
status: v1.0 COMPLETE (2026-05-25)
phase_0_status: COMPLETE
authored_by: TR-P0-S1 (2026-05-24)
sealed_by: TR-P8-S2 (2026-05-25)
---

# MARSYS-JIS Tooling Audit Tracker

Source: MARSYS_JIS_TOOLING_REMEDIATION_PLAN_v1_0.md (87 findings).
Baseline captured: TR-P0-S1, 2026-05-24.
Full baseline data: `eval-results/tooling_audit_baseline_20260524.json`

## §1 — Tool-behaviour findings (C1–C11)

| Code | Finding | Phase | Status | Baseline |
|---|---|---|---|---|
| C1 | chart_summary 0 rows always | 1.1 | OPEN | wrapper — chart_summary misreads ToolBundle envelope; calls query_chart_facts primitive correctly but reads envelope.result.rows_by_category directly instead of unwrapping results[0].content JSON string |
| C2 | holistic_bundle UCN/RM/CDLM error | 5.1 | OPEN | wrapper — holistic_bundle requires mandatory query_text param (z.string().min(3)); calls without it fail schema validation |
| C3 | cross_school_lookup always silent | 2.1 | OPEN | wrapper — claim param not forwarded; platform primitive receives topic='surgical_primitive:cross_school_lookup' from queryPlan.query_text; all 7 schools return coverage_type:silent |
| C4 | query_signals filters ignored | 1.3 | OPEN | wrapper — forward_looking and min_confidence (confidence_floor) params not translated from MCP input to toolParams; invocation_params confirms forward_looking:false/confidence_floor:0.6 regardless of caller values |
| C5 | query_ephemeris date_range schema mismatch | 1.4 | OPEN | wrapper — schema uses start/end not from/to; single planet not array; correct params work (returns data); date_range filter may still need verification |
| C6 | query_transit_event event_type missing | 1.2 | OPEN | confirmed wrapper — event_type not in MCP input schema; tool returns note:'Unknown event_type undefined' for all calls; caller cannot specify ingress/station/aspect/conjunction |
| C7 | query_dasha_periods no PD/SD | 7.1 | OPEN | confirmed data_empty — 28 rows returned (MD+AD level only); pd_lord null in all rows; no PD/SD rows ingested in dasha_vimshottari category; DB has 50 dasha_vimshottari rows all MD/AD |
| C8 | query_panchanga missing enrichment cols | 1.6 | OPEN | wrapper — enrichment data IS in DB (special_yogas, choghadiya, hora, inauspicious, auspicious all populated in 27393 rows since 2026); wrapper SELECT does not include JSONB enrichment columns |
| C9 | read_asset ENOENT | 1.5 | OPEN | prod_env — MARSYS_REPO_ROOT not set in Cloud Run prod; files resolve from '/' path which doesn't exist; both MACRO_PLAN and LEL fail identically; code correct, env config gap |
| C10 | read_classical_text no results | 2.5 | OPEN | wrapper — text_id='BPHS' maps to schools=['bphs'] filter on ct.school, but ct.school='parashari' for BPHS; should filter ct.text_key='bphs'; 8349 classical_chunks with 8337 embeddings exist in DB |
| C11 | query_chart_facts empty categories | 3.1 | DATA RESOLVED (TR-P3-S1 2026-05-25) | data_empty root cause fixed — deity_assignment=16, ishta_kashta=7, chandra_placement=12, avastha=7 rows now in DB. query_chart_facts wrapper itself unchanged (no wrapper bug confirmed for these categories). |

## §2 — Data-layer findings (D1–D7)

| Code | Finding | Phase | Status | Baseline |
|---|---|---|---|---|
| D1 | deity_assignment/ishta_kashta/chandra_placement/avastha empty | 3.1 | RESOLVED (TR-P3-S1 2026-05-25) | Backfill complete. Extractor: platform/python-sidecar/pipeline/loaders/chart_facts_loader.py against FORENSIC_v8_0.md. Extracted: deity_assignment=16, ishta_kashta=7, chandra_placement=12, avastha=7. Upserted 215 rows (19 categories) — 0 errors. DB after: deity_assignment=16, ishta_kashta=7, chandra_placement=12, avastha=7. Also resolved: sensitive_point=25, arudha_occupancy=12, mrityu_bhaga=11, kakshya_zone=8, chalit_shift=9, longevity_indicator=10. Total chart_facts: 2475→2681. See eval-results/chart_facts_extractor_run.json. |
| D2 | shadbala no roll-up | 6.4 | OPEN | DB has shadbala:63 rows. Tool returns them but no roll-up/total_rupas aggregation. schema confirmed missing roll-up. |
| D3 | read_asset ENOENT in prod | 1.5 | OPEN | Same as C9 — prod_env root cause: MARSYS_REPO_ROOT missing from Cloud Run env vars |
| D4 | school_convergence_index all silent | 2.1 | OPEN | **TR-P2-S1 CONFIRMED** 574 rows (signal-level MV, one row per MSR signal). Columns: signal_id, parashari_present, jaimini_present, kp_present, tajika_present, convergence_score, missing_schools. Coverage: parashari=499/574, jaimini=546/574, kp=459/574, tajika=484/574. Data is good; **branch_decision=fix_wrapper** — C3 bug is wrapper not forwarding claim param (detail: eval-results/school_convergence_baseline.json). |
| D5 | chart_facts 2717 row claim disputed | 3.4 | OPEN | Actual DB count: 2475 rows (not 2717). 27 categories present. varshphal=1566 dominates. |
| D6 | rag_chunks 4589 claim unverified | 2.4 | OPEN | Actual rag_chunks count: 6931 (not 4589). ADDITIONALLY: classical_chunks table exists separately with 8349 rows + 8337 embeddings — this is what read_classical_text uses. Plan conflated two separate tables. |
| D7 | only 4 classical texts indexed | 2.4 | OPEN | Actual: 14 classical texts in classical_texts table (bphs, jaimini_sutra, kp_texts, tajaka_neelakanthi, plus brihat_jataka, brihat_samhita, chandra_kala_nadi, dhruva_nadi_sampler, hora_sara, phaladeepika, prashna_marga, saravali, uttara_kalamrita, bhrigu_nandi_nadi). Plan said 4 — actual is 14. |

## §3 — Missing tools (Class A — wrap existing engine)

| Tool | Phase | Status |
|---|---|---|
| query_varshphal | 4.1 | DONE (TR-P4-S1) |
| query_divisional_chart | 4.2 | DONE (TR-P4-S1) |
| query_remedial_mantras | 4.3 | DONE (TR-P4-S1) |
| muhurta_finder | 4.4 | DONE (TR-P4-S2) |
| tara_balam_for_native | 4.5 | DONE (TR-P4-S2) |
| chandra_balam_for_native | 4.6 | DONE (TR-P4-S2) |

## §4 — Missing tools (Class B — build engine)

| Tool | Phase | Status |
|---|---|---|
| query_transits_over_natal | 6.1 | DONE (TR-P6-S1) |
| query_yogas_active_now | 6.2 | DONE (TR-P6-S2) |
| get_planet_avastha | 6.3 | DONE (TR-P6-S3) |
| get_shadbala_full | 6.4 | DONE (TR-P6-S3) |
| query_planetary_period_predictions | 7.3 | DONE (TR-P7-S3) |
| query_dasamsha_career | 7.4 | DONE (TR-P7-S3) |
| query_shashtiamsha | 7.5 | DONE (TR-P7-S4) |
| query_drekkana_drishti | 7.6 | DONE (TR-P7-S4) |
| query_remedies_prescribed | 8.3 | DONE (TR-P8-S2) |

## §5 — Missing tools (Class C — implement stub)

| Tool | Phase | Status |
|---|---|---|
| query_jaimini_chara_dasha | 7.2 | DONE (TR-P7-S2) |
| query_eclipse_transits | 8.1 | DONE (TR-P8-S1) |
| query_planet_war | 8.2 | DONE (TR-P8-S1) |

## §6 — Missing tools (Class D — deferred / greenfield)

| Tool | Phase | Status |
|---|---|---|
| compute_synastry | 12.1 | DEFERRED (needs spouse data) |
| compute_business_chart | 12.2 | DEFERRED (needs founding data) |
| query_kp_horary | 12.3 | DEFERRED v1.1 |
| vastu_audit | 12.4 | DEFERRED v1.1 |
| numerology_sync | 12.5 | DEFERRED v1.1 |
| compute_progressions | 12.6 | DEFERRED v1.1 |

## §7 — Methodology (Part IV)

| Rule | Phase | Status |
|---|---|---|
| Session-start diagnostic (data_coverage + tool_health) | 10.1 | DONE (TR-P9-S1) |
| No date estimation — use query_ephemeris | 10.2 | DONE (TR-P9-S1) |
| log_prediction mandatory | 10.3 | DONE (TR-P9-S1) |
| flag_disagreement on broken tools | 10.4 | DONE (TR-P9-S1) |
| Cross-school required before high-confidence | 10.5 | DONE (TR-P9-S1) |
| Pre-compute chart summary at session start | 10.6 | DONE (TR-P9-S1) |
| vector_search + get_cgm_subgraph proactive | 10.7 | DONE (TR-P9-S1) |
| Triangulate MSR→chart_facts→ephemeris | 10.8 | DONE (TR-P9-S1) |
| Mark permanent / dasha-tied / transit-tied | 10.9 | DONE (TR-P9-S1) |
| Re-read tool schemas before first use | 10.10 | DONE (TR-P9-S1) |

## §8 — Server-level (Part V)

| Item | Phase | Status |
|---|---|---|
| Schema param honour-check | 9.1 | DONE (TR-P9-S1) |
| Streaming / pagination for large responses | 9.2 | DEFERRED v1.1 (out-of-scope v1.0) |
| Better error messages | 9.3 | DONE (TR-P9-S1) |
| list_available_assets endpoint | 9.4 | DONE (TR-P5-S1 list_assets tool) |
| populated_count on every category | 9.5 | DONE (TR-P9-S1) |
| Composition recipes (3 for v1.0) | 9.6 | DONE (TR-P9-S2 — interpret_current_dasha + list_canonical_artifact_versions + holistic_bundle recipes) |
| Versioned corpus snapshots endpoint | 9.7 | DONE (TR-P9-S2 list_canonical_artifact_versions) |
| Tier surfacing in descriptions | 9.8 | DONE (TR-P9-S1 tier_catalog + ignored_params) |
| Multi-language Sanskrit output | 9.9 | DONE (TR-P9-S2 Sanskrit encoding support) |
| Real-time ephemeris computation | DEFERRED | out-of-scope v1.0 |

## §9 — Phase 0 Key Surprises (for conductor calibration)

1. **chart_facts rows = 2475, not 2717** (242 row gap from plan claim).
2. **rag_chunks = 6931, not 4589** — plan undercounted; also classical_chunks (8349 rows, separate table) was conflated.
3. **14 classical texts indexed, not 4** — plan severely undercounted.
4. **school_convergence_index schema differs**: it is a signal-level MV (574 rows = 1 per MSR signal) not a school×coverage_type breakdown; cross_school_lookup C3 bug is wrapper not data.
5. **C8 panchanga enrichment is a wrapper bug not a data gap**: all 5 JSONB enrichment columns are fully populated in DB; wrapper SELECT omits them.
6. **C9 read_asset is a prod_env bug**: MARSYS_REPO_ROOT not set in Cloud Run; every asset read fails in prod.
7. **data_coverage and tool_health MVs show all nulls** — operational telemetry is not flowing.
8. **C10 read_classical_text bug**: text_id→school mapping wrong in wrapper (bphs→'parashari' not 'bphs'); data exists, code fix needed.
9. **C1 chart_summary bug**: ToolBundle envelope structure mismatch — wrapper reads wrong nesting level.
