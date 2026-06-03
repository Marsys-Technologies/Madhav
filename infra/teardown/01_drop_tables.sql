-- =============================================================================
-- 01_drop_tables.sql — DROP all legacy data/build/compute tables
-- OPERATOR-RUN ONLY — run AFTER 00_archive.sh completes successfully
-- OPERATOR-RUN ONLY — do NOT execute via automation
--
-- Pre-requisites:
--   1. 00_archive.sh has completed (GCS snapshots + DB dumps in cold storage)
--   2. Running against PRODUCTION database with superuser role
--   3. application pods scaled to 0 (prevent mid-drop in-flight queries)
--
-- To run:
--   psql $DATABASE_URL -f infra/teardown/01_drop_tables.sql
--   OR via Cloud SQL Auth Proxy:
--   PGHOST=localhost PGPORT=5432 PGUSER=postgres PGPASSWORD=<pw> \
--   psql -d amjis -f infra/teardown/01_drop_tables.sql
--
-- Note: CASCADE propagates to dependent views/indexes automatically.
-- Missing tables (already dropped or never created) produce NOTICE, not error.
-- =============================================================================

BEGIN;

-- ─────────────────────────────────────────────────────────────────────────────
-- §1 — L3 meta synthesis tables
-- ─────────────────────────────────────────────────────────────────────────────
DROP TABLE IF EXISTS public.l25_chart_lattice_snapshots         CASCADE;
DROP TABLE IF EXISTS public.l25_vedha_anchor_interactions        CASCADE;
DROP TABLE IF EXISTS public.l25_derivation_graph_nodes           CASCADE;
DROP TABLE IF EXISTS public.l25_derivation_graph_edges           CASCADE;
DROP TABLE IF EXISTS public.l25_pattern_catalog                  CASCADE;
DROP TABLE IF EXISTS public.l25_divergence_ledger                CASCADE;
DROP TABLE IF EXISTS public.l25_negative_space_map               CASCADE;

-- ─────────────────────────────────────────────────────────────────────────────
-- §2 — L2.5 synthesis tables + staging
-- ─────────────────────────────────────────────────────────────────────────────
DROP TABLE IF EXISTS public.l25_msr_signals                      CASCADE;
DROP TABLE IF EXISTS public.l25_ucn_sections                     CASCADE;
DROP TABLE IF EXISTS public.l25_ucn_digests                      CASCADE;
DROP TABLE IF EXISTS public.l25_cdlm_links                       CASCADE;
DROP TABLE IF EXISTS public.l25_cdlm_cells                       CASCADE;
DROP TABLE IF EXISTS public.l25_cgm_nodes                        CASCADE;
DROP TABLE IF EXISTS public.l25_cgm_edges                        CASCADE;
DROP TABLE IF EXISTS public.l25_rm_resonances                    CASCADE;
DROP TABLE IF EXISTS public.l25_msr_signals_staging              CASCADE;
DROP TABLE IF EXISTS public.l25_ucn_sections_staging             CASCADE;
DROP TABLE IF EXISTS public.l25_ucn_digests_staging              CASCADE;
DROP TABLE IF EXISTS public.l25_cdlm_links_staging               CASCADE;
DROP TABLE IF EXISTS public.l25_cdlm_cells_staging               CASCADE;
DROP TABLE IF EXISTS public.l25_cgm_nodes_staging                CASCADE;
DROP TABLE IF EXISTS public.l25_cgm_edges_staging                CASCADE;
DROP TABLE IF EXISTS public.l25_rm_resonances_staging            CASCADE;

-- ─────────────────────────────────────────────────────────────────────────────
-- §3 — L1 chart facts
-- ─────────────────────────────────────────────────────────────────────────────
DROP TABLE IF EXISTS public.chart_facts                          CASCADE;
DROP TABLE IF EXISTS public.chart_facts_staging                  CASCADE;
DROP TABLE IF EXISTS public.chart_facts_history                  CASCADE;
DROP TABLE IF EXISTS public.chart_facts_supersedence             CASCADE;
DROP TABLE IF EXISTS public.divisional_charts                    CASCADE;
DROP TABLE IF EXISTS public.varshaphala                          CASCADE;

