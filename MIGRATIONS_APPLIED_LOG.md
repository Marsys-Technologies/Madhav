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
| 116_trace_mcp_tool_column.sql | 2026-05-23 | MCPT-v32-P5A | query_trace_steps.mcp_tool (TEXT), idx_query_trace_steps_mcp_tool | pending apply; backfills from data_summary->>'mcp_tool' |

---

## Convention (effective 2026-05-22)

After every migration apply, append a row to this file in the same commit that applies. See `00_ARCHITECTURE/MIGRATION_DIRECTORY_POLICY_v1_0.md` for directory rules.

- **Canonical directory:** `platform/migrations/` (next migration: 117)
- **Frozen directory:** `platform/supabase/migrations/` (no new files)
- **Idempotency:** All migrations use `IF NOT EXISTS` guards
- **Verify command:** `psql "$DATABASE_URL" -c "SELECT to_regclass('public.<table>');"`
