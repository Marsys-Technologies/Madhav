---
artifact: TABLE_CONCEPT_DISPOSITIONS_v1_0.md
canonical_id: TABLE_CONCEPT_DISPOSITIONS
version: 1.0
status: GENERATED — v1
generator: platform/scripts/census/generate_concept_reachability.ts
generated_at: 2026-07-19T21:18:10.804Z
---

# Table/Concept Lifecycle Dispositions v1.0 (W-15)

Disposition = SERVED | INTERNAL-BY-DESIGN | RETIRE | DARK-NEEDS-OWNER, for the 77 real DARK tables L1b's mechanical cross-diff found (zero TS-registry-declared route), plus the plan-already-settled non-table dark-set items (GT-49/50/52) carried forward verbatim rather than re-derived. Two corrections this lane independently verified (see body) are folded in, not left as open findings.

## Plan-already-settled (carried forward, not re-derived)

| concept | disposition | citation |
|---|---|---|
| kala_timeline (service) | DARK-UNWIRED (one-line fix, not a build gap): registerKalaTimeline handler exists, never imported into server.ts | GT-49 (Lane E New-Finding 1) |
| ka_graha_sancara (service) | DARK SERVICE — highest-impact single coverage item; call_service_wrappers.ts:200-208 returns "not yet wired to a compute sidecar endpoint", blocking all date-parameterized "positions at time T" retrieval | GT-50 (Lane E New-Finding 2) |
| reference_aspects / reference_signs / reference_planets / reference_nakshatras / reference_vargas (5 tables) | RETIRE — dead-superseded by served bg_* equivalents; NOT wire-up candidates | GT-52 (Lane E New-Finding 4) |
| bg_sign_medical | SERVED — correctly resolved by L1b's own cross-diff (query_sign_medical.ts) | GT-51 (Lane E New-Finding 3); confirmed already-correct in L1b's adjudication_queue.json |

## This lane's own corrections (verified by direct source read)

| table | was (L1b) | now | evidence |
|---|---|---|---|
| `bg_dignity_reference` | INTERNAL-BY-DESIGN (DARK) | **SERVED** | Served by platform-mcp/src/tools/register_p1_reference.ts — outside the two directories (registry/layers, synthesis) L1b's E1 table_hint scan covered. Same false-dark failure mode GT-51 already named for a different grep. |
| `chart_panchanga` | NEEDS-OWNER (DARK) | **SERVED** | Served by platform/src/lib/tools/brahma/l1/query_panchanga.ts — a THIRD serving path (lib/tools/brahma/) outside both the registry/layers scan and platform-mcp; matches GT-51's single-directory-grep false-dark pattern. |

## Full DARK-table disposition set (77 tables, L1b's cross-diff + this lane's corrections)

