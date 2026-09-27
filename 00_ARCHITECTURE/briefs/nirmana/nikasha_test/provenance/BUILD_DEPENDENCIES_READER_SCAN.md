---
artifact: NIKASHA_WAVE1_B3_BUILD_DEPENDENCIES_READER_SCAN
version: "1.0"
generated_at: 2026-09-27T05:59:29.398965+00:00
generator: platform/scripts/governance/catalog_provenance.py --reader-scan
---

# Nikaṣa wave 1 — B-3 `build_dependencies` reader scan

Read-only grep for `\bbuild_dependencies\b` across the repo (excluding `.git`, `node_modules`, `__pycache__`, `.next`, `dist`, `build`). **No change made to the table or any file** — this is evidence for a native decision (R219), not an action.

Total hits: **76**

## `00_ARCHITECTURE/BUILD_GUARANTOR_SWARM_CHARTER_v1_0.md`

- L103: `- **Naming/mapping drift.** Migration 158's `build_dependencies` labels do not match the`

## `00_ARCHITECTURE/BUILD_TRACKER_HARDENING_HANDOFF_v1_0.md`

- L68: ``build_dependencies` table (cascade preview, cosmetic) — reconciliation is a pending governance`
- L167: `4. **Two-DAG-source reconciliation** (asset_registry.depends_on vs build_dependencies) — pending`

## `00_ARCHITECTURE/BUILD_TRACKER_HARDENING_MASTER_v1_0.md`

- L64: `preview reads the `build_dependencies` table. Plan correctness rides on `depends_on`. Reconciliation`
- L107: `- **Two-DAG reconciliation** (F4) — `asset_registry.depends_on` vs `build_dependencies`. Governance`

## `00_ARCHITECTURE/CONDUCTOR/build_e2e_arc/PREFLIGHT_FINDINGS.md`

- L12: `- Migrations 157-160 (bonus): also applied — 157 (audit trigger fix), 158 (build_dependencies already existed + 27 rows seeded), 159 (build_checkpoints new), 160 (per_asset_stop, idempotent)`
- L13: `- `build_dependencies` table: 27 rows (ready for Stream B §B-S3 dispatcher edge emission)`

## `00_ARCHITECTURE/CONDUCTOR/build_e2e_arc/briefs/STREAM_B_DATA_PLUMBING_v1_0.md`

- L69: `3. For each upstream→downstream dependency edge (read from `build_dependencies` table — seeded by migration 154), call `emit_edge_added` ONCE per build when the downstream begins. Dedupe with in-memory `set[tuple[str,str]]`.`

## `00_ARCHITECTURE/CONDUCTOR/build_orchestrator/operator_runs/UX_WORKFLOW_OVERHAUL_REPORT.md`

- L49: `- `_load_dep_graph(conn)` — lazy-loads build_dependencies into in-memory forward-edge map`
- L126: `- `cascade-preview/route.ts` — GET, computes transitive descendants from build_dependencies`
- L218: `3. **A14 slot**: Retired in ASSET_MAP with `retired: true`. AssetTable filters retired assets from display. Backend migration seeds no A14 row in build_dependencies. No action needed.`

## `00_ARCHITECTURE/CONTEXT_HANDOFFS/CONTEXT_HANDOFF_2026-06-01_v1_0.md`

- L82: `The 28-asset DAG with 27 edges is seeded by migration 158 in `build_dependencies`. Build order is enforced by `build_steps.depends_on` and verified post-fact by Pariksha's layer-completion gate (L1 must finish before L2.5 starts, and so on).`

## `00_ARCHITECTURE/CURRENT_STATE_v1_0.md`