-- ─────────────────────────────────────────────────────────────────────────────
-- §4 — L1 temporal tables
-- ─────────────────────────────────────────────────────────────────────────────
DROP TABLE IF EXISTS public.dasha_periods                        CASCADE;
DROP TABLE IF EXISTS public.chart_dashas                         CASCADE;
DROP TABLE IF EXISTS public.l1_time_synchronicity                CASCADE;
DROP TABLE IF EXISTS public.l1_phase_locked_anchors              CASCADE;
DROP TABLE IF EXISTS public.l1_bhrigu_bindu_transits             CASCADE;
DROP TABLE IF EXISTS public.l1_graha_aspects_lifetime            CASCADE;
DROP TABLE IF EXISTS public.l1_vedha_extended                    CASCADE;
DROP TABLE IF EXISTS public.l1_varsha_digest                     CASCADE;
DROP TABLE IF EXISTS public.l1_tajik_varsha_year_lords           CASCADE;

-- ─────────────────────────────────────────────────────────────────────────────
-- §5 — Reference chakra tables
-- ─────────────────────────────────────────────────────────────────────────────
DROP TABLE IF EXISTS public.l1_sarvatobhadra_positions           CASCADE;
DROP TABLE IF EXISTS public.l1_sarvatobhadra_vedha               CASCADE;
DROP TABLE IF EXISTS public.l1_sapta_shalaka                     CASCADE;
DROP TABLE IF EXISTS public.l1_kalanala_chakra                   CASCADE;
DROP TABLE IF EXISTS public.l1_kota_chakra                       CASCADE;
DROP TABLE IF EXISTS public.l1_ckn_chakra                        CASCADE;

-- ─────────────────────────────────────────────────────────────────────────────
-- §6 — Astronomical tables
-- ─────────────────────────────────────────────────────────────────────────────
DROP TABLE IF EXISTS public.ephemeris_daily                      CASCADE;
DROP TABLE IF EXISTS public.ephemeris_daily_staging              CASCADE;
DROP TABLE IF EXISTS public.panchanga_daily                      CASCADE;
DROP TABLE IF EXISTS public.panchanga_daily_staging              CASCADE;
DROP TABLE IF EXISTS public.eclipses_retrogrades                 CASCADE;

-- ─────────────────────────────────────────────────────────────────────────────
-- §7 — RAG / corpus tables
-- ─────────────────────────────────────────────────────────────────────────────
DROP TABLE IF EXISTS public.rag_chunks                           CASCADE;
DROP TABLE IF EXISTS public.rag_chunks_staging                   CASCADE;
DROP TABLE IF EXISTS public.rag_embeddings                       CASCADE;
DROP TABLE IF EXISTS public.rag_embeddings_staging               CASCADE;
DROP TABLE IF EXISTS public.rag_graph_nodes                      CASCADE;
DROP TABLE IF EXISTS public.rag_graph_edges                      CASCADE;
DROP TABLE IF EXISTS public.rag_queries                          CASCADE;
DROP TABLE IF EXISTS public.rag_retrievals                       CASCADE;
DROP TABLE IF EXISTS public.rag_feedback                         CASCADE;
DROP TABLE IF EXISTS public.rag_reproducibility_failures         CASCADE;

-- ─────────────────────────────────────────────────────────────────────────────
-- §8 — Classical text store
-- ─────────────────────────────────────────────────────────────────────────────
DROP TABLE IF EXISTS public.classical_texts                      CASCADE;
DROP TABLE IF EXISTS public.classical_chunks                     CASCADE;
DROP TABLE IF EXISTS public.classical_attributions               CASCADE;

-- ─────────────────────────────────────────────────────────────────────────────
-- §9 — Discovery registers + staging
-- ─────────────────────────────────────────────────────────────────────────────
DROP TABLE IF EXISTS public.pattern_register                     CASCADE;
DROP TABLE IF EXISTS public.resonance_register                   CASCADE;
DROP TABLE IF EXISTS public.cluster_register                     CASCADE;
DROP TABLE IF EXISTS public.contradiction_register               CASCADE;
DROP TABLE IF EXISTS public.pattern_register_staging             CASCADE;
DROP TABLE IF EXISTS public.resonance_register_staging           CASCADE;
DROP TABLE IF EXISTS public.cluster_register_staging             CASCADE;
DROP TABLE IF EXISTS public.contradiction_register_staging       CASCADE;

