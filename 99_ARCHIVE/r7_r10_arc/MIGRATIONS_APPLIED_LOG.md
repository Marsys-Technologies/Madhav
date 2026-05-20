---
artifact: MIGRATIONS_APPLIED_LOG.md
version: "2.0"
status: CURRENT
produced_during: CLOSEOUT-2026-05-22
produced_on: 2026-05-22
executor: Claude Code (autonomous, native-authorized)
---

# Migration Apply Ledger — Production

## Schema basis

- **DB:** `madhav-astrology:asia-south1:amjis-postgres` / DB `amjis`
- **Connection:** Cloud SQL Auth Proxy on `127.0.0.1:5433`
- **User:** `amjis_app`
- **Verified on:** 2026-05-22 (CLOSEOUT-2026-05-22 session)
- **Total prod tables (2026-05-22):** 109

---

## Applied migrations — platform/migrations/ (canonical, sequential)

| File | Applied On | Applied By | Target Objects | Notes |
|------|-----------|-----------|----------------|-------|
| 001_initial_schema.sql | pre-2026-04 | historical | core schema | |
| 002_seed_astrologer.sql | pre-2026-04 | historical | seed data | |
| 003_chat_feedback_and_attachments.sql | pre-2026-04 | historical | message_feedback, chat_attachments | |
| 004_conversation_shares.sql | pre-2026-04 | historical | conversation_shares | |
| 005_pgvector_rag_schema.sql | pre-2026-04 | historical | rag_chunks, rag_embeddings, rag_queries, rag_graph_nodes/edges, rag_feedback | |
| 006_firebase_uid_schema.sql | pre-2026-04 | historical | profiles, access_requests | |
| 007_user_management.sql | pre-2026-04 | historical | user management | |
| 008_per_native_namespacing.sql | pre-2026-04 | historical | charts, namespacing | |
| 009_msr_signals.sql | pre-2026-04 | historical | msr_signals | |
| 010_vertex_ai_embedding_dim.sql | pre-2026-04 | historical | embedding dimension update | |
| 011_audit_log.sql | pre-2026-04 | historical | audit_log | |
| 012_prediction_ledger.sql | pre-2026-04 | historical | prediction_ledger | |
| 013_build_pipeline_staging.sql | pre-2026-04 | historical | build_manifests, staging tables | |
| 014_chart_facts.sql | pre-2026-04 | historical | chart_facts | |
| 015_ephemeris_daily.sql | pre-2026-04 | historical | ephemeris_daily | |
| 016_eclipses_retrogrades.sql | pre-2026-04 | historical | eclipses, retrogrades | |
| 017_life_events_and_sade_sati.sql | pre-2026-04 | historical | life_events, sade_sati_phases | |
| 018_l2_5_structured.sql | pre-2026-04 | historical | l25_msr_signals, l25_ucn_sections, l25_cdlm_links, l25_cgm_nodes/edges, l25_rm_resonances | |
| 019_l3_registers.sql | pre-2026-04 | historical | pattern_register, convergence_scores, contradiction_register, resonance_register | Note: these are platform/migrations tables; supabase has separate versions |
| 020_query_trace_steps.sql | pre-2026-04 | historical | query_trace_steps | |
| 021_cgm_edges_status.sql | pre-2026-04 | historical | cgm edge status | |
| 022_dasha_periods.sql | pre-2026-04 | historical | dasha_periods | |
| 023_signal_states.sql | pre-2026-04 | historical | signal_states | |
| 024_kp_sublords.sql | pre-2026-04 | historical | kp_sublords | |
| 025_varshaphala.sql | pre-2026-04 | historical | varshaphala | |
| 026_audit_events.sql | pre-2026-04 | historical | audit_events | |
| 027_query_plans.sql | pre-2026-04 | historical | query_plans | |
| 028_msr_signals_add_columns.sql | pre-2026-04 | historical | msr_signals column additions | |
| 029_chart_facts_indexes.sql | pre-2026-04 | historical | chart_facts indexes | |
| 030_cgm_edges_indexes.sql | pre-2026-04 | historical | cgm_edges indexes | |
| 031_shadbala.sql | pre-2026-04 | historical | shadbala | |
| 032_llm_call_log.sql | pre-2026-04 | historical | llm_call_log | |
| 033_query_plan_log.sql | pre-2026-04 | historical | query_plan_log | |
| 034_tool_execution_log.sql | pre-2026-04 | historical | tool_execution_log | |
| 035_context_assembly_log.sql | pre-2026-04 | historical | context_assembly_log, context_assembly_item_log | |
| 036_analytics_views.sql | pre-2026-04 | historical | v_cost_by_model_30d, v_grounding_health_7d, v_tool_health_7d | |
| 037_rag_chunks_canonical_id.sql | pre-2026-04 | historical | rag_chunks.canonical_id column | |
| 038_observatory_schema.sql | pre-2026-04 | historical | llm_usage_events, llm_budget_rules, llm_pricing_versions | |
| 039_prediction_calibration.sql | pre-2026-04 | historical | predictions calibration columns | |
| 040_query_trace_capture.sql | pre-2026-04 | historical | query trace capture | |
| 041_observatory_pipeline_stages.sql | pre-2026-04 | historical | observatory pipeline stages | |
| 042_tool_execution_log_scores.sql | pre-2026-04 | historical | tool score columns | |
| 043_performance_schema.sql | pre-2026-04 | historical | performance_queries | |
| 044_eval_runs_and_judge.sql | pre-2026-04 | historical | eval_runs, performance_judge_verdict | |
| 045_audit_events_disclosure_compliance.sql | pre-2026-04 | historical | audit_events disclosure columns | |
| 046_aiops_stack_config.sql | pre-2026-04 | historical | llm_stack_config | |
| 047_aiops_routing_override.sql | pre-2026-04 | historical | llm_stack_routing_override | |
| 048_aiops_param_override.sql | pre-2026-04 | historical | llm_param_override | |
| 049_aiops_model_health.sql | pre-2026-04 | historical | llm_model_health | |
| 050_aiops_config_audit.sql | pre-2026-04 | historical | llm_config_audit | |
| 051_aiops_catalog_snapshot.sql | pre-2026-04 | historical | llm_catalog_snapshot | |
| 052_aiops_seed.sql | pre-2026-04 | historical | aiops seed data | |
| 053_classical_texts.sql | pre-2026-04 | historical | classical_texts | |
| 054_classical_chunks.sql | pre-2026-04 | historical | classical_chunks | |
| 055_classical_attributions.sql | pre-2026-04 | historical | classical_attributions | |
| 056_classical_tier4.sql | pre-2026-04 | historical | classical tier-4 tables | |
| 057_aiops_routing_override_trigger.sql | pre-2026-04 | historical | aiops routing override trigger | |
| 058_aiops_routing_override_ttl.sql | pre-2026-04 | historical | aiops routing TTL | |
| 059_ephemeris_derived_columns.sql | pre-2026-04 | historical | ephemeris_daily derived columns | |
| 060_panchanga_daily.sql | 2026-05-19 | Phase-4C-S0 | panchanga_daily, panchanga_daily_staging | |
| 061_ephemeris_bhava_chalit.sql | pre-2026-05 | historical | ephemeris_daily bhava_chalit columns | |
| 069_extend_panchanga_daily.sql | 2026-05-20 | Phase-4C-S9 PR#110 | 5 JSONB columns + GIN indexes on panchanga_daily + panchanga_daily_staging | migration 069 (panchanga enrichment; in platform/migrations/, not supabase) |
| 110_add_projects_abstraction.sql | 2026-05-20 | R9_Operator_Closeout | projects, project_files, project_conversations | UUID type bug fixed before apply |
| 111_add_personas.sql | 2026-05-20 | R9_Operator_Closeout | personas | |
| 112_add_conversation_message_embeddings.sql | 2026-05-20 | R9_Operator_Closeout | conversation_message_embeddings (vector 768) | UUID type bug fixed; ivfflat index with lists=100 |
| 113_selective_share.sql | 2026-05-22 | CLOSEOUT-2026-05-22 | conversation_shares.hide_reasoning, conversation_shares.hide_methodology | R10 X-S8 |
| 114_truncated_by_user_edit.sql | 2026-05-22 | CLOSEOUT-2026-05-22 | audit_events.truncated_by_user_edit | R10 Y-S5 |