- L1824: `Verify-then-commit pass: ran vitest + typecheck (PASS), committed 8 workstream commits (A1 DAG upstream-closure + L0 exclusion, A2 catalog reconciliation, A3 retire build_dependencies, C1/C2/C3 SSE refetch + hybrid counts + refresh cache-bust, E1 reconciling clear summary, E2 named cascade tree, B1/B2 per-asset bars + global progress bar, D1 plan-seeded DAG, F1 service/data icons, F2 gold palette). Two additional bug fixes: migration 342 FK constraint reorder (3ce92f34) + /cockpit page builds→build_runs try/catch (596c1118). CI green on all commits. Deployed to Cloud Run (amjis-web-qm256lasva-el.a.run.app). Chrome MCP probe on non-native 1c826d5a confirmed: F1 ✓ (icons), F2 ✓ (gold palette), E1 ✓ (reconciling modal arithmetic), E2 ✓ (named layer-grouped tree), C3 ✓ (no-store cache-bust), B2 ✓ (global progress bar gold), D1 ✓ (ArmillaryGraph plan-seeded beads), B1 ✓ (per-asset bars update). C1/C2 code-verified (useActiveRun poll → onCompleted → refetchStats within 5s; stats API hybrid per_chart always count_sql, global bg_* count_sql on ?mode=live). D2 operational gap: SSE is heartbeat-only (GOOGLE_CLOUD_PROJECT absent from Cloud Run amjis-web env; action item for follow-up — does not block tracker functionality). Native chart 482012f1 NEVER touched.`
- L1836: `Claude Code (Antigravity) implemented A1/A2/A3, C1-C3, E1/E2, B1/B2, D1, F1, F2 on the working tree (uncommitted): 24 files modified, migs 342/343 (retire ga_pyjhora_engine + build_dependencies routes),`

## `00_ARCHITECTURE/LAYER_BUILD_RELIABILITY_BRIEF_v1_0.md`

- L36: ``depends_on`. `/api/build/data-readiness` calls `build_dependencies` "the authoritative DAG".`
- L37: `⚠ TWO DAG SOURCES exist — `build_dependencies` table AND `asset_registry.depends_on`. Divergence`
- L60: ``asset_registry WHERE layer=$1 AND is_active=true`, from `build_dependencies`, or a mix?`
- L61: `- Are the two DAG sources (`build_dependencies` vs `asset_registry.depends_on`) CONSISTENT? If a`
- L122: `- DAG-consistency test: `build_dependencies` vs `asset_registry.depends_on` agree for every layer (or`

## `00_ARCHITECTURE/LEGACY_TEARDOWN_CLOSE_v1_0.md`

- L64: `- **Build orchestration (10):** `build_manifests`, `builds`, `build_steps`, `build_events`, `build_notifications`, `build_engine_versions`, `build_checkpoints`, `build_dependencies`, `chart_documents`, `chart_ayanamsha_reports``

## `00_ARCHITECTURE/LEGACY_TEARDOWN_KILL_LIST_v1_0.md`

- L45: `- **Build orchestration tables:** `build_manifests` (013), `builds` (+staging) (124), `build_steps` (125), `build_events` (118), `build_notifications` (127), `build_engine_versions` (126), `build_checkpoints` (159), `build_dependencies` (158), `chart_documents` (131), `chart_ayanamsha_reports` (130).`

## `00_ARCHITECTURE/NIRMANA_BUILD_TRACKER_HARDENING_HANDOFF_v2_0.md`

- L97: `(asset_registry_seed.ts) or a `build_dependencies` table. Enumerate all three; diff them.`
- L106: `- **Two-DAG problem:** `asset_registry.depends_on` (plan builder, authoritative) vs `build_dependencies``

## `00_ARCHITECTURE/PARIKSHA/ASSET_REGISTRY.md`

- L275: `When a new asset is added to the build (new writer + new build_dependencies entry):`

## `00_ARCHITECTURE/SESSION_LOG.md`

- L29184: `workstreams: [A1 DAG upstream-closure, A2 catalog reconciliation, A3 retire build_dependencies, C1-C3 stale numbers, E1 clear reconcile, E2 cascade tree, B1/B2 live bars, D1 live DAG, F1 service/data icons, F2 green→gold]`
- L29260: `- "75fb914f fix(build/A3): retire build_dependencies from all TS routes; use asset_registry DAG"`

## `00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_SIDECAR_RESIDUALS_v1_0.md`

- L176: ``build_dependencies` table seeded by migration 154 in PR #172), emit`

## `00_ARCHITECTURE/briefs/nirmana/NIKASHA_CHANGE_REGISTER_v2_0.md`

- L10: `- "2.1 (2026-09-27, D5 native revision): R85 re-scoped to catalog provenance + DAG closure (the P/V × layer matrix is withdrawn — the planner LLM maps questions to catalog units per query); R218 planner test, R219 dead `build_dependencies`, R220 active population 127, R221 T3 §0.1 re-scope (§2.10). Totals 217 → 221; OPEN 198 → 202."`
- L407: `\| R219 \| `build_dependencies` is a dead pre-rename table (ids `A1`/`A10`, layer `L25`, `category_prefix a1_`; 75 edge rows with **zero** overlap against `asset_registry.depends_on`'s 344) — mark dead / drop; every DAG reader (census closure, cockpit, docs) must use `asset_registry.depends_on`, the DAG the orchestrator walks \| D5 rev. 2.1 closure measurement 2026-09-27 (first closure ran on it and expanded 12→12) \| DEGRADES \| — \| 1 \| OPEN — per D5 rev. 2.1; lands in P6 \|`

