# Ω7 — Dark-Corpus Report (Elevation Campaign v2.1, Stream γ · PŪRṆA)

*Generated 2026-07-25T07:51:42.908789Z · target chart `482012f1-710e-4a25-994a-93821f5871aa` (native — Abhisek Mohanty)*

> **What this measures.** Of every concept the instrument *computes and stores non-empty* for this chart in a flagship domain, how many were **never surfaced** across a fresh execution of the FROZEN dark-corpus replay set (naive + narrow + expert phrasings) through the sealed evaluator harness. This is the direct measurement of the native's ~20% unknown-unknown. **Target: zero.** A dark concept = computed, non-empty, and still not served.

## Headline

| Domain | Served (non-empty) | Dark | Bright | Coverage | Replay runs |
|---|---|---|---|---|---|
| **wealth** | 12,450 | **11,755** | 695 | 5.58% | 21/21 |
| **career** | 12,455 | **11,400** | 1,055 | 8.47% | 21/21 |

The dark count is an **upper bound** (see method): composed-reading tools emit prose that may carry a concept's substance without its fact_id/token, so true coverage is ≥ reported. Even so, the signal is unambiguous — a naive→expert answer corpus surfaces only a few percent of what the instrument holds. The number is honest and is meant to trend toward zero across campaign iterations.

## Wealth — dark-corpus breakdown

- **Served universe (non-empty for this chart):** 12,450
- **Dark:** 11,755  ( tool-never-called 1,351 · substance-absent 10,404 )
- **Bright (surfaced ≥1×):** 695  (5.58% coverage)
- **Replay coverage:** 21/21 questions ran with ≥1 live chart-tool call.
- **Tools the corpus actually called:** Bash, ToolSearch, assess_wealth, chart_snapshot, ganita_chart_facts_get, ganita_dasha_lord_capability_get, ganita_dasha_periods_get, ganita_dashas_get, ganita_positions_get, ganita_special_lagnas_get, ganita_strength_get, ganita_structural_get, ganita_yoga_firings_get, graha_portrait, judgment_query, phala_outlook_get, reading_notes_get

**Dark by layer:**  l1=10,360 · l2=1,277 · l3=77 · l4=24 · l5=17

**Dark by serving tool (top 12):**

| serving tool | dark concepts |
|---|---|
| `ganita_chart_facts_get` | 10,328 |
| `bodha_signals_get` | 1,227 |
| `ganita_dashas_get` | 40 |
| `ganita_positions_get` | 32 |
| `bodha_graph_traverse_get` | 22 |
| `kala_windows_get` | 20 |
| `mimamsa_insight_get` | 14 |
| `bodha_graph_subgraph_get` | 10 |
| `phala_anchors_get` | 9 |
| `bodha_discoveries_get` | 7 |
| `kala_yoga_activation_get` | 6 |
| `gochara_forecast_get` | 5 |

**Dark by concept family (top 15) — the actionable slice:**

| concept family | dark |
|---|---|
| `l1.fact` | 10,328 |
| `l2.msr_signal_type` | 1,195 |
| `l3.dasha_level` | 32 |
| `l1.varga` | 32 |
| `l2.msr_signal_class` | 19 |
| `l2.cgm_edge_relclass` | 11 |
| `l2.cgm_edge_type` | 10 |
| `l3.kala_avadhi_quality` | 10 |
| `l4.phala_anchor_event` | 8 |
| `l3.dasha_system` | 8 |
| `l2.msr_signature_class` | 7 |
| `l2.cgm_node_type` | 7 |
| `l2.msr_tradition` | 6 |
| `l3.kala_activation_sig` | 6 |
| `l5.insight_type` | 6 |

Full dark + bright concept_id lists: `DARK_CORPUS_wealth_482012f1_concepts_v1_0.json`

## Career — dark-corpus breakdown

- **Served universe (non-empty for this chart):** 12,455
- **Dark:** 11,400  ( tool-never-called 1,369 · substance-absent 10,031 )
- **Bright (surfaced ≥1×):** 1,055  (8.47% coverage)
- **Replay coverage:** 21/21 questions ran with ≥1 live chart-tool call.
- **Tools the corpus actually called:** assess_career, assess_career (jq-extracted from saved file), bodha_domain_reading_get, bodha_mechanisms_get, ganita_chart_facts_get, ganita_dasha_lord_capability_get, ganita_dasha_periods_get, ganita_positions_get, ganita_sade_sati_get, ganita_strength_get, ganita_structural_get, ganita_yoga_firings_get, graha_portrait, judgment_query, kala_life_arc_get, kala_windows_get, query, synth_tail_divergence_get

