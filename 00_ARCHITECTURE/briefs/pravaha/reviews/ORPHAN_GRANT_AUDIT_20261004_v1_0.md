---
artifact: ORPHAN_GRANT_AUDIT
version: "1.0"
status: EVIDENCE REPORT — read-only audit result with a recommendation; authorises NOTHING
date: 2026-10-04
author: Stream B (Śāstra), session madhav-8b (steward C-RETIRED-QUEUED: commit the evidence with a plain-language risk paragraph and a recommended action)
audit_sql: platform/scripts/readbacks/orphan_dml_grant_audit.sql (PR #3117, queued) — sha256 dd40255957255c50ecfd530a8d073d256817f8fccfd9763cb380cef74363a7db (verified before running)
read_at: 2026-10-04T15:26:56Z (a first identical run a few minutes earlier gave the same 309 rows; diff of the two sorted results = 0)
how_run: ONE SELECT, session forced read-only (transaction_read_only = on), through the campaign's read-only production login; nothing written, no credential printed
changelog:
  - "1.0 (2026-10-04): first version."
---

# Orphan-grant audit — result (production, 2026-10-04)

## 1. What was asked and what the SQL does
"Does any role besides role_orchestrator look like it?" The pinned SQL lists every role that **cannot log in** and **has no members** (nobody holds it through a role membership) yet holds **INSERT / UPDATE / DELETE / TRUNCATE** on a table in schema `public`, with the table owner and the grantor. Out of scope by design: SELECT-only grants, roles that can log in, roles that have members, and a table owner's own implicit rights.

## 2. Result in one table
Of 31 roles that cannot log in, 21 have no members; **5 of those 21 hold write grants — 309 role-by-table rows in all** (all grants made by the table owner, `amjis_app`, except four tables owned by `purna_inquiry_owner`).

| role (cannot log in, no members) | tables with write grants | rights | Gochara-related tables |
|---|---|---|---|
| role_orchestrator | **286** | insert, update, delete | 10 (bg_gochara_arcs, bg_gochara_citation_resolution, gochara_resonance_map, gochara_v3_calibration, kala_gochara_authority, kala_gochara_v2_build_state, kala_gochara_windows__ssv_20260728c, kala_gochara_windows_archive_20260805, kala_gochara_windows_v2, kala_vedha_gochara) |
| role_ledger_write | 13 | insert + update (12), update (1): the mimamsa / prediction ledgers and the pariprashna ledger outbox | 0 |
| utkarsha_builder | 5 | mixed | 3 (kala_gochara_windows: INSERT only; kala_gochara_v2_build_state: insert + update; kala_gochara_windows_v2: insert, update, delete) |
| purna_inquiry_owner | 4 | insert, update, delete, truncate (it owns the four planner_inquiry / planner_managed tables) | 0 |
| role_jobs | 1 | insert + update on conversation_summaries | 0 |

Correction to the first message of this session: utkarsha_builder holds write grants on **three** Gochara tables (not two): kala_gochara_windows (insert), kala_gochara_v2_build_state, kala_gochara_windows_v2.

## 3. What it means, in plain words
These five are **old keys left in a drawer**: roles that nobody can log in as and that nobody has been handed. An ordinary login cannot use them unless someone with administrative rights first gives it to that login; so today they are **dormant, not an open door**. The risk is the **drawer, not the keys**: role_orchestrator alone could write to 286 tables, so one careless "grant this role to that service" in the future, or a restore that re-creates memberships, would hand over write access to almost the whole database — including the Gochara tables the campaign is protecting — without anyone deciding to. role_orchestrator is therefore a **pattern, not a one-off**: four other roles have the same shape. The Gochara-scoped part is the part this campaign must care about: **13 role-by-table rows** (10 role_orchestrator, 3 utkarsha_builder).

## 4. Recommended action (for the steward / owner to decide)
1. **Revoke the Gochara-scoped grants in the next protected window** (the second window already planned for 1241 v7, the L1 read grants and act 2b). The draft migration 1303 (PR #3099) already revokes role_orchestrator's writes on five Gochara tables; extend its scope to the **13 rows above** (10 + 3) so the Gochara estate has no dormant writer at all before the full build. Same method as 1302: surgical REVOKE statements by the table owner, verified by a read-back with this audit SQL (expected: zero Gochara rows).
2. **Do NOT mass-revoke the other ~296 rows in the same change.** The non-Gochara grants (the ledger, jobs and planner roles; role_orchestrator's other 276 tables) are outside the Gochara campaign, and a blanket revoke risks a hidden break in a path nobody has traced (a job that uses SET ROLE, a restore script). Instead: give the owner the table and let the owner decide to either (a) keep the roles and record them as intentionally dormant, or (b) have an owner-approved usage check followed by a dated revoke of role_orchestrator on all tables.
3. Add this audit to the post-window read-backs so a new dormant writer shows up as a changed row count, not as a surprise (the audit SQL is already one read-only SELECT; the runner is in PR #3117).

## 5. What this audit does NOT show
- It lists **grants**, not **use**: it cannot say whether any of these roles was ever used (no usage statistics were read).
- Roles that **can** log in, roles **with** members, SELECT-only grants and column-level grants are out of scope; PUBLIC-executable functions are a separate item.
- The window membership claim is as of the read time above; role memberships can change.

## Appendix — the 309 rows (role, table, table owner, grantor, rights), C-sorted
```
purna_inquiry_owner	planner_inquiry_action_reservations	purna_inquiry_owner	purna_inquiry_owner	DELETE,INSERT,TRUNCATE,UPDATE
purna_inquiry_owner	planner_inquiry_evidence_receipts	purna_inquiry_owner	purna_inquiry_owner	DELETE,INSERT,TRUNCATE,UPDATE
purna_inquiry_owner	planner_inquiry_lifecycles	purna_inquiry_owner	purna_inquiry_owner	DELETE,INSERT,TRUNCATE,UPDATE
purna_inquiry_owner	planner_managed_prashna_jobs	purna_inquiry_owner	purna_inquiry_owner	DELETE,INSERT,TRUNCATE,UPDATE
role_jobs	conversation_summaries	amjis_app	amjis_app	INSERT,UPDATE
role_ledger_write	brahma_mimamsa_prediction_ledger	amjis_app	amjis_app	INSERT,UPDATE
role_ledger_write	brahma_prospective_ledger	amjis_app	amjis_app	INSERT,UPDATE
role_ledger_write	mcp_prediction_outcomes	amjis_app	amjis_app	INSERT,UPDATE
role_ledger_write	mimamsa_adjudication_log	amjis_app	amjis_app	INSERT,UPDATE
role_ledger_write	mimamsa_calibration	amjis_app	amjis_app	INSERT,UPDATE
role_ledger_write	mimamsa_calibration_snapshot	amjis_app	amjis_app	INSERT,UPDATE
role_ledger_write	mimamsa_intervention_ledger	amjis_app	amjis_app	INSERT,UPDATE
role_ledger_write	mimamsa_multipliers	amjis_app	amjis_app	INSERT,UPDATE
role_ledger_write	mimamsa_pool_contributions	amjis_app	amjis_app	INSERT,UPDATE
role_ledger_write	mimamsa_predictions	amjis_app	amjis_app	INSERT,UPDATE
role_ledger_write	mimamsa_resonance_feedback	amjis_app	amjis_app	INSERT,UPDATE
role_ledger_write	mimamsa_snapshot_cosign	amjis_app	amjis_app	INSERT,UPDATE
role_ledger_write	pariprashna_ledger_outbox	amjis_app	amjis_app	UPDATE
role_orchestrator	_migrations_applied	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	access_requests	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	admin_audit_log	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	asset_coefficients	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	asset_registry	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	asset_throughput	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	asset_throughput__ssv_20260728c	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	audit_events	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	audit_log	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	bg_avastha_schemes	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	bg_combustion_orbs	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	bg_dignity_reference	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	bg_gochara_arcs	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	bg_gochara_citation_resolution	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	bg_graha_dik	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	bg_graha_naisargika_friendship	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	bg_kota_chakra_rings	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	bg_kp_sublord_division	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	bg_medical_mappings	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	bg_motion_state_thresholds	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	bg_muhurta_activity_rules	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	bg_muhurta_factor_census	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	bg_muhurta_lattice	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	bg_nakshatra_medical	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	bg_parihara_rules	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	bg_phaladeepika_latta	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	bg_prashna_fructification_rules	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	bg_prashna_lagna_methods	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	bg_prashna_significators	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	bg_prashna_special_techniques	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	bg_prashna_tajik_yogas	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	bg_sarvatobhadra_grid	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	bg_shashtiamsha_deities	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	bg_sign_medical	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	bg_sky_calendar	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	bg_synthetic_cohort	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	bg_synthetic_cohort_md	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	bg_transit_av_gates	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	bg_transit_engine	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	bg_transit_moorti	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	bg_transit_rules	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	bg_transit_vedha	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	bg_vastu_direction_remedials	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	bg_vastu_directions	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	bg_vedha_malefic_scale	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	bodha_cdlm_cells__ssv_20260728a	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	bodha_cdlm_evolution_gradients	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	bodha_cgm_edges__ssv_20260728a	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	bodha_cgm_nodes__ssv_20260728a	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	bodha_msr_signals__ssv_20260728a	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	bodha_rm_resonances__ssv_20260728a	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	bodha_signal_embeddings__ssv_20260728a	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	bodha_spine_bundles	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	brahma_activity_ontology	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	brahma_class_priors	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	brahma_compendium_index	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	brahma_dasha_systems	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	brahma_dosha_catalog	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	brahma_event_ontology	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	brahma_formula_constants	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	brahma_ontology	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	brahma_remedy_corpus	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	brahma_vichara_constants	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	brahma_yoga_catalog	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	build_checkpoints	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	build_dependencies	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	build_engine_versions	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	build_events	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	build_notifications	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	build_protected_assets	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	build_run_assets	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	build_runs	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	build_substep_progress	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	build_substep_progress__ssv_20260728c	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	build_substep_progress_archive_20260805	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	builds_staging	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	capability_asset_tool_bindings	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	capability_tool_registry	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	chart_fact_identity	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	chart_facts_history	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	chart_facts_supersedence	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	chart_grants	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	chart_panchanga	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	chart_panchanga_cache	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	charts	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	classical_attributions	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	classical_chunks	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	classical_text_chunks	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	classical_texts	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	classical_texts_source	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	concept_ledger	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	concordance_ayanamsha_flags	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	concordance_ayanamsha_flags_staging	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	context_assembly_item_log	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	convergence_scores	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	conversation_branches	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	conversation_folder_members	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	conversation_folders	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	conversation_message_embeddings	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	conversation_shares	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	engine_versions	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	ephemeris_daily	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	eval_runs	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	event_chart_state_index	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	fact_category_ownership	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	ganita_dashas	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	ganita_graha_sthana	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	gochara_resonance_map	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	gochara_v3_calibration	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	ka_kshetra_tier_basis	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	kala_activation	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	kala_activation_predicates	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	kala_avadhi	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	kala_bhavishya	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	kala_convergence	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	kala_convergence_staging	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	kala_darshana	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	kala_field	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	kala_field_boundaries	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	kala_field_clocks	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	kala_field_gof	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	kala_field_kinematics	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	kala_field_null	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	kala_field_primitives	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	kala_field_promise_edges	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	kala_field_promise_nodes	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	kala_field_provenance	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	kala_field_routes	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	kala_field_salience	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	kala_field_skill	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	kala_field_snapshots	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	kala_field_weight_versions	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	kala_field_weights	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	kala_field_windows	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	kala_gochara_authority	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	kala_gochara_v2_build_state	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	kala_gochara_windows__ssv_20260728c	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	kala_gochara_windows_archive_20260805	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	kala_gochara_windows_v2	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	kala_insights	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	kala_jivana_parva	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	kala_kota_chakra	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	kala_moorti_nirnaya	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	kala_obstruction	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	kala_paddhati_profile	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	kala_sudarshana_varsha	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	kala_taranga	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	kala_timeline_spec	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	kala_tithi_pravesha	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	kala_vedha_gochara	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	l1_tajik_varsha_year_lords__ssv_20260728b	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	l25_cdlm_cells	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	l25_cgm_edges	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	l25_cgm_nodes	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	l25_msr_signals	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	l25_rm_resonances	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	l25_ucn_digests	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	layer_approvals	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	lel_event_class_resolution	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	life_events	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	life_events_staging	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	llm_budget_rules	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	llm_call_log	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	llm_cost_reconciliation	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	llm_pricing_versions	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	llm_provider_cost_reports	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	llm_stack_config	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	llm_usage_events	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	mcp_alerts_config	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	mcp_api_keys	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	mcp_disagreements	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	mcp_oauth_auth_codes	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	mcp_oauth_clients	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	mcp_oauth_tokens	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	mcp_prediction_outcomes	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	mcp_predictions_retired_backup	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	mcp_sessions	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	mimamsa_adjudication_log	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	mimamsa_anchor_adjustment	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	mimamsa_attribution	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	mimamsa_calibration	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	mimamsa_calibration__ssv_20260728b	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	mimamsa_calibration_snapshot	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	mimamsa_convergence_adjustment	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	mimamsa_discoveries	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	mimamsa_event_provenance	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	mimamsa_export_log	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	mimamsa_fact_adjustment	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	mimamsa_insight_embeddings	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	mimamsa_insight_units	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	mimamsa_insight_units__ssv_20260728a	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	mimamsa_insight_units__ssv_20260728b	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	mimamsa_intervention_ledger	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	mimamsa_journal	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	mimamsa_journal__ssv_20260728b	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	mimamsa_load_bearing	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	mimamsa_load_bearing__ssv_20260728b	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	mimamsa_manifestation_grammar	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	mimamsa_manifestation_grammar__ssv_20260728b	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	mimamsa_manifestation_sets	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	mimamsa_multipliers	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	mimamsa_multipliers__ssv_20260728b	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	mimamsa_negative_controls	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	mimamsa_pool_contributions	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	mimamsa_predictions	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	mimamsa_predictions__ssv_20260728b	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	mimamsa_preferences	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	mimamsa_qa_eval	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	mimamsa_qa_eval__ssv_20260728b	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	mimamsa_reliability	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	mimamsa_resonance_feedback	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	mimamsa_signal_adjustment	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	mimamsa_signal_families	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	mimamsa_snapshot_cosign	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	notification_views	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	orchestrator_event_register	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	panchanga_daily	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	pending_streams	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	performance_judge_verdict	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	performance_queries	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	personas	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	phala_anchors	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	phala_anchors__ssv_20260728a	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	phala_anchors__ssv_20260728b	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	phala_mitigation	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	phala_mitigation__ssv_20260728b	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	phala_muhurta	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	phala_muhurta__ssv_20260728b	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	phala_phaladesa	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	phala_phaladesa__ssv_20260728b	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	phala_pramana	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	phala_pramana__ssv_20260728b	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	phala_rectification	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	phala_rectification__ssv_20260728b	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	phala_rectification_best	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	phala_sankrama	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	phala_sankrama__ssv_20260728b	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	phala_sodhana	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	phala_sodhana__ssv_20260728b	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	phala_suddha_sodhana	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	phala_suddha_sodhana__ssv_20260728b	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	plan_alternatives_log	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	prashna_charts	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	prashna_followup_schedule	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	profiles	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	project_conversations	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	project_files	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	projects	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	pyramid_layers	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	query_plan_log	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	query_trace_steps	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	reference_aspects	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	reference_constants	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	reference_dasha_systems	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	reference_doshas	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	reference_glossary	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	reference_houses	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	reference_karakas	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	reference_nakshatra	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	reference_nakshatra_matrix	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	reference_nakshatra_pada	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	reference_nakshatras	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	reference_planets	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	reference_signs	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	reference_strength_systems	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	reference_topic_tags	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	reference_upagrahas	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	reference_vargas	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	reference_yogas	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	remedy_review_queue	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	runtime_config	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	school_analysis_runs	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	school_disagreements	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	school_signal_coverage	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	sutravali_review	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	sutravali_rules	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	synthesis_quality_scorecard__ssv_20260728a	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	system_health	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	tool_execution_log	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	tool_registry	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	vidhi_floor_items	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	vidhi_intent_floors	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	vidhi_primitives	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	yoga_families	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	yoga_family_members	amjis_app	amjis_app	DELETE,INSERT,UPDATE
role_orchestrator	yoga_interaction_rules	amjis_app	amjis_app	DELETE,INSERT,UPDATE
utkarsha_builder	asset_registry	amjis_app	amjis_app	UPDATE
utkarsha_builder	build_substep_progress	amjis_app	amjis_app	INSERT,UPDATE
utkarsha_builder	kala_gochara_v2_build_state	amjis_app	amjis_app	INSERT,UPDATE
utkarsha_builder	kala_gochara_windows	amjis_app	amjis_app	INSERT
utkarsha_builder	kala_gochara_windows_v2	amjis_app	amjis_app	DELETE,INSERT,UPDATE
```