## `00_ARCHITECTURE/briefs/nirmana/NIKASHA_WAVE1_EXECUTION_PROMPT_v1_0.md`

- L102: ``asset_registry.depends_on` (NOT `build_dependencies` — dead pre-rename table, R219). Report: named producers`
- L106: `- **B-3 · R219 reader scan.** Grep the codebase for readers of `build_dependencies`; list them. Do not drop or alter`

## `00_ARCHITECTURE/briefs/nirmana/nikasha_test/DECISIONS_FOR_THE_NATIVE.md`

- L291: `>    `build_dependencies` is a dead pre-rename table, R219) of any asset that does: the transitive`

## `00_ARCHITECTURE/briefs/nirmana/nikasha_test/DECISIONS_RECOMMENDATIONS_v2_0.md`

- L285: `>    `build_dependencies` is a dead pre-rename table, R219) of any asset that does: the transitive`

## `00_ARCHITECTURE/briefs/nirmana/nikasha_test/STATE.md`

- L165: `\| **D5 revised 2.1 by the native** \| The frozen D5 was wrong in kind: Pariprāśna's planner LLM chooses catalog units per question, so no static question→layer table is used. Necessity = catalog provenance + upstream DAG closure, computed (63/127 active today; 64 outside, all 23 ph/mi); P-needs become the planner test; T3 §0.1 re-scoped; no §3.6. Native's two corrections adopted: producer-or-part-producer (no "sole producer"), and closure propagates upstream. Side findings R219 (dead `build_dependencies`), R220 (127 active, not 129). \| v2.1, register §2.10, commits `5d7d2baef` + this one \|`

## `99_ARCHIVE/BRIEFS_RETIRED/CLAUDECODE_BRIEF_WS0B_CODE_CLUSTER_PURGE_v1_0.md`

- L97: `export LEGACY_TABLES='audit_job_runs\|ayanamsha_registry\|build_checkpoints\|build_dependencies\|build_engine_versions\|build_events\|build_manifests\|build_notifications\|build_steps\|builds\|builds_staging\|chart_ayanamsha_reports\|chart_dashas\|chart_documents\|chart_facts\|chart_facts_history\|chart_facts_staging\|chart_facts_supersedence\|chat_attachments\|classical_attributions\|classical_chunks\|classical_texts\|cluster_register\|cluster_register_staging\|context_assembly_log\|contradiction_register\|contradiction_register_staging\|convergence_scores\|data_source_expected\|dasha_periods\|divisional_charts\|documents\|eclipses\|eclipses_retrogrades\|eclipses_staging\|engine_versions\|ephemeris_daily\|ephemeris_daily_staging\|g29_timing_rules\|gate_change_log\|kp_sublords\|l1_bhrigu_bindu_transits\|l1_ckn_chakra\|l1_graha_aspects_lifetime\|l1_kalanala_chakra\|l1_kota_chakra\|l1_phase_locked_anchors\|l1_sapta_shalaka\|l1_sarvatobhadra_positions\|l1_sarvatobhadra_vedha\|l1_tajik_varsha_year_lords\|l1_time_synchronicity\|l1_varsha_digest\|l1_vedha_extended\|l25_cdlm_cells\|l25_cdlm_cells_staging\|l25_cdlm_links\|l25_cdlm_links_staging\|l25_cgm_edges\|l25_cgm_edges_staging\|l25_cgm_nodes\|l25_cgm_nodes_staging\|l25_chart_lattice_snapshots\|l25_derivation_graph_edges\|l25_derivation_graph_nodes\|l25_divergence_ledger\|l25_msr_signals\|l25_msr_signals_staging\|l25_negative_space_map\|l25_pattern_catalog\|l25_rm_resonances\|l25_rm_resonances_staging\|l25_ucn_digests\|l25_ucn_digests_staging\|l25_ucn_sections\|l25_ucn_sections_staging\|l25_vedha_anchor_interactions\|llm_catalog_snapshot\|llm_config_audit\|llm_model_health\|llm_param_override\|llm_stack_routing_override\|mcp_audit_findings\|mcp_bundle_cache\|message_feedback\|messages\|msr_signals\|multi_school_stances\|notification_views\|panchanga_daily\|panchanga_daily_staging\|pattern_register\|pattern_register_staging\|prediction_ledger\|predictions\|pyramid_layers\|query_plans\|rag_chunks\|rag_chunks_staging\|rag_embeddings\|rag_embeddings_staging\|rag_feedback\|rag_graph_edges\|rag_graph_nodes\|rag_queries\|rag_reproducibility_failures\|rag_retrievals\|reports\|resonance_register\|resonance_register_staging\|retrogrades\|retrogrades_staging\|sade_sati_cycles\|sade_sati_phases\|sade_sati_phases_staging\|sankranti_table\|saturn_sign_changes\|school_analysis_runs\|school_convergence_index\|school_disagreements\|school_signal_coverage\|shadbala\|signal_states\|tajaka_annual\|tool_caveats\|varshaphala'`

