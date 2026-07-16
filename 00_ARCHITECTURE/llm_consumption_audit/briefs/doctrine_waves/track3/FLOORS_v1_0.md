---
artifact: TRACK3_FLOORS
type: SOURCE DRAFT (mirrors platform/src/lib/vidhi/registry_data.ts VIDHI_INTENT_FLOORS +
  platform/python-sidecar/pipeline/orchestrator/writers/bg_vidhi_floors.py)
version: 1.0
status: DRAFT
count: 8 intent classes
---

# Vidhi intent-class floors (8/8)

Every intent class the compiler recognizes has a floor — DONE-CHECK per BRIEF_D2.md §F1
Lane V-1. `acharya_floor` = the non-skippable classical checklist; `machine_band` =
computation-only differentiator content (design §3). `depth=retrieval` compiles only the
`acharya_floor` items whose primitive `category=structural`; `depth=structure` compiles
the full `acharya_floor`; `depth=deepdive` compiles both bands.

## floor(wealth_deepdive) — flagship / §G master-acceptance target

Matches `DOCTRINE_CAMPAIGN_DESIGN_v1_0.md §3`'s worked example **verbatim** for its 14
named atoms (items 1-4, 10, 13-17, 22-26 below are exactly those atoms — reordered to
group by band/theme, args unchanged); items 5-9, 11-12, 18-21 are this lane's §B0.4 +
CR-27 extension, making this one floor alone satisfy every §B0.4 tag and every CR-27
instance for the flagship domain.

| order | band | primitive_id | args_override |
|---|---|---|---|
| 1 | acharya_floor | `bhava_condition` | `{house: 2}` |
| 2 | acharya_floor | `bhavesha_condition` | `{house: 2}` |
| 3 | acharya_floor | `karaka_condition` | `{karaka: 'jupiter'}` |
| 4 | acharya_floor | `from_moon_view` | — |
| 5 | acharya_floor | `chalit_cusp_read` | — |
| 6 | acharya_floor | `bhava_bala_scan` | — |
| 7 | acharya_floor | `ashtakavarga_scan` | — |
| 8 | acharya_floor | `sensitive_degree_check` | — |
| 9 | acharya_floor | `divisional_facts` | `{varga: 'D2'}` |
| 10 | acharya_floor | `varga_ratification` | `{vargas: ['D2','D9','D11']}` |
| 11 | acharya_floor | `karakamsa_read` | — |
| 12 | acharya_floor | `kp_cusp_sublord_read` | — |
| 13 | acharya_floor | `special_lagna_read` | `{lagnas: ['indu','sree']}` |
| 14 | acharya_floor | `chara_karaka_read` | `{chara_karaka: 'AmK'}` |
| 15 | acharya_floor | `dhana_yoga_scan` | `{domain: 'wealth'}` |
| 16 | acharya_floor | `nbry_scan` | — |
| 17 | acharya_floor | `wealth_loss_mechanism_scan` | `{domain: 'wealth'}` |
| 18 | acharya_floor | `sudarshana_agreement_check` | — |
| 19 | acharya_floor | `bhavat_bhavam_check` | — |
| 20 | acharya_floor | `nakshatra_semantics` | — |
| 21 | acharya_floor | `mechanism_read` | — |
| 22 | machine_band | `dasha_spine_lord_capability` | — |
| 23 | machine_band | `taranga_curve` | `{domain: 'wealth'}` |
| 24 | machine_band | `lel_retrodiction` | `{domain: 'wealth'}` |
| 25 | machine_band | `statistical_context` | — |
| 26 | machine_band | `intervention_synthesis` | — |

CR-27 coverage: CR-27a, CR-27b, CR-27c, CR-27d, CR-36 (see `CR27_MAPPING_v1_0.md`).

## floor(career_deepdive)

D10/D9 multi-varga per CR-62's wealth {D1,D2,D9,D11} / career {D1,D9,D10} map.

`bhava_condition(10)` · `bhavesha_condition(10)` · `karaka_condition(sun)` ·
`divisional_facts(D10)` · `divisional_facts(D9)` · `varga_ratification(D1,D9,D10)` ·
`dhana_yoga_scan(career, family=raja)` · `nakshatra_semantics` · `mechanism_read` ‖
`dasha_spine_lord_capability` · `taranga_curve(career)` · `intervention_synthesis`

CR-27 coverage: CR-27c, CR-27d.

## floor(health_deepdive)

`bhava_condition(6)` · `bhavesha_condition(6)` · `karaka_condition(mars)` · `dignity_scan` ·
`sensitive_degree_check` · `divisional_facts(D6)` · `dosha_scan` ‖
`dasha_spine_lord_capability` · `taranga_curve(health)` · `remedy_scan(health)`

CR-27 coverage: CR-27b.

## floor(marriage_deepdive)

`bhava_condition(7)` · `bhavesha_condition(7)` · `karaka_condition(venus)` ·
`divisional_facts(D9)` · `varga_ratification(D1,D9)` · `dosha_scan` · `karakamsa_read` ‖
`dasha_spine_lord_capability` · `remedy_scan(marriage)`

CR-27 coverage: CR-27b.

## floor(structure_read)

Narrow/structure depth — the "show me my D1" canonical example (design §3 §8). No
machine band (deliberate — a structure read is not a deepdive).

`positions_snapshot` · `dignity_scan` · `shadbala_rank` · `chalit_cusp_read` ·
`bhava_bala_scan`

## floor(panoramic_breadth)

The "unleash my financial potential"-shaped wide sweep — domain-agnostic breadth, not
depth.

`positions_snapshot` · `shadbala_rank` · `nakshatra_semantics` · `arudha_read` ·
`mechanism_read` ‖ `contradiction_scan` · `statistical_context` ·
`dasha_spine_lord_capability`

CR-27 coverage: CR-27a, CR-27c, CR-27d.

## floor(retrieval_only)

Minimal, single-fact-shaped question (design §3 §8 canonical example).

`positions_snapshot`

## floor(general_synthesis)

Fallback for questions that don't cleanly map to a domain deepdive.

`bhava_condition(1)` · `shadbala_rank` · `mechanism_read` ‖
`dasha_spine_lord_capability` · `contradiction_scan` · `intervention_synthesis`

CR-27 coverage: CR-27a.
