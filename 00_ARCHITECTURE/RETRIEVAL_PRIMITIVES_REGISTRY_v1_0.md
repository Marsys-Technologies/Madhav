---
artifact: RETRIEVAL_PRIMITIVES_REGISTRY
canonical_id: RETRIEVAL_PRIMITIVES_REGISTRY
version: 1.0
status: CURRENT
created: 2026-06-28
author: Claude Code (D8 governance wave)
classification: D8 governance deliverable — versioned registry of all retrieval capability URIs
parent_brief: CLAUDECODE_BRIEF_RETRIEVAL_D8_EVAL_SEAL_v1_1.md §3.3
implements: §3.3 — drift_detector.py / schema_validator.py coverage for retrieval primitives
drift_detector_check: each URI's source_file must exist, export CapabilityDescriptor with required_inputs declared, contain no literal native chart_id, and have chart_id in required_inputs if scope=per_chart
changelog:
  - v1.0 (2026-06-28): Initial registry from D1–D7 waves + D-PROFILES. ~61+ URIs across L0–L5 + router, MARO, D6, D7.
---

# RETRIEVAL PRIMITIVES REGISTRY v1.0

> **What this is.** A versioned `.md` artifact listing every registered capability URI,
> its source file, wave, and status. This is the surface `drift_detector.py` and
> `schema_validator.py` can check — filling the gap identified in D8 §3.3.
>
> **Governance check spec (for schema_validator.py):**
> For every URI in this registry, confirm the source file:
> (a) exists at the stated path
> (b) exports a `CapabilityDescriptor` with `required_inputs` declared
> (c) has no literal native chart_id `482012f1-…`
> (d) has `chart_id` in `required_inputs` for scope=`per_chart` capabilities
>
> **Living artifact.** Add new URIs here when new capabilities are registered.
> Version bump required on any change.

---

## L0 Brahmagyan capabilities (wave D5.0)

| URI | Source file | Scope | Wave | Status |
|---|---|---|---|---|
| `marsys://tool/L0/brahmagyan/asset-registry-all` | `registry/layers/L0_brahmagyan/asset_registry_all.ts` | global | D5.0 | CURRENT |
| `marsys://tool/L0/brahmagyan/asset-registry` | `registry/layers/L0_brahmagyan/asset_registry_l0.ts` | global | D5.0 | CURRENT |
| `marsys://resource/ephemeris-cache/native-lifetime` | `registry/layers/L0_brahmagyan/ephemeris_cache_native_lifetime.ts` | global | D5.0 | CURRENT (documented exception: native-scoped by design) |
| `marsys://resource/ephemeris-cache/year` | `registry/layers/L0_brahmagyan/ephemeris_cache_year.ts` | global | D5.0 | CURRENT |
| `marsys://tool/L0/brahmagyan/intent-classify` | `registry/layers/L0_brahmagyan/intent_classify.ts` | global | D5.0 | CURRENT |
| `marsys://tool/L0/brahmagyan/list-entities` | `registry/layers/L0_brahmagyan/list_entities.ts` | global | D5.0 | CURRENT |
| `marsys://tool/L0/brahmagyan/query-aspects-at-time` | `registry/layers/L0_brahmagyan/query_aspects_at_time.ts` | per_chart | D5.0 | CURRENT |
| `marsys://tool/L0/brahmagyan/query-classical-texts` | `registry/layers/L0_brahmagyan/query_classical_texts.ts` | global | D5.0 | CURRENT |
| `marsys://tool/L0/brahmagyan/query-dosha-catalog` | `registry/layers/L0_brahmagyan/query_dosha_catalog.ts` | global | D5.0 | CURRENT |
| `marsys://tool/L0/brahmagyan/query-planet-position` | `registry/layers/L0_brahmagyan/query_planet_position.ts` | global | D5.0 | CURRENT |
| `marsys://tool/L0/brahmagyan/query-planet-transit` | `registry/layers/L0_brahmagyan/query_planet_transit.ts` | global | D5.0 | CURRENT |
| `marsys://tool/L0/brahmagyan/query-remedy-corpus` | `registry/layers/L0_brahmagyan/query_remedy_corpus.ts` | global | D5.0 | CURRENT |
| `marsys://tool/L0/brahmagyan/query-retrograde-periods` | `registry/layers/L0_brahmagyan/query_retrograde_periods.ts` | global | D5.0 | CURRENT |
| `marsys://tool/L0/brahmagyan/query-yoga-catalog` | `registry/layers/L0_brahmagyan/query_yoga_catalog.ts` | global | D5.0 | CURRENT |
| `marsys://tool/L0/brahmagyan/resolve-entity` | `registry/layers/L0_brahmagyan/resolve_entity.ts` | global | D5.0 | CURRENT |