## `99_ARCHIVE/BRIEFS_RETIRED/CLAUDECODE_BRIEF_WS0C_RESIDUAL_PURGE_v1_0.md`

- L98: `export LEGACY_TABLES='audit_job_runs\|ayanamsha_registry\|build_checkpoints\|build_dependencies\|build_engine_versions\|build_manifests\|build_notifications\|chart_ayanamsha_reports\|chart_dashas\|chart_documents\|chart_facts\|chart_facts_history\|chart_facts_staging\|chart_facts_supersedence\|chat_attachments\|classical_attributions\|classical_chunks\|classical_texts\|cluster_register\|cluster_register_staging\|context_assembly_log\|contradiction_register\|contradiction_register_staging\|convergence_scores\|data_source_expected\|dasha_periods\|divisional_charts\|documents\|eclipses\|eclipses_retrogrades\|eclipses_staging\|engine_versions\|ephemeris_daily\|ephemeris_daily_staging\|g29_timing_rules\|gate_change_log\|kp_sublords\|l1_bhrigu_bindu_transits\|l1_ckn_chakra\|l1_graha_aspects_lifetime\|l1_kalanala_chakra\|l1_kota_chakra\|l1_phase_locked_anchors\|l1_sapta_shalaka\|l1_sarvatobhadra_positions\|l1_sarvatobhadra_vedha\|l1_tajik_varsha_year_lords\|l1_time_synchronicity\|l1_varsha_digest\|l1_vedha_extended\|l25_cdlm_cells\|l25_cdlm_cells_staging\|l25_cdlm_links\|l25_cdlm_links_staging\|l25_cgm_edges\|l25_cgm_edges_staging\|l25_cgm_nodes\|l25_cgm_nodes_staging\|l25_chart_lattice_snapshots\|l25_derivation_graph_edges\|l25_derivation_graph_nodes\|l25_divergence_ledger\|l25_msr_signals\|l25_msr_signals_staging\|l25_negative_space_map\|l25_pattern_catalog\|l25_rm_resonances\|l25_rm_resonances_staging\|l25_ucn_digests\|l25_ucn_digests_staging\|l25_ucn_sections\|l25_ucn_sections_staging\|l25_vedha_anchor_interactions\|llm_catalog_snapshot\|llm_config_audit\|llm_model_health\|llm_param_override\|llm_stack_routing_override\|mcp_audit_findings\|mcp_bundle_cache\|message_feedback\|messages\|msr_signals\|multi_school_stances\|notification_views\|panchanga_daily\|panchanga_daily_staging\|pattern_register\|pattern_register_staging\|prediction_ledger\|predictions\|pyramid_layers\|query_plans\|rag_chunks\|rag_chunks_staging\|rag_embeddings\|rag_embeddings_staging\|rag_feedback\|rag_graph_edges\|rag_graph_nodes\|rag_queries\|rag_reproducibility_failures\|rag_retrievals\|resonance_register\|resonance_register_staging\|retrogrades\|retrogrades_staging\|sade_sati_cycles\|sade_sati_phases\|sade_sati_phases_staging\|sankranti_table\|saturn_sign_changes\|school_analysis_runs\|school_convergence_index\|school_disagreements\|school_signal_coverage\|shadbala\|signal_states\|tajaka_annual\|tool_caveats\|varshaphala'`

## `99_ARCHIVE/BRIEFS_RETIRED/CLAUDECODE_BRIEF_WS0_LEGACY_PURGE_v1_0.md`

