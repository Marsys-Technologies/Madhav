---
artifact: RETRIEVAL_ASTRO_COVERAGE_AND_OUTPUT_QUALITY
canonical_id: RETRIEVAL_ASTRO_COVERAGE_AND_OUTPUT_QUALITY
version: 1.0
status: DRAFT — Part A Audit 3
created: 2026-07-02
author: Claude Code (retrieval audit execution)
parent: CLAUDECODE_BRIEF_RETRIEVAL_TOOL_BLUEPRINT_AND_AUDIT v2.0 §4
source: RETRIEVAL_TO_SYNTHESIS_ANALYSIS_AND_INTERVENTION_v1_0.md PART 2 + live code analysis
---

# Retrieval Astrological Coverage & Output Quality v1.0

## §7 Verification Checklist (this document's scope: items 4–5)

| Item | Status | Evidence |
|------|--------|---------|
| §7.4 Astro-completeness: full classical-topic checklist present | ✅ PASS | §1 has 35 topics + extensions; gaps explicit in §2 |
| §7.5 Output quality: all 53 tools rated (complete/accurate/optimized) | ✅ PASS | §3 has 53-row table |
| §7.10 Frame applied (VOLUME/RELEVANCE/ACCURACY/RANKING; BULK/AGENTIC) | ✅ PASS | Used throughout §3 |
| §7.9 Judgment boundary: astrological rankings are [NATIVE-RATIFY] | ✅ PASS | Ranking weights flagged |

---

## §1 — Astrological Topic Reachability Checklist

> Key: **REACHABLE** = an LLM can retrieve this topic's meaningful content via a live MCP tool call.
> **PARTIAL** = some content reachable but incomplete or requiring workarounds.
> **NOT REACHABLE** = no MCP tool exposes this topic's content.

