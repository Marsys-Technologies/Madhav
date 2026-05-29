---
artifact: RETRIEVAL_INTERFACE_REGISTER_v1_0.md
document: Retrieval Interface Register — Canonical MCP schemas for A1-A16 + G + META
status: LOCKED
version: 1.0
date: 2026-05-29
authored_by: Cowork (native-confirmed: every asset must have retrieval-tool-ready schemas; MCP-consumable design is non-negotiable)
intended_for: Claude Code sub-agents implementing the MCP retrieval-tool layer + Cloud SQL view layer
prime_directive: Every L1.5/L2.5 row must be retrievable via a typed, documented, LLM-consumable MCP tool. No silent rows. No undocumented JSONB shapes. No retrieval gaps.
binds: A1-A16 asset specs + G27 + G29 corpus prereqs + META_ENHANCEMENTS_SPEC + INTERFACE_NORMALIZATION_REGISTER_v1_0
---

# Retrieval Interface Register

## §0 — Mission

For every per-chart asset (A1-A16), global asset (G-series), and synthesis-layer (META α-ε), this register codifies:

1. **What retrieval tool(s) expose the asset to the MCP**
2. **The Zod input schema** (typed parameter shape)
3. **The Zod output schema** (typed response shape)
4. **The LLM-facing tool description** (what the model sees in its tool list)
5. **Citation envelope** (every row carries citation_ref + citation_human)
6. **Channel adapters** (chat / report / visual / audio / dashboard re-shapes)
7. **Tier filtering** (super_admin / acharya / client)
8. **Cross-asset linkage** (foreign-key relationships exposed via tool joins)

This is the **contract** the build orchestrator must satisfy before any asset is considered done. **No asset is "complete" without its retrieval tool registered here and tested.**

## §1 — Interface standards (every retrieval tool conforms)

### §1.A — Naming convention

Tool name pattern: `query_<asset_or_table_short_name>[_<qualifier>]`. Examples:
- `query_forensic_chart` (A2)
- `query_chart_facts` (A3)
- `query_panchanga_at_date` (A4)
- `query_sensitive_points` (A5)
- `query_vargas` (A6)
- `query_dashas` (A7)
- `query_t1_structural` (A8)
- `query_sade_sati` (A9)
- `query_msr_signals` (A10)
- `query_cdlm_cells` (A11)
- `query_cgm_subgraph` (A12)
- `query_rm_prescriptions` (A13)
- `query_synchronicity_at_date` (A15)
- `query_anchors_in_range` (A16)
- `query_lattice_at_date` (META-α)
- `query_patterns` (META-β)
- `query_divergences` (META-γ)
- `query_negative_space` (META-δ)
- `query_derivation_trail` (META-ε)
- `query_ucd` (UCD conceptual surface joining A8+A11+A12+A13 chart_summaries)

Write tools (M6 outcome tracking, prediction logging, disagreement flagging) follow `record_<verb>` or `log_<noun>` pattern.

### §1.B — Standard input envelope

Every read tool accepts at minimum:

```typescript
const StandardReadInput = z.object({
  chart_id: z.string().uuid(),
  ayanamsha_id: z.enum(['lahiri', 'true_chitra', 'kp', 'raman', 'surya_siddhanta']).optional()
    .default('lahiri'),
  tier: z.enum(['super_admin', 'acharya', 'client']).optional().default('client'),
  channel: z.enum(['chat', 'report', 'visual', 'audio', 'dashboard']).optional().default('chat'),
  // ... asset-specific params ...
});
```

The `tier` and `channel` are honored by tier-conditioned house-rules and channel adapters respectively at the tool implementation layer.

### §1.C — Standard output envelope

Every read tool returns:

```typescript
const StandardReadOutput = z.object({
  rows: z.array(z.record(z.unknown())),              // typed per-asset
  citations: z.array(z.object({
    ref: z.string(),                                  // citation_ref from the row
    human: z.string(),                                // citation_human
    classical_source_id: z.string().optional()
  })),
  derivation_trail_pointers: z.array(z.string().uuid()).optional(),  // Φ-TRAIL claim_ids
  tier_filtered: z.object({
    tier: z.string(),
    rows_redacted_count: z.number(),
    redaction_reason: z.array(z.string())
  }),
  channel_adapter_applied: z.string(),                // which channel adapter ran
  divergences: z.array(z.object({                    // when META-γ surfaces apply
    divergence_id: z.string().uuid(),
    severity: z.string(),
    surface_uncertainty: z.boolean()
  })).optional(),
  meta: z.object({
    build_id: z.string().uuid(),
    asset_version: z.string(),
    computed_at: z.string()
  })
});
```

Every response carries citations. Every response declares the tier + channel applied. Every response can surface divergence flags from META-γ. Every claim has an optional derivation-trail pointer back into META-ε for "show your work."