**Dark by layer:**  l1=10,006 · l2=1,276 · l3=75 · l4=25 · l5=18

**Dark by serving tool (top 12):**

| serving tool | dark concepts |
|---|---|
| `ganita_chart_facts_get` | 9,974 |
| `bodha_signals_get` | 1,227 |
| `ganita_dashas_get` | 41 |
| `ganita_positions_get` | 32 |
| `bodha_graph_traverse_get` | 22 |
| `kala_windows_get` | 18 |
| `mimamsa_insight_get` | 15 |
| `bodha_graph_subgraph_get` | 10 |
| `phala_anchors_get` | 10 |
| `bodha_discoveries_get` | 7 |
| `kala_yoga_activation_get` | 6 |
| `gochara_forecast_get` | 5 |

**Dark by concept family (top 15) — the actionable slice:**

| concept family | dark |
|---|---|
| `l1.fact` | 9,974 |
| `l2.msr_signal_type` | 1,195 |
| `l3.dasha_level` | 32 |
| `l1.varga` | 32 |
| `l2.msr_signal_class` | 19 |
| `l2.cgm_edge_relclass` | 11 |
| `l2.cgm_edge_type` | 10 |
| `l3.dasha_system` | 9 |
| `l3.kala_avadhi_quality` | 9 |
| `l4.phala_anchor_event` | 8 |
| `l2.msr_signature_class` | 7 |
| `l2.cgm_node_type` | 7 |
| `l2.msr_tradition` | 6 |
| `l3.kala_activation_sig` | 6 |
| `l5.insight_type` | 6 |

Full dark + bright concept_id lists: `DARK_CORPUS_career_482012f1_concepts_v1_0.json`

## Method (faithful to the sealed evaluator harness)

Fresh general-purpose sub-agent per replay question, sealed-harness system framing (SEALED_EVALUATOR_HARNESS_v1_0.md #1): no charter text, no EL vocabulary, no concept names, no mention of dossier/Lane-Omega. One user turn per run; the agent chose its own tools. A methodologically-neutral tool-access + transcript-capture instruction was appended (plumbing only) — see deviations.

**Matching rule.** Faithful to the harness grader: each served concept maps to one serving tool + sample fact_ids + a distinguishing concept token. A concept is BRIGHT iff, across the UNION of all replay transcripts, its serving tool was actually called AND (one of its sample fact_ids appears verbatim in that tool's raw result OR its distinguishing token appears in that result). Else DARK. Two dark sub-reasons: tool_never_called (serving tool absent from the entire corpus) and substance_absent (tool called but concept substance never surfaced).

**Bias direction.** Conservative toward OVER-reporting dark: fact_id evidence is only 3 samples per concept, and composed-reading tools (assess_*, judgment_query) emit prose that may carry a concept's substance without its fact_id or exact token. So the true bright set is >= reported; the dark count is an UPPER bound. This matches Omega-7's intent (silent omission is a build failure — err toward flagging, not hiding).

## Deviations from the sealed harness (declared, per §0 no-silent-omission)

- No Agent-SDK transcript interceptor was available, so each consumer wrote its own tool-call log (tool, arguments, result_raw verbatim) to a file rather than the harness capturing it externally. The capture instruction reveals nothing about what is measured (no concept/dossier vocabulary).
- A neutral tool-access note (the chart tools are under mcp__marsys-jis-direct__ and need no auth) was appended after an early run (DC-W-09 first attempt) failed by confusing the auth-gated claude.ai MARSYS-JIS connector with the working direct namespace. Note names a spread of example tools, not a routing hint.
- Second chart 1c826d5a NOT executed (time budget) — see coverage.chart_1c826d5a_status.

## Coverage / what is NOT covered

- **chart_482012f1_status:** EXECUTED (both flagship domains)
- **chart_1c826d5a_status:** NOT EXECUTED — time budget; queued for next Omega-7 iteration