| # | Classical Topic | Status | Tool(s) | Gap Description |
|---|---|---|---|---|
| 1 | Graha positions (sidereal longitude, sign, nakshatra, pada, retrograde, combust) | REACHABLE | get_positions (#34), compute_natal_positions (#11) | Fully covered for natal; chart_facts graha_position categories correct |
| 2 | Graha dignities (exaltation, debilitation, own sign, friend/enemy/neutral/great-enemy) | NOT REACHABLE | — | bg_dignity_reference (151 rows of dignity definitions) has NO tool. ga_structural includes dignity computations but get_strength is not wired. `layers/L1_ganita/get_dignity.ts` exists but NO MCP bridge. |
| 3 | Shadbala — all 6 components (Sthana, Dig, Kala, Cheshta, Naisargika, Drig bala + Ishta/Kashta Phala) | NOT REACHABLE | — | ga_strength is the primary asset. `layers/L1_ganita/get_strength.ts` EXISTS but NOT wired. This is the most consequential single gap: shadbala is the raw material of ranking. |
| 4 | Ashtakavarga (Sarva-AV + Bhinna-AV, per-graha rasi-wise bindu counts) | NOT REACHABLE | — | Stored in ga_strength (fact_category: ashtakavarga). `layers/L1_ganita/get_ashtakavarga.ts` exists but NOT wired. Ironically, the signals that *do* reach the LLM are dominated by AV bindu counts from bo_laksana, but the structured AV data is unreachable. |
| 5 | Bhava bala (house strength) | NOT REACHABLE | — | ga_strength contains bhava_bala. `layers/L1_ganita/get_bhava_bala.ts` exists but NOT wired. |
| 6 | Divisional charts D1–D60 (all vargas per graha per ayanamsha) | PARTIAL | query_chart_facts (#48), holistic_bundle_chart_facts (#14) | ga_vargas has 20,877 facts. No structured varga interface (get_divisionals not wired). LLM must use raw chart_facts search with varga_position category filter. D9 and D10 used by assess_* but via "drill URI" reference, not a live tool call. |
| 7 | Planetary aspects — graha drishti (special: Mars 4th/8th, Jupiter 5th/9th, Saturn 3rd/10th) | NOT REACHABLE | — | ga_structural stores aspect firings. `layers/L1_ganita/get_aspects.ts` exists but NOT wired. |
| 8 | Rasi drishti (sign-to-sign Jaimini aspects) | NOT REACHABLE | — | Stored in ga_structural. No dedicated tool. |
| 9 | Argala (planetary interventions on houses/signs; obstructors) | NOT REACHABLE | — | `layers/L1_ganita/get_argala.ts` EXISTS but NOT wired. |
| 10 | Dispositor chains (parivartana, neecha bhanga, mutual exchange) | NOT REACHABLE | — | `layers/L1_ganita/get_dispositors.ts` EXISTS but NOT wired. Stored in ga_structural. |
| 11 | Yogas — classical combinations (Raja, Dhana, Pancha-Mahapurusha, Arishta, etc.) | PARTIAL | yoga_activation_by_dasha (#46, via bo_laksana), get_signals (#32), assess_* (#42-45) | Yogas are accessible as signals in bo_laksana (signal_type_class='yoga'). But: (a) yoga firings from ga_yoga/ga_structural not directly accessible; (b) ranking is degenerate so yogas are buried behind AV bindu counts; (c) timing via kala_activation is empty. |
| 12 | Doshas — Kuja dosha, Kala Sarpa, Graha Yuddha, combustion | PARTIAL | get_signals (#32, via bo_laksana) | Dosha signals exist in bo_laksana. `layers/L1_ganita/get_yoga_dosha.ts` exists but NOT wired directly. bg_doshas (catalog) has no tool. |
| 13 | Nakshatra substructure (lord, KP lord, pada, gandanta detection) | PARTIAL | get_positions (#34, partial), query_chart_facts (#48) | ga_nakshatra (1,802 facts) partially reachable via raw chart_facts search. `layers/L1_ganita/get_tara_chandra_bala.ts` not wired. |
| 14 | Nakshatra bala — Tara bala, Chandra bala | NOT REACHABLE | — | `layers/L1_ganita/get_tara_chandra_bala.ts` EXISTS but NOT wired. |
| 15 | Sahams (lots/Arabic parts; Tajika special points) | PARTIAL | query_chart_facts (#48), query_special_lagnas (#13, live compute) | ga_sensitive stores sahams. DB-stored sahams reachable via raw search; no structured interface. |
| 16 | Arudha padas (A1–A12) | PARTIAL | query_chart_facts (#48) | ga_sensitive stores arudhas. Raw chart_facts search only; `layers/L1_ganita/get_sensitive_points.ts` not wired. |
| 17 | Karakamsa / Swamsa | PARTIAL | query_chart_facts (#48) | Stored in ga_sensitive. Raw search only. |
| 18 | Upagrahas (Gulika, Maandi, Dhuma, Vyatipata, Parivesh, Indrachapa) | PARTIAL | get_positions (#34, upagraha_position category), query_special_lagnas (#13) | graha_position categories include upagraha_position (fact_category). Structured sub-lord (KP) not independently accessible. |
| 19 | Special lagnas (Hora, Ghati, Bhava, Sree, Varnada, etc.) | PARTIAL | query_special_lagnas (#13, live compute), query_chart_facts (#48) | Live compute via PyJHora; DB-stored in ga_sensitive. No structured special-lagna interface from DB. |
| 20 | Vimshottari dasha system (all levels: Maha, Antar, Pratyantara, Sookshma, Prana) | REACHABLE | get_dashas (#35), query_dasha_periods (#12) | ga_dashas (536,471 rows) reachable. Known issues: shadbala_null for lord condition, pre-birth dates included, pagination required at volume. |
| 21 | Other dasha systems (Yogini, Kalachakra, Narayana, Ashtottari, etc.; 17 systems in ga_dashas) | PARTIAL | get_dashas (#35) | ga_dashas stores 18 systems including non-Vimshottari. Default returns Vimshottari; other systems reachable with explicit system_id param. bg_dasha_systems (definitions catalog) has NO tool. |
| 22 | Transits (current planetary positions over natal chart) | PARTIAL | query_planet_position (#6), query_planet_transit (#7) | Current positions retrievable from ephemeris. Per-chart transit activation (ka_kalasutra) is EMPTY. Structured transit-over-natal overlap not computed. |
| 23 | Sade Sati (Saturn 7.5-year transit phases) | NOT REACHABLE | — | ga_sade_sati (11,019 facts per chart) exists. `layers/L1_ganita/get_sade_sati.ts` EXISTS but NOT wired. |
| 24 | Eclipse flags (graha within orb of Rahu/Ketu) | NOT REACHABLE | — | `layers/L1_ganita/get_eclipse_flags.ts` EXISTS but NOT wired. |
| 25 | Causal/semantic graph (CGM — cause-effect relationships) | REACHABLE | traverse_graph (#33), get_cgm_subgraph (#47) | bo_bimba (140 nodes), bo_karanajala (365 edges) well-covered. Contradiction pairs (1,034) returned raw with null resolution_hint. |
| 26 | Cross-domain linkage matrix (CDLM — how career↔character↔wealth co-activate) | PARTIAL | get_domain_reading (#31), assess_* (#42-45) | bo_sangati/bo_cdlm_summary (70 cells) partially reachable. Domain filter broken: returns chart-wide not domain-scoped. |
| 27 | Remedies (Jyotish — mantras, stones, charitable acts, timing, vastu, tantric) | REACHABLE | query_remedies (#16), query_remedies_for_chart (#17), list_remedies_by_category (#18), read_remedy (#19), query_tantric_remedies (#20), query_remedies_by_planet (#21), query_mantras (#22), get_remedies (#39) | bg_remedies well-covered (8 tools). bo_upaya chart-scoped resonances also reachable. DEGRADED: remedy scores all = 0.28 (degenerate). |
| 28 | Calibration / accuracy scoring (prediction→outcome tracking, Brier score) | PARTIAL | query_calibration (#29), record_outcome (#28) | mi_pramana partially exposed. Write path works; full Brier breakdown not queryable. |
| 29 | Medical / health indicators (6th house, health yogas, medical nakshatra) | NOT REACHABLE | — | bg_medical_mappings, bg_nakshatra_medical, ga_medical — all UNCOVERED. No MCP tool for medical domain. (assess_health (#44) exists but reads same L2 signals without medical-specific data.) |
| 30 | Vastu indicators | NOT REACHABLE | — | bg_vastu_directions, bg_vastu_direction_remedials, ga_vastu — all UNCOVERED. |
| 31 | Prashna (horary astrology) | NOT REACHABLE | — | bg_prashna_rules, ga_prashna — both UNCOVERED. |
| 32 | Tajika (Varshaphala / annual chart; Sahams, year-lords) | NOT REACHABLE | — | ga_tajaka (240 facts, year-lords) stored. `layers/L1_ganita/get_tajik.ts` EXISTS but NOT wired. |
| 33 | Temporal activation (yogas/planets live NOW via dasha+transit convergence) | NOT REACHABLE* | get_temporal_windows (#36), yoga_activation_by_dasha (#46) | *Tools exist and are wired, but kala_activation returns 0 rows for native chart — L3 not built. Structurally REACHABLE; operationally EMPTY. |
| 34 | Life Event Log (observed real-world events vs astrological windows) | REACHABLE | lel_query (#27) | mi_jivanaghatana (held-out LEL) accessible. Read path solid. |
| 35 | Cross-chart / birth-time rectification data | NOT REACHABLE | — | ph_rectification stored but NO MCP tool. |

**Astrological topic summary:**
- REACHABLE (fully): 6 (positions, dashas, classical texts, remedies, CGM graph, LEL)
- PARTIAL (accessible but degraded/incomplete): 13 (vargas, yogas, doshas, nakshatra, sahams/arudhas/sensitive, special lagnas, other dashas, transits, CDLM, calibration, upagrahas, karakamsa)
- NOT REACHABLE: 16 (dignities, shadbala, AV structured, bhava_bala, graha drishti, rasi drishti, argala, dispositors, nakshatra bala, sade_sati, eclipse flags, medical, vastu, prashna, tajika, rectification)
- OPERATIONALLY EMPTY: 1 (temporal activation — tools exist, data empty)

---

## §2 — Astrological Gap Summary

The following classical topics are NOT REACHABLE via any MCP tool, despite having data in the DB:

**Priority-1 gaps (ranking/synthesis blockers):**
1. **Shadbala** (ga_strength) — the primary strength metric; without it the LLM cannot weigh planetary capacity. All 6 shadbala components + Ishta/Kashta phala unavailable. `layers/L1_ganita/get_strength.ts` not wired.
2. **Graha dignities** (bg_dignity_reference + ga_structural dignity computations) — the qualitative strength layer. `layers/L1_ganita/get_dignity.ts` not wired.
3. **Graha aspects** (ga_structural aspect_firing records) — the relational structure. `layers/L1_ganita/get_aspects.ts` not wired.
4. **Argala** (ga_structural argala records) — the intervention structure. `layers/L1_ganita/get_argala.ts` not wired.
5. **Temporal activation** (ka_kalasutra) — L3 is empty for native chart.

**Priority-2 gaps (topic completeness):**
6. Sade Sati (ga_sade_sati) — `get_sade_sati.ts` not wired.
7. Tajika/Varshaphala (ga_tajaka) — `get_tajik.ts` not wired.
8. Dispositor chains (ga_structural) — `get_dispositors.ts` not wired.
9. Nakshatra Tara/Chandra bala — `get_tara_chandra_bala.ts` not wired.
10. Eclipse flags — `get_eclipse_flags.ts` not wired.

**Priority-3 gaps (domain completeness):**
11. Medical indicators (bg_medical_mappings, ga_medical) — no tools at all.
12. Vastu (bg_vastu_directions, ga_vastu) — no tools at all.
13. Prashna/horary (bg_prashna_rules, ga_prashna) — no tools at all.
14. Rectification data (ph_rectification) — no tool.
15. Insight surface (mi_darshana) — no tool; the synthesis endpoint is dark.

---

## §3 — Per-Tool Output Quality Ratings (all 53 tools)

Rating dimensions:
- **C (COMPLETE):** Are all promised fields populated? No deferred/empty fields?
- **A (ACCURATE):** Astrologically correct? Correct table joins? Fact_ids resolve?
- **O (OPTIMIZED):** Bounded? Ranked by astrological significance? Structured by reasoning chain? UUIDs resolved?

`✅` = satisfactory | `⚠️` = partial issue | `❌` = significant defect

| # | Tool | C | A | O | Key Defect | File:Line |
|---|---|---|---|---|---|---|
| 1 | resolve_entity | ✅ | ✅ | ✅ | None. Canonical entity resolution works. | `tools/l0_brahmagyan.ts:49` |
| 2 | list_entities | ✅ | ✅ | ⚠️ | No pagination boundary documented; large entity list potentially unbounded. | `tools/l0_brahmagyan.ts:99` |
| 3 | asset_registry_all | ✅ | ✅ | ✅ | Complete asset catalog returned. | `layers/L0_brahmagyan/asset_registry_all.ts:40` |
| 4 | asset_registry_l0 | ✅ | ✅ | ✅ | L0-scoped asset catalog returned. | `tools/l0_brahmagyan.ts:169` |
| 5 | intent_classify | ✅ | ⚠️ | ⚠️ | ACCURATE: uses bg_rules but classification quality not independently tested. OPTIMIZED: returns intent label only, no confidence score or alternative intents. | `tools/l0_brahmagyan.ts:222` |
| 6 | query_planet_position | ✅ | ✅ | ✅ | Correct ephemeris_daily data. Sidereal offset documented in description (`tools/l0_ephemeris.ts:61-63`). | `tools/l0_ephemeris.ts:59` |
| 7 | query_planet_transit | ✅ | ✅ | ✅ | Transit window query correct. Not chart-specific (no natal overlay). | `tools/l0_ephemeris.ts:97` |
| 8 | query_aspects_at_time | ✅ | ✅ | ⚠️ | Correct instantaneous aspects. OPTIMIZED: flat list, no aspect-strength ranking. | `tools/l0_ephemeris.ts:137` |
| 9 | query_retrograde_periods | ✅ | ✅ | ✅ | Retrograde windows correct and bounded. | `tools/l0_ephemeris.ts:177` |
| 10 | ephemeris_cache_year | ✅ | ✅ | ⚠️ | OPTIMIZED: year slice is large; no per-planet or per-period structure. VOLUME concern for bulk mode. | `tools/l0_ephemeris.ts:215` |
| 11 | compute_natal_positions | ✅ | ✅ | ⚠️ | ACCURATE: PyJHora natal correct (matches FORENSIC 7/7 anchors). OPTIMIZED: live computation; cannot be cached (returns identical result to get_positions for same chart). Redundant with DB path. | `tools/retrieval/pyhora_natal.ts:69` |
| 12 | query_dasha_periods | ✅ | ⚠️ | ⚠️ | ACCURATE: Vimshottari correct. KNOWN ISSUES: shadbala_null for lord condition. OPTIMIZED: live compute, large output; no pagination. | `tools/retrieval/pyhora_natal.ts:122` |
| 13 | query_special_lagnas | ✅ | ✅ | ⚠️ | ACCURATE: PyJHora upagrahas correct. OPTIMIZED: flat list; no astrological significance ordering. | `tools/retrieval/pyhora_natal.ts:178` |
| 14 | holistic_bundle_chart_facts | ⚠️ | ✅ | ⚠️ | COMPLETE: categories filtered by bundle config — not all 85 asset categories included. OPTIMIZED: bundle is large; no signification annotation; RANKING flat. | `tools/retrieval/holistic_bundle.ts:51` |
| 15 | kala_temporal_bundle | ❌ | ❌ | ❌ | **EMPTY:** kala_activation = 0 rows for native chart. L3 not built. Returns structurally correct envelope with 0 meaningful content. ALL dimensions fail when data is absent. | `tools/retrieval/kala_temporal.ts:408`; `layers/L3_kala/query_temporal_activation.ts:5-6` |
| 16 | query_remedies | ✅ | ✅ | ⚠️ | COMPLETE: correct remedy corpus. OPTIMIZED: no chart-relevance ranking at global level. | `tools/retrieval/remedy_tools.ts:28` |
| 17 | query_remedies_for_chart | ✅ | ❌ | ❌ | COMPLETE: resonance rows returned. ACCURATE: **scores all = 0.28 (degenerate constant)** — chart-specific resonance scoring is broken; all remedies appear equally relevant. RANKING: meaningless. | `tools/retrieval/remedy_tools.ts:55` |
| 18 | list_remedies_by_category | ✅ | ✅ | ⚠️ | OPTIMIZED: flat categorical list; no efficacy or chart-relevance ranking. | `tools/retrieval/remedy_tools.ts:80` |
| 19 | read_remedy | ✅ | ✅ | ✅ | Single-remedy fetch correct. | `tools/retrieval/remedy_tools.ts:107` |
| 20 | query_tantric_remedies | ✅ | ✅ | ⚠️ | OPTIMIZED: tantric-category subset; no chart-scoring. | `tools/retrieval/remedy_tools.ts:131` |
| 21 | query_remedies_by_planet | ✅ | ✅ | ⚠️ | OPTIMIZED: planet-filtered; no chart-relevance scoring. | `tools/retrieval/remedy_tools.ts:156` |
| 22 | query_mantras | ✅ | ✅ | ⚠️ | OPTIMIZED: mantra subset; no planet-strength or dasha weighting. | `tools/retrieval/remedy_tools.ts:181` |
| 23 | event_anchors | ✅ | ✅ | ✅ | COMPLETE: event anchors with falsifiers populated. OPTIMIZED: bounded. | `tools/phala_event_anchors.ts:234` |
| 24 | mitigation_map | ✅ | ✅ | ✅ | COMPLETE: mitigation map correct. | `tools/phala_mitigation_map.ts:240` |
| 25 | muhurta_finder | ✅ | ✅ | ✅ | COMPLETE: muhurta windows with auspiciousness scores. | `tools/muhurta_finder.ts:301` |
| 26 | phala_outlook | ✅ | ✅ | ⚠️ | COMPLETE: composite L4 bundle. OPTIMIZED: VOLUME may be large (4 L4 assets combined); no cross-domain ranking. | `tools/phala_outlook.ts:206` |
| 27 | lel_query | ✅ | ✅ | ⚠️ | COMPLETE: LEL events correct. OPTIMIZED: chronological only; no astrological-relevance scoring of events. | `tools/mimamsa_lel_intake.ts:91` |
| 28 | record_outcome | ✅ | ✅ | ✅ | Write path: correctly records prediction outcome. | `tools/mimamsa_outcome.ts:229` |
| 29 | query_calibration | ✅ | ✅ | ⚠️ | OPTIMIZED: calibration scores readable but mi_pramana full Brier decomposition not exposed. | `tools/mimamsa_outcome.ts:348` |
| 30 | get_chart_orientation | ✅ | ✅ | ✅ | UCD holistic portrait returned correctly. Bounded. | `tools/registry_bridge.ts:252` |
| 31 | get_domain_reading | ⚠️ | ❌ | ❌ | COMPLETE: fields populated but domain-wrong content returned. ACCURATE: **bodha_question_lenses has no domain column** (`layers/L2_bodha/query_domain_reading.ts:189,205`) — career query returns progeny lens. RELEVANCE BROKEN. RANKING: flat. | `tools/registry_bridge.ts:306`; `layers/L2_bodha/query_domain_reading.ts:189` |
| 32 | get_signals | ⚠️ | ⚠️ | ❌ | COMPLETE: bodha_msr_signals rows returned. ACCURATE: DEFECT-001 — constituent_facts_array orphans at ~91.5%. **RANKING CRUX:** computed_salience collapses to ~3 constants (0.58/1.16/2.33); `signature_tier` = 100% "background". Top signals = AV bindu counts, ZERO yogas. VOLUME: unbounded by default. | `tools/registry_bridge.ts:401`; `layers/L2_bodha/query_signals.ts:192` |
| 33 | traverse_graph | ✅ | ✅ | ✅ | CGM graph traversal correct; bounded. Contradiction UUIDs present (resolution_hint null but this is a known data state). | `tools/registry_bridge.ts:436` |
| 34 | get_positions | ✅ | ✅ | ⚠️ | COMPLETE: position categories correct. OPTIMIZED: flat rows, no dignity/strength annotation inline; RANKING requires separate get_strength call (which is not wired). | `tools/registry_bridge.ts:467`; `layers/L1_ganita/get_positions.ts:60` |
| 35 | get_dashas | ⚠️ | ⚠️ | ⚠️ | COMPLETE: 536,471 rows (must paginate). ACCURATE: KNOWN ISSUES: (a) shadbala_null for lord natal condition; (b) pre-birth periods included without birth-date filter; (c) default system = Vimshottari only. OPTIMIZED: pagination required; no dasha-strength ranking. | `tools/registry_bridge.ts:491`; `layers/L1_ganita/get_dashas.ts` |
| 36 | get_temporal_windows | ❌ | ❌ | ❌ | **OPERATIONALLY EMPTY:** kala_activation = 0 rows for native chart. Tool is structurally correct (`layers/L3_kala/query_temporal_activation.ts:137`) but L3 has not been built. Returns empty result. | `tools/registry_bridge.ts:530`; `layers/L3_kala/query_temporal_activation.ts:5-6` |
| 37 | get_projections | ✅ | ✅ | ⚠️ | COMPLETE: kala_projections returned. OPTIMIZED: no probability-weighted ordering documented. | `tools/registry_bridge.ts:559` |
| 38 | get_classical_citation | ✅ | ✅ | ✅ | bg_texts search + concordance supplement. Chunked + embedded. Bounded. | `tools/registry_bridge.ts:602` |
| 39 | get_remedies | ✅ | ❌ | ❌ | COMPLETE: bo_upaya resonances returned. ACCURATE: **scores all = 0.28 (degenerate)** — same defect as #17. RANKING: meaningless. | `tools/registry_bridge.ts:625` |
| 40 | get_chart_quality | ✅ | ✅ | ✅ | Synthesis scorecard (bo_pramana_mapa) returned correctly. Bounded. | `tools/registry_bridge.ts:651` |
| 41 | list_assets | ✅ | ✅ | ✅ | Complete asset registry catalog. | `tools/registry_bridge.ts:676` |
| 42 | assess_marriage | ❌ | ❌ | ❌ | **DOES NOT SYNTHESIZE.** COMPLETE: activating_dasha EMPTY (kala_activation = 0). Contradictions = raw UUID pairs, resolution_hint null. Citations DEFERRED. ACCURATE: domain filter broken (progeny lens in marriage query — `register_d8_assess_domain.ts:176`). VOLUME: unbounded. RANKING: 93.8% raw signal rows at degenerate salience. | `tools/registry_bridge.ts:703`; `layers/register_d8_assess_domain.ts:151,176,292` |
| 43 | assess_career | ❌ | ❌ | ❌ | Same as assess_marriage. Career-specific: D10 referenced as drill URI but not returned inline. `register_d8_assess_domain.ts:338` "Career domain synthesis reconciles 10th lord + Saturn... require acharya review of assembled bundle." VOLUME: 6.2MB measured. | `tools/registry_bridge.ts:727`; `layers/register_d8_assess_domain.ts:313,338,355` |
| 44 | assess_health | ❌ | ❌ | ❌ | Same structural issues. Health: 1st/6th/8th lords referenced via chart_facts drill. bg_medical_mappings not included. VOLUME: unbounded. | `tools/registry_bridge.ts:751`; `layers/register_d8_assess_domain.ts:376,418` |
| 45 | assess_wealth | ❌ | ❌ | ❌ | Same structural issues. Wealth: 2nd/11th lords + Jupiter kāraka via chart_facts drill. VOLUME: unbounded. | `tools/registry_bridge.ts:775`; `layers/register_d8_assess_domain.ts:463,480` |
| 46 | yoga_activation_by_dasha | ❌ | ❌ | ❌ | **OPERATIONALLY EMPTY:** kala_activation = 0 rows — JOIN bodha_msr_signals × kala_activation returns 0 activated yogas for native chart. `register_d8_assess_domain.ts:628-629`: `FROM bodha_msr_signals m JOIN kala_activation ka ON ka.signal_id = m.signal_id`. No results until L3 is built. | `tools/registry_bridge.ts:799`; `layers/register_d8_assess_domain.ts:628-629` |
| 47 | get_cgm_subgraph | ✅ | ✅ | ⚠️ | COMPLETE: CGM nodes+edges+paths+motifs returned. OPTIMIZED: "convergence" mode = 53KB. ACCURATE: 1,034 contradictions returned (resolution_hint null — correct as-is since contradictions are a computed output not a content error). | `tools/registry_bridge.ts:839` |
| 48 | query_chart_facts | ✅ | ✅ | ⚠️ | COMPLETE: general chart_facts search works. OPTIMIZED: requires LLM to know fact_category values; no structured guidance for astrological use; flat rows without significance annotation. Powerful but requires expert usage. | `tools/registry_bridge.ts:883` |
| 49 | vector_search | ✅ | ⚠️ | ⚠️ | COMPLETE: bo_samskara embeddings searched. ACCURATE: semantic relevance untested at astrological quality. OPTIMIZED: similarity scores returned but not cross-validated against astrological correctness. | `tools/registry_bridge.ts:934` |
| 50 | list_my_charts | ✅ | ✅ | ✅ | Navigation tool; correct. | `tools/chart_selection.ts:107` |
| 51 | select_chart | ✅ | ✅ | ✅ | Chart validation + chart_id resolution correct. | `tools/chart_selection.ts:169` |
| 52 | recall_session | ✅ | ✅ | ✅ | Session recall with entitlement re-check. | `tools/session_tools.ts:42` |
| 53 | list_my_sessions | ✅ | ✅ | ✅ | Session history correct. | `tools/session_tools.ts:125` |

**Tool count: 53 ✓**

---

## §4 — Priority Defect List (Top 10 by impact on LLM synthesis quality)

Ranked by: (astrological cost to the LLM's ability to synthesize acharya-grade insight) × (number of tools affected). Frame: BULK and AGENTIC-LOOP impact.

| Priority | Defect | Tools Affected | BULK Impact | AGENTIC Impact | Root Location |
|---|---|---|---|---|---|
| P1 ★★★★ | **Salience degeneracy / ranking collapse** — computed_salience collapses to 3 constants; top signals = AV bindu counts; ZERO yogas/raja-yogas surface; signature_tier unused. | #32, #42-45 | FATAL — model receives equal-weighted data, cannot find what matters | FATAL — cannot decide what to drill | `layers/L2_bodha/query_signals.ts`; bo_laksana signal computation |
| P2 ★★★★ | **ga_strength / shadbala completely unreachable** — 18 L1 registry capabilities not wired as MCP tools; shadbala (the primary planet-strength metric) invisible. | 0 tools cover it | FATAL — cannot weigh planetary capacity | FATAL — cannot assess planet power in any drill | `layers/L1_ganita/get_strength.ts` (not wired) |
| P3 ★★★★ | **kala_activation EMPTY** — L3 not built for native chart; all timing, yoga-ripening, dasha windows return 0. | #15, #36, #46, #42-45 | SEVERE — timing dimension absent | FATAL — timing queries waste loop steps | kala_activation table (build gap) |
| P4 ★★★★ | **assess_* do not synthesize** — 6.2MB ingredient dump; activating_dasha=0; contradictions raw UUID pairs; citations deferred; no prose verdict. | #42-45 | SEVERE — must reconstruct reading from raw rows | SEVERE — no verdict to anchor drilling | `layers/register_d8_assess_domain.ts` |
| P5 ★★★ | **Domain filter inert** — bodha_question_lenses has no domain column; career query returns progeny lens. | #31, #42-45 | HIGH — off-topic content dilutes all domain readings | HIGH — wastes drill steps on wrong lenses | `layers/L2_bodha/query_domain_reading.ts:189` |
| P6 ★★★ | **DEFECT-001: constituent_facts_array orphan rate ~91.5%** — machine grounding broken; fact_ids in bo_laksana don't resolve to chart_facts. | #32, #39, #42-45 | HIGH — claims unverifiable at volume | HIGH — drill-to-fact returns empty | `layers/L2_bodha/query_signals.ts` |
| P7 ★★★ | **Unbounded payloads** — assess_career=6.2MB (~1.5M tokens); get_positions=63KB; get_cgm_subgraph "convergence"=53KB. | #32, #42-45, #47 | SEVERE — overflows 1M context | FATAL — blows loop's per-call budget | `tools/registry_bridge.ts` (missing caps) |
| P8 ★★★ | **Remedy scores degenerate (all = 0.28)** — bo_upaya resonance scoring broken; all remedies appear equally relevant. | #17, #39 | HIGH — LLM cannot differentiate which remedies apply | MED — drill-to-remedy returns meaningless ranking | `layers/L2_bodha/query_remedies.ts` |
| P9 ★★ | **ga_structural / aspects / argala / dispositors completely unreachable** — the relational structure of the chart (77,821 facts) invisible. | 0 tools cover it | HIGH — LLM cannot assess relational structure | HIGH — no drill path for aspects/argala | `layers/L1_ganita/get_aspects.ts`, `get_argala.ts`, `get_dispositors.ts` (not wired) |
| P10 ★★ | **get_dashas known issues** — shadbala_null on lord condition; pre-birth periods included; 17 non-Vimshottari systems inaccessible by default. | #35, #12 | MED — dasha chain has gaps | MED — lord condition queries fail on null | `layers/L1_ganita/get_dashas.ts` |

---

## §5 — The Positives to Preserve

These aspects are working well and must not be regressed by any intervention:

1. **Entitlement + session + auth architecture** — M0-M8 stack (entitlement gate, chart-by-name, OAuth, MARO surface spec, rate limiting) is solid and correctly implemented. Source: `tools/auth.ts`, `server.ts:204`.
2. **Ephemeris + natal computation correctness** — ephemeris_daily (1900-2150) is correct; PyJHora natal matches FORENSIC 7/7 anchors (Sun=Capricorn, Moon=PB, Lagna=Aries). Source: `tools/retrieval/pyhora_natal.ts`.
3. **Tool DESCRIPTIONS are acharya-literate** — the D7/D8 tool descriptions promise the right astrological framing (10th lord + Saturn kāraka + D10 + yoga detection + activating dasha). The INTENT is correct. Source: `tools/registry_bridge.ts:306-320`.
4. **Provenance envelopes + self-reporting** — tools return `provenance.tables` arrays, `judgment_flags`, and honest self-reporting ("assembled bundle", "acharya review required"). Source: `layers/register_d8_assess_domain.ts:292,355,418,480`.
5. **Registry architecture (single-source)** — both MCP and chat channels call the same `CapabilityDescriptor.handler`; drift between channels is structurally impossible. Source: `tools/registry_bridge.ts:1-36`.
6. **L4 Phala tools are clean** — event_anchors, mitigation_map, muhurta_finder all return correct, bounded, well-structured output. The L4 layer is the best-performing layer on quality metrics.

*End of RETRIEVAL_ASTRO_COVERAGE_AND_OUTPUT_QUALITY v1.0 — Part A Audit 3.*
