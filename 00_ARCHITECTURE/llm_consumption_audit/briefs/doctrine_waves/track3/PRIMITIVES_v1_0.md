---
artifact: TRACK3_PRIMITIVES
type: SOURCE DRAFT (mirrors platform/src/lib/vidhi/registry_data.ts VIDHI_PRIMITIVES +
  platform/python-sidecar/pipeline/orchestrator/writers/bg_vidhi_primitives.py)
version: 1.0
status: DRAFT
count: 37
---

# Vidhi primitives (37 atoms)

Design §3 targets "~30"; this catalog carries 7 extra atoms so that every §B0.4
mandatory-surface tag and all four CR-27 improvisation instances (+ the CR-36 specimen)
are each satisfied by a named, floor-consumed primitive — see `CR27_MAPPING_v1_0.md`.

Every `known_gap` below cites only an **OPEN** or **LOGGED** CR per BRIEF_D2.md §B0.1 —
never a CLOSED one (`platform/src/lib/vidhi/cr_status.ts` is the enforced allowlist; see
that file's header for the documented CR-55 status conflict this catalog does not cite).

| primitive_id | category | live_tool | fallback_face | known_gap | mandatory_tags | cr27_prevents |
|---|---|---|---|---|---|---|
| `bhava_condition` | structural | `ganita_structural_get` | `ganita_chart_facts_get(category=bhava)` | — | — | — |
| `bhavesha_condition` | structural | `ganita_condition_get` | `ganita_structural_get` | — | — | — |
| `karaka_condition` | structural | `ganita_condition_get` | `ganita_strength_get` | — | — | CR-36 |
| `from_moon_view` | structural | `ganita_chart_facts_get` | `ganita_structural_get` | — | — | — |
| `varga_ratification` | signal | `bodha_signals_get` | `ganita_chart_facts_get(divisional_chart=…)` | — (CR-57 CLOSED_WITH_EVIDENCE, live) | varga_ratification_divergence | CR-36 |
| `special_lagna_read` | structural | `ganita_special_lagnas_get` | `query_special_lagnas` | CR-16 | — | — |
| `chara_karaka_read` | structural | `ganita_condition_get` | `ganita_structural_get` | — | — | — |
| `dhana_yoga_scan` | doctrine | `ganita_yoga_firings_get` | `ganita_yogas_get` | CR-56 | — | CR-27c |
| `nbry_scan` | doctrine | `ganita_yogas_get` | `ganita_condition_get` | CR-59 | — | — |
| `wealth_loss_mechanism_scan` | signal | `bodha_signals_get` | `judgment_query` | CR-54 | — | CR-27c |
| `dasha_spine_lord_capability` | temporal | `ganita_dasha_lord_capability_get` | `ganita_dashas_get` | — (CR-60 CLOSED_WITH_EVIDENCE, live) | dasha_lord_capability | CR-36, CR-27a |
| `taranga_curve` | temporal | `kala_temporal_bundle` | `kala_windows_get` | CR-66 | — | — |
| `lel_retrodiction` | temporal | `lel_query` | `mimamsa_lel_query` | CR-68 | — | — |
| `intervention_synthesis` | remedy | `bodha_remedies_get` | `get_remedies` | CR-69 | — | CR-27b |
| `positions_snapshot` | structural | `ganita_positions_get` | `get_positions` | — | — | — |
| `dignity_scan` | strength | `ganita_condition_get` | `ganita_strength_get` | — | — | — |
| `shadbala_rank` | strength | `ganita_strength_get` | `bodha_chart_digest_get` | — | — | — |
| `nakshatra_semantics` | signal | `ganita_nakshatra_get` | `bodha_signals_get(signal_type_class=nakshatra_semantic)` | CR-64 | — | CR-27d |
| `sensitive_degree_check` | structural | `ganita_sensitive_degrees_get` | `ganita_chart_facts_get` | — (R-47 CLOSED, live) | sensitive_degree | — |
| `divisional_facts` | structural | `ganita_chart_facts_get` | — | — (CR-58 CLOSED_WITH_EVIDENCE, live) | varga_hora_class | — |
| `dasha_window` | temporal | `ganita_dasha_periods_get` | `ganita_dashas_get` | — | — | — |
| `yoga_activation_scan` | temporal | `kala_yoga_activation_get` | `yoga_activation_by_dasha` | CR-37 | — | — |
| `transit_window_scan` | temporal | `kala_windows_get` | `query_planet_transit` | — | — | — |
| `muhurta_scan` | temporal | `kala_muhurta_get` | `muhurta_finder` | — | — | — |
| `mechanism_read` | signal | `get_cgm_subgraph` | `bodha_graph_subgraph_get` | CR-24 | — | CR-27c |
| `arudha_read` | signal | `ganita_condition_get` | `bodha_signals_get(frame=arudha)` | CR-61 | — | — |
| `dosha_scan` | doctrine | `ref_doshas_get` | `bodha_signals_get(signal_type_class=dosha_label)` | CR-73 | — | — |
| `statistical_context` | utility | `mimamsa_calibration_get` | `bodha_quality_get` | — (L5 structural-mode by design) | — | — |
| `remedy_scan` | remedy | `bodha_remedies_search` | `query_remedies_for_chart` | CR-67 | — | CR-27b |
| `contradiction_scan` | utility | `bodha_discoveries_get` | `get_signals` | — | — | — |
| `chalit_cusp_read` | structural | `ganita_chart_facts_get` | `ganita_structural_get` | — | chalit_cusp | — |
| `sudarshana_agreement_check` | signal | `bodha_signals_get` | `ganita_chart_facts_get` | — | sudarshana_agreement | — |
| `bhavat_bhavam_check` | signal | `bodha_signals_get` | `ganita_structural_get` | — | bhavat_bhavam | — |
| `bhava_bala_scan` | strength | `ganita_strength_get` | `ganita_structural_get` | — | bhava_bala | — |
| `ashtakavarga_scan` | structural | `ganita_chart_facts_get` | `ganita_structural_get` | — | ashtakavarga_bindu | — |
| `karakamsa_read` | structural | `ganita_condition_get` | `ganita_special_lagnas_get` | — | karakamsa | — |
| `kp_cusp_sublord_read` | structural | `ganita_chart_facts_get` | `ganita_structural_get` | CR-30 | kp_cusp_sublord | CR-36 |

## §B0.4 mandatory-surface tag coverage (all 11 present)

| §B0.4 item | tag | carrier primitive |
|---|---|---|
| chalit/bhava-cusp facts | `chalit_cusp` | `chalit_cusp_read` |
| Sudarśana agreement | `sudarshana_agreement` | `sudarshana_agreement_check` |
| Bhavat Bhavam | `bhavat_bhavam` | `bhavat_bhavam_check` |
| bhāva-bala atoms (`house_bhava_bala_total`) | `bhava_bala` | `bhava_bala_scan` |
| `ashtakavarga_bindu_sign` | `ashtakavarga_bindu` | `ashtakavarga_scan` |
| D2 `varga_hora_class` via `divisional_facts` | `varga_hora_class` | `divisional_facts` |
| `karakamsa_position` | `karakamsa` | `karakamsa_read` |
| real KP cusps + sub-lords | `kp_cusp_sublord` | `kp_cusp_sublord_read` |
| `dasha_lord_capability` | `dasha_lord_capability` | `dasha_spine_lord_capability` |
| `varga_ratification_divergence` | `varga_ratification_divergence` | `varga_ratification` |
| sensitive-degree checks | `sensitive_degree` | `sensitive_degree_check` |

All 11 carriers are consumed by `floor(wealth_deepdive)` (see `FLOORS_v1_0.md`) — asserted
by `platform/src/lib/vidhi/__tests__/floor_coverage.test.ts`.