-- ─────────────────────────────────────────────────────────────────────────────
-- §10 — Build orchestration tables
-- ─────────────────────────────────────────────────────────────────────────────
DROP TABLE IF EXISTS public.build_manifests                      CASCADE;
DROP TABLE IF EXISTS public.builds                               CASCADE;
DROP TABLE IF EXISTS public.builds_staging                       CASCADE;
DROP TABLE IF EXISTS public.build_steps                          CASCADE;
DROP TABLE IF EXISTS public.build_events                         CASCADE;
DROP TABLE IF EXISTS public.build_notifications                  CASCADE;
DROP TABLE IF EXISTS public.build_engine_versions                CASCADE;
DROP TABLE IF EXISTS public.build_checkpoints                    CASCADE;
DROP TABLE IF EXISTS public.build_dependencies                   CASCADE;
DROP TABLE IF EXISTS public.chart_documents                      CASCADE;
DROP TABLE IF EXISTS public.chart_ayanamsha_reports              CASCADE;

-- ─────────────────────────────────────────────────────────────────────────────
-- §11 — §3 corrections (computed/legacy, not ground-truth)
-- ─────────────────────────────────────────────────────────────────────────────
DROP TABLE IF EXISTS public.sade_sati_phases                     CASCADE;
DROP TABLE IF EXISTS public.sade_sati_phases_staging             CASCADE;
DROP TABLE IF EXISTS public.school_signal_coverage               CASCADE;
DROP TABLE IF EXISTS public.school_analysis_runs                 CASCADE;
DROP TABLE IF EXISTS public.convergence_scores                   CASCADE;
DROP TABLE IF EXISTS public.school_disagreements                 CASCADE;
DROP TABLE IF EXISTS public.multi_school_stances                 CASCADE;
DROP TABLE IF EXISTS public.school_convergence_index             CASCADE;
DROP TABLE IF EXISTS public.data_source_expected                 CASCADE;
DROP TABLE IF EXISTS public.pyramid_layers                       CASCADE;
DROP TABLE IF EXISTS public.documents                            CASCADE;
-- predictions (mig 062, Chat V2 PPL / Prospective Prediction Log) is a KEEP table —
-- it is a core Learning Layer asset (sacrosanct per CLAUDE.md §E). Do NOT drop it here.
DROP TABLE IF EXISTS public.mcp_bundle_cache                     CASCADE;
DROP TABLE IF EXISTS public.mcp_audit_findings                   CASCADE;
DROP TABLE IF EXISTS public.audit_job_runs                       CASCADE;

-- ─────────────────────────────────────────────────────────────────────────────
-- §12 — Drop the mv_data_source_coverage view (references DROP tables)
-- ─────────────────────────────────────────────────────────────────────────────
DROP MATERIALIZED VIEW IF EXISTS public.mv_data_source_coverage  CASCADE;

-- ─────────────────────────────────────────────────────────────────────────────
-- §13 — Signal table (legacy; superseded by l25_msr_signals)
-- ─────────────────────────────────────────────────────────────────────────────
DROP TABLE IF EXISTS public.msr_signals                          CASCADE;
DROP TABLE IF EXISTS public.signal_states                        CASCADE;
DROP TABLE IF EXISTS public.kp_sublords                          CASCADE;

COMMIT;

-- =============================================================================
-- Post-drop verification (run manually to confirm):
--
--   SELECT table_name FROM information_schema.tables
--   WHERE table_schema = 'public'
--   ORDER BY table_name;
--
-- Expected survivors (KEEP set):
--   audit_events, audit_log, capability_asset_tool_bindings,
--   capability_tool_registry, chart_grants, charts, context_assembly_item_log,
--   conversation_branch_messages, conversation_branches, conversation_folder_members,
--   conversation_folders, conversation_messages, conversation_shares, conversations,
--   eval_runs, feature_flags, life_events, life_events_staging,
--   llm_budget_rules, llm_call_log, llm_cost_reconciliation, llm_pricing_versions,
--   llm_provider_cost_reports, llm_stack_config, llm_usage_events,
--   mcp_alerts_config, mcp_api_keys, mcp_disagreements, mcp_prediction_outcomes,
--   mcp_predictions, pending_streams, performance_judge_verdict,
--   performance_queries, personas, plan_alternatives_log, predictions, profiles,
--   project_conversations, project_files, projects, query_baseline_stats,
--   query_plan_log, query_trace_steps, runtime_config, selective_shares,
--   synthesis_quality_scorecard, tool_execution_log, tool_registry
-- =============================================================================