- L310: `DROP TABLE IF EXISTS build_dependencies CASCADE;`
- L710: `LEGACY_TABLES='audit_job_runs\|ayanamsha_registry\|build_checkpoints\|build_dependencies\|build_engine_versions\|build_events\|build_manifests\|build_notifications\|build_steps\|builds\|builds_staging\|chart_ayanamsha_reports\|chart_dashas\|chart_documents\|chart_facts\|chart_facts_history\|chart_facts_staging\|chart_facts_supersedence\|chat_attachments\|classical_attributions\|classical_chunks\|classical_texts\|cluster_register\|cluster_register_staging\|context_assembly_log\|contradiction_register\|contradiction_register_staging\|convergence_scores\|data_source_expected\|dasha_periods\|divisional_charts\|documents\|eclipses\|eclipses_retrogrades\|eclipses_staging\|engine_versions\|ephemeris_daily\|ephemeris_daily_staging\|g29_timing_rules\|gate_change_log\|kp_sublords\|l1_bhrigu_bindu_transits\|l1_ckn_chakra\|l1_graha_aspects_lifetime\|l1_kalanala_chakra\|l1_kota_chakra\|l1_phase_locked_anchors\|l1_sapta_shalaka\|l1_sarvatobhadra_positions\|l1_sarvatobhadra_vedha\|l1_tajik_varsha_year_lords\|l1_time_synchronicity\|l1_varsha_digest\|l1_vedha_extended\|l25_cdlm_cells\|l25_cdlm_cells_staging\|l25_cdlm_links\|l25_cdlm_links_staging\|l25_cgm_edges\|l25_cgm_edges_staging\|l25_cgm_nodes\|l25_cgm_nodes_staging\|l25_chart_lattice_snapshots\|l25_derivation_graph_edges\|l25_derivation_graph_nodes\|l25_divergence_ledger\|l25_msr_signals\|l25_msr_signals_staging\|l25_negative_space_map\|l25_pattern_catalog\|l25_rm_resonances\|l25_rm_resonances_staging\|l25_ucn_digests\|l25_ucn_digests_staging\|l25_ucn_sections\|l25_ucn_sections_staging\|l25_vedha_anchor_interactions\|llm_catalog_snapshot\|llm_config_audit\|llm_model_health\|llm_param_override\|llm_stack_routing_override\|mcp_audit_findings\|mcp_bundle_cache\|message_feedback\|messages\|msr_signals\|multi_school_stances\|notification_views\|panchanga_daily\|panchanga_daily_staging\|pattern_register\|pattern_register_staging\|prediction_ledger\|predictions\|pyramid_layers\|query_plans\|rag_chunks\|rag_chunks_staging\|rag_embeddings\|rag_embeddings_staging\|rag_feedback\|rag_graph_edges\|rag_graph_nodes\|rag_queries\|rag_reproducibility_failures\|rag_retrievals\|reports\|resonance_register\|resonance_register_staging\|retrogrades\|retrogrades_staging\|sade_sati_cycles\|sade_sati_phases\|sade_sati_phases_staging\|sankranti_table\|saturn_sign_changes\|school_analysis_runs\|school_convergence_index\|school_disagreements\|school_signal_coverage\|shadbala\|signal_states\|tajaka_annual\|tool_caveats\|varshaphala'`
- L983: `LEGACY_TABLES='audit_job_runs\|ayanamsha_registry\|build_checkpoints\|build_dependencies\|build_engine_versions\|build_events\|build_manifests\|build_notifications\|build_steps\|builds\|builds_staging\|chart_ayanamsha_reports\|chart_dashas\|chart_documents\|chart_facts\|chart_facts_history\|chart_facts_staging\|chart_facts_supersedence\|chat_attachments\|classical_attributions\|classical_chunks\|classical_texts\|cluster_register\|cluster_register_staging\|context_assembly_log\|contradiction_register\|contradiction_register_staging\|convergence_scores\|data_source_expected\|dasha_periods\|divisional_charts\|documents\|eclipses\|eclipses_retrogrades\|eclipses_staging\|engine_versions\|ephemeris_daily\|ephemeris_daily_staging\|g29_timing_rules\|gate_change_log\|kp_sublords\|l1_bhrigu_bindu_transits\|l1_ckn_chakra\|l1_graha_aspects_lifetime\|l1_kalanala_chakra\|l1_kota_chakra\|l1_phase_locked_anchors\|l1_sapta_shalaka\|l1_sarvatobhadra_positions\|l1_sarvatobhadra_vedha\|l1_tajik_varsha_year_lords\|l1_time_synchronicity\|l1_varsha_digest\|l1_vedha_extended\|l25_cdlm_cells\|l25_cdlm_cells_staging\|l25_cdlm_links\|l25_cdlm_links_staging\|l25_cgm_edges\|l25_cgm_edges_staging\|l25_cgm_nodes\|l25_cgm_nodes_staging\|l25_chart_lattice_snapshots\|l25_derivation_graph_edges\|l25_derivation_graph_nodes\|l25_divergence_ledger\|l25_msr_signals\|l25_msr_signals_staging\|l25_negative_space_map\|l25_pattern_catalog\|l25_rm_resonances\|l25_rm_resonances_staging\|l25_ucn_digests\|l25_ucn_digests_staging\|l25_ucn_sections\|l25_ucn_sections_staging\|l25_vedha_anchor_interactions\|llm_catalog_snapshot\|llm_config_audit\|llm_model_health\|llm_param_override\|llm_stack_routing_override\|mcp_audit_findings\|mcp_bundle_cache\|message_feedback\|messages\|msr_signals\|multi_school_stances\|notification_views\|panchanga_daily\|panchanga_daily_staging\|pattern_register\|pattern_register_staging\|prediction_ledger\|predictions\|pyramid_layers\|query_plans\|rag_chunks\|rag_chunks_staging\|rag_embeddings\|rag_embeddings_staging\|rag_feedback\|rag_graph_edges\|rag_graph_nodes\|rag_queries\|rag_reproducibility_failures\|rag_retrievals\|reports\|resonance_register\|resonance_register_staging\|retrogrades\|retrogrades_staging\|sade_sati_cycles\|sade_sati_phases\|sade_sati_phases_staging\|sankranti_table\|saturn_sign_changes\|school_analysis_runs\|school_convergence_index\|school_disagreements\|school_signal_coverage\|shadbala\|signal_states\|tajaka_annual\|tool_caveats\|varshaphala'`