### §1.D — Channel adapter contract

Channel adapters re-shape the same data for different consumption surfaces:

| Channel | Shape rule |
|---|---|
| `chat` | Top-K limited (default 10), citations inlined with markdown footnotes, full JSONB collapsed to summary keys |
| `report` | Full rows, citations as endnotes, JSONB expanded with field labels, paginated |
| `visual` | Pre-shaped for Mermaid/Cytoscape/Plotly (GraphML hooks from A12 surface here) |
| `audio` | Plain prose accessible-summary form, no markdown, no JSONB syntax |
| `dashboard` | Compact tile-shape — single metric or count per response field |

Tool implementations call the appropriate adapter at the end of the SQL → output marshalling step.

### §1.E — Tier filtering contract

| Tier | What's surfaced |
|---|---|
| `super_admin` | All rows, all fields including instrument-meta (verification_pass_status, ephemeris_audit_jsonb, build_id, derivation_trail) |
| `acharya` | All structural rows, classical citations expanded, intermediate derivations visible; ops tools (log_prediction/record_outcome) allowed |
| `client` | Top-K limited, presentation-friendly fields only, instrument-meta + raw build_id hidden; LLM applies house-rules system prompt for client-appropriate framing |

Tier filtering happens BEFORE channel adapter. Filter then shape.

### §1.F — Cross-asset linkage contract

Foreign keys exposed in tool outputs so the LLM can do multi-tool joins:

- Every row carries `chart_id` + `ayanamsha_id` for cross-tool joining
- Every L2.5+ row carries `derivation_trail_pointer_id` linking to META-ε
- Every pattern carries `cross_pattern_links_array` linking to META-β catalog
- Every prescription carries `targets_motif_id` linking to A12 motifs
- Every motif carries `underlying_msr_signal_ids_array` linking to A10
- Every cell carries `shared_signal_ids_array` linking to A10
- Every anchor carries `associated_synchronicity_id` linking to A15

The LLM can chain tool calls: `query_anchors_in_range` → take an anchor_id → `query_derivation_trail` → trace upward to L1 facts.

## §2 — Per-asset retrieval registration

The full per-asset retrieval registration is in each asset's spec §-retrieval-contract. This register cross-references and codifies the standards.

### §2.A — Per-chart writers (A1-A16)