**L0 count: 15 capabilities**

---

## L1 Gaṇita capabilities (wave D5.1)

| URI | Source file | Scope | Wave | Status |
|---|---|---|---|---|
| `marsys://tool/L1/ganita/coverage-matrix` | `registry/layers/L1_ganita/coverage_matrix.ts` | per_chart | D5.1 | CURRENT |
| `marsys://tool/L1/ganita/get-argala` | `registry/layers/L1_ganita/get_argala.ts` | per_chart | D5.1 | CURRENT |
| `marsys://tool/L1/ganita/get-ashtakavarga` | `registry/layers/L1_ganita/get_ashtakavarga.ts` | per_chart | D5.1 | CURRENT |
| `marsys://tool/L1/ganita/get-aspects` | `registry/layers/L1_ganita/get_aspects.ts` | per_chart | D5.1 | CURRENT |
| `marsys://tool/L1/ganita/get-avasthas` | `registry/layers/L1_ganita/get_avasthas.ts` | per_chart | D5.1 | CURRENT |
| `marsys://tool/L1/ganita/get-bhava-bala` | `registry/layers/L1_ganita/get_bhava_bala.ts` | per_chart | D5.1 | CURRENT |
| `marsys://tool/L1/ganita/get-dashas` | `registry/layers/L1_ganita/get_dashas.ts` | per_chart | D5.1 | CURRENT |
| `marsys://tool/L1/ganita/get-dignity` | `registry/layers/L1_ganita/get_dignity.ts` | per_chart | D5.1 | CURRENT |
| `marsys://tool/L1/ganita/get-dispositors` | `registry/layers/L1_ganita/get_dispositors.ts` | per_chart | D5.1 | CURRENT |
| `marsys://tool/L1/ganita/get-divisionals` | `registry/layers/L1_ganita/get_divisionals.ts` | per_chart | D5.1 | CURRENT |
| `marsys://tool/L1/ganita/get-eclipse-flags` | `registry/layers/L1_ganita/get_eclipse_flags.ts` | per_chart | D5.1 | CURRENT |
| `marsys://tool/L1/ganita/get-karakas` | `registry/layers/L1_ganita/get_karakas.ts` | per_chart | D5.1 | CURRENT |
| `marsys://tool/L1/ganita/get-panchanga` | `registry/layers/L1_ganita/get_panchanga.ts` | per_chart | D5.1 | CURRENT |
| `marsys://tool/L1/ganita/get-positions` | `registry/layers/L1_ganita/get_positions.ts` | per_chart | D5.1 | CURRENT |
| `marsys://tool/L1/ganita/get-sade-sati` | `registry/layers/L1_ganita/get_sade_sati.ts` | per_chart | D5.1 | CURRENT |
| `marsys://tool/L1/ganita/get-sensitive-points` | `registry/layers/L1_ganita/get_sensitive_points.ts` | per_chart | D5.1 | CURRENT |
| `marsys://tool/L1/ganita/get-strength` | `registry/layers/L1_ganita/get_strength.ts` | per_chart | D5.1 | CURRENT |
| `marsys://tool/L1/ganita/get-tajik` | `registry/layers/L1_ganita/get_tajik.ts` | per_chart | D5.1 | CURRENT |
| `marsys://tool/L1/ganita/get-tara-chandra-bala` | `registry/layers/L1_ganita/get_tara_chandra_bala.ts` | per_chart | D5.1 | CURRENT |
| `marsys://tool/L1/ganita/get-yoga-dosha` | `registry/layers/L1_ganita/get_yoga_dosha.ts` | per_chart | D5.1 | CURRENT |