## `ANTIGRAVITY_PASTE_WS0B_HOTPATCH.md`

- L323: `export LEGACY_TABLES='audit_job_runs\|ayanamsha_registry\|build_checkpoints\|build_dependencies\|build_engine_versions\|build_manifests\|build_notifications\|chart_ayanamsha_reports\|chart_dashas\|chart_documents\|chart_facts\|chart_facts_history\|chart_facts_staging\|chart_facts_supersedence\|chat_attachments\|classical_attributions\|classical_chunks\|classical_texts\|cluster_register\|cluster_register_staging\|context_assembly_log\|contradiction_register\|contradiction_register_staging\|convergence_scores\|data_source_expected\|dasha_periods\|divisional_charts\|documents\|eclipses\|eclipses_retrogrades\|eclipses_staging\|engine_versions\|ephemeris_daily\|ephemeris_daily_staging\|g29_timing_rules\|gate_change_log\|kp_sublords\|l1_bhrigu_bindu_transits\|l1_ckn_chakra\|l1_graha_aspects_lifetime\|l1_kalanala_chakra\|l1_kota_chakra\|l1_phase_locked_anchors\|l1_sapta_shalaka\|l1_sarvatobhadra_positions\|l1_sarvatobhadra_vedha\|l1_tajik_varsha_year_lords\|l1_time_synchronicity\|l1_varsha_digest\|l1_vedha_extended\|l25_cdlm_cells\|l25_cdlm_cells_staging\|l25_cdlm_links\|l25_cdlm_links_staging\|l25_cgm_edges\|l25_cgm_edges_staging\|l25_cgm_nodes\|l25_cgm_nodes_staging\|l25_chart_lattice_snapshots\|l25_derivation_graph_edges\|l25_derivation_graph_nodes\|l25_divergence_ledger\|l25_msr_signals\|l25_msr_signals_staging\|l25_negative_space_map\|l25_pattern_catalog\|l25_rm_resonances\|l25_rm_resonances_staging\|l25_ucn_digests\|l25_ucn_digests_staging\|l25_ucn_sections\|l25_ucn_sections_staging\|l25_vedha_anchor_interactions\|llm_catalog_snapshot\|llm_config_audit\|llm_model_health\|llm_param_override\|llm_stack_routing_override\|mcp_audit_findings\|mcp_bundle_cache\|message_feedback\|messages\|msr_signals\|multi_school_stances\|notification_views\|panchanga_daily\|panchanga_daily_staging\|pattern_register\|pattern_register_staging\|prediction_ledger\|predictions\|pyramid_layers\|query_plans\|rag_chunks\|rag_chunks_staging\|rag_embeddings\|rag_embeddings_staging\|rag_feedback\|rag_graph_edges\|rag_graph_nodes\|rag_queries\|rag_reproducibility_failures\|rag_retrievals\|resonance_register\|resonance_register_staging\|retrogrades\|retrogrades_staging\|sade_sati_cycles\|sade_sati_phases\|sade_sati_phases_staging\|sankranti_table\|saturn_sign_changes\|school_analysis_runs\|school_convergence_index\|school_disagreements\|school_signal_coverage\|shadbala\|signal_states\|tajaka_annual\|tool_caveats\|varshaphala'`