---

## Applied migrations — platform/supabase/migrations/ (frozen; historical Chat-V2/Observatory/M5-Coverage)

| File | Applied On | Applied By | Target Objects | Notes |
|------|-----------|-----------|----------------|-------|
| 057_school_signal_coverage.sql | 2026-05 | historical | school_signal_coverage | |
| 058_school_analysis_runs.sql | 2026-05 | historical | school_analysis_runs | |
| 059_convergence_scores.sql | 2026-05 | historical | convergence_scores (supabase ver.) | |
| 060_school_disagreements.sql | 2026-05 | historical | school_disagreements | |
| 061_conversations_v2.sql | 2026-05 | historical | conversations.archived_at + more | archived_at column verified present |
| 062_predictions.sql | 2026-05 | historical | predictions | |
| 063_pending_streams.sql | 2026-05 | historical | pending_streams | |
| 065_msr_signals_domains_affected.sql | 2026-05 | historical | l25_msr_signals.domains_affected | |
| 070_mcp_api_keys.sql | 2026-05-21 | MCP_WORKSTREAM | mcp_api_keys + 2 indexes | Applied during MCP workstream; 9 columns verified |
| 071_mcp_predictions_disagreements.sql | 2026-05-21 | MCP_WORKSTREAM | mcp_predictions, mcp_disagreements | Applied during MCP workstream |
| 070_capability_tool_registry.sql | 2026-05-22 | CLOSEOUT-2026-05-22 | capability_tool_registry, capability_asset_tool_bindings | COV-S2 workstream |
| 071_sade_sati_cycles.sql | 2026-05-22 | CLOSEOUT-2026-05-22 | sade_sati_cycles | M5-Coverage workstream |
| 064_query_trace_steps_user_id.sql | 2026-05-22 | R8-MIGRATIONS-APPLY (CLOSEOUT-2026-05-22 follow-up) | query_trace_steps.user_id | R8-adjacent; column verified present post-apply |
| 066_conversation_branches.sql | 2026-05-22 | R8-MIGRATIONS-APPLY (CLOSEOUT-2026-05-22 follow-up) | conversation_branches (table) | R8-S1 branches persistence; verified via to_regclass |
| 067_pg_trgm_conversation_messages.sql | 2026-05-22 | R8-MIGRATIONS-APPLY (CLOSEOUT-2026-05-22 follow-up) | pg_trgm extension + idx_conv_messages_body_trgm (GIN index) | R8-S3 sidebar FTS search; both objects verified |
| 068_pin_archive_folders.sql | 2026-05-22 | R8-MIGRATIONS-APPLY (CLOSEOUT-2026-05-22 follow-up) | conversation_folders, conversation_folder_members (tables), conversations.pinned (column) | R8-S4 pin/archive/folders; note: table names differ from brief assumptions; all 3 objects verified |
| 069_performance_wiring_fixes.sql | 2026-05-22 | R8-MIGRATIONS-APPLY (CLOSEOUT-2026-05-22 follow-up) | performance_queries: retrieval_scores (jsonb), compose_bundle_latency_ms (int), latency_complete (bool) | PERF-S1 wiring; all 3 columns verified |
| 116_trace_mcp_tool_column.sql | 2026-05-25 | DAR-P2-S5 | query_trace_steps.mcp_tool (TEXT), idx_query_trace_steps_mcp_tool | APPLIED 2026-05-25; 85 historical rows backfilled; column verified present; index created |
| 117_audience_tier_acharya_enum.sql | 2026-05-25 | DAR-P2-S5 | mcp_api_keys.audience_tier CHECK constraint now includes 'acharya' | APPLIED 2026-05-25; SQL bug fixed (pg_constraint.consrc → pg_get_constraintdef); constraint verified: ARRAY['client','super_admin','acharya'] |
| 072_mcp_bundle_cache.sql | 2026-05-22 | inferred_from_workstream_close | mcp_bundle_cache (content-addressable 5-min bundle cache; key=sha256(query+params+tier+chart_id)) | MCPT v3.1.0-S2 |
| 073_perf_log_extensions.sql | 2026-05-22 | inferred_from_workstream_close | tool_execution_log: 5 perf-system columns for nightly audit | MCPT v3.1.0-S4 |
| 074_audit_findings.sql | 2026-05-22 | inferred_from_workstream_close | mcp_audit_findings, audit_job_runs | MCPT v3.1.0-S4 |
| 075_prediction_outcomes.sql | 2026-05-22 | inferred_from_workstream_close | mcp_prediction_outcomes, mcp_predictions calibration columns | MCPT v3.1.0-S4 |
| 075b_prediction_outcomes_remediation.sql | 2026-05-22 | inferred_from_workstream_close | mcp_predictions/mcp_prediction_outcomes schema remediation | MCPT v3.1.0-S4 |
| 076_data_source_expected_and_caveats.sql | 2026-05-22 | inferred_from_workstream_close | data_source_expected (expected row counts per tool/category), tool_caveats | MCPT v3.1.0-S4 |
| 077_mcp_alerts_config_and_tool_registry.sql | 2026-05-22 | inferred_from_workstream_close | mcp_alerts_config (per-metric thresholds + dispatch targets), tool_registry (DB-level tool enable/disable) | MCPT v3.1.0-S5 |
| 078_multi_school_extensions.sql | 2026-05-22 | inferred_from_workstream_close | school_signal_coverage: notes column + substantive-coverage index | MCPT v3.2-S4 |
| 079_tajaka_and_convergence.sql | 2026-05-22 | inferred_from_workstream_close | school_convergence_index (materialized view), tajaka_annual (muntha_sign deterministic; year_lord/annual_lagna/saham=EXTERNAL_COMPUTATION_REQUIRED) | MCPT v3.2-S5 |
| 080_classical_texts_work_column.sql | 2026-05-22 | inferred_from_workstream_close | classical_texts.work (generated column = upper(text_key)), idx for per-work queries | MCPT v3.2 (enables read_classical_text MCP tool) |
| 081_build_manifests_asset_id.sql | 2026-05-22 | inferred_from_workstream_close | build_manifests.asset_id (text column) | MCPT v3.5 housekeeping; closes AC.*.4 schema-mismatch residual |
| 082_perf_system_materialized_views.sql | 2026-05-22 | inferred_from_workstream_close | 4 perf-system materialized views + MCP-aware columns on tool_execution_log | MCPT v3.7 Operational Gap Closure Phase B |