| Asset | Spec | Retrieval tools | Storage |
|---|---|---|---|
| A1 Engine | `01_FACTS_LAYER/A1_*` (existing) | `query_engine_status(chart_id)` | n/a (computational) |
| A2 FORENSIC render | `A2_FORENSIC_RENDER_SPEC_v1_0.md` (to author) | `query_forensic_chart(chart_id, ayanamsha_id)`, `read_asset('FORENSIC', chart_id)` | chart-rendered markdown |
| A3 chart_facts | `A3_CHART_FACTS_SPEC_v1_0.md` | `query_chart_facts(chart_id, ayanamsha_id, fact_category?, top_k?)` | l1_chart_facts |
| A4 panchanga | `A4_PANCHANGA_SPEC_v1_0.md` | `query_panchanga_at_date`, `query_panchanga_natal`, `query_inauspicious_windows`, `query_auspicious_windows`, `query_muhurta_finder` | l1_panchanga_chart + panchanga_daily |
| A5 sensitive points | `A5_SENSITIVE_POINTS_SPEC_v1_0.md` | `query_sensitive_points(chart_id, ayanamsha_id, category?)`, `query_arudha_lagna`, `query_sahams`, `query_midpoints`, `query_karakas` | l1_sensitive_points |
| A6 vargas | `A6_VARGAS_SPEC_v1_0.md` | `query_varga(chart_id, ayanamsha_id, varga_id)`, `query_vargottama_for_graha`, `query_d9_navamsa`, `query_d10_dasamsa`, `query_d60_shashtiamsa` | l1_vargas |
| A7 chart_dashas | `A7_DASHAS_SPEC_v1_0.md` | `query_dasha_at_date(chart_id, ayanamsha_id, date, system?, level?)`, `query_dasha_range`, `query_active_dashas_now`, `query_dasha_transitions_in_range` | l1_chart_dashas (range-partitioned) |
| A8 T1 structural | `A8_T1_STRUCTURAL_SPEC_v1_0.md` + amendments | `query_t1_structural(chart_id, ayanamsha_id, aspect?)`, `query_aspects`, `query_shadbala`, `query_bhava_bala`, `query_ashtakavarga`, `query_yogas_active`, `query_doshas_active`, `query_near_miss_yogas`, `query_purushartha_balance` | l1_a8_* |
| A9 sade sati | `A9_SADE_SATI_SPEC_v1_0.md` | `query_sade_sati(chart_id, ayanamsha_id, date?)`, `query_sade_sati_phases_lifetime` | l1_sade_sati |
| A10 MSR | `A10_MSR_SPEC_v1_0.md` | `query_msr_signals(chart_id, ayanamsha_id, signal_class?, min_salience?, top_k?)`, `query_msr_at_date`, `query_msr_by_predicate`, `query_signal_type_registry` | l25_msr_signals + g52_signal_type_registry |
| A11 CDLM | `A11_CDLM_SPEC_v1_0.md` + amendments | `query_cdlm_static_natal`, `query_cdlm_dynamic_at_date`, `query_cdlm_cell`, `query_cdlm_pattern_clusters`, `query_cdlm_chart_summary` (with UCD fold), `query_cdlm_per_tradition`, `query_cdlm_evolution_gradients` | l25_cdlm_* |
| A12 CGM | `A12_CGM_SPEC_v1_0.md` + amendments | `query_cgm_static_graph`, `query_cgm_dynamic_at_date`, `query_cgm_motifs`, `query_cgm_topology_summary` (with UCD karmic+arudha), `query_cgm_per_graha_arc`, `query_cgm_subgraph`, `query_cgm_similar_charts`, `query_recursive_influence_reach` | l25_cgm_* |
| A13 RM | `A13_RM_SPEC_v1_0.md` | `query_rm_resonances`, `query_rm_prescriptions_for_graha`, `query_rm_dasha_windowed`, `query_rm_dosha_bundle`, `query_rm_pattern_remedies`, `query_rm_top_priority`, `query_rm_acharya_review_queue`, `query_rm_feasibility_profile`, `query_rm_similar_charts` | l25_rm_* |
| A14 UCN | RETIRED | conceptual surface UCD — see UCD entry | n/a |
| A15 Time-Synchronicity | `A15_TIME_SYNCHRONICITY_SPEC_v1_0.md` | `query_synchronicity_at_date`, `query_synchronicity_in_range`, `query_top_resonance_windows`, `query_convergence_clusters`, `query_synchronicity_peers` | l25_time_synchronicity + clusters |
| A16 Phase-Locked Anchors | `A16_PHASE_LOCKED_EVENT_ANCHORS_SPEC_v1_0.md` | `query_anchors_in_range`, `query_anchors_by_class`, `query_anchors_at_date`, `query_next_anchor`, `query_top_corroborated_anchors`, `query_anchor_causal_chain`, `query_anchor_peers`, `record_outcome` (write) | l25_phase_locked_event_anchors |

### §2.B — Synthesis (META) layer

| META | Spec | Retrieval tools | Storage |
|---|---|---|---|
| META-α Λ-LATTICE | `META_ENHANCEMENTS_SPEC_v1_0.md` §1 | `query_lattice_at_date`, `query_lattice_in_range`, `query_lattice_high_resonance_windows`, `query_lattice_peers` | mv_chart_lattice_at_date + on-demand |
| META-β Π-CATALOG | `META_ENHANCEMENTS_SPEC_v1_0.md` §2 | `query_patterns(chart_id, ayanamsha_id, pattern_kind?, severity?, active_only?, domain?)`, `query_pattern_links`, `query_pattern_peers` | l25_pattern_catalog |
| META-γ Δ-LEDGER | `META_ENHANCEMENTS_SPEC_v1_0.md` §3 | `query_divergences`, `query_divergence_at_structural_point` | l25_divergence_ledger |
| META-δ Ω-SPACE | `META_ENHANCEMENTS_SPEC_v1_0.md` §4 | `query_negative_space`, `query_distinctive_absences` | l25_negative_space_map |
| META-ε Φ-TRAIL | `META_ENHANCEMENTS_SPEC_v1_0.md` §5 | `query_derivation_trail`, `query_supporting_l1_facts`, `query_corpus_citations_for_claim`, `query_contributing_derivation_rules`, `query_claims_derived_from_l1_fact` | l25_derivation_graph_* |

### §2.C — UCD (Unified Chart Digest) — conceptual surface

| Tool | Purpose |
|---|---|
| `query_ucd(chart_id, ayanamsha_id, snapshot_type?)` | Single wide row joining A8 chart_summary + A11 chart_summary + A12 chart_topology_summary + A13 chart_summary (with all UCD folded fields: classical_archetype + karmic_signature + purushartha + arudha_divergence + master_convergence) |
| `query_ucd_archetype_assignment(chart_id, ayanamsha_id)` | Just the classical archetype match |
| `query_ucd_karmic_signature(chart_id, ayanamsha_id)` | Just the karmic axis |
| `query_ucd_master_convergence_decomposition(chart_id, ayanamsha_id)` | Decomposed coherence factors |

Backed by Postgres view `vw_chart_digest` joining the 4 chart_summary tables.