## `ANTIGRAVITY_PASTE_WS0C_SUBS_B_D_E_C.md`

- L52: `export LEGACY_TABLES='audit_job_runs\|ayanamsha_registry\|build_checkpoints\|build_dependencies\|build_engine_versions\|build_manifests\|build_notifications\|chart_ayanamsha_reports\|chart_dashas\|chart_documents\|chart_facts\|chart_facts_history\|chart_facts_staging\|chart_facts_supersedence\|chat_attachments\|classical_attributions\|classical_chunks\|classical_texts\|cluster_register\|cluster_register_staging\|context_assembly_log\|contradiction_register\|contradiction_register_staging\|convergence_scores\|data_source_expected\|dasha_periods\|divisional_charts\|documents\|eclipses\|eclipses_retrogrades\|eclipses_staging\|engine_versions\|ephemeris_daily\|ephemeris_daily_staging\|g29_timing_rules\|gate_change_log\|kp_sublords\|l1_bhrigu_bindu_transits\|l1_ckn_chakra\|l1_graha_aspects_lifetime\|l1_kalanala_chakra\|l1_kota_chakra\|l1_phase_locked_anchors\|l1_sapta_shalaka\|l1_sarvatobhadra_positions\|l1_sarvatobhadra_vedha\|l1_tajik_varsha_year_lords\|l1_time_synchronicity\|l1_varsha_digest\|l1_vedha_extended\|l25_cdlm_cells\|l25_cdlm_cells_staging\|l25_cdlm_links\|l25_cdlm_links_staging\|l25_cgm_edges\|l25_cgm_edges_staging\|l25_cgm_nodes\|l25_cgm_nodes_staging\|l25_chart_lattice_snapshots\|l25_derivation_graph_edges\|l25_derivation_graph_nodes\|l25_divergence_ledger\|l25_msr_signals\|l25_msr_signals_staging\|l25_negative_space_map\|l25_pattern_catalog\|l25_rm_resonances\|l25_rm_resonances_staging\|l25_ucn_digests\|l25_ucn_digests_staging\|l25_ucn_sections\|l25_ucn_sections_staging\|l25_vedha_anchor_interactions\|llm_catalog_snapshot\|llm_config_audit\|llm_model_health\|llm_param_override\|llm_stack_routing_override\|mcp_audit_findings\|mcp_bundle_cache\|message_feedback\|messages\|msr_signals\|multi_school_stances\|notification_views\|panchanga_daily\|panchanga_daily_staging\|pattern_register\|pattern_register_staging\|prediction_ledger\|predictions\|pyramid_layers\|query_plans\|rag_chunks\|rag_chunks_staging\|rag_embeddings\|rag_embeddings_staging\|rag_feedback\|rag_graph_edges\|rag_graph_nodes\|rag_queries\|rag_reproducibility_failures\|rag_retrievals\|resonance_register\|resonance_register_staging\|retrogrades\|retrogrades_staging\|sade_sati_cycles\|sade_sati_phases\|sade_sati_phases_staging\|sankranti_table\|saturn_sign_changes\|school_analysis_runs\|school_convergence_index\|school_disagreements\|school_signal_coverage\|shadbala\|signal_states\|tajaka_annual\|tool_caveats\|varshaphala'`

## `infra/teardown/00_archive.sh`

- L114: `build_dependencies`

## `infra/teardown/01_drop_tables.sql`

- L140: `DROP TABLE IF EXISTS public.build_dependencies                   CASCADE;`

## `platform/docs/superpowers/plans/2026-06-26-nirmana-build-tracker-hardening.md`