| table | layer | row_count | disposition |
|---|---|---|---|
| `bg_avastha_schemes` | L0 | 35 | INTERNAL-BY-DESIGN |
| `bg_combustion_orbs` | L0 | 8 | INTERNAL-BY-DESIGN |
| `bg_dignity_reference` | L0 | 9 | SERVED (corrected this lane — was DARK/INTERNAL-BY-DESIGN in L1b's queue) |
| `bg_graha_dik` | L0 | 9 | INTERNAL-BY-DESIGN |
| `bg_graha_naisargika_friendship` | L0 | 72 | INTERNAL-BY-DESIGN |
| `bg_medical_mappings` | L0 | 21 | INTERNAL-BY-DESIGN |
| `bg_motion_state_thresholds` | L0 | 27 | INTERNAL-BY-DESIGN |
| `bg_nakshatra_medical` | L0 | 27 | INTERNAL-BY-DESIGN |
| `bg_prashna_fructification_rules` | L0 | 5 | INTERNAL-BY-DESIGN |
| `bg_prashna_lagna_methods` | L0 | 5 | NEEDS-OWNER |
| `bg_prashna_significators` | L0 | 12 | NEEDS-OWNER |
| `bg_prashna_special_techniques` | L0 | 3 | NEEDS-OWNER |
| `bg_prashna_tajik_yogas` | L0 | 16 | NEEDS-OWNER |
| `bg_shashtiamsha_deities` | L0 | 60 | INTERNAL-BY-DESIGN |
| `bg_transit_av_gates` | L0 | 8 | NEEDS-OWNER |
| `bg_transit_engine` | L0 | 9 | NEEDS-OWNER |
| `bg_transit_moorti` | L0 | 27 | INTERNAL-BY-DESIGN |
| `bg_transit_rules` | L0 | 57 | INTERNAL-BY-DESIGN |
| `bg_transit_vedha` | L0 | 33 | INTERNAL-BY-DESIGN |
| `bg_vastu_direction_remedials` | L0 | 24 | INTERNAL-BY-DESIGN |
| `bg_vastu_directions` | L0 | 8 | INTERNAL-BY-DESIGN |
| `bodha_anomalies` | L2 | 4954 | NEEDS-OWNER |
| `bodha_cdlm_domain_rollups` | L2 | 60 | NEEDS-OWNER |
| `bodha_cdlm_evolution_gradients` | L2 | 0 | NEEDS-OWNER |
| `bodha_cdlm_pattern_clusters` | L2 | 10 | NEEDS-OWNER |
| `bodha_cgm_chart_topology_summary` | L2 | 10 | NEEDS-OWNER |
| `bodha_cgm_edges` | L2 | 1573 | NEEDS-OWNER |
| `bodha_cgm_nodes` | L2 | 649 | NEEDS-OWNER |
| `bodha_cgm_sub_graphs` | L2 | 10 | NEEDS-OWNER |
| `bodha_contradictions` | L2 | 23 | NEEDS-OWNER |
| `bodha_convergence` | L2 | 60 | NEEDS-OWNER |
| `bodha_rm_chart_summary` | L2 | 10 | NEEDS-OWNER |
| `bodha_rm_dasha_windowed_prescriptions` | L2 | 0 | NEEDS-OWNER |
| `bodha_rm_dosha_remedy_bundles` | L2 | 0 | NEEDS-OWNER |
| `bodha_rm_pattern_remedies` | L2 | 90 | NEEDS-OWNER |
| `bodha_signal_embeddings` | L2 | 85997 | NEEDS-OWNER |
| `bodha_triangulation` | L2 | 200 | NEEDS-OWNER |
| `brahma_activity_ontology` | L0 | 12 | NEEDS-OWNER |
| `brahma_class_priors` | L0 | 164 | NEEDS-OWNER |
| `brahma_compendium_index` | L0 | 9538 | NEEDS-OWNER |
| `brahma_dasha_systems` | L0 | 18 | NEEDS-OWNER |
| `brahma_event_ontology` | L0 | 27 | NEEDS-OWNER |
| `brahma_formula_constants` | L0 | 18 | NEEDS-OWNER |
| `brahma_prospective_ledger` | L0 | 7 | NEEDS-OWNER |
| `brahma_vichara_constants` | L0 | 7 | NEEDS-OWNER |
| `chart_facts_history` | L1 | 0 | INTERNAL-BY-DESIGN |
| `chart_facts_supersedence` | L1 | 0 | INTERNAL-BY-DESIGN |
| `chart_grants` | L1 | 9 | NEEDS-OWNER |
| `chart_panchanga` | L1 | 0 | SERVED (corrected this lane — was DARK/NEEDS-OWNER in L1b's queue) |
| `chart_panchanga_cache` | L1 | 0 | INTERNAL-BY-DESIGN |
| `ga_condition_composite` | L1 | 90 | NEEDS-OWNER |
| `ga_prashna_judgment` | L1 | 5 | NEEDS-OWNER |
| `ga_prashna_lagna` | L1 | 5 | NEEDS-OWNER |
| `ganita_dashas` | L1 | 0 | NEEDS-OWNER |
| `ganita_graha_sthana` | L1 | 0 | NEEDS-OWNER |
| `kala_activation_predicates` | L3 | 78996 | NEEDS-OWNER |
| `kala_convergence_staging` | L3 | 0 | INTERNAL-BY-DESIGN |
| `kala_gochara_windows` | L3 | 5 | NEEDS-OWNER |
| `mimamsa_adjudication_log` | L5 | 0 | INTERNAL-BY-DESIGN |
| `mimamsa_anchor_adjustment` | L5 | 384 | NEEDS-OWNER |
| `mimamsa_attribution` | L5 | 0 | NEEDS-OWNER |
| `mimamsa_calibration_snapshot` | L5 | 0 | INTERNAL-BY-DESIGN |
| `mimamsa_convergence_adjustment` | L5 | 1000 | NEEDS-OWNER |
| `mimamsa_discoveries` | L5 | 45 | NEEDS-OWNER |
| `mimamsa_event_provenance` | L5 | 57 | NEEDS-OWNER |
| `mimamsa_export_log` | L5 | 0 | INTERNAL-BY-DESIGN |
| `mimamsa_fact_adjustment` | L5 | 121100 | NEEDS-OWNER |
| `mimamsa_insight_embeddings` | L5 | 0 | NEEDS-OWNER |
| `mimamsa_journal` | L5 | 0 | NEEDS-OWNER |
| `mimamsa_load_bearing` | L5 | 10 | NEEDS-OWNER |
| `mimamsa_manifestation_sets` | L5 | 384 | NEEDS-OWNER |
| `mimamsa_negative_controls` | L5 | 4 | NEEDS-OWNER |
| `mimamsa_pool_contributions` | L5 | 0 | INTERNAL-BY-DESIGN |
| `mimamsa_preferences` | L5 | 0 | NEEDS-OWNER |
| `mimamsa_resonance_feedback` | L5 | 0 | INTERNAL-BY-DESIGN |
| `mimamsa_signal_adjustment` | L5 | 97504 | NEEDS-OWNER |
| `mimamsa_snapshot_cosign` | L5 | 0 | INTERNAL-BY-DESIGN |

## Disposition-class summary

- INTERNAL-BY-DESIGN: **24**
- SERVED (corrected): **2**
- NEEDS-OWNER: **51**

`INTERNAL-BY-DESIGN` rows were auto-proposed by L1b's cross-diff via two transparent, inspectable naming-pattern rules (bookkeeping-suffix tables, `bg_*` reference-keyword tables) — not individually researched per row. `NEEDS-OWNER` rows are honestly left for a human/conductor call, per L1b's own scope statement (52/77 not individually researched). Neither this lane nor L1b re-derives dispositions the plan itself already settled (GT-49/50/52, table above) — those are carried forward verbatim.

---

*End of TABLE_CONCEPT_DISPOSITIONS v1.0 — Lane L1d, W1. Source data: `platform/src/generated/harvest/adjudication_queue.json` (L1b) + this lane's two verified corrections + GROUND_TRUTH_REGISTER.md GT-49/50/52 (carried forward).*