| 315_ga_prashna_count_sql_fix.sql | 2026-06-18 | FOUNDATION-SESSION-1 | ga_prashna count_sql: remove stray leading `(` → valid SQL | SHA256: cf logged in Foundation Session 1 close |
| 316_bg_nakshatra_medical_dosha.sql | 2026-06-18 | FOUNDATION-SESSION-1 | bg_nakshatra_medical ADD COLUMN dosha TEXT | IF NOT EXISTS guard; dosha column populated by bg_medical_mappings rebuild |
| 317_ga_pyjhora_engine_reset_stale_error.sql | 2026-06-18 | FOUNDATION-SESSION-1 | Reset ga_pyjhora_engine asset_throughput state to 'dormant' | Bug fixed in migration: state=NULL → state='dormant' to satisfy NOT NULL |
| 318_ga_structural_target_floor_update.sql | 2026-06-18 | GA-STRUCTURAL-REMEDIATION | asset_registry target_floor for ga_structural: 74034 → 77821 | SHA256: 9caadb418b0c6957a443c8bbdd003e2495082f69cf04dc3088ed64a802f83341 |
| 319_ga_structural_count_sql_phase2.sql | 2026-06-18 | PRE-L2-TAKE-STOCK | ga_structural count_sql: full 65-category explicit IN list covering Phase-2 depth | SHA256: b320af08824d6bdbed8b2e5349e8119c6ce4e47ad7b3a9595d815090bf818998; returns exactly 77,821 for chart 482012f1 |
| 320_ga_prashna_fix_description.sql | NOT_APPLIED | — | ga_prashna asset_registry description: chart_facts reference | Reads graha positions from chart_facts (written by ga_positions) instead of ga_positions directly |
| 321_build_runs_last_error.sql | 2026-06-18 | BUILD-EXECUTOR-FIX | build_runs: ADD COLUMN last_error TEXT | Stores dispatch failure message (D1 fix) and watchdog planned-orphan reaper message (D2 fix); mirrors asset_throughput.last_error |
| 322_fix_asset_registry_names_and_status.sql | 2026-06-19 | GA-YOGA-REDDOT-CLEANUP | asset_registry: strip bracketed (id) suffix from ga_yoga + ga_transit_anchors english_name; promote ga_yoga + ga_prashna catalog_status DRAFT→CURRENT | Supersedes drift from migrations 240 (ga_yoga bracketed name) + 268 (ga_transit_anchors bracketed name) + 294 (deferred Gate-3). Seed already clean; 4 rows updated. |
| 323_ga_structural_graph_theoretic_floor_update.sql | 2026-06-19 | GA-STRUCTURAL-V2-SEAL | ga_structural count_sql + target_floor: 69-category IN list, floor=106,014 | Graph-theoretic rebuild sealed; old orphan build 22fcef22 purged. |
| 324_ga_structural_phase3_nakshatra_relationship_floor.sql | 2026-06-19 | GA-STRUCTURAL-PHASE3-GATE | ga_structural count_sql + target_floor: add nakshatra_co_tenancy + nakshatra_lord_relationship + tara_bala (72 categories), floor=106,103 | Phase-3 gate fix: nakshatra_relationship double bug (graha_position source + jsonb constituent refs) and bhava_chalit inline equal-bhava computation. Build a712b250. |

---

## Convention (effective 2026-05-22)

After every migration apply, append a row to this file in the same commit that applies. See `00_ARCHITECTURE/MIGRATION_DIRECTORY_POLICY_v1_0.md` for directory rules.

- **Canonical directory:** `platform/migrations/` (next migration: 117)
- **Frozen directory:** `platform/supabase/migrations/` (no new files)
- **Idempotency:** All migrations use `IF NOT EXISTS` guards
- **Verify command:** `psql "$DATABASE_URL" -c "SELECT to_regclass('public.<table>');"`