**L1 count: 20 capabilities** (including coverage_matrix)

---

## L2 Bodha capabilities (wave D5.2)

| URI | Source file | Scope | Wave | Status |
|---|---|---|---|---|
| `marsys://tool/L2/bodha/query-contradictions` | `registry/layers/L2_bodha/query_contradictions.ts` | per_chart | D5.2 | CURRENT |
| `marsys://tool/L2/bodha/query-domain-reading` | `registry/layers/L2_bodha/query_domain_reading.ts` | per_chart | D5.2 | CURRENT |
| `marsys://tool/L2/bodha/query-quality-scorecard` | `registry/layers/L2_bodha/query_quality_scorecard.ts` | per_chart | D5.2 | CURRENT |
| `marsys://tool/L2/bodha/query-remedies` | `registry/layers/L2_bodha/query_remedies.ts` | per_chart | D5.2 | CURRENT |
| `marsys://tool/L2/bodha/query-signals` | `registry/layers/L2_bodha/query_signals.ts` | per_chart | D5.2 | CURRENT |
| `marsys://tool/L2/bodha/query-ucd` | `registry/layers/L2_bodha/query_ucd.ts` | per_chart | D5.2 | CURRENT |
| `marsys://tool/L2/bodha/register-d4-graph` | `registry/layers/L2_bodha/register_d4_graph.ts` | per_chart | D4 | CURRENT |
| `marsys://tool/L2/bodha/traverse-chart-graph` | `registry/layers/L2_bodha/traverse_chart_graph.ts` | per_chart | D4 | CURRENT |

**L2 count: 8 capabilities**

---

## L3 Kāla capabilities (wave D5.3)

| URI | Source file | Scope | Wave | Status |
|---|---|---|---|---|
| `marsys://tool/L3/kala/query-convergence-windows` | `registry/layers/L3_kala/query_convergence_windows.ts` | per_chart | D5.3 | CURRENT |
| `marsys://tool/L3/kala/query-life-arc` | `registry/layers/L3_kala/query_life_arc.ts` | per_chart | D5.3 | CURRENT |
| `marsys://tool/L3/kala/query-obstruction-periods` | `registry/layers/L3_kala/query_obstruction_periods.ts` | per_chart | D5.3 | CURRENT |
| `marsys://tool/L3/kala/query-projections` | `registry/layers/L3_kala/query_projections.ts` | per_chart | D5.3 | CURRENT |
| `marsys://tool/L3/kala/query-temporal-activation` | `registry/layers/L3_kala/query_temporal_activation.ts` | per_chart | D5.3 | CURRENT |
| `marsys://tool/L3/kala/query-temporal-view` | `registry/layers/L3_kala/query_temporal_view.ts` | per_chart | D5.3 | CURRENT |
| `marsys://tool/L3/kala/call-service-wrappers` | `registry/layers/L3_kala/call_service_wrappers.ts` | per_chart | D5.3 | CURRENT |

**L3 count: 7 capabilities**

---

## L4 Phala capabilities (wave D5.4)

| URI | Source file | Scope | Wave | Status |
|---|---|---|---|---|
| `marsys://tool/L4/phala/query-domain-result` | `registry/layers/L4_phala/query_domain_result.ts` | per_chart | D5.4 | CURRENT |
| `marsys://tool/L4/phala/query-phala-calibration` | `registry/layers/L4_phala/query_phala_calibration.ts` | per_chart | D5.4 | CURRENT |
| `marsys://tool/L4/phala/query-predictive-anchors` | `registry/layers/L4_phala/query_predictive_anchors.ts` | per_chart | D5.4 | CURRENT |

**L4 count: 3 capabilities**

---

## L5 Mīmāṃsā capabilities (wave D5.5)