### §2.D — Write tools (M6 prospective + governance)

| Tool | Purpose |
|---|---|
| `log_prediction(prediction)` | Log a time-indexed prediction with falsifier (per M6 discipline) |
| `record_outcome(anchor_id_or_prediction_id, outcome_data)` | Record observed outcome — populates outcome_tracking_placeholder + scores against falsifier |
| `flag_disagreement(structural_point, kind, evidence)` | Add to Δ-LEDGER from interactive review |

### §2.E — Global assets

| Asset | Tools |
|---|---|
| G8 archetype library | `query_archetype_definitions(archetype_id?)`, `query_archetype_matches_for_chart(chart_id)` |
| G19 karakas | `query_natural_karakas`, `query_chara_karakas(chart_id)` |
| G27 remedy corpus | `query_remedy(remedy_id_g27, tradition?, category?)`, `query_remedies_by_target_graha`, `query_g27_coverage_audit` |
| G29 Classical Timing Rule Catalog | `query_timing_rule(rule_id)`, `query_timing_rules_for_event_class`, `query_g29_coverage_audit` |
| G52 signal_type_registry | `query_signal_type(signal_predicate)`, `query_signal_predicates_by_factor` |

## §3 — LLM-facing tool description standard

Every MCP tool registration emits a description string the model sees in its tool list. The description must include:

1. **One-sentence purpose** (what the tool does)
2. **Class of question it answers** (when LLM should reach for it)
3. **Required inputs + defaults**
4. **Output highlights** (what the model gets back)
5. **Cross-tool composition hints** (when to chain with other tools)
6. **Tier note** (which tier this tool is available to)

Example for `query_lattice_at_date`:

```
purpose: Return the unified structural lattice for a chart at a specific date.
when_to_use: For "tell me about date X" questions or any moment-in-time chart read.
inputs: chart_id (required), date_iso (required), ayanamsha_id (default lahiri), tier (default client), channel (default chat).
output: One row joining active dasha (3 systems) + CDLM dynamic snapshot + CGM dynamic snapshot + RM active prescriptions + A15 synchronicity + A16 anchors + A8 transit yogas + A9 Sade Sati + A4 panchanga.
compose_with: query_derivation_trail when the LLM wants to show its work for any specific claim from the lattice.
tier: all (super_admin / acharya / client) — tier-conditioned fields filtered automatically.
```

This description appears in the tool registration; the LLM at retrieval time chooses the right tool based on these.

## §4 — Implementation checklist per asset

For each asset (A1-A16 + META), implementation is not complete until:

- [ ] Spec authored + locked
- [ ] Storage tables / views created with declared schema
- [ ] Writer pipeline implemented + two-pass verified
- [ ] **Retrieval tools registered in this register** (this is the new gate)
- [ ] Zod input + output schemas authored
- [ ] LLM-facing description written
- [ ] Channel adapters tested (chat/report/visual/audio/dashboard)
- [ ] Tier filtering tested (super_admin/acharya/client)
- [ ] Citation envelope confirmed populated
- [ ] Cross-asset linkage tested (e.g., derivation_trail_pointer_id resolves)
- [ ] Integration test: LLM-as-judge can use the tool to answer a representative question
- [ ] CAPABILITY_MANIFEST.json updated with tool entry

This checklist is the acceptance criteria for any A1-A16 + META implementation session.

## §5 — Implementation amendment to CAPABILITY_MANIFEST.json

Every retrieval tool registered here MUST appear in `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` per the existing manifest discipline (cutover 2026-04-27). The manifest is the source of truth for what's wired up; this register is the source of truth for what SHOULD be wired up. Drift between them is a `drift_detector.py` failure.

## §6 — Tool count summary

By the time all 15 writer assets + 5 META + 5 G + UCD + write tools are registered:

- A1 through A16 writer-tool families: ~80 tools
- META α-ε retrieval families: ~15 tools
- UCD conceptual surface: 4 tools
- G-series tools: ~10 tools
- Write tools (M6 + governance): ~5 tools

**Total retrieval surface: ~115 tools.** Currently shipped: 55 (per UDA campaign). Remaining: ~60 to register over the implementation arc.

## §7 — Final locked surface

1. Every asset A1-A16 + META + G + UCD has its retrieval tool registration documented here
2. Standard input/output envelope mandatory
3. Standard channel adapter conformance (5 channels)
4. Standard tier filtering (3 tiers)
5. Citation envelope mandatory in every output
6. Cross-asset FK exposure mandatory
7. LLM-facing description format codified
8. Implementation checklist per asset codified
9. CAPABILITY_MANIFEST.json sync mandatory
10. ~115-tool target retrieval surface

---

*End of RETRIEVAL_INTERFACE_REGISTER_v1_0.md — LOCKED 2026-05-29.*