- L47: `\| `src/app/api/build/cascade-preview/route.ts` \| Rewrite \| Retire `build_dependencies`; compute downstream from `asset_registry.depends_on` via `computeDownstreamClosure`; return layer + human names \|`
- L49: `\| `src/app/api/build/data-readiness/route.ts` \| Modify \| Repoint off `build_dependencies` \|`
- L100: `**Root cause (verified, doubly broken):** cascade-preview walks the legacy `build_dependencies` table (`migrations/154`) which (a) is keyed on the **dead `A1..A22 / META_*` id scheme**, not `bg_/ga_/bo_/...`, and (b) is queried with a **phantom column** `depends_on_asset_id` / `descendant_id` that does not exist (real schema: `asset_id`, `depends_on text[]`). It would fail at runtime and never matches what actually builds.`
- L103: `- [ ] **Step 2:** Repoint `cascade/route.ts` and `data-readiness/route.ts` off `build_dependencies` to the same `asset_registry.depends_on` source. Grep for every remaining `build_dependencies` reference (incl. `plan.test.ts`) and update or remove.`
- L104: `- [ ] **Step 3:** Per the destructive-brief reverse-citation gate: grep all live code for `build_dependencies` BEFORE dropping the table. Only after zero live citations remain, add a forward migration marking `build_dependencies` retired (defer the physical `DROP TABLE` to a follow-up per ROOT_FILE_POLICY; a commented retirement migration is acceptable now).`
- L279: `- **Destructive ops** (retiring `build_dependencies`) go through the reverse-citation gate (grep live code for every kill target first; reclassify any with active citations as KEEP-OR-REPOINT). Defer physical `DROP TABLE` per ROOT_FILE_POLICY.`

## `platform/migrations/154_build_dependencies.sql`

- L5: `CREATE TABLE IF NOT EXISTS build_dependencies (`
- L13: `INSERT INTO build_dependencies (asset_id, depends_on, layer, sort_order, display_name, category_prefix) VALUES`

## `platform/migrations/343_retire_build_dependencies_ts_routes.sql`

- L1: `-- Migration 343: Document build_dependencies retirement progress (TS routes only)`
- L12: `--   • python-sidecar/pipeline/dispatcher.py still queries build_dependencies`
- L17: `-- When dispatcher.py is repointed: add a follow-up migration to DROP TABLE build_dependencies.`

## `platform/migrations/_archive/158_build_dependencies.sql`

- L5: `CREATE TABLE IF NOT EXISTS build_dependencies (`
- L13: `INSERT INTO build_dependencies (asset_id, depends_on, layer, sort_order, display_name, category_prefix) VALUES`

## `platform/python-sidecar/pipeline/dispatcher.py`

- L5: `- _load_dep_graph(conn)       — load forward-edge dependency graph from build_dependencies`
- L29: `"""Load forward-edge dependency graph from build_dependencies table."""`
- L33: `cur = _execute_once(conn, "SELECT asset_id, depends_on FROM build_dependencies")`
- L213: `"SELECT asset_id, category_prefix FROM build_dependencies WHERE asset_id = ANY(%s)",`

## `platform/python-sidecar/tests/test_ga_idempotency.py`

- L266: `if compact.startswith("SELECT asset_id, depends_on FROM build_dependencies"):`
- L268: `elif compact.startswith("SELECT asset_id, category_prefix FROM build_dependencies"):`

## `platform/scripts/governance/__tests__/test_catalog_provenance.py`

- L294: `scan finds its own prior report (which lists 'build_dependencies' on every hit`
- L303: `"cur.execute('SELECT asset_id, depends_on FROM build_dependencies')\n"`
- L309: `stale_report.write_text("\n".join(f"- L{i}: `build_dependencies`" for i in range(50)))`
- L322: `line mentioning 'build_dependencies' while describing the scan itself`
- L332: `"cur.execute('SELECT asset_id, depends_on FROM build_dependencies')\n"`
- L337: `"\n".join(f"mentions build_dependencies on line {i}" for i in range(20))`

## `platform/scripts/governance/catalog_provenance.py`

- L14: `read-only grep, never drops or alters `build_dependencies`)`
- L61: `# and the gate's own B_REVIEW.md) mentions "build_dependencies" many times while`
- L1116: `# §10 — B-3 build_dependencies reader scan (read-only grep; never touches the table)`
- L1127: `which both discuss 'build_dependencies' at length while describing this very`
- L1129: `previous output file listing 'build_dependencies' on every line, and hit`
- L1267: `lines.append("# Nikaṣa wave 1 — B-3 `build_dependencies` reader scan")`
- L1441: `print(f"[B-3] build_dependencies reader scan: {len(hits)} hits -> {READER_SCAN_PATH}")`

## `platform/src/generated/harvest/e2_db_truth.json`

- L554: `"table_name": "build_dependencies",`