| URI | Source file | Scope | Wave | Status |
|---|---|---|---|---|
| `marsys://tool/L5/mimamsa/query-calibration` | `registry/layers/L5_mimamsa/query_calibration.ts` | per_chart | D5.5 | CURRENT |
| `marsys://tool/L5/mimamsa/query-insights` | `registry/layers/L5_mimamsa/query_insights.ts` | per_chart | D5.5 | CURRENT |
| `marsys://tool/L5/mimamsa/query-manifestation-grammar` | `registry/layers/L5_mimamsa/query_manifestation_grammar.ts` | per_chart | D5.5 | CURRENT |
| `marsys://tool/L5/mimamsa/query-predictions` | `registry/layers/L5_mimamsa/query_predictions.ts` | per_chart | D5.5 | CURRENT |
| `marsys://tool/L5/mimamsa/query-signal-families` | `registry/layers/L5_mimamsa/query_signal_families.ts` | per_chart | D5.5 | CURRENT |

**L5 count: 5 capabilities**

---

## D2 Router capability (wave D2)

| URI | Source file | Scope | Wave | Status |
|---|---|---|---|---|
| `marsys://tool/router/route` | `registry/layers/router_registration.ts` | per_chart | D2 | CURRENT |

**Router count: 1 capability**

---

## D-PROFILES MARO capability (wave D-PROFILES)

| URI | Source file | Scope | Wave | Status |
|---|---|---|---|---|
| `marsys://tool/maro/orchestrate` | `registry/layers/dprofiles_registration.ts` | per_chart | D-PROFILES | CURRENT |

**D-PROFILES count: 1 capability**

---

## D6 Synergy capabilities (wave D6)

| URI | Source file | Scope | Wave | Status |
|---|---|---|---|---|
| `marsys://tool/synergy/pipeline` | `registry/layers/register_d6_synergy.ts` | global | D6 | CURRENT |
| `marsys://tool/synergy/cross-layer` | `registry/layers/register_d6_synergy.ts` | per_chart | D6 | CURRENT |

**D6 count: 2 capabilities**

---

## D7 Channel capabilities (wave D7)

| URI | Source file | Scope | Wave | Status |
|---|---|---|---|---|
| `marsys://tool/channel/mcp-wiring` | `registry/layers/register_d7_channel.ts` | global | D7 | CURRENT |
| `marsys://tool/channel/chat-dispatch` | `registry/layers/register_d7_channel.ts` | global | D7 | CURRENT (migration_status: PENDING) |

**D7 count: 2 capabilities**

---

## MCP bridge (cross-wave)

| URI | Source file | Scope | Wave | Status |
|---|---|---|---|---|
| `marsys://bridge/mcp-capability` | `registry/mcp_capability_bridge.ts` | global | D7 | CURRENT |

---

## Registry totals

| Layer/Wave | Count |
|---|---|
| L0 Brahmagyan | 15 |
| L1 Gaṇita | 20 |
| L2 Bodha | 8 |
| L3 Kāla | 7 |
| L4 Phala | 3 |
| L5 Mīmāṃsā | 5 |
| D2 Router | 1 |
| D-PROFILES MARO | 1 |
| D6 Synergy | 2 |
| D7 Channel | 2 |
| MCP Bridge | 1 |
| **Total** | **65** |

---

## Drift detector check spec

Add to `platform/scripts/governance/schema_validator.py`:

```python
# RETRIEVAL_PRIMITIVES check (D8 §3.3)
# For every URI in RETRIEVAL_PRIMITIVES_REGISTRY_v1_0.md:
#   (a) source_file exists at the stated path (relative to platform/src/lib/retrieval/)
#   (b) source_file exports a CapabilityDescriptor with required_inputs declared
#   (c) no literal native chart_id '482012f1-710e-4a25-994a-93821f5871aa' in source_file
#   (d) if scope=per_chart: 'chart_id' is in required_inputs
#
# Implementation note: parse this .md file for the table rows, then check each
# source_file path and run a text scan for the forbidden patterns.
```

---

*End of RETRIEVAL_PRIMITIVES_REGISTRY v1.0 (2026-06-28 — D8 governance wave).*
*65 capabilities registered across L0–L5 + D2, D-PROFILES, D6, D7.*
*All source files in platform/src/lib/retrieval/registry/.*
